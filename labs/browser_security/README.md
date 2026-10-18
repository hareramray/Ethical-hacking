# Browser Security Lab: Vue + Django

A runnable companion to [CSP_XSS_HARMLESS_TESTS.md](../../CSP_XSS_HARMLESS_TESTS.md), with additional lessons for [path traversal](PATH_TRAVERSAL.md), [SQL injection](SQL_INJECTION.md), [access control](ACCESS_CONTROL.md), and [CSRF/CORS](CSRF_CORS.md). Vue provides the controls and evidence panels; Django runs the comparisons against synthetic data.

Further lessons cover [authentication and sessions](AUTH_SESSIONS.md), [SSRF](SSRF.md), and [business logic and race conditions](BUSINESS_LOGIC.md). Each compares deliberately vulnerable behavior with a repair and a legitimate positive control.

Interpreter lessons add [server-side template injection](TEMPLATE_INJECTION.md), [command and argument injection](COMMAND_INJECTION.md), and [XML external entities](XML_ENTITIES.md). They execute predefined harmless inputs through real renderers, processes, and parsers.

API lessons cover [write authorization and mass assignment](API_WRITES.md), [JWT validation](JWT_VALIDATION.md), and [webhook replay protection](WEBHOOKS.md). Compare actual stored changes, token decisions, and event-ledger effects using fresh fictional fixtures.

Content-handling lessons cover [Markdown and rich-text sanitization](SANITIZATION.md), [cross-frame postMessage security](POSTMESSAGE.md), and [bounded ZIP extraction](ARCHIVE_EXTRACTION.md). Follow saved HTML into the browser, distinguish message origin from sender identity, and inspect actual file writes inside disposable directories.

The application runs on your own computer at **http://127.0.0.1:8766/**. The examples use fixed console/DOM markers. Experimental documents and upload previews are sandboxed separately from the controller. This is a teaching application, not a service to deploy publicly.

## Start

Prerequisites: **Python 3.12+** and **Node.js 24 LTS with npm**. Run these from the repository root:

```powershell
python labs/browser_security/run_lab.py --setup
python labs/browser_security/run_lab.py
```

Setup creates a local `.venv`, installs the pinned Python dependencies and locked npm dependencies, builds Vue, and creates the SQLite tables. The first setup requires internet access for packages; ordinary lab use requires no CDN or external service. It does not change your global Python packages.

After pulling updates that add dependencies, rerun `--setup`. The JWT lesson uses pinned PyJWT; sanitization uses pinned markdown-it-py and nh3 from `requirements.txt`.

Open **http://127.0.0.1:8766/**. The launcher also starts a companion on **http://127.0.0.1:8767/** for the CSRF/CORS and postMessage lessons. Leave the terminal running; `Ctrl+C` stops both servers. A different main port automatically moves the companion to the next port:

```powershell
python labs/browser_security/run_lab.py --port 8876
```

That uses ports 8876 and 8877. Set `--peer-port` explicitly if needed; the two ports must differ and both must be free. The launcher always binds to loopback. The older authorization exercise uses port 8765, so the default ports do not conflict. Do not reuse these fixtures with real credentials or private data.

## Exercises

