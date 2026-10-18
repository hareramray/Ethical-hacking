# 11. Tutorial: web application security

[Index](README.md) · [Complete source curriculum](curriculum/11-web-application-security.md) · [Original roadmap](../roadmaps/11-web-application-security.md)

## Build a system you can explain

Prerequisites are HTTP, TLS, DNS, HTML/JavaScript, SQL, Git, one server-side language, and resettable local storage. Use a disposable two-tenant application with fictional users, invoices, uploads, and queued exports. The [shared examples](examples/README.md) provide additional practice fixtures; the inline exercises here run independently. Bind any training server to loopback. Begin with secure behavior, then weaken one clearly marked local fixture at a time.

Every issue should have a boundary, preconditions, root cause, smallest harmless verification, demonstrated impact, durable repair, and positive/negative regression tests. Scanner labels do not substitute for understanding the application. The following lessons cover the core and advanced families; advanced intermediary work requires its own disposable proxy/backend fixture.

## Lesson 1: map requests, identity, and state

Draw browser → CDN/cache → reverse proxy → handler → database → queue/worker → partner service. At each step identify decoding, authentication, authorization, validation, execution, serialization, caching, and logging. Mark identity sources, tenant selection, trusted proxy headers, worker messages, and administrative impersonation. A value read from a database can remain untrusted if a user originally supplied it.

Create a route catalog with method, path, input schema, identity requirement, authorization policy, side effects, sensitivity, cache policy, and resource limits. Include forms, hidden fields, JavaScript calls, mobile/alternate API versions, search, nested objects, administrative features, sharing, exports, file handlers, webhooks, and asynchronous jobs. Use browser developer tools, a scoped intercepting proxy, logs, debugger, and database inspection to trace one normal operation end to end.

| HTTP concept | Security consequence to understand |
| --- | --- |
| Methods, status codes, redirects | A denied-looking response may still cause a write; inspect state and redirect destinations |
| Headers, content types, multipart bodies | Select parsers and upload behavior; mismatched assumptions can bypass validation |
| URL encoding and Unicode normalization | Meaning can change after validation if layers decode differently |
| Compression and framing | Compressed size differs from expanded work; message-boundary agreement matters |
| HTTP/1.1, HTTP/2, HTTP/3 | Framing and transport differ; gateway translation needs explicit compatibility testing |
| Origin versus site | Origin includes scheme, host, and port; site-based cookie rules are a different boundary |
| Same-origin policy and CORS | Browser read restrictions do not provide server-side object authorization |

Write business invariants: a coupon is used once, only permitted roles approve invoices, a tenant cannot read another tenant's records, and canceled orders cannot become shipped without the defined transition. Diagram pending → approved → completed, including canceled and expired states. Identify atomic transitions and actions needing fresh authentication.

## Lesson 2: identity, sessions, authorization, and CSRF

Authentication establishes an identity. Authorization decides whether that identity may perform a particular action on a particular object and property. Horizontal boundaries separate peers; vertical boundaries separate ordinary and privileged functions; tenant boundaries add organizational context. Unpredictable identifiers reduce guessing but do not replace authorization.

Review registration verification, account-enumeration behavior, login alternatives, passwordless flows, recovery/reset-token expiry and reuse, email changes, MFA enrollment/reset, recovery codes, remembered devices, and account linking. A strong login can be undermined by a weaker recovery path. Define enrollment and recovery proof before testing these transitions.

Sessions need unpredictable identifiers, appropriate rotation, cookie scope and flags, idle/absolute lifetime, logout, revocation, device/session visibility, concurrent-session policy, and suspension behavior. Test identity changes with fresh and existing sessions. A user removed from a role may retain stale authority through cached claims or an already queued job.

Build a matrix for anonymous, owner, same-tenant peer, other tenant, administrator, suspended, and deleted identities. Cover read/create/update/delete/share/bulk operations, ownership transfer, invitation acceptance, shared links, lists, detail, nested paths, search, exports, downloads, alternate versions, and workers. Verify both response and stored side effects. A denied export request must not silently enqueue a report. Centralized policy helps make these paths consistent. [OWASP authorization guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).

CSRF arises when a browser supplies ambient credentials to a state-changing operation an attacker can cause. Review anti-CSRF tokens, origin checks, login CSRF, and SameSite behavior in the actual deployment. CORS alone is not a general CSRF defense, and XSS can undermine browser-side protections. Keep state-changing actions out of incidental reads and test legitimate forms after adding protections.

## Lesson 3: follow data into interpreters

The central question is whether untrusted data can become executable structure or alter a privileged operation. Learn parser grammar and data flow instead of collecting payload strings.

