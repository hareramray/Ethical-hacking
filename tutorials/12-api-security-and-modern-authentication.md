# 12. Tutorial: API security and modern authentication

[Index](README.md) · [Complete source curriculum](curriculum/12-api-security-and-modern-authentication.md) · [Original roadmap](../roadmaps/12-api-security-and-modern-authentication.md)

## Separate contracts, identity, and permission

An API request passes three different tests: is its structure valid, is its identity acceptable, and may that identity perform this operation? A signed token does not answer the third question. Prerequisites are tutorial 11, JSON/XML, TLS, asymmetric-cryptography concepts, and basic API clients. Use fictional tenants Alpha and Beta, a local API, and an established identity library with a local provider or permitted test tenant. Do not implement your own production token validator for the exercise.

REST/JSON, property/object/function authorization, lifecycle, and OAuth/OIDC form the core path. GraphQL, gRPC, streams, SAML, and WebAuthn are taught below as distinct modules so the whole curriculum remains visible, even when your first application uses only one transport.

## Lesson 1: specify a resource contract

Define an invoice with identifier, tenant, owner, status, amount, currency, and display label. Tenant, owner, role, and approval state should not become caller-controlled merely because a serializer accepts them. Specify mutable and read-only fields, required and nullable fields, enumerations, lengths, numeric bounds, nested objects, array sizes, filter operators, sorting fields, pagination, and batch limits.

Absent, null, empty string, zero, and false are not interchangeable. In a partial update, absent might mean “keep current value” while null might mean “clear,” if permitted. Replacement has a different contract. Duplicate/unknown fields and incompatible content types need defined behavior. Schema validity still cannot authorize an impossible transition such as approving a canceled invoice.

Inventory documented and undocumented routes, old versions, mobile/partner/admin interfaces, exports, background consumers, batch endpoints, and the implementation's OpenAPI or equivalent contract. Record method, status/error schema, content negotiation, side effects, identity, authorization, response sensitivity, idempotency, limits, and version compatibility. Schema evolution can leave old clients or workers enforcing obsolete policy.

Review output serialization independently. Input filtering does not stop a response from exposing internal roles, secret fields, or unrelated records. Use explicit response schemas and correlation IDs; return useful client errors without stack traces or sensitive records. Compare returned content and stored state with the contract.

## Lesson 2: a complete property-authorization lab

Save this as `profile_lab.py` and run `python profile_lab.py` with Python 3 on Windows or Linux. It uses only in-memory synthetic data.

```python
from copy import deepcopy

profiles = {"alice": {"tenant": "alpha", "role": "member",
                      "display_name": "Alice", "internal_note": "TRAINING"}}

def update_profile(subject, account, body):
    stored = profiles[account]
    if not subject["active"] or subject["tenant"] != stored["tenant"]:
        raise PermissionError("denied")
    if subject["name"] != account:
        raise PermissionError("denied")
    if set(body) - {"display_name"}:
        raise ValueError("unsupported property")
    label = body.get("display_name", stored["display_name"])
    if not isinstance(label, str) or not 1 <= len(label) <= 40:
        raise ValueError("invalid display name")
    stored["display_name"] = label
    return {"display_name": stored["display_name"]}

alice = {"name": "alice", "tenant": "alpha", "active": True}
assert update_profile(alice, "alice", {"display_name": "A. Example"}) == {
    "display_name": "A. Example"}
before = deepcopy(profiles)
try:
    update_profile(alice, "alice", {"role": "admin"})
except ValueError:
    pass
else:
    raise AssertionError("forbidden property accepted")
assert profiles == before
assert "internal_note" not in update_profile(alice, "alice", {})
print("valid update passed; forbidden write denied; internal field absent")
```

The expected printed line confirms three independent claims. Now test inactive Alice, a Beta identity, and a second Alpha user. Add null, empty, overlong, and numeric display names. A denial must leave state unchanged. The [runnable API write lesson](../labs/browser_security/API_WRITES.md) compares blind assignment with object and field checks against disposable SQLite profiles. Inspect before/after state for legitimate updates, peer and tenant boundaries, protected fields, and mixed patches that must fail without partial changes.

Create at least twenty cases by crossing identities with direct lookup, list/search, nested object, property edit, export, old API version, batch, and asynchronous operation. Define mixed-batch semantics: reject all atomically or report item-level decisions without applying denied items. Bind idempotency keys to subject/tenant/action and preserve authorization on repeats. Idempotency does not grant permission.

## Lesson 3: resources, workflows, partners, and webhooks

Bound cost across page and batch sizes, uploads, query complexity, concurrency, background jobs, and paid integrations. Account-level and tenant-level limits matter when many individual credentials can each stay below a per-token threshold. Use a fixed small number of local operations and explicit time/memory budgets when measuring limits.

