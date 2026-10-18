# Authentication and session lifecycle

Start the lab from the repository root, open <http://127.0.0.1:8766/>, and choose **Authentication & sessions**:

```powershell
python labs/browser_security/run_lab.py
```

Run `python labs/browser_security/run_lab.py --setup` first if dependencies are not installed. See the [lab guide](README.md) for prerequisites and browser setup.

This lesson executes real Python authentication handlers using Django password hashing, generated opaque tokens, and two disposable in-memory stores. It compares what happens after login, logout, and password reset. The evidence comes from actual handler calls and reads of the resulting state.

**This is a handler harness, not a Django account-login implementation.** One HTTP comparison runs an entire scripted flow. Its tokens never become browser cookies, and it does not change the dashboard's session or CSRF token. It therefore demonstrates server-side lifecycle decisions without demonstrating browser cookie attributes, authentication middleware, or a complete account-recovery system.

## Run the comparisons

Select a scenario, then choose **Compare lifecycles**. Each result includes the executed steps, virtual timestamps, and observed checks. `PASS` means the named security or legitimate-use check succeeded. `exposed` means at least one check failed; `protected` means all checks passed in that scenario. Both control scenarios should return `control_passed` for both implementations.

| Scenario | Vulnerable result | Fixed result |
| --- | --- | --- |
| Rotate the session token at login | Saved anonymous token becomes authenticated and can be replayed | Login issues a different token; saved predecessor no longer reads |
| Invalidate the session at logout | Removing the client's copy leaves the server session usable | Saved authenticated token no longer reads after logout |
| Reject an expired password reset | A reset at its expiry boundary changes the password | Reset is rejected and the original password still works |
| Reject a reused password reset | Replaying the same reset token replaces the new password again | First redemption succeeds; second is rejected and password 2 remains valid |
| Control: reject an incorrect password | Incorrect password is rejected; anonymous token cannot read | Same legitimate rejection |
| Control: allow a valid password reset | Reset succeeds before expiry; only the new password logs in | Same legitimate success |

The only account is the fictional `alice@example.invalid`. Its public starting password is `Public-Lab-Password-1!`. Reset flows use equally public fixture passwords ending in `2!` and `3!`. The protected content is only `ALICE_AUTH_SESSION_FIXTURE`.

The dashboard labels generated session tokens **S1/S2** and the reset token **R1**; the labels are not the tokens themselves. Rotation checks compare the actual opaque values. A read after logout explicitly reuses a saved token, so hiding a button or deleting a client's copy cannot make the check pass.

## Trace the handlers

The code is in [auth_lab.py](backend/securitylab/auth_lab.py). Both modes verify the supplied password against an encoded hash. They differ at the lifecycle checks:

```python
# Fixed login: invalidate the predecessor before creating the authenticated token.
self.sessions.pop(token, None)
token = secrets.token_urlsafe(24)
self.sessions[token] = "alice"

# Fixed logout: revoke the token in the server store.
self.sessions.pop(token, None)

# Fixed reset: reject an already-used or expired token before changing the hash.
if record["used"]:
    return "already_used"
if self.now >= record["expires"]:
    return "expired"
```

After a valid fixed reset, the handler hashes the replacement password, marks that reset token used, and clears existing fixture sessions. The vulnerable reset handler checks only that a token exists and omits expiry and used-state enforcement.

The app uses Django's configured password hasher through `make_password()` and `check_password()`. It does not compare plaintext stored passwords or weaken the application's hash work factor. See [Django's password management documentation](https://docs.djangoproject.com/en/6.0/topics/auth/passwords/).

For a real Django application, use its authentication and session facilities rather than copying this small token store. Django documents how `login()` uses session-key cycling and how `logout()` flushes session data. The details depend on the selected session backend. See [Django's session documentation](https://docs.djangoproject.com/en/6.0/topics/http/sessions/).

## Virtual time and scope

Every store starts at virtual time **100**. A reset expires at **160**. The expiry scenario advances directly to 160; the valid-reset and reuse scenarios run at 159. No wall-clock time changes and no waiting are involved. `now >= expires` makes the exact expiration boundary testable.

Each comparison constructs separate vulnerable and fixed stores, executes the bounded scenario, and clears both in `finally` blocks, including when execution raises an exception. Re-running a scenario begins with the original password. No fixture account, password change, session token, or reset token survives into another comparison. Browser-visible evidence remains in the current result cards until the next selection or run.

The fixed reset implementation covers the lifecycle of **one token in a sequential flow**. It does not model email delivery, multiple concurrently outstanding reset links, database transactions for simultaneous redemptions, account enumeration, rate limits per account, MFA, password policy, idle session expiry, or production token storage. Those require separate tests and design decisions. OWASP recommends reset tokens with expiration and single use as part of a broader recovery flow; see its [Forgot Password guidance](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html).

## API and verification

`POST /api/auth/compare/` accepts exactly one JSON field:

```json
{"scenario":"rotation"}
```

Allowed values are `rotation`, `logout`, `reset-expiry`, `reset-reuse`, `invalid-password`, and `legitimate-reset`. Normal Django CSRF protection applies. The response contains `results.vulnerable` and `results.fixed`, each with an outcome, a step log, and checks. It never returns live fixture tokens or password hashes.

Unknown, duplicate, or extra fields return 400. Bodies larger than 1024 bytes return 413. At most two comparisons hash passwords simultaneously in each server process; a further request receives 429 with `Retry-After: 2`. Responses inherit the lab's `Cache-Control: no-store` policy.

```powershell
labs/browser_security/.venv/Scripts/python.exe labs/browser_security/backend/manage.py test securitylab.test_auth_lab
python labs/browser_security/run_lab.py --test
```

Stop running lab servers before the full test command, because browser tests need ports 8766 and 8767. Backend tests cover all scenarios, unknown tokens, independent stores, successful and exceptional cleanup, input validation, concurrency limits, CSRF, and unchanged controller cookies. Flow tests use a fast hasher only inside their test settings; a separate check executes the real Django PBKDF2 hasher. Browser tests verify the displayed evidence and that changing scenarios clears previous results.