| Family | Root cause and harmless local exercise | Durable repair |
| --- | --- | --- |
| SQL, ORM escape hatches, second-order input | Stored or immediate data enters query text; compare a synthetic quoted name against a parameterized query | Parameterize values, allowlist dynamic identifiers, restrict database rights; retain business validation |
| NoSQL, LDAP, XPath, expression and log injection | Caller-controlled operators/grammar change query or log structure | Typed builders, explicit operators/attributes, structured logging and context-appropriate encoding |
| OS command and argument injection | Data becomes shell syntax or an unintended executable option | Structured process APIs, executable/option allowlists, limited worker identity; use a stub that only records arguments |
| Server-side templates | User data is interpreted as template structure or reaches dangerous helpers | Keep templates trusted and pass input as data; do not rely solely on a sandbox |
| Traversal, inclusion, archives | Canonical paths, links, separators, or archive members escape a storage root | Enforce resolved boundaries and safe link/archive handling; test only harmless sentinel files |
| SSRF | A fetch feature trusts schemes, hosts, redirects, DNS, or parser differences | Constrain destinations and redirects, control egress and credentials; use only owned local mock destinations |
| XML external entities/DTD | Parsing resolves external resources or expands expensive structures | Disable unnecessary resolution, configure limits, and separate schema validation from resolver safety |
| Unsafe deserialization | Input controls object construction/types or unsafe convenience APIs | Schema-driven data formats and restricted types; signatures do not make a dangerous parser safe |
| Uploads | Filename/type assumptions, execution paths, worker rights, or retrieval authorization fail | Generated names, content checks, isolated storage/processing, size limits, safe headers, authorized downloads |
| Type/parser disagreement | Duplicate keys/parameters, null, coercion, encoding, or content-type differences change meaning | One explicit schema and normalization order, reject ambiguous structure |
| Headers, redirects, CSV/email/PDF/document output | Input reaches another interpreter after the original request | Structured APIs, safe destination policy, and escaping for the final consumer |
| Resource exhaustion | Regex, recursion, decompression, queries, pagination, or job creation has unbounded cost | Size/depth/time/concurrency/complexity budgets; measure only small local inputs |

Run this Python 3 exercise locally. It uses an in-memory database and demonstrates values remaining data without an exploitation string:

```python
import html
import sqlite3

db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE comments (author TEXT, body TEXT)")
name, body = "O'Brien", "<b>TRAINING_TEXT</b>"
db.execute("INSERT INTO comments VALUES (?, ?)", (name, body))
rows = db.execute("SELECT body FROM comments WHERE author = ?", (name,)).fetchall()
assert rows == [(body,)]
print(rows[0][0])
print(html.escape(rows[0][0]))
```

Expect the stored string unchanged and the HTML-display form `&lt;b&gt;TRAINING_TEXT&lt;/b&gt;`. Parameterization protects the query boundary; output encoding protects a different boundary. Neither decides whether the caller may read the comment. For rich HTML, define allowed formatting and use a maintained sanitizer rather than escaping all formatting or creating a homemade blacklist.

## Lesson 4: browser and frontend boundaries

Reflected XSS returns input immediately; stored XSS processes persisted input; DOM-based XSS occurs through client-side data flow. Trace URL, storage, message, and API sources into text, HTML, URL, and script sinks. `textContent` displays text; HTML interpretation requires a separate content policy. Framework escaping can be bypassed by raw-HTML escape hatches. [OWASP XSS prevention guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html).

Use a local HTML file with a fixed element and assign the literal marker `<b>TRAINING</b>` through `textContent`; confirm that angle brackets appear as text. Compare intentional sanitized formatting in a separate component. Inspect server rendering and client reconstruction independently: an encoded server response can become unsafe when JavaScript later reparses it.

| Browser topic | What to learn and verify |
| --- | --- |
| `postMessage`, DOM clobbering, prototype pollution | Validate sender origin/source and schemas; avoid trusting DOM names or inherited object properties as authority |
| Dynamic scripts, JSONP, legacy routing, extensions, analytics | Third-party code can run with page privileges; inventory producers and destinations |
| CORS and preflight | Exact intended origin relationship, credentials, allowed methods/headers, and exposed response headers |
| Clickjacking and framing | Sensitive actions should follow intended framing policy; test allowed integrations too |
| Opener relationships, cross-origin leaks, referrers, URLs | Navigation and metadata can disclose state; keep credentials and sensitive records out of URLs |
| CSP, nonces/hashes, Trusted Types | Supporting controls limit dangerous interpretation; verify platform support and actual violations |
| HSTS, MIME handling, mixed content, Permissions Policy, cross-origin isolation | Transport and browser capability policies need deployment/compatibility tests |
| Service workers, Cache Storage, local/session storage, IndexedDB | Inventory persistence across logout, account switching, tenant changes, and offline operation |
| Source maps, frontend build variables | Anything shipped to the browser is available to its user; build-time configuration is not secret storage |
| SSR, hydration, static generation, incremental revalidation, server components | Determine where code runs and whether privileged data enters public generated output or shared caches |

