# 12. API security and modern authentication

[All topic roadmaps](README.md) | [Original master roadmap](../../ETHICAL_HACKING_ROADMAP.md#12-api-security-and-modern-authentication)

<!-- TOPIC-TOC:START -->

## Contents

- [12.1 API design and attack-surface coverage](#121-api-design-and-attack-surface-coverage)
- [12.2 Protocol-specific learning](#122-protocol-specific-learning)
- [12.3 Identity protocols and credential lifecycle](#123-identity-protocols-and-credential-lifecycle)
- [Expanded API and identity curriculum](#expanded-api-and-identity-curriculum)
  - [Module 1: contracts, schemas, and consistent interpretation](#module-1-contracts-schemas-and-consistent-interpretation)
  - [Module 2: authorization across all resource paths](#module-2-authorization-across-all-resource-paths)
- [Authentication lifecycle: state transitions to learn and test](#authentication-lifecycle-state-transitions-to-learn-and-test)
- [Protocol practice in a deliberate order](#protocol-practice-in-a-deliberate-order)
  - [OAuth, OpenID Connect, and tokens: core implementation path](#oauth-openid-connect-and-tokens-core-implementation-path)
  - [Additional protocol modules: choose by system](#additional-protocol-modules-choose-by-system)
- [Scenario labs with evidence and repairs](#scenario-labs-with-evidence-and-repairs)
  - [Lab A: mass assignment and excessive response fields](#lab-a-mass-assignment-and-excessive-response-fields)
  - [Lab B: account suspension during a stream](#lab-b-account-suspension-during-a-stream)
  - [Lab C: webhook replay and key rotation](#lab-c-webhook-replay-and-key-rotation)
- [Troubleshooting and final portfolio](#troubleshooting-and-final-portfolio)

<!-- TOPIC-TOC:END -->



**Priority:** Core: REST/JSON, object/function/property authorization, lifecycle controls, and OAuth/OIDC concepts. Track depth: implement and assess the additional protocols used by your target systems, including SAML, gRPC, advanced GraphQL, and WebAuthn details.

**Prerequisites:** Section 11, JSON/XML, API clients, TLS, asymmetric cryptography concepts, and the ability to read a protocol sequence diagram. Begin with an API you implement and a local identity provider or documented test tenant.

## 12.1 API design and attack-surface coverage

- [ ] REST: resource models, methods, status codes, pagination, filtering, partial updates, content negotiation, idempotency, schema validation, and version compatibility.
- [ ] Inventory documented and undocumented endpoints, deprecated versions, administrative routes, mobile-specific APIs, partner interfaces, exports, batch methods, and background consumers. Compare implementation with OpenAPI or equivalent contracts.
- [ ] Authorization at object, function, and property levels; mass assignment; excessive returned fields; nested-resource ownership; tenant context; and authorization on every bulk item.
- [ ] Resource consumption limits across page size, batch size, upload volume, search complexity, paid integrations, concurrency, and asynchronous jobs. Include account- and tenant-level accounting.
- [ ] Sensitive workflows: purchase, reservation, invitation, password recovery, content publication, and inventory allocation. Define misuse-resistant state transitions before evaluating automation controls.
- [ ] Third-party API consumption: transport trust, schema/length checks, credential scope, timeouts, retries, redirects, unexpected error content, and trust in partner-supplied identifiers.
- [ ] Webhooks: signing, timestamp/replay handling, key rotation, delivery authentication, destination validation, idempotency, event ordering, and dead-letter recovery.

Use the [OWASP API Security Top 10 project](https://owasp.org/projects/api-security-project) as an awareness checklist; supplement it with endpoint-specific contracts and authorization requirements rather than treating ten categories as complete coverage.

## 12.2 Protocol-specific learning

- [ ] GraphQL: schema, queries, mutations, subscriptions, resolvers, node identifiers, aliases, batching, field-level authorization, nested relationship access, depth/cost limits, and error leakage. Introspection visibility alone does not establish a vulnerability.
- [ ] gRPC: Protocol Buffers, services/methods, metadata, unary and streaming calls, deadlines, message limits, interceptors, transport security, service identity, reflection exposure, and per-method/per-message authorization.
- [ ] WebSockets: handshake origin validation, authentication, subscription scope, message schemas, reconnection, token expiration, session revocation, message size/frequency limits, and authorization after initial connection.
- [ ] Event-driven APIs: producer/consumer identity, queue/topic permissions, message provenance, schema evolution, replay, duplicate delivery, tenant routing, and delayed authorization decisions.

**Lab:** Expose the same synthetic object through REST and either GraphQL, gRPC, or WebSockets. Test a cross-tenant read, prohibited property update, and expired identity on each interface. Fix the shared policy, then verify equivalent denial and permitted behavior across transports.

## 12.3 Identity protocols and credential lifecycle

- [ ] Distinguish authentication, authorization, federation, provisioning, and session management. Diagram resource owner, client, authorization server, identity provider, resource server, and relying party.
- [ ] OAuth: authorization-code flow, PKCE, confidential/public clients, redirect URI validation, scopes, resource/audience restrictions, state binding, consent, client authentication, token exchange, and refresh-token rotation/reuse handling.
- [ ] Study implicit and password-grant flows as legacy review concerns; consult the security guidance when selecting implementations. Understand code interception, issuer mix-up, replay, and redirect trust at the design level. Use [RFC 9700](https://www.rfc-editor.org/info/rfc9700/) as the OAuth security reference.
- [ ] OpenID Connect: discovery, ID versus access tokens, issuer/audience verification, nonce, subject identifiers, UserInfo, authentication freshness, account linking, and logout. Validate tokens for their intended purpose; an ID token is not a substitute for API authorization. Reference [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html).
- [ ] JWT/JWS/JWE: encoding versus signing versus encryption, trusted algorithms and keys, signature verification, expiration/not-before, issuer/audience, key IDs, JWKS retrieval/rotation, token-type separation, and revocation tradeoffs. Decoding a token does not validate it.
- [ ] SAML: service/identity providers, metadata trust, assertions, signatures, audience, recipient, destination, request correlation, time windows, replay prevention, XML parsing, signature-wrapping concepts, and certificate rollover.
- [ ] WebAuthn/passkeys: registration and authentication ceremonies, relying-party ID/origin, challenges, user presence/verification, credential records, authenticator options, recovery, device loss, synchronization considerations, and enrollment protection. Study the [W3C WebAuthn specification](https://www.w3.org/TR/webauthn-3/) alongside your platform's supported implementation.
- [ ] Full lifecycle: invitation → registration → verification → enrollment → login → elevation → recovery → revocation → deletion. Include MFA resets, lost devices, changed emails, disabled employees, service accounts, API keys, and SCIM provisioning/deprovisioning.
- [ ] Storage and logging: prevent tokens in URLs, analytics, crash reports, browser-accessible storage without a deliberate design, and debugging output. Separate production and testing identities, issuers, keys, and audiences.

**Lab:** Implement code flow with PKCE through an established library. Test wrong issuer/audience, expired credentials, invalid state/nonce, replayed completion, recovery, and revoked sessions using only your test accounts. Add regression tests at the component responsible for each validation.

**Exit evidence:** a complete identity sequence diagram; an API inventory; at least 20 authorization/lifecycle test cases across two tenants; a cross-protocol policy test; a key-rotation exercise; and documented behavior when users, sessions, refresh credentials, or signing keys are revoked.

## Expanded API and identity curriculum

The core track ends with a reliable REST API, a documented authorization model, and correctly integrated standards-based login. Select additional protocols because your applications use them. Becoming an expert in SAML, WebAuthn, streaming RPCs, and every GraphQL implementation is a specialization path rather than a single beginner prerequisite.

### Module 1: contracts, schemas, and consistent interpretation

- [ ] Describe one resource in an API contract: identifier, ownership, tenant, mutable fields, read-only fields, required fields, nullable fields, enumerations, length bounds, numeric ranges, and sensitivity.
- [ ] Define how absent, null, empty, zero, false, duplicate, and unknown fields are handled. Check whether partial updates have different semantics from replacement operations.
- [ ] Specify object nesting, array cardinality, pagination limits, filtering operators, sorting fields, and maximum batch size. Reject unsupported structure without leaking internal implementation details.
- [ ] Compare ingress validation with domain validation. A well-formed request can still request an impossible state transition or unauthorized property change.
- [ ] Review serialization separately from input validation. Use explicit response schemas so administrative, internal, or secret fields do not appear accidentally.
- [ ] Keep authorization outside caller-controlled fields. Resolve the authenticated subject, tenant, and permitted resource scope through trusted server context.
- [ ] Define error schemas and correlation identifiers. Ensure error handling distinguishes client mistakes from server failures without exposing stack traces, credentials, or sensitive records.
- [ ] Study schema evolution: added fields, removed fields, changed defaults, incompatible enumerations, old clients, versioned endpoints, and background consumers. Security policies must remain consistent during migration.

**Practice:** create a contract test table containing valid requests, boundary values, malformed structure, forbidden properties, unauthorized nested objects, and excessive-but-bounded inputs. Record expected status, response schema, side effects, and audit event for each case.

### Module 2: authorization across all resource paths

- [ ] Model subject, action, resource, tenant, and relevant context. Write policies in business terms before translating them into middleware or resolver checks.
- [ ] Test object access through direct lookup, collection filtering, search, related objects, exports, batch operations, and alternate API versions.
- [ ] Verify every item in a bulk request. Decide whether mixed authorized/unauthorized items fail atomically or return documented item-level outcomes; test the chosen contract.
- [ ] Evaluate property-level updates and reads independently. Being allowed to edit a profile does not imply permission to set its role, owner, billing state, or tenant.
- [ ] Verify access again when a job runs if the business policy requires current authorization. Include deletion, role changes, ownership changes, and suspended tenants.
- [ ] Distinguish idempotency from authorization. An idempotency key must be bound to the appropriate caller/context and cannot authorize an otherwise forbidden operation.
- [ ] Define rate and cost controls at useful boundaries: credential, account, tenant, endpoint, job type, and external paid operation. Use small local load fixtures with fixed resource limits.

**Deliverable:** twenty or more explicit authorization cases, including both allowed and denied operations, two tenants, and at least one asynchronous operation.

## Authentication lifecycle: state transitions to learn and test

Treat identity as a system that changes over time. For each stage, define entry conditions, trusted proof, state changes, expiration, revocation, notification, logging, and recovery.

| Lifecycle stage | Study and validation goals |
| --- | --- |
| Invitation and registration | Bind an invitation to its intended organization/identity; handle reuse, expiration, conflicting accounts, and revoked invitations |
| Contact verification | Verify the selected address or channel without unintentionally granting unrelated permissions; protect changes during pending verification |
| Credential enrollment | Require adequate proof before enrolling passwords, MFA methods, passkeys, API keys, or recovery methods |
| Login and federation | Bind the protocol response to the initiating request; validate issuer, intended recipient, freshness, and selected account |
| Session creation | Rotate or create session identity appropriately; document lifetime, device association, cookie settings, and server-side state |
| Privilege elevation | Require the defined fresh proof and narrow the duration and scope of elevated authority |
| Credential refresh | Validate refresh state and client binding as applicable; handle rotation, duplicate requests, and reuse according to the identity provider's model |
| Recovery and factor reset | Prevent a weaker recovery path from bypassing the intended authentication assurance; notify and log sensitive changes |
| Email, organization, or ownership change | Re-evaluate account linking, permissions, active sessions, and pending invitations |
| Suspension and deprovisioning | Measure when local accounts, sessions, cached claims, API keys, and downstream SaaS access stop working |
| Logout and revocation | Distinguish browser logout, application-session termination, refresh revocation, and access-token lifetime |
| Deletion and retention | Remove access, handle retained audit records appropriately, and prevent accidental reuse or reassociation of identity identifiers |

Use only synthetic accounts in the exercise. Write down the intended revocation delay before testing: locally verified access tokens and server-side sessions can have different invalidation mechanisms. A documented design tradeoff must still satisfy the application's security requirement.

## Protocol practice in a deliberate order

### OAuth, OpenID Connect, and tokens: core implementation path

1. Diagram the browser, client, authorization server, identity provider, and resource server. Mark which component receives each code or token and which communication uses the browser.
2. Integrate authorization-code flow with PKCE using a maintained library and a local provider or permitted test tenant. Learn configuration and validation responsibilities before extending the library.
3. Review redirect URI registration, request correlation, state, nonce where applicable, code lifetime, client authentication, issuer selection, audience, scopes, and consent. Use RFC 9700 and OpenID Connect Core linked above for exact protocol requirements.
4. At the API, validate the credential intended for that resource. Separate ID-token processing from API access-token processing and check authorization beyond signature validity.
5. Study key discovery and caching. Plan bounded retrieval, trusted issuer configuration, supported key rotation, failure handling, and how the application responds to unavailable discovery services.
6. Exercise normal refresh, logout, factor reset, role removal, account suspension, and signing-key rollover. Record the remaining lifetime of previously issued credentials and the intended mitigation.

Do not build a custom cryptographic token validator as the default learning implementation. Study the library's checks, configure them correctly, and create tests that detect missing validation.

### Additional protocol modules: choose by system

- **GraphQL:** trace schema fields into resolvers and shared policy; cover nested authorization, aliases, batching, subscriptions, query cost, pagination, resolver errors, and changes to authorization while subscribed. Compare exposed introspection with the intended product policy instead of assigning severity from visibility alone.
- **gRPC:** read the service definition and metadata contract; verify transport identity, method authorization, streaming-message validation, deadlines, cancellation, compression/message bounds, and errors. Confirm interceptors cover every service method that needs them.
- **WebSockets and event systems:** bind connections/subscriptions to identities, validate each message type, handle expiration/revocation, enforce tenant routing, and test reconnect/replay behavior. A successful handshake is not a permanent authorization grant.
- **SAML:** study metadata trust, signed assertions, trusted keys, recipient/audience, request correlation, assertion lifetime, replay protection, parsing behavior, and certificate rollover using an established implementation.
- **WebAuthn:** study challenge lifecycle, origin and relying-party checks, credential association, user presence/verification policy, enrollment protection, device loss, and recovery. Test the actual supported platform and library behavior against the linked specification.

## Scenario labs with evidence and repairs

### Lab A: mass assignment and excessive response fields

**Setup:** a fictional profile API with editable display name and server-managed role/tenant fields. **Action:** compare permitted updates with an attempted forbidden-field update and inspect serialized responses. **Expected result:** forbidden properties remain unchanged and sensitive fields stay absent. **Evidence:** contract, request, response, stored state, and policy decision. **Control:** ordinary profile editing still succeeds. **Fix:** explicit input/output schemas and field-level authorization, then retest alternate update routes.

### Lab B: account suspension during a stream

**Setup:** one local REST endpoint plus a WebSocket or GraphQL subscription serving synthetic tenant events. **Action:** establish legitimate access, suspend the test user, and observe subsequent requests and events. **Expected result:** access ends within the documented policy interval across both transports. **Evidence:** timeline, identity state, token/session state, messages, and server logs. **Control:** an active user keeps receiving permitted events. **Fix:** consistent revocation checks, subscription cleanup, and bounded session/token policy.

### Lab C: webhook replay and key rotation

**Setup:** local sender and receiver, synthetic order events, and two disposable signing keys. **Action:** send a valid event, repeat it, deliver an older event, rotate the key, and attempt an event with the retired key according to the documented overlap policy. **Expected result:** authenticity checks succeed only as designed and repeated delivery does not repeat the business effect. **Evidence:** event identifier, validation decision, stored order state, rotation timeline, and redacted logs. **Control:** a new valid event still processes once. **Fix:** authenticated delivery, replay/idempotency state, explicit rotation policy, and safe retry handling.

## Troubleshooting and final portfolio

Authentication failures can arise from clock drift, issuer mismatch, audience mismatch, stale key caches, wrong environment, redirect configuration, or expired request state. Diagnose these separately from missing authorization. Successful signature verification does not establish that a token belongs to this API or that its subject may access a particular object. When revocation appears delayed, identify which credential and cache still confer access.

Pass by submitting the contract, endpoint inventory, lifecycle state model, protocol sequence, cross-tenant test matrix, three repaired lab findings, and key/revocation exercises. Every negative case needs a matching legitimate control, observable stored state, and a repeatable fixture. Explain which advanced protocol modules remain outside your chosen track and how you would assess them when encountered.