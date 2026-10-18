# Server-side request forgery: destinations and redirects

Open the lab at `http://127.0.0.1:8766/` and select **SSRF**. The shared [setup instructions](README.md) start the Vue interface and Django server. No extra dependency or service setup is needed for this lesson.

The intended feature fetches information from an approved public service. The vulnerable handler also accepts a private service and follows redirects into it. The fixed handler checks the public-origin allowlist before its first request and before every redirected request.

The requests are real HTTP exchanges, with synthetic data only. For each comparison, Django starts a temporary service on an operating-system-assigned loopback port. Two logical hostnames select its fixed routes:

| Logical origin | Purpose | Marker |
| --- | --- | --- |
| `http://public.fixture.test` | Approved public service | `PUBLIC_SSRF_FIXTURE` |
| `http://private.fixture.test` | Private demonstration service | `PRIVATE_SSRF_SENTINEL_ONLY_FOR_LAB` |

These names are never sent to a DNS resolver. The HTTP client connects directly to `127.0.0.1` on the port owned by that comparison. This routing is an outer isolation boundary around both handlers; it is separate from the application allowlist demonstrated by the fixed handler. It is not a production SSRF protection library or a DNS-rebinding exercise.

## Compare the fixtures

Select a fixture and click **Compare requests**. Each result shows the marker, the requests actually sent, and any redirect destination. A displayed `Location` header does not mean its destination was requested: inspect the next trace entry.

| Fixture | Vulnerable result | Fixed result |
| --- | --- | --- |
| Public `/info` | Public marker; one request | Same |
| Private `/marker` | Private marker; one request | Blocked before any request |
| Public `/redirect-private` | Redirect, then private marker | Public redirect received; private destination blocked |
| Public `/redirect-public` | Redirect, then public marker | Same legitimate behavior |
| `http://outside.invalid/info` | Boundary blocks before any request | Same |
| Public `/redirect-external` | Public redirect received; boundary blocks the outside destination | Same |
| Public `/loop` | Stops after four requests | Same bounded result |

The comparison API may return HTTP 200 with an outcome of `blocked` or `boundary_blocked`; that status describes successful completion of the comparison. The individual HTTP responses appear in the trace.

Custom input accepts a deliberately narrow, canonical URL format. Credentials, explicit ports, encoded characters, queries, fragments, whitespace, and other schemes are rejected with HTTP 400. Unknown hosts and routes are stopped by the outer boundary. Try an invalid URL after a successful private read and verify that the old marker disappears.

## Read the implementation

- [ssrf_lab.py](backend/securitylab/ssrf_lab.py): `parse_target` accepts the lesson's URL grammar; `compare_target` enforces isolation and the fixed handler's per-hop policy; `OwnedConnection` connects only to the owned socket.
- [SsrfLab.vue](frontend/src/SsrfLab.vue): submits the comparison and renders all results as text.
- [test_ssrf_lab.py](backend/securitylab/test_ssrf_lab.py): exercises actual HTTP, destination checks, redirect and response budgets, no resolver/proxy use, cleanup, partial-request deadlines, validation, and CSRF.
- [ssrf.spec.js](frontend/tests/ssrf.spec.js): checks the user-visible comparisons, legitimate requests, limits, and clearing stale evidence.

Only GET requests reach the fixture service. Browser cookies, credentials, custom request headers, and arbitrary response bodies are not forwarded. The API that starts a comparison retains Django's normal CSRF protection. Each handler makes at most four requests and reads at most 1,024 response bytes; socket and accepted-request deadlines are one second. Four comparisons can run simultaneously. The temporary listener and its worker are closed when the comparison ends. These limits keep the lesson finite and self-contained.

Run the backend checks from `labs/browser_security`:

```powershell
.\.venv\Scripts\python.exe backend/manage.py test securitylab.test_ssrf_lab
```

After building the frontend, stop the running lab before starting browser tests, because Playwright manages its own two-port server pair. From `labs/browser_security/frontend`:

```powershell
$env:LAB_BROWSER_CHANNEL = 'chrome'
npx playwright test tests/ssrf.spec.js
```

## Apply the lesson

For an application that calls known services, define its permitted destinations and enforce that policy at the request boundary. Automatic redirects can invalidate a check made only on the starting URL; this lesson follows redirects manually so each new destination is checked. OWASP recommends disabling automatic redirect following and using application and network controls together. [OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)

Parsing a URL is not equivalent to validating it. The custom grammar here makes the exercise easy to inspect; a production design must also account for its actual resolver, address families, proxies, redirect behavior, and connection lifecycle. Those DNS and deployment questions are outside this fixture's coverage. [Python URL parsing security](https://docs.python.org/3/library/urllib.parse.html#url-parsing-security)

For the HTTP primitives used here, see [Python's HTTP client documentation](https://docs.python.org/3/library/http.client.html). Return to the [lab overview](README.md) for the other vulnerable/fixed comparisons.