Use two owned local origins for origin/cookie/message exercises. State which origin is trusted and why. Add CSP incrementally, observe violations, and preserve encoding and authorization tests even if the browser policy blocks a demonstration. Browser refusal to expose a response does not prove the server avoided its side effect.

## Lesson 5: intermediaries, caches, and business logic

An edge proxy, framework router, and backend must agree on message boundaries, paths, methods, identity headers, and cacheability. Request smuggling/desynchronization concerns inconsistent framing, normalization, connection reuse, and protocol translation. Study these with configuration and paired logs in a dedicated proxy/backend lab without unrelated traffic; no live shared service is needed for this lesson.

Host and forwarded headers affect URL construction, redirects, and client identity. Only trusted proxies should provide security-sensitive forwarded identity; test the real trust configuration. Alternative methods, method overrides, routing variants, and normalization must reach the same authorization policy.

Cache poisoning means an input influences a cached response in a way the key fails to represent. Cache deception causes unintended private content to be treated as cacheable. Inspect cache keys, query handling, unkeyed headers, `Vary`, authentication state, path rules, CDN configuration, and purge behavior. Start with private personalized responses excluded from shared caching, while public static content remains cacheable.

Business logic defects violate rules despite syntactically valid requests: skipped approval, caller-supplied price/quantity/currency, rounding inconsistencies, duplicate coupons/refunds, entitlement/trial/referral misuse, invitation/consent/account-linking confusion, and excessive administrative overrides. Describe each as a state invariant and test both legitimate and prohibited transitions.

For a single-use coupon, check-then-act code can let two concurrent requests both observe “unused.” The durable fix is an atomic conditional update, transaction/locking strategy, or uniqueness constraint appropriate to the data model. In an isolated SQLite fixture, create a row with `used = 0`, execute `UPDATE coupons SET used = 1 WHERE id = ? AND used = 0`, and treat exactly one changed row as success. Repeat the operation: the second attempt must change zero rows. Then add a bounded two-connection concurrency exercise with a timeout and verify the same invariant.

Idempotency makes retries safe only when keys are scoped to caller and operation and outcomes are recorded consistently. Test partial failures, queue redelivery, stale caches, delayed revocation, and dependency outages. Fail-open authorization and incomplete cleanup are security-relevant reliability defects. Also inspect debug pages, verbose errors, backup artifacts, test endpoints, directory indexes, public storage links, defaults, and secrets in logs.

## Four focused labs and evidence

**Export after role change.** Create an authorized queued export, reduce the fictional requester's role, then process and download it. Choose and document whether current authority is required at execution/delivery. Capture job context, policy decisions, output tenant, and download logs. Repair worker and storage authorization together. A second authorized export must still succeed.

**Structured input and stored output.** Extend the SQLite example into local search and comments. Trace parameterization, persistence, serialization, and rendering. Verify a quoted name, permitted rich formatting, inert unexpected markup, and authorization separately. Preserve a source-to-sink diagram and tests for each boundary.

**Upload and worker.** Use a harmless text attachment, unsupported extension, normalized filename, and small configured size boundary. Inspect generated storage names, owner-only retrieval, thumbnail/document worker identity, and failed-job cleanup. No executable upload is necessary. A valid attachment must remain processable and downloadable by its owner.

**Personalized cache.** Place two synthetic users behind an owned local cache. Request the same personalized route as A then B, compare response markers, cache decisions, and backend logs. Repair cacheability/key policy and invalidate old entries. Repeat relevant routing/query variants; verify public static assets still cache normally.

## Troubleshooting and completion

When a result changes, check session/CSRF freshness, account lifecycle, API version, feature flags, backend instance, and cache state. An error does not itself prove injection, a blocked browser read does not prove server denial, and a denied response does not prove absence of side effects. Repair the underlying invariant and test a small set of equivalent benign inputs.

Use the [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) to organize coverage. Complete 25 guided training exercises across the families above and revisit five without walkthroughs. In an owned local Juice Shop or WebGoat deployment, separate scanner suggestions from verified findings. Produce eight findings across at least five root causes, four source repairs, and then a fresh capstone with six repaired weaknesses across four families, including a worker/lifecycle issue and a manual business-logic issue. Preserve one explicitly inconclusive observation and coverage gaps.

**Answer-guided checks:** Does hiding a button authorize an operation? No; the server needs a policy decision. Does parameterization validate business rules? No; it keeps query structure separate from values. Does logout necessarily erase offline browser data? Only if the product explicitly implements that behavior. Why test the worker after a role change? Earlier request authorization may no longer match the required execution-time policy. Why retain a successful purchase or upload control? A repair that disables the feature has not preserved the intended contract.
