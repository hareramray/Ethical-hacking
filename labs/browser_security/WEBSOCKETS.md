# WebSocket security: connections, messages, and current permissions

This lesson opens real browser WebSockets to a local ASGI handler. It compares a deliberately broad policy with explicit origin, tenant, action, and current-permission checks. Messages contain only fictional tenant markers; no external socket address, arbitrary code, or private data is accepted.

Run the [lab setup](README.md), open the printed main URL, and select **WebSocket security**. Choose a fixture and click **Compare WebSocket policies**. Use the launcher rather than Django's HTTP-only `runserver`: it starts Uvicorn on the existing main and companion ports, routes HTTP to Django, and routes `/ws/security/vulnerable/` and `/ws/security/fixed/` to this lesson.

## Five runnable fixtures

| Fixture | Vulnerable behavior | Fixed behavior |
| --- | --- | --- |
| Allowed origin and tenant | Upgrades and delivers `HARMLESS_ALPHA_EVENT`. | The same allowed connection and subscription succeed. |
| Companion origin | Accepts the fixed companion's origin and delivers a marker. | Rejects that origin before accepting the WebSocket; no messages reach the handler. |
| Foreign tenant | An alpha reader receives `HARMLESS_BETA_EVENT`. | Accepts the connection, then returns `WS_TENANT_DENIED` for the subscription. |
| Forbidden action | A reader receives `FICTIONAL_PUBLISH_ACCEPTED`. | Checks the action and returns `WS_ACTION_DENIED`. No actual publication service exists in either mode. |
| Permission revoked | Delivers a second alpha event using the old permission assumption. | Both sockets initially subscribe successfully. After a separate HTTP request revokes the fictional permission, the next delivery request returns `WS_PERMISSION_DENIED`. |

The last fixture uses the same two connections throughout. The controller waits until both received their first event, makes a CSRF-protected revocation request, and then tells the harness to request another delivery. Expected delivery counts are two for the vulnerable path and one for the fixed path. This changes a disposable lesson permission; it does not log out the Django dashboard or implement distributed session revocation.

## Inspect actual protocol evidence

Open browser developer tools, select Network, and inspect the WebSocket connections and messages. Compare three observations:

1. **Browser connection and message evidence:** whether `open` occurred, which JSON marker arrived, and the close code.
2. **Independent server state:** the handshake decision, number of received messages, number of delivered events, and application permission decision, read through the owner-bound HTTP state endpoint.
3. **The decision being exercised:** an accepted connection does not authorize every tenant or action, and an earlier permission decision does not authorize a later delivery automatically.

A browser socket error alone does not prove an origin rejection. The fixed wrong-origin run records `origin refused` on the server with zero received messages. Under ASGI, closing before acceptance rejects the handshake with HTTP 403; browser JavaScript may report an abnormal close such as 1006 instead of exposing that HTTP status. See the [ASGI WebSocket protocol specification](https://asgi.readthedocs.io/en/stable/specs/www.html#close-send-event).

The browser tests observe Playwright's actual WebSocket frame events. They verify the first and second messages around permission revocation without replacing the socket transport or manufacturing server evidence.

## Follow the implementation

The [ASGI dispatcher](backend/config/asgi.py) sends ordinary HTTP scopes to Django and WebSocket scopes to [websocket_lab.py](backend/securitylab/websocket_lab.py). The [Vue component](frontend/src/WebSocketLab.vue) prepares a run, mounts a fixed harness, and reads independent server state. The harness uses real `WebSocket` objects and closes them when it finishes or is removed.

| Endpoint | Purpose |
| --- | --- |
| `POST /api/websocket/prepare/` | Accept one server-owned fixture ID and create two single-use connection capabilities. |
| `GET /api/websocket/state/?run=...` | Return evidence only to the session that prepared the run. |
| `POST /api/websocket/revoke/` | Revoke the fictional permission once, after both live subscriptions exist. |
| `/lab/websocket/frame/`, `/lab/websocket/boot.js` | Fixed main-origin harness and script. |
| `/peer/websocket/`, `/peer/websocket/boot.js` | Fixed companion-origin harness and script for the wrong-origin fixture. |
| `/ws/security/<mode>/` | Upgrade and process bounded lesson messages. |

Both comparison modes retain the outer exercise restrictions. The handshake requires a loopback client, the exact main host, a configured main or companion origin, an existing Django session, and the matching run capability. Duplicate sensitive headers and malformed query parameters are refused. The ASGI handler performs these checks itself because Django's HTTP middleware does not process WebSocket scopes. A new Django session cannot reuse another session's capability.

Only the documented vulnerable policy checks are omitted. Both paths recheck the underlying Django session on messages, so deleting that session prevents further sends even in vulnerable mode. The live permission fixture separately demonstrates an application-permission change; a session's continued existence does not imply that permission remains granted.

The process retains at most 128 runs and four recent runs per owner. Runs expire after five minutes; each capability is usable for one connection attempt. Each accepted socket lasts at most 12 seconds and processes at most three text messages, each no more than 512 UTF-8 bytes. The launcher also limits protocol message size to 1024 bytes. Binary messages, duplicate JSON keys, unknown actions, and malformed schemas are rejected without echoing their contents. Restarting the server clears all lesson state.

The main and companion harnesses contain only trusted, fixed scripts. Their iframe `allow-scripts allow-same-origin` configuration preserves origin and session behavior for this comparison; it is not isolation for arbitrary untrusted JavaScript. The companion never exposes the dashboard's APIs. Capability-bearing query strings are kept out of access logs and responses use `Referrer-Policy: no-referrer` and `Cache-Control: no-store`.

## Run the checks

Install updated dependencies with `python labs/browser_security/run_lab.py --setup` from the repository root. The launcher pins Uvicorn and websockets, uses one worker per origin to keep lesson state in the same process, disables forwarded-header trust and access logs, and binds only to loopback. See [Uvicorn settings](https://uvicorn.dev/settings/) for the server options.

From `labs/browser_security/backend`:

```powershell
..\.venv\Scripts\python.exe manage.py test securitylab.test_websocket_lab
```

Stop the normal launcher so ports 8766 and 8767 are free. From `labs/browser_security/frontend`:

```powershell
npm run build
$env:LAB_BROWSER_CHANNEL = 'chrome'
npm run test:e2e -- tests/websocket.spec.js
```

Backend checks cover handshake transport guards, session/capability binding and reuse, message schema and limits, tenant/action checks, live permission changes, session deletion, and role-scoped harnesses. Browser checks cover real upgrades and JSON frames, wrong-origin refusal, permission revocation on the existing sockets, fresh runs, and abandoned preparations.

## Scope

This is plaintext `ws://` on loopback, with two different origins on the same site. It does not test `wss://`, cross-site cookie behavior, external identity providers, reconnect/resumption, push fan-out, compression attacks, production rate limits, broker authorization, or multi-process revocation. The server returns fictional events in response to bounded client requests; it is not a general subscription server.

[OWASP WebSocket security guidance](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html) describes origin validation, message authorization, session management, and limits as separate controls. Continue with the [API security tutorial](../../tutorials/12-api-security-and-modern-authentication.md), [access-control lesson](ACCESS_CONTROL.md), and [GraphQL authorization lesson](GRAPHQL.md) to compare how the same application policy applies across interfaces.
