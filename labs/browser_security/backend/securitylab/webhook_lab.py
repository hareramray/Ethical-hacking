"""Signed, server-owned deliveries updating disposable SQLite point ledgers."""
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
from contextlib import closing

from django.http import JsonResponse

PROVIDER = "fixture-provider"
ACCOUNT = "DEMO_ACCOUNT"
WINDOW_SECONDS = 300
SIGNING_FORMAT = "HMAC-SHA256(secret, ASCII(timestamp) + b'.' + raw_body)"
FIXTURES = {
    "normal": {"label": "Control: one valid event", "expectation": "Both handlers credit 10 synthetic points for a fresh, correctly signed event."},
    "body-tampered": {"label": "Body changed after signing", "expectation": "Both handlers reject the invalid signature and leave the balance at zero."},
    "stale": {"label": "Valid signature, old timestamp", "expectation": "Signature-only processing credits 10 points. The fixed handler rejects the old delivery before recording its event ID."},
    "duplicate": {"label": "Replay the identical delivery", "expectation": "Signature-only processing credits 20 points. The fixed handler applies the event once and acknowledges the duplicate without another credit."},
    "resigned-retry": {"label": "Fresh signature, same event ID", "expectation": "A new delivery signature does not create a new business event. The fixed handler still credits only 10 points."},
    "distinct-events": {"label": "Control: two distinct valid events", "expectation": "Both handlers credit 20 points. Deduplication permits a genuinely different valid event."},
    "future": {"label": "Valid signature, future timestamp", "expectation": "Signature-only processing credits 10 points. The fixed handler rejects a timestamp beyond its clock-skew allowance."},
    "invalid-schema": {"label": "Valid signature, invalid event data", "expectation": "Both handlers reject an unsupported account. A valid signature alone does not make business data valid."},
}
WEBHOOK_METADATA = {"fixtures": [{"id": key, **value} for key, value in FIXTURES.items()],
                    "windowSeconds": WINDOW_SECONDS, "signingFormat": SIGNING_FORMAT}


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON field")
        value[key] = item
    return value


def sign_delivery(secret, timestamp, raw_body):
    message = str(timestamp).encode("ascii") + b"." + raw_body
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def verify_signature(secret, delivery):
    timestamp, signature = delivery["timestamp"], delivery["signature"]
    if type(timestamp) is not int or timestamp < 0 or not isinstance(signature, str):
        return False
    if not re.fullmatch(r"[0-9a-f]{64}", signature):
        return False
    expected = sign_delivery(secret, timestamp, delivery["rawBody"])
    return hmac.compare_digest(expected, signature)


def event_body(event_id="evt_demo_1", account=ACCOUNT):
    return json.dumps({"id": event_id, "type": "points.credit", "account": account, "units": 10},
                      separators=(",", ":")).encode("utf-8")


def signed_delivery(secret, timestamp, raw_body):
    return {"timestamp": timestamp, "rawBody": raw_body,
            "signature": sign_delivery(secret, timestamp, raw_body)}


def fixture_deliveries(fixture, secret, now):
    timestamp = now - 10
    if fixture == "stale":
        timestamp = now - WINDOW_SECONDS - 1
    elif fixture == "future":
        timestamp = now + WINDOW_SECONDS + 1
    raw_body = event_body(account="UNSUPPORTED_ACCOUNT") if fixture == "invalid-schema" else event_body()
    first = signed_delivery(secret, timestamp, raw_body)
    if fixture == "body-tampered":
        first = {**first, "rawBody": raw_body.replace(b'"units":10', b'"units":20')}
    if fixture == "duplicate":
        return [first, first.copy()]
    if fixture == "resigned-retry":
        return [first, signed_delivery(secret, now - 5, raw_body)]
    if fixture == "distinct-events":
        return [first, signed_delivery(secret, now - 5, event_body("evt_demo_2"))]
    return [first]


def parse_event(raw_body):
    if len(raw_body) > 1024:
        raise ValueError("Event body exceeds the lesson limit.")
    event = json.loads(raw_body, object_pairs_hook=unique_object)
    if not isinstance(event, dict) or set(event) != {"id", "type", "account", "units"}:
        raise ValueError("Event fields do not match the lesson schema.")
    if not isinstance(event["id"], str) or not re.fullmatch(r"evt_[A-Za-z0-9_]{1,48}", event["id"]):
        raise ValueError("Invalid event identifier.")
    if event["type"] != "points.credit" or event["account"] != ACCOUNT:
        raise ValueError("Unsupported event type or account.")
    if type(event["units"]) is not int or not 1 <= event["units"] <= 100:
        raise ValueError("Points must be an integer from 1 to 100.")
    return event


def create_store():
    connection = sqlite3.connect(":memory:", isolation_level=None)
    connection.executescript(
        "CREATE TABLE ledger (id INTEGER PRIMARY KEY CHECK (id = 1), balance INTEGER NOT NULL);"
        "INSERT INTO ledger VALUES (1, 0);"
        "CREATE TABLE processed_events (provider TEXT NOT NULL, event_id TEXT NOT NULL, "
        "PRIMARY KEY (provider, event_id));"
    )
    return connection


