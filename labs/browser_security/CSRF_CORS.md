# CSRF and CORS: two local origins with Vue + Django

This lesson compares a request changing server state with a script reading a response. A fixed companion page sends real browser requests to the main Django application. The only data involved is a pair of synthetic counters and the marker `CORS_SYNTHETIC_SECRET`.

## Start both origins

From the repository root, run setup once and then start the launcher:

```powershell
python labs/browser_security/run_lab.py --setup
python labs/browser_security/run_lab.py
```

For an existing installation, rebuild with `python labs/browser_security/run_lab.py --build`, stop the old launcher, and restart it. Open **http://127.0.0.1:8766/** and select **CSRF & CORS**. Use the printed `127.0.0.1` address consistently; substituting `localhost` changes the origin.

| Role | Default origin | Purpose |
| --- | --- | --- |
| Main | `http://127.0.0.1:8766` | Vue controller, Django APIs, session state |
| Companion | `http://127.0.0.1:8767` | Fixed page and script making the cross-origin requests |

The launcher starts both servers on loopback and stops both with **Ctrl+C**. Choose other ports if necessary:

```powershell
python labs/browser_security/run_lab.py --port 8770 --peer-port 8771
```

If `--peer-port` is omitted, it defaults to the main port plus one. Both ports must be available, distinct, and between 1024 and 65535. The interface receives the configured origins from Django, so the same exercises work with the chosen pair. See the [lab guide](README.md) for prerequisites.

## Understand the cookie boundary