Describe purchase, reservation, invitation, password recovery, publication, and inventory allocation as legal state transitions. Server-derived price and allocation decisions should survive retries and partial failures. Test delayed jobs after deletion, role change, ownership transfer, or tenant suspension according to the documented policy.

Partner APIs are untrusted inputs despite business relationships. Validate TLS/transport identity, schemas, lengths, identifiers, and error content. Scope credentials, constrain redirects, use deadlines, and make retries bounded and idempotent where required. An upstream identifier is not proof the current user owns the local object it names.

For webhooks, separate authenticity, freshness, and business deduplication. Verify signatures with the provider's defined byte representation and library, enforce the chosen timestamp policy, track event IDs, constrain delivery destinations, and define key rotation overlap. Duplicate delivery is normal in many event systems; it must not duplicate a payment or inventory effect. Event ordering and dead-letter recovery need explicit state handling.

The [runnable webhook lesson](../labs/browser_security/WEBHOOKS.md) demonstrates these first three boundaries with real HMAC checks and a disposable points ledger. Compare a valid event, tampered bytes, stale deliveries, and signed retries with the same event ID. The lesson's local signing format is explicit and does not represent every provider's protocol.

## Lesson 4: understand the protocol roles

Authentication proves who is acting; authorization grants an operation; federation lets systems rely on an identity authority; provisioning creates or updates local accounts; sessions preserve application state. These functions can fail independently.

| Role | Responsibility |
| --- | --- |
| Resource owner/user | Authorizes a client and authenticates where required |
| Client | Requests access and handles the protocol response |
| Authorization server | Issues authorization codes and access credentials under policy |
| Identity provider | Supplies authentication information to relying applications |
| Resource server | Validates the access credential intended for it and enforces API policy |
| Relying party | Consumes an authentication assertion for its own login/session purpose |

In authorization-code flow, the browser navigates to the provider, authentication/consent occurs there, and the client receives a short-lived code at a registered callback. The client exchanges it under the protocol's checks. PKCE binds the exchange to the initiating client instance through a verifier/challenge. Confidential and public clients have different credential capabilities. Do not embed a confidential client secret in a browser application.

Configure exact redirect trust, issuer selection, correlation/state, PKCE, client authentication where applicable, resource/audience restrictions, scopes, consent, refresh policy, and token exchange as supported. Implicit and password-grant flows belong in legacy review; select new designs from current security guidance. Study interception, mix-up, replay, and redirects as failed binding assumptions. [OAuth security best current practice, RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html).

OIDC adds an identity layer: discovery, ID tokens, subject identifiers, UserInfo, nonce, authentication freshness, account linking, and logout. An ID token is intended for the relying party's authentication processing; it is not automatically an API access credential. Validate issuer, audience, request binding, and token purpose using the library's supported configuration. [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html).

JWT is a representation; JWS supplies signing/integrity and JWE supplies encryption. Base64 decoding does not authenticate a token. Validators need trusted algorithm/key selection, signature checks, issuer/audience, expiration/not-before, token-type separation, and the appropriate application policy. Key IDs choose among trusted issuer keys, not arbitrary untrusted locations. JWKS retrieval/caching/rotation needs bounded network behavior and explicit failure handling. Document how key rollover and revocation interact with already issued credentials.

Practice signature and claim validation in the [runnable JWT lesson](../labs/browser_security/JWT_VALIDATION.md). It uses PyJWT, fresh local signing keys, fixed token scenarios, and a separate subject permission check. It does not implement OAuth/OIDC, discovery, key rotation, or browser authentication.

## Lesson 5: model the complete identity lifecycle

For each transition, record entry conditions, proof, state changes, expiry, revocation, notification, audit event, and recovery. Set a measurable revocation requirement before the lab; locally verified access tokens and server-side sessions can have different invalidation mechanisms.

| Stage | Boundary to teach and test |
| --- | --- |
| Invitation and registration | Intended organization/identity, expiration, revocation, reuse, conflicting account |
| Contact verification | Proves a selected channel, not unrelated authority; pending contact changes stay controlled |
| Enrollment | Passwords, MFA, passkeys, API keys, recovery methods require adequate prior proof |
| Login/federation | Response belongs to this request, issuer, recipient, and selected account |
| Session creation | New/rotated identity, cookie settings, lifetime, device association, server state |
| Elevation | Fresh proof, limited authority, bounded duration |
| Refresh | Correct client/state; rotation, duplicate requests, and reuse follow provider semantics |
| Recovery/factor reset | Does not silently lower assurance; sensitive changes notify and log |
| Email/organization/ownership change | Re-evaluate linking, local roles, sessions, and pending invitations |
| Suspension/deprovisioning | Measure directory, local account, cached claim, API key, session, and SaaS delay |
| Logout/revocation | Browser logout, application session termination, refresh revocation, and access expiry differ |
| Deletion/retention | Remove access, retain required audit evidence safely, prevent identifier reassociation |

