"""Disposable coupon fixtures demonstrating a check-then-act race and its repair."""
import json
import sqlite3
import tempfile
import threading
import time
from contextlib import closing
from pathlib import Path

from django.http import JsonResponse

from .sql_lab import unique_object

REWARD_UNITS = 10
SQL_TIMEOUT = 0.5
BARRIER_TIMEOUT = 2.0
WORKER_TIMEOUT = 4.0
ACTIVE_COMPARISONS = threading.BoundedSemaphore(4)
LOGIC_METADATA = {
    "scenarios": [
        {"id": "single", "label": "One legitimate redemption", "description": "One attempt should credit exactly 10 synthetic points in both handlers."},
        {"id": "sequential", "label": "Replay after the first attempt finishes", "description": "Two sequential attempts should still credit only 10 points."},
        {"id": "concurrent", "label": "Two overlapping attempts", "description": "A scheduling barrier exposes the gap between checking and consuming a single-use coupon."},
    ],
    "rewardUnits": REWARD_UNITS,
    "maximumAttempts": 2,
}


def connection_to(path):
    return sqlite3.connect(path, timeout=SQL_TIMEOUT, isolation_level=None)


def create_store(path):
    with closing(connection_to(path)) as connection:
        connection.executescript(
            "CREATE TABLE coupons (id TEXT PRIMARY KEY, used INTEGER NOT NULL CHECK (used IN (0, 1)));"
            "CREATE TABLE credits (attempt_id INTEGER PRIMARY KEY, units INTEGER NOT NULL CHECK (units = 10));"
            "INSERT INTO coupons VALUES ('DEMO_ONCE', 0);"
        )


def redeem(path, mode, attempt_id, gate=None, stop=None):
    """Only fixed SQL and two synthetic attempt IDs enter these connections."""
    with closing(connection_to(path)) as connection:
        if mode == "vulnerable":
            # This check ends before the write transaction starts. Both workers
            # can therefore observe used=0 before either changes it.
            available = connection.execute("SELECT used FROM coupons WHERE id = ?", ("DEMO_ONCE",)).fetchone()[0] == 0
            if gate is not None:
                gate.wait(timeout=BARRIER_TIMEOUT)
            if stop is not None and stop.is_set():
                raise RuntimeError("Comparison cancelled.")
            if not available:
                return {"attemptId": attempt_id, "outcome": "already_used", "rewardUnits": 0}
        elif gate is not None:
            # Align the fixed attempts before the transaction, without placing
            # a barrier inside a transaction while holding a write lock.
            gate.wait(timeout=BARRIER_TIMEOUT)
        if stop is not None and stop.is_set():
            raise RuntimeError("Comparison cancelled.")
        connection.execute("BEGIN IMMEDIATE")
        try:
            if mode == "fixed":
                changed = connection.execute(
                    "UPDATE coupons SET used = 1 WHERE id = ? AND used = 0", ("DEMO_ONCE",)
                ).rowcount
                if changed != 1:
                    connection.rollback()
                    return {"attemptId": attempt_id, "outcome": "already_used", "rewardUnits": 0}
            else:
                # Serializing writes alone cannot repair the stale decision.
                connection.execute("UPDATE coupons SET used = 1 WHERE id = ?", ("DEMO_ONCE",))
            connection.execute("INSERT INTO credits (attempt_id, units) VALUES (?, ?)", (attempt_id, REWARD_UNITS))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    return {"attemptId": attempt_id, "outcome": "redeemed", "rewardUnits": REWARD_UNITS}


def overlapping_attempts(path, mode):
    """Exactly two workers, a bounded rendezvous, and bounded database lock waits."""
    gate = threading.Barrier(2)
    stop = threading.Event()
    outcomes = [None, None]
    failures = [None, None]

    def worker(index):
        try:
            outcomes[index] = redeem(path, mode, index + 1, gate, stop)
        except Exception as exc:
            failures[index] = exc
            stop.set()
            gate.abort()

    workers = [threading.Thread(target=worker, args=(index,), name=f"coupon-fixture-{mode}-{index + 1}", daemon=True)
               for index in range(2)]
    started = []
    try:
        for worker_thread in workers:
            worker_thread.start()
            started.append(worker_thread)
        deadline = time.monotonic() + WORKER_TIMEOUT
        for worker_thread in started:
            worker_thread.join(timeout=max(0, deadline - time.monotonic()))
        if any(worker_thread.is_alive() for worker_thread in started):
            raise RuntimeError("The fixture workers exceeded their deadline.")
        if any(failures):
            raise RuntimeError("A fixture worker could not complete.") from next(failure for failure in failures if failure)
        return outcomes
    finally:
        stop.set()
        gate.abort()
        # A failed thread start or rendezvous releases its peer. The workers do
        # no network I/O and SQLite lock waits are limited to SQL_TIMEOUT.
        for worker_thread in started:
            if worker_thread.is_alive():
                worker_thread.join(timeout=BARRIER_TIMEOUT + SQL_TIMEOUT + 0.5)


def run_fixture(scenario, mode):
    with tempfile.TemporaryDirectory(prefix="coupon-fixture-") as directory:
        path = Path(directory) / "coupon.sqlite3"
        create_store(path)
        if scenario == "concurrent":
            attempts = overlapping_attempts(path, mode)
        else:
            count = 1 if scenario == "single" else 2
            attempts = [redeem(path, mode, index + 1) for index in range(count)]
        # Read committed evidence from the ledger, independently of response
        # counters. A boolean used flag alone would hide the duplicate credit.
        with closing(connection_to(path)) as connection:
            redemptions, reward_units = connection.execute("SELECT COUNT(*), COALESCE(SUM(units), 0) FROM credits").fetchone()
            used = connection.execute("SELECT used FROM coupons WHERE id = ?", ("DEMO_ONCE",)).fetchone()[0]
        return {"mode": mode, "attempts": attempts, "redemptions": redemptions,
                "rewardUnits": reward_units, "couponUsed": bool(used)}


def logic_compare(request):
    def error(reason, status=400, outcome="invalid"):
        return JsonResponse({"outcome": outcome, "reason": reason, "results": {}}, status=status)

    if request.method != "POST":
        response = error("Use POST with an application/json body.", 405)
        response["Allow"] = "POST"
        return response
    if request.GET or request.content_type != "application/json":
        return error("Use an application/json body without query parameters.")
    if len(request.body) > 1024:
        return error("The fixture request is too large.")
    try:
        data = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError):
        return error("Invalid JSON or duplicate fields.")
    if not isinstance(data, dict) or set(data) != {"scenario"}:
        return error("Provide exactly scenario.")
    scenario = data["scenario"]
    if not isinstance(scenario, str) or scenario not in {"single", "sequential", "concurrent"}:
        return error("Choose single, sequential, or concurrent.")
    if not ACTIVE_COMPARISONS.acquire(blocking=False):
        return error("The local fixture is busy. Retry when another comparison finishes.", 503, "unavailable")
    try:
        results = {mode: run_fixture(scenario, mode) for mode in ("vulnerable", "fixed")}
        return JsonResponse({"scenario": scenario, "outcome": "compared", "rewardUnits": REWARD_UNITS,
                             "schedulingFixture": scenario == "concurrent", "results": results})
    except (sqlite3.Error, OSError, RuntimeError):
        return error("The bounded fixture could not finish. No comparison result is available; try again.", 503, "unavailable")
    finally:
        ACTIVE_COMPARISONS.release()
