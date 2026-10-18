# CSP workers and HTTP violation reporting

This local Vue + Django lesson runs a real dedicated worker under three policies and receives the browser's actual CSP HTTP reports. Each worker only returns `HARMLESS_WORKER_MARKER` and closes. There are no arbitrary scripts, remote URLs, service-worker registrations, or persistent background tasks.

Start the lab using the [README](README.md), open the printed main-origin URL, and choose **CSP workers & reporting**. The default is `http://127.0.0.1:8766/`. Use that exact host and port; alias hosts fail with an origin error rather than silently losing messages or reports.

## Observe three different things

1. **Worker result:** the marker comes from a message sent by the actual dedicated worker. A constructor/error event alone does not identify why execution failed.
2. **Local policy event:** the frame listens for `securitypolicyviolation` and displays the `worker-src` directive and `enforce` or `report` disposition. An event does not prove a report reached a server.
3. **HTTP receipt:** Django accepts a matching `application/csp-report` POST at a local collector. The dashboard polls Django separately and displays the accepted count and normalized fields. It never increments this counter from a frame message.

The collector uses **legacy `report-uri`**, which CSP documents as deprecated in favor of `report-to`. This lesson intentionally exercises the legacy wire format supported by the configured Chromium tests. It does not implement Reporting API endpoints, batching, or `Reporting-Endpoints`.

## Fixtures and positive control

Every run includes an allowed control frame as well as the selected experiment.

| Fixture | Experiment policy | Worker result | Local event | HTTP report |
| --- | --- | --- | --- | --- |
| Explicit allow | Enforced `worker-src 'self'` | Marker arrives | None expected | None expected |
| Enforced deny | Enforced `worker-src 'none'` | No marker; worker error | `worker-src`, `enforce` | Accepted enforcement report |
| Report-only deny | Enforced `worker-src 'self'` plus report-only `worker-src 'none'` | Marker arrives | `worker-src`, `report` | Accepted report-only report |

The allowed control verifies that the worker route, browser Worker support, fixed script, and message handler work. The report-only case demonstrates that reporting a violation does not itself block execution. An independently enforced policy can still block a resource even when another policy is report-only.

## Walkthrough

1. Run **Control: explicitly allow the local worker**. Both frames show the marker; the initial observation should contain zero HTTP reports.
2. Select **Enforce: deny the local worker** and run again. The allowed control still works. The experiment has a local `worker-src: enforce` event and no worker marker.
3. Inspect DevTools Network for `POST /api/worker/report/` with `Content-Type: application/csp-report` and status `204`. Inspect the response headers of the experiment frame to find its enforced CSP and report destination.
4. Read the dashboard's accepted HTTP report count. This is fetched from Django, separate from the event displayed in step 2.
5. Select **Report-only: observe without blocking**. Both workers now return the marker, while the experiment records a local `report` event and a received HTTP report.
6. Inspect both response headers. `Content-Security-Policy` allows the worker; `Content-Security-Policy-Report-Only` observes `worker-src 'none'`.

The dashboard waits up to 15 seconds for execution and HTTP delivery. Reports can be delayed or suppressed by browser behavior, extensions, or network failures. A timeout is shown as **inconclusive**, never as proof that a policy was safe or that an HTTP report arrived. Rerun to create fresh documents if delivery is delayed. Zero reports describes the observation so far, not a permanent guarantee.

## Implementation boundaries

- Preparation is a normal CSRF-protected POST with one exact fixture identifier. Frame, worker-script, and receipt-reading requests are session-owned and restricted to the configured main origin.
- Each new run invalidates that session's previous run. A locked in-process store keeps at most 128 runs for 300 seconds, with at most eight accepted reports per mode. Starting enough other runs evicts the oldest run; restarting Django loses receipts. This is a single-process teaching collector, not durable or distributed storage.
- The report callback alone is CSRF-exempt because the browser protocol cannot attach the application's CSRF header. A fresh 192-bit capability in its URL binds delivery to a prepared run and mode; report delivery does not depend on cookies.
- The collector limits body size and fields, rejects duplicate JSON fields, and checks the exact document URI, blocked worker URI, policy, directive, disposition, and document status against the current run. It retains only normalized directive/disposition/path/status fields. Raw policy, URL, or sample strings are never displayed as HTML.
- Possession of a report capability and its expected policy is enough to submit a matching report. CSP reports are untrusted telemetry, not cryptographic evidence of a particular browser. The automated browser tests additionally observe the browser's own POST; manually posting a report only tests the parser.
- Both the iframe attribute and enforced header use `sandbox allow-scripts allow-same-origin`. Same-origin access is needed for this fixed worker route. This combination is **not isolation for arbitrary untrusted JavaScript**; the documents contain only trusted, server-owned code. Do not reuse this frame contract for uploaded HTML or freeform XSS payloads.
- The document allows only its nonced observer/style and the selected worker source. Forms, nested frames, connections, and objects are denied. The worker response has its own policy denying further script imports, connections, and workers.
- The dashboard accepts local telemetry only from the expected frame window, exact origin, current run, known mode, and bounded schema. Such validation handles accidental or unrelated messages; it is not a defense against malicious same-origin code.

The small worker's only behavior is:

```javascript
self.postMessage('HARMLESS_WORKER_MARKER');
self.close();
```

An enforced policy selects whether that worker may start:

```http
Content-Security-Policy: ...; worker-src 'none'; report-uri /api/worker/report/?run=...&mode=experiment&cap=...
```

The report-only comparison instead leaves enforced worker loading permitted and adds:

```http
Content-Security-Policy-Report-Only: worker-src 'none'; report-uri /api/worker/report/?run=...&mode=experiment&cap=...
```

## Verification and remaining scope

Backend tests cover fixture selection, fresh nonces, correct policy headers, session separation, capability revocation, malformed or mismatched reports, strict origin checks, report/run caps, expiration, and the narrow CSRF exemption. Browser tests exercise real dedicated workers and actual browser-generated HTTP reports for both enforcement and report-only policies, plus positive controls and stale/forged telemetry handling.

This lesson does not cover SharedWorker, ServiceWorker, blob/data worker source rules, module workers, worker import graphs, `child-src`/`script-src`/`default-src` fallback precedence, nested workers, browser interoperability, Reporting API delivery, report deduplication pipelines, or production retention/privacy policy. Those need additional fixtures and deployment decisions. See the main [CSP/XSS checklist](../../CSP_XSS_HARMLESS_TESTS.md) for broader CSP topics.

## Primary references

- [W3C CSP: worker-src](https://www.w3.org/TR/CSP3/#directive-worker-src)
- [W3C CSP: report-only response header](https://www.w3.org/TR/CSP3/#csp-report-only-header)
- [W3C CSP: report-uri and its deprecated report format](https://www.w3.org/TR/CSP3/#directive-report-uri)
- [W3C CSP: violation DOM events](https://www.w3.org/TR/CSP3/#violation-events)