def read_balance(connection):
    return connection.execute("SELECT balance FROM ledger WHERE id = 1").fetchone()[0]


def apply_event(connection, event, mode, provider=PROVIDER):
    """The event claim and ledger write share one transaction in the fixed path."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        if mode == "fixed":
            changed = connection.execute(
                "INSERT INTO processed_events (provider, event_id) VALUES (?, ?) "
                "ON CONFLICT (provider, event_id) DO NOTHING", (provider, event["id"])
            ).rowcount
            if changed == 0:
                connection.rollback()
                return "duplicate"
        connection.execute("UPDATE ledger SET balance = balance + ? WHERE id = 1", (event["units"],))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return "applied"


def receive_delivery(connection, mode, delivery, secret, now):
    before = read_balance(connection)
    result = {"eventId": None, "timestamp": delivery["timestamp"],
              "rawBody": delivery["rawBody"].decode("utf-8"), "signature": delivery["signature"],
              "signatureValid": False, "outcome": "rejected", "reason": "",
              "balanceBefore": before, "balanceAfter": before, "sideEffect": 0}
    # Authenticate exact bytes before parsing data or consulting event IDs.
    if not verify_signature(secret, delivery):
        result["reason"] = "The signature does not authenticate these exact body bytes and timestamp."
        return result
    result["signatureValid"] = True
    if mode == "fixed" and abs(now - delivery["timestamp"]) > WINDOW_SECONDS:
        result["reason"] = "The signed timestamp is outside the 300-second past/future allowance. No event ID was recorded."
        return result
    try:
        event = parse_event(delivery["rawBody"])
    except (ValueError, UnicodeDecodeError, RecursionError):
        result["reason"] = "The authenticated event fails the allowed event type, account, or data schema. No event ID was recorded."
        return result
    result["eventId"] = event["id"]
    outcome = apply_event(connection, event, mode)
    result["outcome"] = outcome
    result["balanceAfter"] = read_balance(connection)
    result["sideEffect"] = result["balanceAfter"] - before
    result["reason"] = (
        "This provider/event ID was already committed. Acknowledge the duplicate without repeating the credit."
        if outcome == "duplicate" else
        "The event ID and credit committed in one SQLite transaction."
        if mode == "fixed" else
        "The signature and event schema passed. This handler skips freshness and event-ID deduplication."
    )
    return result


def compare_fixture(fixture):
    now = int(time.time())
    secret = secrets.token_bytes(32)
    deliveries = fixture_deliveries(fixture, secret, now)
    results = {}
    for mode in ("vulnerable", "fixed"):
        with closing(create_store()) as connection:
            receipts = [{"number": index, **receive_delivery(connection, mode, delivery, secret, now)}
                        for index, delivery in enumerate(deliveries, start=1)]
            results[mode] = {
                "outcome": "processed" if any(receipt["sideEffect"] for receipt in receipts) else "blocked",
                "balanceBefore": 0, "balanceAfter": read_balance(connection), "deliveries": receipts,
                "processedEventIds": [row[0] for row in connection.execute(
                    "SELECT event_id FROM processed_events WHERE provider = ? ORDER BY event_id", (PROVIDER,))],
                "reason": "Both handlers validate the signature and event schema. " + (
                    "This handler omits delivery freshness and event-ID deduplication."
                    if mode == "vulnerable" else
                    "This handler also checks delivery freshness and atomically claims each provider/event ID with its ledger write."),
            }
    return {"fixture": fixture, "expectation": FIXTURES[fixture]["expectation"], "clock": now,
            "windowSeconds": WINDOW_SECONDS, "signingFormat": SIGNING_FORMAT, "results": results}


def webhook_compare(request):
    """Browser harness protected by CSRF; this is not a public webhook receiver."""
    def invalid(reason, status=400):
        return JsonResponse({"error": reason}, status=status)

    if request.method != "POST":
        response = invalid("Use POST with a JSON fixture identifier.", 405)
        response["Allow"] = "POST"
        return response
    if request.GET or request.content_type != "application/json":
        return invalid("Use application/json without query parameters.")
    if len(request.body) > 2048:
        return invalid("The fixture request is too large.")
    try:
        body = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return invalid("Invalid JSON or duplicate fields.")
    if not isinstance(body, dict) or set(body) != {"fixture"}:
        return invalid("Provide exactly fixture; event bodies, secrets, and URLs are not accepted.")
    if not isinstance(body["fixture"], str) or body["fixture"] not in FIXTURES:
        return invalid("Choose a listed webhook fixture.")
    try:
        return JsonResponse(compare_fixture(body["fixture"]))
    except sqlite3.Error:
        return invalid("The disposable ledger could not finish. Try the comparison again.", 503)
