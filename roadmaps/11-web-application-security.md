# 11. Web application security

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#11-web-application-security)

<!-- TOPIC-TOC:START -->

## Contents

- [11.1 Map the application before testing](#111-map-the-application-before-testing)
- [11.2 Identity, authorization, and session weaknesses](#112-identity-authorization-and-session-weaknesses)
- [11.3 Injection, interpretation, and unsafe server behavior](#113-injection-interpretation-and-unsafe-server-behavior)
- [11.4 Browser, frontend, and content security](#114-browser-frontend-and-content-security)
- [11.5 HTTP intermediaries, caches, and application logic](#115-http-intermediaries-caches-and-application-logic)
- [11.6 Practice sequence and exit criteria](#116-practice-sequence-and-exit-criteria)
- [Expanded study sequence: build, trace, test, repair](#expanded-study-sequence-build-trace-test-repair)
  - [Phase A: understand normal requests and state](#phase-a-understand-normal-requests-and-state)
  - [Phase B: make authorization and lifecycle reliable](#phase-b-make-authorization-and-lifecycle-reliable)
  - [Phase C: follow data into interpreters](#phase-c-follow-data-into-interpreters)
  - [Phase D: browser behavior and content boundaries](#phase-d-browser-behavior-and-content-boundaries)
- [Focused scenario labs](#focused-scenario-labs)
  - [Lab 1: export authorization after a role change](#lab-1-export-authorization-after-a-role-change)
  - [Lab 2: structured input and stored output](#lab-2-structured-input-and-stored-output)
  - [Lab 3: upload and background processing](#lab-3-upload-and-background-processing)
  - [Lab 4: personalized content and shared caching](#lab-4-personalized-content-and-shared-caching)
- [Common errors, troubleshooting, and completion](#common-errors-troubleshooting-and-completion)

<!-- TOPIC-TOC:END -->



**Priority:** Core: application mapping, access control, sessions, common injection, browser boundaries, business logic, and reporting. Track depth: unusual interpreters, desynchronization, advanced cache interactions, and framework-specific behavior. Treat advanced items as a continuing study backlog rather than requiring expert ability before every junior role.

**Prerequisites:** TCP/IP, DNS, TLS, HTTP, HTML/CSS/JavaScript, cookies, SQL, one server-side language, Git, and an isolated application you can reset. First build a small application with registration, login, two user roles, two tenants, a database, uploads, and a background task. Understanding normal behavior is part of testing it.

**Study method:** For every flaw below, record the trust boundary, root cause, preconditions, smallest harmless verification, affected security property, durable remediation, and a regression test. Use your own applications or explicitly provided training environments. Keep synthetic identities and data throughout. The assignments and completion thresholds here are suggested learning targets.

## 11.1 Map the application before testing

- [ ] Trace browser → CDN/cache → reverse proxy → application → database → queue/worker → third-party service. Mark where identity, authorization, decoding, validation, and logging happen.
- [ ] Learn request methods, status codes, headers, content types, redirects, compression, multipart bodies, URL encoding, Unicode normalization, HTTP/1.1 framing, HTTP/2 streams, and HTTP/3 concepts.
- [ ] Distinguish origin from site; understand same-origin policy, CORS, credentialed requests, browser storage, cookie scope, and the difference between a browser restriction and a server authorization decision.
- [ ] Inventory routes, parameters, hidden fields, forms, JavaScript bundles, API calls, file handlers, administrative features, exports, search, webhooks, alternate formats, and asynchronous jobs.
- [ ] Make a role–resource–action matrix covering anonymous, ordinary, privileged, suspended, and deleted users; add a tenant dimension. Include read, create, update, delete, share, bulk operations, and background processing.
- [ ] Record feature prerequisites and business invariants: who owns an object, whether a discount is single-use, which state transitions are legal, and which actions require fresh authentication.
- [ ] Practice browser developer tools, an intercepting proxy, request comparison, application logs, debugger breakpoints, and database inspection. Learn tool scope controls and request budgets before using automation.

Use the [OWASP Web Security Testing Guide](https://owasp.org/projects/web-security-testing-guide) to organize assessment coverage and [OWASP ASVS](https://owasp.org/projects/asvs) to select verifiable security requirements. Record the version used because requirement identifiers and content can change.

## 11.2 Identity, authorization, and session weaknesses

- [ ] Authentication: account enumeration, inconsistent login paths, weak registration verification, recovery flows, reset-token lifecycle, email changes, MFA enrollment/reset, recovery codes, remembered devices, and passwordless login.
- [ ] Sessions: unpredictable identifiers, fixation, rotation after authentication or privilege changes, cookie flags, idle and absolute timeout, logout, revocation, concurrent sessions, device lists, and session handling after account suspension.
- [ ] Access control: horizontal and vertical privilege boundaries, insecure direct object references, function-level checks, object-property restrictions, tenant isolation, ownership transfers, invitation acceptance, and shared-link permissions.
- [ ] Check authorization again in exports, search results, nested resources, batch operations, downloads, workers, caches, and alternative API versions. Hiding a control in the interface does not enforce access.
- [ ] CSRF: identify browser-supplied ambient credentials, state-changing actions, login CSRF, anti-CSRF token validation, origin checks, and SameSite limitations. Understand how XSS can undermine browser-side defenses.

**Lab:** Create two users in separate tenants and one administrator. Demonstrate one missing ownership check using a single synthetic record. Add centralized authorization, then test owner, non-owner, other tenant, administrator, anonymous, and suspended identities. Verify both content and side effects: a denied response alone is insufficient if a worker still performs the action.

## 11.3 Injection, interpretation, and unsafe server behavior

- [ ] SQL injection: query construction, prepared statements, ORM escape hatches, dynamic identifiers, second-order data, and database privilege boundaries. Learn why parameterization and business validation solve different problems.
- [ ] NoSQL, LDAP, XPath, expression-language, and log injection: recognize the interpreter and grammar involved instead of assuming every injection behaves like SQL.
- [ ] OS command and argument injection: shell invocation, unsafe process construction, option interpretation, executable allowlists, and least-privilege workers.
- [ ] Server-side template injection: user-controlled templates versus ordinary template data, dangerous rendering helpers, and sandbox limitations.
- [ ] Path traversal and local/remote file inclusion: canonicalization, alternate separators, symbolic links, archive extraction, working directories, and storage-root enforcement.
- [ ] SSRF: URL-fetching features, redirects, parser discrepancies, DNS resolution, private/internal destinations, service credentials, allowed schemes, egress controls, and response handling. Verify only against a local mock service you own.
- [ ] XML external entities and unsafe XML processing: external resource resolution, DTD behavior, parser defaults, schema validation, and resource exhaustion safeguards.
- [ ] Unsafe deserialization: automatic object construction, untrusted type metadata, framework signing assumptions, schema-based formats, and unsafe convenience methods. Separate integrity protection from safe parsing.
- [ ] File uploads: extension/MIME/content agreement, generated filenames, authorization, executable content, storage outside served code paths, image/document processing, size limits, archive handling, and safe download headers.
- [ ] Type confusion and parser differences: duplicate parameters, parameter pollution, duplicate JSON keys, content-type mismatch, numeric coercion, null handling, Unicode ambiguity, and mismatched validation across layers.
- [ ] Header injection/response splitting, unsafe redirects, and generated-content injection in CSV exports, email, PDFs, and documents. Follow data into the next interpreter, including a spreadsheet opened by an administrator.
- [ ] Resource exhaustion: inefficient regular expressions, large/recursive documents, decompression, expensive queries, unbounded pagination, and uncontrolled job creation. Study limits through bounded local tests, not service disruption.

**Lab:** Choose three different interpreters or parsers. For each, trace untrusted input to its dangerous use, verify a harmless observable effect, replace the unsafe construction with a safe API or strict schema, and add tests for valid input, rejected input, encoding variants, and downstream behavior.

## 11.4 Browser, frontend, and content security

- [ ] Reflected, stored, and DOM-based XSS; context-sensitive output encoding; HTML sanitization; safe DOM APIs; framework escape bypasses; and third-party script trust.
- [ ] DOM sources and sinks, `postMessage` origin/source checks, DOM clobbering, JavaScript prototype pollution, dynamic script loading, JSONP/legacy integrations, and unsafe client-side routing.
- [ ] CORS origin matching, credential behavior, preflight handling, exposed headers, and why permitted browser reads must match the application's intended trust relationship.
- [ ] Clickjacking, framing policy, opener relationships, cross-origin information leaks, referrer leakage, mixed content, open redirects, and sensitive information in URLs.
- [ ] Content Security Policy, nonces/hashes, Trusted Types where supported, HSTS, MIME handling, Permissions Policy, and cross-origin isolation. Treat headers as supporting controls, with compatibility and deployment tests.
- [ ] Service workers, cache storage, local/session storage, IndexedDB, source maps, browser extensions, analytics scripts, and frontend build-time variables. Determine which data persists after logout or account switching.
- [ ] Server-side rendering, hydration, static generation, incremental revalidation, and server components: identify which code runs where and where privileged data can enter a public response.

**Lab:** Repair one stored-content flaw and one DOM data-flow flaw in your own application. Verify the intended formatted content still works, unsafe input stays inert, private data does not appear in public output, and the relevant browser policy is enforced without breaking legitimate pages.

## 11.5 HTTP intermediaries, caches, and application logic

- [ ] Request smuggling/desynchronization: inconsistent message boundaries, normalization, HTTP/2-to-HTTP/1 translation, connection reuse, and frontend/backend disagreement. Practice only in a dedicated proxy/backend lab with no unrelated users.
- [ ] Host and forwarded-header trust, absolute URL generation, proxy identity headers, redirect construction, and trusted-proxy configuration.
- [ ] Alternative HTTP methods, method overrides, routing inconsistencies, path normalization, and access controls that differ between the edge, framework router, and application handler.
- [ ] Cache poisoning and cache deception: cache keys, unkeyed inputs, `Vary`, personalized responses, authentication state, path normalization, query handling, CDN rules, and purge behavior.
- [ ] Business logic: skipped workflow steps, price/quantity/currency trust, rounding, coupon reuse, refunds, entitlements, trials, referral systems, invitations, consent, account linking, and administrative overrides.
- [ ] Races and state transitions: check-then-act flaws, duplicate redemption, transaction isolation, unique constraints, locking, atomic updates, idempotency keys, retry semantics, and partial failure recovery.
- [ ] Information exposure and configuration: debug pages, verbose errors, backup artifacts, test endpoints, directory indexes, weak security defaults, public object storage links, and secrets in application logs.
- [ ] Reliability as a security property: fail-open checks, inconsistent authorization during outages, stale caches, delayed revocation, queue retries, and incomplete cleanup after failed transactions.

The [PortSwigger topic catalog](https://portswigger.net/web-security/all-topics) provides practice across server, browser, and advanced web topics. Its [race-condition material](https://portswigger.net/web-security/race-conditions) is useful when studying concurrent state changes.

**Lab:** Implement a synthetic single-use coupon and test bounded concurrent requests locally. Enforce the invariant with an atomic database operation or transaction, then verify retries, duplicate requests, and worker processing cannot create a second redemption. Separately configure a local cache and prove that two accounts never receive one another's personalized response.

## 11.6 Practice sequence and exit criteria

1. Build and document the small application; perform a manual walkthrough before scanning.
2. Complete at least 25 training exercises spanning identity, access control, injection, browser security, files, SSRF, logic, and intermediaries. Revisit five without walkthroughs after a delay.
3. Assess a local [OWASP Juice Shop](https://owasp.org/projects/juice-shop) or [WebGoat](https://owasp.org/projects/webgoat) deployment and distinguish verified findings from scanner suggestions.
4. Produce at least eight concise finding records and remediate four in source code, with positive and negative regression tests.
5. Pass a fresh application review: explain coverage gaps, detect a planted authorization defect, identify an unsafe input-to-sink path, and propose a fix that preserves intended behavior.

**Exit evidence:** application map; role/tenant matrix; repeatable notes; eight findings across at least five root causes; four verified repairs; and a checklist explaining tested, untested, and inapplicable controls.

## Expanded study sequence: build, trace, test, repair

Use a small two-tenant application as the continuous reference project. Keep a resettable database containing fictional users, invoices, uploads, and scheduled exports. Implement the secure form first when possible; deliberately weaken one clearly labeled local fixture at a time. Do not publish the vulnerable fixture as a public service.

### Phase A: understand normal requests and state

- [ ] Trace registration, login, record creation, sharing, export, and logout through browser requests, server handlers, database transactions, and background jobs.
- [ ] Identify all places that create or change identity context: authentication middleware, trusted proxy headers, tenant selection, worker messages, and administrative impersonation features.
- [ ] Draw a state machine for one workflow, including pending, approved, canceled, and expired states. Write which roles may perform each transition and which transitions must be atomic.
- [ ] Build a route catalog containing method, input schema, authentication requirement, authorization policy, side effects, response sensitivity, cache policy, and rate or size limit.
- [ ] Establish browser and server controls: ordinary successful request, deliberately invalid request, unauthenticated request, another tenant's request, and suspended-user request.
- [ ] Learn to preserve a reproducible request without saving real credentials. Replace session values and personal data with documented test-fixture references in portfolio material.

**Phase gate:** explain where a request is decoded, authenticated, authorized, validated, executed, serialized, cached, and logged. If a stage is absent, record whether that is intentional.

### Phase B: make authorization and lifecycle reliable

- [ ] Test resources through list, detail, nested relationship, search, export, download, and batch routes. A protected detail route does not prove an export uses the same policy.
- [ ] Compare object creation and updates: determine whether the server derives ownership and tenant identity from trusted context or accepts them from the caller.
- [ ] Test invitations, ownership transfers, account suspension, restored accounts, and role removal. Identify stale sessions, caches, and queued work that retain earlier permissions.
- [ ] For sensitive actions, define when fresh authentication is required and how the server verifies that freshness. Include MFA reset and recovery because they change the authentication boundary.
- [ ] Verify both response and stored state after denial. Inspect whether messages, emails, files, billing events, or scheduled work were created despite a rejected request.
- [ ] Add positive tests for intended sharing and delegated administration so a restrictive repair preserves legitimate use.

**Phase gate:** produce a role-resource-action matrix with explicit tenant and lifecycle dimensions, then demonstrate one repaired authorization path across both direct and asynchronous access.

### Phase C: follow data into interpreters

Learn one representative flaw deeply before broadening to another interpreter. For each family, name the parser, encoding layers, trusted data, untrusted data, dangerous operation, and invariant that should hold. Use harmless markers and local mock destinations for all validation.

| Family | Minimal learning validation | Durable repair to verify |
| --- | --- | --- |
| SQL and related query injection | Trace controlled data into a query and compare a bounded synthetic query result | Parameterize values; constrain dynamic identifiers; use an appropriately limited database identity |
| NoSQL, LDAP, and XPath | Verify whether caller-supplied structure changes the intended query shape | Build typed queries with appropriate APIs and explicit allowed operators or attributes |
| Command or argument injection | Use a local stub executable that records received arguments | Avoid shell construction; use structured argument APIs and constrain executable/options |
| Template injection | Check whether supplied text becomes template structure in an isolated renderer | Keep templates trusted and pass untrusted values only as data |
| Path traversal and archive extraction | Attempt access to a harmless sentinel outside the intended test directory | Resolve and enforce storage boundaries; handle links and archive members safely |
| SSRF | Observe contact with a local mock service outside the intended allowed destination set | Restrict schemes/destinations, validate redirects and resolution behavior, and enforce egress policy |
| XML external resource handling | Observe a local mock resource request during bounded parsing | Disable unnecessary external resolution and configure parser limits explicitly |
| Unsafe deserialization | Show unexpected type construction or side effect using a benign test class | Use schema-driven formats and restricted data structures; avoid untrusted object construction |
| File upload | Verify storage location, interpretation, access policy, and download behavior using harmless files | Generate names, constrain accepted content, separate storage from execution, authorize retrieval |
| Header and generated-document injection | Track a marker through a local response, email preview, or document fixture | Use structured APIs and escaping appropriate to the final interpreter |
| Type and parser disagreement | Compare duplicate, missing, null, differently encoded, and differently typed values | Use one documented schema and consistent normalization before validation |
| Resource exhaustion | Measure cost with small bounded input growth and a strict timeout | Enforce size, depth, time, concurrency, and complexity limits at relevant layers |

An error alone rarely proves a security impact. Describe how the changed parsing crosses a trust boundary and confirm the corrected implementation accepts legitimate input.

### Phase D: browser behavior and content boundaries

- [ ] Trace data from URL, storage, messages, and API responses into DOM operations. Distinguish text insertion, HTML interpretation, URL handling, and script execution contexts.
- [ ] Compare output encoding with HTML sanitization. Encoding is appropriate when displaying text; intentional rich content needs a defined allowed-content policy and a maintained sanitizer.
- [ ] Verify reflected, stored, and DOM-mediated content separately. A server-side repair may leave client-side reconstruction unsafe.
- [ ] Test framing, CORS, `postMessage`, opener relationships, and cookie behavior using two local origins you own. State exactly which origin is trusted and why.
- [ ] Examine persistent browser data across logout, tenant changes, role reduction, and offline use. Distinguish accidental local retention from data that the product deliberately supports offline.
- [ ] Introduce CSP or another supporting browser policy incrementally and inspect violations. Keep application-level encoding and authorization tests even when the browser policy blocks a demonstration.

**Phase gate:** explain whether a restriction belongs to the browser, server, application policy, or network. Do not assume a browser refusing to expose a response means the server refused its side effect.

## Focused scenario labs

### Lab 1: export authorization after a role change

**Setup:** two tenants, ordinary and administrator roles, and a queued export of fictional records. **Action:** create an export, reduce the requester's privileges, and observe download and worker authorization using test identities. **Expected result:** behavior matches a documented policy for queued work after revocation. **Evidence:** submission identity, policy decision, job record, generated file scope, and download log. **Control:** an authorized export remains usable. **Fix:** enforce the selected policy when processing and delivering results, including tenant-specific storage access.

### Lab 2: structured input and stored output

**Setup:** a local comment feature, a query-backed search, and rich-text rendering. **Action:** trace harmless controlled input through query construction, persistence, serialization, and browser rendering. **Expected result:** inputs retain their intended data meaning at each stage. **Evidence:** source-to-sink diagram, relevant code, request/response, and browser result. **Control:** valid searching and permitted formatting work. **Fix:** parameterize the query and use context-correct encoding or sanitization; add separate regression checks for each boundary.

### Lab 3: upload and background processing

**Setup:** local file storage, a thumbnail worker, and a fictional user attachment. **Action:** test ownership, unsupported file types, filename normalization, bounded size limits, and failed processing. **Expected result:** unsupported content is rejected safely, permitted content is isolated, and failed jobs do not expose partial files. **Evidence:** storage path, access decision, worker logs, and cleanup state. **Control:** a valid upload can be processed and downloaded by its owner. **Fix:** enforce safe storage, constrained processing, explicit limits, and authorization at retrieval.

### Lab 4: personalized content and shared caching

**Setup:** a dedicated local caching proxy with two synthetic users and no unrelated traffic. **Action:** request a personalized page as each identity and inspect cache keys, headers, and backend logs. **Expected result:** private content is never served to the wrong identity. **Evidence:** identities, cache decisions, response identifiers, and before/after configuration. **Control:** explicitly public static content remains cacheable. **Fix:** correct cacheability and key policy, invalidate affected entries, and test relevant routing variants. Advanced desynchronization experiments require a separate disposable proxy/backend fixture.

## Common errors, troubleshooting, and completion

When a test stops reproducing, verify account state, CSRF/session freshness, route version, feature flags, cache state, and backend instance before assuming a repair. When a response is denied, inspect side effects. When the browser blocks a request, compare the actual server decision. When a scanner reports a class, identify the exact sink and preconditions. When one payload-shaped fixture is blocked, test the underlying invariant with a small set of equivalent benign forms.

Complete a repeatable capstone with an application map, authorization matrix, six confirmed-and-repaired weaknesses spanning at least four families, and evidence for both denied and permitted behavior. At least one finding must involve a background job or lifecycle change, and one must require manual business reasoning. Include an intentionally inconclusive observation and explain the evidence still needed. Pass when another learner can reset the fixture, reproduce the boundary failure, apply the fix, and rerun meaningful regression tests. Use the WSTG, ASVS, and implementation references above to record what was covered and what remains a specialization backlog.