Changing the port creates a different **origin**, but these two URLs remain the same **site**. Same-site evaluation ignores the port. This is why the lesson can send its session cookie from the companion even though the browser applies cross-origin response restrictions. [MDN: site and origin](https://developer.mozilla.org/en-US/docs/Glossary/Site)

Cookies are also not isolated by port. A service on another port of the same host can receive matching cookies, and changing ports does not isolate JavaScript-readable cookies. The companion in this lab never reads `document.cookie` or uses Django session data. [HTTP cookie specification, section 8.5](https://httpwg.org/specs/rfc6265.html#section-8.5)

The main session cookie has `SameSite=Lax` and `HttpOnly`; the CSRF cookie has `SameSite=Strict`. Because this experiment is same-site, those SameSite values do not prevent the browser from attaching cookies to these requests. The companion explicitly uses `credentials: 'include'`. This setup isolates Origin checks, token checks, and response visibility; it does not demonstrate cookie delivery between different sites.

## Exercise 1: observe CSRF side effects

1. Leave **Lesson** set to **CSRF · request side effects**.
2. Select **Run from companion origin**. The main page prepares a fresh session-scoped run, with both counters at zero.
3. The companion sends one form POST to each endpoint, with cookies and without a CSRF token.
4. Compare the peer's response visibility with the counters independently fetched by the main page.

| Observation after one run | Vulnerable endpoint | Fixed endpoint |
| --- | --- | --- |
| Peer response | Unreadable | Unreadable |
| HTTP status available to peer JavaScript | Unavailable | Unavailable |
| Server counter checked from main origin | `1` | `0` |
| Actual server response, inspectable in browser developer tools | HTTP 200 | HTTP 403 |

Both responses omit CORS permission. That prevents the companion from reading them, while the vulnerable POST has already incremented its counter. The fixed POST is rejected by Django's CSRF middleware before its handler changes state. An unreadable response alone does not establish which of these outcomes occurred.

The companion's request is equivalent to this fragment from [the teaching script](backend/securitylab/cross_origin.py), with `url` selected from the configured main origin and current run:

```javascript
const response = await fetch(url, {
  method: 'POST',
  credentials: 'include',
  body: new URLSearchParams({ action: 'increment' }),
});
```

This form request uses a CORS-safelisted content type and adds no custom headers, so it can be sent without a CORS preflight. Changing it to JSON or adding a custom request header would introduce a different test: preflight can stop an actual request before its handler runs. Browsers can send simple cross-origin requests while withholding their responses from the calling script. [MDN: simple CORS requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS#simple_requests)

Select **Send legitimate fixed request with CSRF token**. The main page now sends a same-origin POST with a valid `X-CSRFToken` header. The notice should report HTTP 200, and the fixed counter should become `1`. This positive control confirms that the protected feature remains usable.

Django verifies the request's `Origin` against the accepted origin configuration and checks the CSRF token for unsafe methods. The companion origin is not added to `CSRF_TRUSTED_ORIGINS`. Even a valid token does not make that peer-origin POST acceptable. A same-origin POST still needs its token. Both conditions are covered separately by the backend tests. [Django CSRF protection](https://docs.djangoproject.com/en/6.0/ref/csrf/)

Only `/api/cross-origin/change/vulnerable/` has the deliberate `csrf_exempt` decorator. Its handler accepts only the configured main or companion origin, the active run for that browser session, and the single form field `action=increment`. It changes a synthetic counter capped at ten. These restrictions contain the exercise; the fixed handler retains ordinary Django CSRF protection.

## Exercise 2: observe CORS response visibility

1. Change **Lesson** to **CORS · response visibility**.
2. Select **Run from companion origin** again. Each run creates fresh counters and replaces the previous run identifier.
3. Compare the returned marker and the peer's ability to inspect each response.

| Observation | Vulnerable endpoint | Fixed endpoint |
| --- | --- | --- |
| Peer response | Readable | Unreadable |
| HTTP status available to peer JavaScript | `200` | Unavailable |
| Marker received by companion | `CORS_SYNTHETIC_SECRET` | No marker readable |
| Effect on either counter | None | None |

Both endpoints perform a read-only GET and return the same synthetic JSON to the requesting session. The difference is whether the response grants the peer permission to read it. For the exact configured companion origin, the vulnerable endpoint adds:

```http
Access-Control-Allow-Origin: http://127.0.0.1:8767
Access-Control-Allow-Credentials: true
Vary: Origin
```

The allow-origin value follows the configured companion port. It is an exact comparison, not arbitrary reflection of a supplied origin. The fixed endpoint sends no cross-origin permission. Neither endpoint installs CORS headers globally.

This deliberately grants the companion access to a marker intended to remain private to the main origin. Such a grant is the lesson's policy error; granting access to a genuinely trusted application can be intentional. Credentialed CORS responses require an explicit allowed origin rather than `*`. [MDN: requests with credentials](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS#requests_with_credentials)

The fixed GET still reaches Django and receives a response. CORS controls whether the peer's script can read that response; the lesson does not use CORS as authorization for changing state.

## Follow the evidence and boundaries

The `runId` is a fixture selector, **not a CSRF token**. The main page intentionally gives it to the companion in the iframe URL. Server state is also bound to the browser session, so knowing another session's identifier does not grant access to its counters or marker. Preparing a new run resets both counters and invalidates the previous run. Unknown or stale runs return HTTP 404; duplicate or unexpected query parameters return HTTP 400. At ten increments, a counter refuses further changes until a new run is prepared.

This lesson uses the companion's `/peer/` and `/peer/boot.js` routes; `/api/health` supports startup checks. The companion also serves the four fixed document/script routes described in the [postMessage lesson](POSTMESSAGE.md), plus `/peer/framing/` and `/peer/framing/boot.js` for the [framing lesson](CLICKJACKING_FRAMING.md). These teaching documents do not access Django sessions or issue cookies; role middleware denies the dashboard, other APIs, uploads, and existing XSS frames. Browser cookies can still accompany requests to its host because port numbers do not isolate them.

The companion iframe preserves its real origin. Its CSP permits its fixed script, connections to the configured main origin, and embedding by that main origin. It does not reuse the opaque sandbox used for XSS exercises. The Vue component accepts completion messages only from the current iframe, exact companion origin, current run, and selected lesson. It then fetches server counters independently from the main origin. See [the Vue component](frontend/src/CrossOriginLab.vue) and [Django handlers](backend/securitylab/cross_origin.py).

For closer inspection, open browser developer tools before running a lesson and filter Network requests by `cross-origin`. In the CSRF exercise, check the peer `Origin`, the form content type, the absence of a supplied CSRF token, the POST responses, and the later main-origin state response. In the CORS exercise, compare the allow-origin and allow-credentials headers. Developer tools can inspect information that the companion's JavaScript cannot read.

A network failure or timeout can also make a response unreadable. If the companion does not complete, verify both launcher processes and ports are available, use the printed main URL, and start a fresh run. Missing evidence should not be treated as successful protection.

## Verify and extend

[Backend tests](backend/securitylab/test_cross_origin.py) cover Origin/token controls, session isolation, run reset, bounded counters, CORS scope, query validation, and companion route restrictions. [Browser tests](frontend/tests/cross-origin.spec.js) exercise actual response-reading restrictions and the Vue workflow. Stop the running launcher first, then use the full verification command:

```powershell
python labs/browser_security/run_lab.py --test
```

Browser installation and Chrome-channel alternatives are documented in the [lab guide](README.md). This lesson uses two HTTP origins on one site. The separate [CORS preflight lesson](CORS_PREFLIGHT.md) adds actual OPTIONS permission checks and independently records handler effects and response readability. Different-site SameSite behavior, HTTPS/Secure cookies, and third-party-cookie policies still require separate fixtures.