| Section | Try this | Observe |
| --- | --- | --- |
| XSS | Run a supplied marker as escaped text, then as deliberately parsed HTML with script restrictions off. | Literal text versus a marker event; HTML rendering alone is not JavaScript execution. |
| XSS: DOM | Select the DOM source and compare safe text rendering with the HTML sink. | Event-handler execution or a CSP/Trusted Types rejection. |
| XSS: stored | Save a fixture, reload the application, then run the stored source. Delete it afterward. | Persistence in this browser's Django session, not a shared public comment system. |
| CSP | Select a policy and a probe such as an inline script, dynamic script, string evaluation, or callback timer. | Real browser enforcement, a positive bootstrap control, and violation details. |
| JSONP | Compare parser-inserted and trusted dynamic loading under `self`, `nonce`, and `dynamic`. | Intended callback execution versus source blocking. |
| Uploads | Download the PNG/HTML/SVG sample files. Compare strict validation with lab acceptance. | Validation errors, stored metadata, safe downloads, and isolated preview behavior. |
| Path traversal | Compare `readme.txt` and `../private/sentinel.txt` in the vulnerable and fixed handlers. | Real reads of disposable markers, resolved directory boundaries, and legitimate downloads after the fix. |
| [SQL injection](SQL_INJECTION.md) | Compare a public name, an apostrophe, and the supplied OR-condition fixture. | Concatenated SQL exposes a private marker; bound parameters preserve the intended query. A fresh in-memory database is used for every request. |
| [Access control](ACCESS_CONTROL.md) | Switch synthetic personas, records, and read/review actions. | Owner, tenant, administrator, and anonymous decisions enforced by the server. |
| [CSRF / CORS](CSRF_CORS.md) | Run a request from the companion origin, then try a legitimate protected request. | Server-side counter changes and browser-readable responses are measured separately. |
| [Authentication & sessions](AUTH_SESSIONS.md) | Compare login rotation, logout replay, expired reset tokens, and reused reset tokens. | Actual token-store decisions in fresh fictional account flows, with an explicit virtual clock for expiry. |
| [SSRF](SSRF.md) | Request a public mock service, a private marker, and a public-to-private redirect. | Real HTTP requests confined to disposable local mock services; fixed destination checks apply at every hop. |
| [Business logic & races](BUSINESS_LOGIC.md) | Redeem a coupon once, sequentially twice, and with two overlapping attempts. | A ledger exposes duplicate rewards; an atomic conditional update allows only one redemption. |
| [Template injection](TEMPLATE_INJECTION.md) | Compare a normal name, a context-variable expression, a conditional, and HTML text. | Django evaluates template source but preserves values passed as data; output escaping addresses a different boundary. |
| [Commands & arguments](COMMAND_INJECTION.md) | Select a normal operand, a shell separator, and an injected option. | Fixed marker-only processes show shell interpretation versus argument parsing, then literal operand handling. |
| [XML external entities](XML_ENTITIES.md) | Parse ordinary XML, a built-in entity, and a document referencing a synthetic external resource. | The vulnerable parser resolves the marker; the fixed parser rejects the DTD before resolution. |
| [API write authorization](API_WRITES.md) | Edit an owned profile, a peer's profile, and protected properties. | Inspect database state before and after the write; fixed object and field checks reject forbidden patches without partial changes. |
| [JWT validation](JWT_VALIDATION.md) | Compare valid, tampered, expired, and wrongly scoped synthetic tokens. | Decoding alone trusts claims; PyJWT verifies the signature and required claims before the separate subject permission check. |
| [Webhook replay protection](WEBHOOKS.md) | Deliver valid, tampered, stale, and repeated fictional events. | Signature checks, freshness checks, and event deduplication protect different boundaries; an atomic ledger update prevents duplicate rewards. |
| [Sanitization](SANITIZATION.md) | Save Markdown and rich-text fixtures, then reload their previews. | Compare parsed HTML, sanitized HTML, final DOM, and harmless marker execution; legitimate formatting survives the fix. |
| [postMessage security](POSTMESSAGE.md) | Compare trusted senders, wrong origins, wrong windows, malformed messages, and HTML text. | Real browser messages expose independent origin, source, schema, and rendering decisions. |
| [Archive extraction](ARCHIVE_EXTRACTION.md) | Extract tiny normal, traversal, collision, and limit-check ZIP fixtures. | Actual writes expose an intended-directory escape; fixed validation and bounded staging reject unsafe archives before writing files. |

The controller uses Vue's compiled templates and text interpolation. It never evaluates the payload. Django returns the actual experiment document with the chosen response policy; entering code in DevTools is not part of the test.

The **Path traversal** tab compares both handlers side by side. Follow the [walkthrough and expected results](PATH_TRAVERSAL.md), including backslash normalization, sibling-prefix mistakes, and URL decoding. Its filesystem fixtures are created and removed per request; both handlers are restricted to the four disposable files. CSP controls are separate from this server-side exercise.

