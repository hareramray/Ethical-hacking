"""Execute bounded authentication flows in disposable, synthetic token stores.

This is a handler harness, not Django's login/session-cookie implementation.
"""
import json
import secrets
from threading import BoundedSemaphore

from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse

FIXTURE_PASSWORD = "Public-Lab-Password-1!"
NEW_PASSWORD = "Public-Lab-Password-2!"
REPLAY_PASSWORD = "Public-Lab-Password-3!"
MARKER = "ALICE_AUTH_SESSION_FIXTURE"
RESET_TTL = 60
COMPARISON_SLOTS = BoundedSemaphore(2)
AUTH_METADATA = {
    "account": "alice@example.invalid",
    "password": FIXTURE_PASSWORD,
    "resetLifetime": RESET_TTL,
    "scenarios": [
        {"id": "rotation", "label": "Rotate the session token at login", "description": "Log in, then replay the anonymous token saved before login."},
        {"id": "logout", "label": "Invalidate the session at logout", "description": "Read a fixture, log out, then replay the previously authenticated token."},
        {"id": "reset-expiry", "label": "Reject an expired password reset", "description": "Issue a reset token and advance the virtual clock to its expiration boundary."},
        {"id": "reset-reuse", "label": "Reject a reused password reset", "description": "Redeem a valid reset token, then submit the same token a second time."},
        {"id": "invalid-password", "label": "Control: reject an incorrect password", "description": "Try an incorrect password and read with the original anonymous token."},
        {"id": "legitimate-reset", "label": "Control: allow a valid password reset", "description": "Reset just before expiry, then try the old and new passwords."},
    ],
}
SCENARIOS = frozenset(item["id"] for item in AUTH_METADATA["scenarios"])


class FixtureAuth:
    """Small real handlers; only fixed mode enforces the lifecycle rules."""

    def __init__(self, mode, password_hash):
        self.fixed = mode == "fixed"
        self.password_hash = password_hash
        self.sessions = {}
        self.resets = {}
        self.now = 100
        self.closed = False

    def anonymous(self):
        token = secrets.token_urlsafe(24)
        self.sessions[token] = None
        return token

    def login(self, token, password):
        if not check_password(password, self.password_hash):
            return None
        if self.fixed or token not in self.sessions:
            self.sessions.pop(token, None)
            token = secrets.token_urlsafe(24)
        self.sessions[token] = "alice"
        return token

    def read(self, token):
        return MARKER if self.sessions.get(token) == "alice" else None

    def logout(self, token):
        if self.fixed:
            self.sessions.pop(token, None)
        # Vulnerable flow only forgets the client's copy; server token survives.

    def issue_reset(self):
        token = secrets.token_urlsafe(24)
        self.resets[token] = {"expires": self.now + RESET_TTL, "used": False}
        return token

    def reset(self, token, password):
        record = self.resets.get(token)
        if record is None:
            return "unknown_token"
        if self.fixed and record["used"]:
            return "already_used"
        if self.fixed and self.now >= record["expires"]:
            return "expired"
        self.password_hash = make_password(password)
        if self.fixed:
            record["used"] = True
            self.sessions.clear()
        return "accepted"

    def close(self):
        self.sessions.clear()
        self.resets.clear()
        self.password_hash = ""
        self.closed = True