SCIM provisioning/deprovisioning, service accounts, changed emails, lost devices, disabled employees, and application-issued keys all belong in this lifecycle. Keep production and test issuers, audiences, keys, and identities separate. Prevent tokens entering URLs, analytics, crash reports, debug output, or browser-readable storage without an explicit architecture decision.

## Lesson 6: apply the same policy across protocols

| Protocol | Core mechanism | Exercise and repair focus |
| --- | --- | --- |
| GraphQL | Schema fields dispatch to resolvers; queries/mutations/subscriptions can nest relationships | Share object/property policy across resolvers, node IDs, aliases and batches; bound depth/cost/pagination, sanitize errors, revisit subscription authorization |
| gRPC | Protocol Buffers define services/messages; metadata and interceptors carry context | Verify transport/service identity, every method and streaming message, deadlines/cancellation, compression/message limits, and errors; reflection exposure alone does not prove impact |
| WebSockets | Handshake opens a persistent channel with later messages/subscriptions | Validate origin, identity and message schema; bind tenant subscriptions, enforce size/frequency limits, expiration/revocation, and reconnect behavior |
| Event-driven APIs | Producers and consumers communicate through queues/topics | Review permissions, provenance, schema evolution, tenant routing, replay/duplicates, delayed decisions, ordering and recovery |
| SAML | Identity provider issues assertions consumed by a service provider | Trusted metadata/keys, signature processing, audience/recipient/destination, request correlation, time/replay, XML safety, identity mapping, certificate rollover |
| WebAuthn/passkeys | Registration associates credentials; authentication proves possession under RP/origin/challenge rules | Verify challenge freshness, RP ID/origin, user presence/verification policy, credential association, enrollment, authenticator options, sync/device-loss/recovery |

For SAML, signature-wrapping concerns arise when verified XML and the assertion used by the application are not the same trusted object; use a maintained implementation instead of writing signature parsing. For WebAuthn, study the [W3C specification](https://www.w3.org/TR/webauthn-3/) with the actual platform/library support. Introspection, reflection, or credential synchronization features are not automatically vulnerabilities: compare their behavior to intended policy and actual consequence.

Expose the same synthetic invoice through REST and one second transport. Compare owner success, cross-tenant denial, forbidden property update, and expired identity. Repair the shared policy and verify equivalent behavior through both interfaces. This avoids treating a secure REST handler as evidence that its subscription resolver is secure.

## Three scenario labs and the identity integration exercise

**Mass assignment and response exposure:** use `profile_lab.py`, preserve the response schema and stored-state assertions, and repeat through any alternate update route. Record input, output, internal state, and policy outcome. Ordinary display-name editing is the control.

**Suspension during a stream:** establish a legitimate synthetic subscription, record time, suspend the user, and observe subsequent REST requests and stream events. Keep a second active user subscribed. Access must stop within the documented interval. Repair revocation checks, session/token policy, and subscription cleanup; capture the exact credential/cache that previously retained authority.

**Webhook replay and rotation:** use a local sender/receiver with disposable keys and fictional order events. Send a valid event, replay it, deliver an older event, rotate to a second key, and test the retired key according to an explicit overlap policy. Expect each valid business event to apply once. Record event IDs, order state, validation decisions, and rotation times without recording secret keys.

**Standards-based login:** integrate code flow with PKCE through a maintained library. In the local provider/test tenant, exercise wrong issuer/audience, expired credentials, invalid state/nonce where applicable, repeated completion, refresh, logout, recovery, revoked sessions, role removal, and key rollover. Test at the component responsible for each validation rather than mutating production tokens. Document remaining access lifetime and outage behavior when discovery is unavailable.

## Troubleshooting and completion

Authentication errors can reflect clock drift, issuer/audience mismatch, stale JWKS caches, wrong environment, redirect configuration, or expired request state. Authorization failures require a separate subject/action/resource analysis. When revocation is delayed, identify the credential, session, group cache, or local role still granting access. Fixing signature validation alone cannot fix a missing tenant check.

Submit contract, endpoint inventory, lifecycle model, identity sequence, twenty or more authorization cases across two tenants, cross-protocol comparison, three repaired scenarios, key rotation, and revocation timelines. Every denial needs a legitimate control and a stored-state observation. Use the [OWASP API Security project](https://owasp.org/www-project-api-security/) as an awareness map, alongside the application's actual contracts.

**Answer-guided checks:** Why validate output separately? Safe input does not stop internal-field disclosure. Why is a successful handshake insufficient? Account state and message scope can change afterward. Why is an ID token insufficient for API access? Token purpose, intended recipient, and operation policy differ. Why might replay protection still need deduplication? A valid delivery can legitimately be retried without authorizing a second business effect.