The **CSRF / CORS** tab uses two real origins. Different loopback ports are still the same site, and cookies are not separated by port. The companion serves a fixed teaching script; it does not expose the dashboard APIs or change session cookies. This fixture demonstrates Origin checks and CORS response visibility, not a cross-site SameSite-cookie test. See the [walkthrough](CSRF_CORS.md) for expected counters and limitations.

The **Authentication & sessions** tab executes scripted clients against a disposable teaching token store. It does not log you into the dashboard or replace Django's session machinery. The **SSRF** tab routes reserved fixture hostnames directly to sockets owned by the current exercise, without DNS or access to other services. The **Business logic & races** tab uses two database connections and an explicit scheduling barrier to make a check-then-act race repeatable. Its points are synthetic, and its files are temporary.

The **Template injection**, **Commands & arguments**, and **XML external entities** tabs accept only known fixture identifiers. Their server-owned templates, commands, and XML documents cannot be replaced through the API. Template rendering uses scalar fixture context, processes print or record markers, and the XML resolver can supply only one in-memory resource. These outer exercise limits are distinct from each fixed handler's repair.

The **API write authorization**, **JWT validation**, and **Webhook replay protection** tabs also use fixed fixture selectors and fresh comparison state. They do not modify the dashboard's accounts, accept real tokens, or receive external webhook deliveries. JWT validation is a token-verification lesson, not an OAuth/OIDC login flow. The webhook's signed-message format is a local teaching contract; provider integrations must follow their own signing specification.

The **Sanitization** tab saves one fixture comparison in the browser's Django session and renders both results in opaque sandboxed frames. Both previews permit the harmless marker, so a missing marker is not attributed to a stricter CSP in fixed mode. The **postMessage security** tab uses actual sender and receiver windows on the two configured origins; the companion exposes only fixed lesson documents and scripts, never dashboard APIs. Its receivers preserve their origin for this comparison.

The **Archive extraction** tab reads server-created ZIP fixtures and writes only inside fresh disposable outer directories. Vulnerable extraction can reach a sibling of the intended extraction directory, but cannot access host files. Fixed extraction checks all members and stages bounded reads before writing. No actual symlinks are created, and this is not a demonstration of concurrent symlink replacement or an unrestricted archive-upload service.

### Policy meanings

| Policy | Script behavior |
| --- | --- |
| `off` | No script-source restrictions in the experiment. The isolation sandbox remains enforced. |
| `self` | Same-origin scripts are permitted; arbitrary inline script and string evaluation are restricted. |
| `nonce` | Only authorized script elements carrying this response's nonce are permitted. |
| `hash` | Only the exact authorized script bytes are permitted. |
| `dynamic` | Nonce-based trust propagates through dynamic script creation under `strict-dynamic`. |
| `report` | Script violations are reported but not blocked by the report-only policy. The isolation sandbox remains enforced. |
| `tt` | Nonce CSP plus Trusted Types enforcement where the browser supports it. |

The current CSP3 draft and browsers can permit dynamically created inline scripts with `strict-dynamic`; do not label the trusted loader's expected execution a bypass. Nonces do not repair unsafe data interpolation inside an already trusted script. Browser support and insertion context matter. The original Markdown contains the detailed interpretation rules and primary references.

Every run receives a new ID and an isolated document. The evidence panel accepts messages only from its current experiment frame, with the correct run ID and message type. A bootstrap event shows the fixture initialized; it does not alone show that the selected probe executed.