def run_scenario(scenario, mode, password_hash):
    if scenario not in SCENARIOS or mode not in {"vulnerable", "fixed"}:
        raise ValueError("Unknown fixture scenario or mode")
    store = FixtureAuth(mode, password_hash)
    steps, checks = [], []

    def step(action, result):
        steps.append({"action": action, "result": str(result), "time": store.now})

    def check(label, passed):
        checks.append({"label": label, "passed": bool(passed)})

    def read(token, description):
        marker = store.read(token)
        step(description, marker or "Access denied; no marker")
        return marker

    try:
        if scenario == "rotation":
            old = store.anonymous()
            step("Create anonymous token S1", "Unauthenticated")
            current = store.login(old, FIXTURE_PASSWORD)
            step("Log in with the fixture password", "Token changed: S1 -> S2" if current != old else "Token unchanged: S1 -> S1")
            check("Legitimate login reads the fixture", read(current, "Read with the current token") == MARKER)
            check("Successful login rotates the token", current is not None and current != old)
            check("Replay of the pre-login token is denied", read(old, "Replay saved token S1 after login") is None)
        elif scenario == "logout":
            current = store.login(store.anonymous(), FIXTURE_PASSWORD)
            check("Legitimate session reads before logout", read(current, "Read before logout") == MARKER)
            saved = current
            store.logout(current)
            current = None
            step("Log out and discard the client token", "Client token removed")
            check("Client with no token cannot read", read(current, "Read without a token") is None)
            check("Server rejects replay after logout", read(saved, "Replay the saved authenticated token") is None)
        elif scenario in {"reset-expiry", "reset-reuse", "legitimate-reset"}:
            token = store.issue_reset()
            step("Issue reset token R1", f"Expires at virtual time {store.resets[token]['expires']}")
            store.now += RESET_TTL if scenario == "reset-expiry" else RESET_TTL - 1
            step("Advance the virtual clock", "No real waiting; only this store's clock changes")
            first = store.reset(token, NEW_PASSWORD)
            step("Redeem R1 with password 2", first)
            if scenario == "reset-expiry":
                check("Reset at the expiration boundary is rejected", first == "expired")
                old_works = check_password(FIXTURE_PASSWORD, store.password_hash)
                new_works = check_password(NEW_PASSWORD, store.password_hash)
                step("Check original password after expired reset", "Accepted" if old_works else "Rejected")
                step("Check replacement password after expired reset", "Accepted" if new_works else "Rejected")
                check("Expired reset leaves the original password intact", old_works and not new_works)
            elif scenario == "reset-reuse":
                check("First valid redemption succeeds", first == "accepted")
                second = store.reset(token, REPLAY_PASSWORD)
                step("Replay R1 with password 3", second)
                first_works = check_password(NEW_PASSWORD, store.password_hash)
                replay_works = check_password(REPLAY_PASSWORD, store.password_hash)
                step("Check password 2 after replay", "Accepted" if first_works else "Rejected")
                step("Check password 3 after replay", "Accepted" if replay_works else "Rejected")
                check("Second redemption is rejected", second == "already_used")
                check("Replay cannot replace the legitimate new password", first_works and not replay_works)
            else:
                check("Valid reset before expiry succeeds", first == "accepted")
                old_login = store.login(store.anonymous(), FIXTURE_PASSWORD)
                new_login = store.login(store.anonymous(), NEW_PASSWORD)
                step("Log in with the old password", "Rejected" if old_login is None else "Accepted")
                check("Old password no longer logs in", old_login is None)
                check("New password logs in and reads the fixture", read(new_login, "Read after login with password 2") == MARKER)
        elif scenario == "invalid-password":
            old = store.anonymous()
            current = store.login(old, "Intentionally-Wrong-Password!")
            step("Log in with an incorrect password", "Rejected" if current is None else "Accepted")
            check("Incorrect password is rejected", current is None)
            check("Anonymous token remains unauthenticated", read(old, "Replay the original anonymous token") is None)
        passed = all(item["passed"] for item in checks)
        return {
            "outcome": ("control_passed" if scenario in {"invalid-password", "legitimate-reset"} else "protected") if passed else "exposed",
            "reason": "All listed security and legitimate-use checks passed." if passed else "One or more lifecycle checks failed; inspect the executed steps below.",
            "steps": steps, "checks": checks,
        }
    finally:
        store.close()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def auth_compare(request):
    """Protected by the application's normal Django CSRF middleware."""
    def invalid(reason, status=400):
        return JsonResponse({"outcome": "invalid", "reason": reason, "results": {}}, status=status)

    if request.method != "POST":
        response = invalid("Use POST with an application/json body.", 405)
        response["Allow"] = "POST"
        return response
    if request.GET or request.content_type != "application/json":
        return invalid("Use an application/json body without query parameters.")
    if len(request.body) > 1024:
        return invalid("The scenario body must be at most 1024 bytes.", 413)
    try:
        data = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError):
        return invalid("Invalid JSON or duplicate fields.")
    if not isinstance(data, dict) or set(data) != {"scenario"}:
        return invalid("Provide exactly scenario.")
    scenario = data["scenario"]
    if not isinstance(scenario, str) or scenario not in SCENARIOS:
        return invalid("Choose one of the listed scenarios.")
    # Bound simultaneous password-hashing work without queueing more threads.
    if not COMPARISON_SLOTS.acquire(blocking=False):
        response = invalid("Two authentication comparisons are already running. Try again shortly.", 429)
        response["Retry-After"] = "2"
        return response
    try:
        # An immutable starting hash is shared, but each mode owns separate stores.
        password_hash = make_password(FIXTURE_PASSWORD)
        results = {mode: run_scenario(scenario, mode, password_hash) for mode in ("vulnerable", "fixed")}
    finally:
        COMPARISON_SLOTS.release()
    return JsonResponse({"scenario": scenario, "clockUnit": "virtual seconds", "results": results})
