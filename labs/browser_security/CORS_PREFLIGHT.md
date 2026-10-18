# CORS preflight: request permission, authorization, and readable responses

This lesson sends real browser requests from the fixed companion origin to Django. It compares the browser's `OPTIONS` preflight decision, the actual handler's permission decision, and whether companion JavaScript can read the response. Every action changes only a disposable counter belonging to the session that prepared the run.

## Run

From the repository root:

```powershell
python labs/browser_security/run_lab.py --setup
python labs/browser_security/run_lab.py
```

Open the printed main URL, normally `http://127.0.0.1:8766/`, select **CORS preflight**, choose a fixture, and click **Compare preflight policies**. Keep both local processes running. The companion normally uses port 8767; the launcher configures both origins when you change ports.

Open DevTools Network before running a comparison. Filter for `/api/preflight/probe/` and inspect the `OPTIONS` exchange and any following `POST` or `PUT`. The dashboard obtains server evidence through a separate same-origin request: an unreadable companion response therefore does not conceal whether the handler ran.

## Fixtures and expected observations

Every mode should receive one real `OPTIONS` request. The browser sends no cookies on that preflight. The following table assumes the local servers are reachable and the browser permits this same-site setup.

| Fixture | Vulnerable or misconfigured mode | Fixed mode |
| --- | --- | --- |
| Allowed JSON and custom header | Actual POST, one counter change, readable 200 | Same allowed positive control |
| PUT absent from method allowlist | Broad grant permits actual PUT and readable 200 | Preflight lists POST only; actual handler remains untouched |
| Extra header absent from header allowlist | Broad grant includes `X-Lab-Extra`; actual request runs | Preflight omits that header; actual handler remains untouched |
| Companion absent from origin allowlist | Grant explicitly permits the local companion | Grant names only the main origin; companion cannot proceed |
| Actual response omits CORS | Preflight succeeds and counter changes, but response is unreadable | Counter changes and required response headers expose the result |
| Application permission denied | CORS succeeds; fictional permission check is skipped and counter changes | CORS succeeds; readable 403, actual handler reached, no counter change |

The last fixture teaches application authorization independently. Denying a browser method, header, or origin grant is **not** an authorization check on the server. A non-browser client with the owning session and this endpoint's required request shape can still invoke the handler. The backend tests deliberately demonstrate that distinction.

## What the browser actually sends

The fixed peer script uses this shape, with a fresh server-issued run ID:

```javascript
fetch(mainOrigin + '/api/preflight/probe/fixed/?run=' + runId, {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
    'X-Lab-Marker': 'PREFLIGHT_LOCAL_MARKER',
  },
  body: JSON.stringify({ action: 'increment' }),
})
```

JSON content type and the custom header require a preflight. The method-denial fixture uses `PUT`, because it is not a CORS-safelisted method; omitting `POST` from a method list would not establish the same method-denial experiment. The extra-header fixture adds only the predefined `X-Lab-Extra: fixed-extra` header. No arbitrary methods, destinations, header values, or bodies can be entered through this lesson.

The allowed preflight response uses these grants:

```http
Access-Control-Allow-Origin: http://127.0.0.1:8767
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: POST, PUT
Access-Control-Allow-Headers: Content-Type, X-Lab-Marker, X-Lab-Extra
Access-Control-Max-Age: 0
Vary: Origin, Access-Control-Request-Method, Access-Control-Request-Headers
```

The actual credentialed response must also carry the appropriate `Access-Control-Allow-Origin` and `Access-Control-Allow-Credentials` headers. A successful preflight does not supply those headers on behalf of the actual response. Each new comparison uses a new run URL, and preflight grants use a zero maximum age; `Cache-Control: no-store` alone is not the mechanism that controls the separate CORS-preflight cache.

These explanations follow the normative [Fetch Standard CORS protocol](https://fetch.spec.whatwg.org/#http-cors-protocol), [CORS-preflight algorithm](https://fetch.spec.whatwg.org/#cors-preflight-fetch), and [CORS-preflight cache](https://fetch.spec.whatwg.org/#cors-preflight-cache). Browser error text is implementation dependent; the lesson records observations instead of interpreting any failed fetch as proof of a CORS block.

## Evidence and containment

- The parent reads independent counts for OPTIONS, accepted actual-handler entries, and counter changes, plus the application's authorization result. The peer reports readability, visible status, and a fixed marker.
- Preparation uses Django CSRF protection. Only the bounded synthetic probe endpoint is CSRF-exempt so its actual companion-origin requests can exercise CORS independently of Django's CSRF rejection. OPTIONS is a safe method and would not require a CSRF token in either case. Actual mutations still require the owning session, the exact configured peer Origin, a fixed custom marker, and the exact JSON counter action. This is a teaching boundary, not a general CSRF protection recipe.
- Preflight needs no session cookie. It identifies a bounded run by its unguessable ID. That ID alone cannot read the parent's evidence or change a counter without the owner session.
- A lock protects process-local records. Each mode accepts at most three preflights and one actual action; runs expire after five minutes, and the store holds at most 192 runs. Restarting the main process clears this disposable evidence. This is not shared state for a multi-process deployment.
- The peer document runs a fixed script with a restrictive CSP and sandbox. Telemetry requires the exact peer origin, iframe source, run ID, fixture, mode, and bounded result schema. Changing tabs or rerunning removes old frames and rejects stale results.

## Verification

From `labs/browser_security`:

```powershell
.\.venv\Scripts\python.exe backend\manage.py test securitylab.test_preflight_lab --noinput
```

Build the frontend and stop any running lab on ports 8766 and 8767 first. Playwright starts its own servers. From `labs/browser_security/frontend`:

```powershell
npm run build
npx playwright test tests/preflight.spec.js
```

The backend tests check grants, ownership, exact inputs, expiry, replay bounds, and the separation between CORS and authorization. Browser tests check real preflight decisions, actual server counters, readable 403 responses, unreadable successful mutations, fresh positive controls, malformed-evidence recovery, and delayed-response cleanup.

## Scope

The two origins use the same scheme and host with different ports, so they remain the **same site**. This does not test genuinely cross-site SameSite cookies, HTTPS/Secure-cookie handling, third-party-cookie restrictions, redirects during preflight, wildcard credential rules, exposed response headers, browser private-network protections, or every preflight-cache behavior. The [CSRF/CORS lesson](CSRF_CORS.md) separately covers simple requests that can reach the server without a preflight. Cross-origin permissions never replace the [application authorization checks](ACCESS_CONTROL.md).