Nested `srcdoc` frames remain blocked by the isolation policy in every mode. JavaScript URL clicks did not execute in this opaque-origin lab in Chrome 155, including with script restrictions off; this is a measured limitation, not evidence that the selected script policy caused the block. Use the clickable event-handler fixture as a positive execution control. JavaScript URL navigation also has origin checks in the [HTML navigation specification](https://html.spec.whatwg.org/multipage/browsing-the-web.html#the-javascript:-url-special-case).

### Upload boundaries

- Files are limited to **64 KiB**; each browser session has a bounded collection.
- **Strict** mode accepts supported plain UTF-8 text and validated PNG images. PNGs are decoded, bounded in dimensions, and re-encoded; a PNG filename or claimed MIME alone is insufficient.
- **Lab** mode permits the small supported marker formats for content-handling demonstrations. It is intentionally more permissive than strict mode.
- Files use generated storage identifiers. Reads and deletes are scoped to the browser's session; another session does not gain access merely by knowing an ID.
- Downloads use attachment disposition, `nosniff`, and a restrictive policy.
- Blocked previews prevent uploaded scripts; a nonce-authorized observer can still report violations. Active previews permit harmless markers inside a response sandbox that does **not** grant same-origin access. Direct preview navigation retains the response sandbox.
- A script file viewed as plain text is not the same test as loading it through a script element. SVG image mode and SVG document mode also have different execution behavior.

Use the application's delete button to remove only the test upload you created. Clearing browser cookies changes the session and can leave earlier test records inaccessible through the UI; use a fresh disposable data directory for a fresh lab installation when needed.

## Check the implementation

Install the browser used by the automated checks once:

```powershell
cd labs/browser_security/frontend
npm exec playwright install chromium
cd ../../..
python labs/browser_security/run_lab.py --test
```

The command runs Django checks and tests, rebuilds Vue, then runs Playwright against a real browser. Browser-test data is separate from learner data. Tests exercise SQL isolation, object and property permissions, session/reset-token decisions, JWT signatures and claims, webhook authentication and replay, local HTTP routing, concurrent coupon redemption, template interpretation, process argument boundaries, XML resolution, CSRF boundaries, CORS visibility, upload validation and retrieval, and actual marker behavior rather than treating source text as proof of execution.

Stop any running lab on ports 8766 and 8767 before running the browser checks; the tests start their own servers on those ports.

You can use an existing Chrome installation instead of downloading Chromium:

```powershell
$env:LAB_BROWSER_CHANNEL = 'chrome'
python labs/browser_security/run_lab.py --test
Remove-Item Env:LAB_BROWSER_CHANNEL
```

On Linux/macOS use `LAB_BROWSER_CHANNEL=chrome python labs/browser_security/run_lab.py --test`. Browser installation and channel availability vary by machine. Unsupported Trusted Types behavior must be distinguished from a passed enforcement test.

## Develop

```text
browser_security/
  run_lab.py             Setup, build, test, and loopback launcher
  requirements.txt       Python dependencies
  backend/
    config/              Django configuration and routing
    securitylab/         Views, policies, fixtures, models, tests
    data/                Ignored SQLite database and uploads
  frontend/
    src/                 Vue application and styles
    tests/               Browser checks
    dist/                Ignored build served by Django
```

After editing Vue files:

```powershell
python labs/browser_security/run_lab.py --build
```

Reload the browser to use the new build. Restart the launcher after backend edits; both child servers run without the autoreloader. Serving the built frontend through the main Django server keeps the controller and APIs on one origin and preserves the actual response headers used by the exercises. The companion uses a separate port and restricted routes for the two-origin lesson.

For an isolated dataset, set `LAB_DATA_DIR` to a new directory before starting. The default is `backend/data/`. Keep that directory, `.venv`, frontend dependencies/build output, and test artifacts out of source control.

## Scope

This application implements local browser exercises from the reference guide. It is not a scanner for arbitrary sites, a sanitizer certification suite, a malware-upload tester, or a complete reproduction of every framework-specific behavior. Some reference topics—such as blind observations, browser-specific parser mutation, and third-party integrations—still require their own target-specific fixtures.

Design references: [Vue security guidance](https://vuejs.org/guide/best-practices/security.html), [Django file uploads](https://docs.djangoproject.com/en/6.0/topics/http/file-uploads/), [Django CSRF integration](https://docs.djangoproject.com/en/6.0/howto/csrf/), and [Playwright web servers](https://playwright.dev/docs/test-webserver).
