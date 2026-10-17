# 08. Security principles and cryptography

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#08-security-principles-and-cryptography)

<!-- TOPIC-TOC:START -->

## Contents

- [Security reasoning and architecture](#security-reasoning-and-architecture)
- [Identity and access management](#identity-and-access-management)
- [Cryptographic building blocks and operational use](#cryptographic-building-blocks-and-operational-use)
- [Safe practice and exit criteria](#safe-practice-and-exit-criteria)
- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1 — Convert security goals into testable claims](#stage-1--convert-security-goals-into-testable-claims)
  - [Stage 2 — Separate identity, access, and session state](#stage-2--separate-identity-access-and-session-state)
  - [Stage 3 — Choose a primitive by the required property](#stage-3--choose-a-primitive-by-the-required-property)
  - [Stage 4 — Password storage and key lifecycle](#stage-4--password-storage-and-key-lifecycle)
  - [Stage 5 — Certificates and encrypted transport](#stage-5--certificates-and-encrypted-transport)
- [Guided labs with evidence](#guided-labs-with-evidence)
  - [Lab A — Access decisions and denied cases](#lab-a--access-decisions-and-denied-cases)
  - [Lab B — Authenticated encryption and lifecycle](#lab-b--authenticated-encryption-and-lifecycle)
  - [Lab C — Certificate trust, name, and time](#lab-c--certificate-trust-name-and-time)
  - [Lab D — Password verification and recovery boundaries](#lab-d--password-verification-and-recovery-boundaries)
- [Capstone rubric and retention](#capstone-rubric-and-retention)

<!-- TOPIC-TOC:END -->



**Prerequisites:** Networking, operating-system basics, and introductory programming. **Priority:** Core concepts for everyone; cryptographic engineering is an advanced specialty.

## Security reasoning and architecture

- [ ] Explain confidentiality, integrity, availability, authenticity, accountability, privacy, and resilience using concrete system examples.
- [ ] Distinguish assets, threats, vulnerabilities, exposures, exploits, controls, findings, incidents, and risk. A severe-sounding weakness needs evidence and context.
- [ ] Apply least privilege, least functionality, secure defaults, complete mediation, separation of duties, defense in depth, and fail-safe behavior.
- [ ] Draw data flows and trust boundaries; identify what crosses each boundary, who controls it, and where authorization must occur.
- [ ] Understand attack surface, threat modeling, abuse cases, dependency trust, compensating controls, residual risk, and defense validation.
- [ ] Consider availability and privacy when designing a test; collect only evidence needed to demonstrate the issue.

## Identity and access management

- [ ] Distinguish identification, authentication, authorization, and accounting; understand that valid login does not grant access to every object.
- [ ] Learn password storage, unique salts, password-derived key functions, rate limiting, recovery flows, account lifecycle, and session expiration/revocation.
- [ ] Compare RBAC, ABAC, ownership checks, tenant isolation, service identities, and privileged access. Trace authorization from identity to resource to action.
- [ ] Understand MFA factors, phishing-resistant authentication concepts, passkeys/WebAuthn, device enrollment, recovery, and the risk introduced by weaker fallback paths.
- [ ] Learn OAuth 2.0 authorization, OpenID Connect authentication, SAML federation, access/refresh tokens, scopes, audience, issuer, signatures, and expiry at a conceptual level.
- [ ] Distinguish browser sessions, bearer tokens, API keys, certificates, and workload identities; understand their storage, exposure, rotation, and revocation needs.

## Cryptographic building blocks and operational use

- [ ] Distinguish encoding, hashing, password hashing, message authentication codes, encryption, key exchange, and digital signatures.
- [ ] Understand symmetric versus asymmetric cryptography, authenticated encryption, nonces/IVs, salts, cryptographic randomness, key derivation, and replay protection.
- [ ] Learn why strong algorithms still fail through weak keys, nonce reuse, missing authentication, incorrect validation, exposed secrets, or broken protocols.
- [ ] Understand certificate subjects, subject alternative names, certificate authorities, chains, hostname validation, trust anchors, expiry, and revocation concepts.
- [ ] Compare encryption in transit, at rest, and end to end; identify which endpoints and administrators can still access plaintext.
- [ ] Learn key generation, distribution, storage, access restrictions, rotation, revocation, destruction, backups, and recovery. Recognize KMS/HSM roles.
- [ ] Use maintained cryptographic libraries and established protocols; understand that writing an algorithm from scratch is an educational exercise, not a deployment plan.
- [ ] **Advanced:** Study entropy estimation, protocol composition, padding/oracle concepts, side channels, forward secrecy, cryptographic agility, and post-quantum migration considerations using current standards.

For implementation-oriented reading, use the [OWASP cryptographic-storage guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html), checking its current recommendations before building a real system.

## Safe practice and exit criteria

**Labs:** Build an access-control matrix for your local application and verify allowed and denied cases. Use a maintained library to encrypt synthetic data, then show that modified ciphertext fails authentication. Create lab certificates and observe trusted, untrusted, expired, and hostname-mismatch outcomes. Inspect a toy password-storage implementation and replace insecure storage with a maintained password-hashing facility. Document a key-rotation and recovery exercise with test secrets.

**Exit gate:** Explain which cryptographic primitive solves a stated problem; reject encoding as secrecy and ordinary fast hashing as password storage; identify a missing authorization check; and describe who can decrypt data throughout its lifecycle.

**Common gaps:** Confusing OAuth with authentication; believing signatures hide content; assuming encrypted data is safe when the key is beside it; validating tokens without checking audience/issuer; treating MFA as protection against every account-compromise scenario.

## Detailed learning sequence

Complete the **practical track** by reasoning about a small application's access boundaries, using maintained cryptographic interfaces correctly in a lab, checking certificates, and rehearsing key recovery. The **awareness track** covers formal cryptanalysis, side channels, protocol construction, and post-quantum migration until a specialization requires deeper mathematics or implementation review. Memorizing algorithm names is insufficient; for each mechanism, state the property it supplies, the assumptions it needs, and the failures it cannot prevent.

### Stage 1 — Convert security goals into testable claims

- [ ] Inventory assets: synthetic records, identities, configuration, keys, backups, service availability, and audit evidence. Record an owner and an intended access/use policy for each.
- [ ] Give a concrete confidentiality, integrity, and availability failure for the same application. Add authenticity, accountability, privacy, and recoverability without assuming one control supplies every property.
- [ ] Distinguish a threat actor's capability from a vulnerability and a demonstrated finding. A reachable service is exposure; a verified unauthorized action is evidence of a specific failure. Keep hypothetical impact separate from observed behavior.
- [ ] Draw users, browser, API, database, identity provider, and backup storage with trust boundaries. Label data, credentials, and control messages crossing each boundary, including asynchronous jobs and administrative paths.
- [ ] Write misuse cases as actor, precondition, action, protected asset, and expected control. Include an ordinary authenticated user attempting an action outside their permitted role or ownership.
- [ ] Apply secure defaults and complete mediation: reject an unrecognized case, check every relevant operation, and keep a consistent authorization decision when an action is exposed through multiple interfaces.
- [ ] Separate preventive, detective, corrective, and recovery controls. Explain residual risk after each control and how a test establishes that the control works for the stated scenario.
- [ ] Learn that a simple likelihood-times-impact score is a decision aid with assumptions, not a precise measured probability by default. Record uncertainty, operational context, and evidence behind the rating.
- [ ] Include privacy and availability in the test design: minimize synthetic evidence, bound requests, define a stop condition, and prove a finding with the smallest necessary action.

**Checkpoint:** For one proposed finding, state the affected asset, intended rule, observed result, preconditions, impact, uncertainty, remediation, and a test that would falsify your explanation.

### Stage 2 — Separate identity, access, and session state

- [ ] Trace identification, authentication, authorization, and accounting independently. A login result establishes a session identity; the later resource operation still needs its own access decision.
- [ ] Build an access matrix with actor, role, tenant, resource owner, action, and contextual attributes. Include anonymous, ordinary user, another user's resource, administrator, disabled account, and service identity.
- [ ] Compare RBAC with ABAC and relationship/ownership checks. Roles alone may be too coarse when two users share a role but own different records.
- [ ] Make denied cases first-class tests, including direct API access, changed object identifiers, batch operations, background jobs, and alternate export routes. Use [OWASP's authorization guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) to review consistent enforcement and least privilege.
- [ ] Learn session creation, renewal, expiration, revocation, logout, and reauthentication for sensitive changes. Explain the difference between removing a browser cookie and invalidating the corresponding server-side authority.
- [ ] Study account enrollment, recovery, credential changes, device replacement, and deprovisioning as part of authentication. A strong sign-in method can be undermined by a weaker recovery route.
- [ ] Distinguish factor categories from repeated examples of the same factor. Learn how phishing-resistant authenticators bind a ceremony to the intended relying party at a conceptual level; study enrollment and recovery alongside ordinary sign-in.
- [ ] Compare bearer tokens, proof-of-possession mechanisms, API keys, client certificates, and workload identities. For each, record where it is stored, who can use it, how long it lasts, and how it is revoked.
- [ ] Distinguish OAuth delegation from OpenID Connect authentication. Learn clients, authorization/resource servers, redirect handling, scopes, audiences, issuers, and consent before studying protocol weaknesses.
- [ ] Treat decoding a token as inspection only. Validation may require an allowed algorithm, trusted key, correct issuer/audience, validity times, and application-specific claims. A valid signature alone does not authorize every action.

### Stage 3 — Choose a primitive by the required property

| Mechanism | What to learn first | What it does not establish by itself |
| --- | --- | --- |
| Encoding | Reversible representation such as Base64 or hexadecimal | Secrecy, integrity, or identity |
| Cryptographic hash | Fixed-size digest; preimage, second-preimage, and collision concepts | Trusted origin of a digest supplied by an untrusted party |
| Password hashing/KDF | Salt, cost parameters, verification, upgrade path | Resistance to unlimited guessing of a very weak password |
| MAC/HMAC | Integrity and authenticity among holders of a shared secret | Which particular holder created the message |
| Symmetric authenticated encryption | Confidentiality plus tamper detection with a secret key | Correct authorization of everyone who can obtain that key |
| Digital signature | Public verification of a message under a trusted public key | Confidentiality or the signer's human intent |
| Key agreement | Establishing shared secret material between participants | Peer identity unless authenticated by the surrounding protocol |

- [ ] Learn the difference between collision resistance and preimage resistance using toy examples. Never infer that a toy hash demonstration describes the practical strength of a modern cryptographic hash.
- [ ] Separate symmetric key size, asymmetric key size, algorithm family, and estimated security strength. Equal numerical key lengths across different families do not imply equal security.
- [ ] Understand that signatures authenticate bytes. Serialization, canonicalization, context, and key identity matter when deciding what a verified signature means to an application.
- [ ] Use a cryptographically secure random source for keys and security tokens. A general-purpose pseudo-random generator may be excellent for simulation while inappropriate for secrets.
- [ ] Distinguish salts, nonces, IVs, keys, and associated data. A salt can be public; a key must remain secret; a nonce's uniqueness or randomness requirements depend on the algorithm and protocol.
- [ ] For common AEAD schemes such as AES-GCM, respect nonce uniqueness under a given key. Associated data is authenticated but not encrypted. Treat failed authentication as failure of the whole message, with no application use of unauthenticated plaintext. Consult the [cryptography library's AEAD interface](https://cryptography.io/en/latest/hazmat/primitives/aead/) and the documentation matching the installed stable release.
- [ ] Learn key derivation as a separate task from encryption. Do not use a human password directly as an encryption key or invent a construction by concatenating secrets and hashes.
- [ ] Add replay protection at the protocol/application layer when needed. A correctly authenticated old message can still be harmful if the system accepts it again as a new operation.

### Stage 4 — Password storage and key lifecycle

- [ ] Use a maintained password-hashing facility that manages salts and verification formats. Study current Argon2id guidance, cost tuning, and library rehash/upgrade mechanisms; avoid fast general-purpose hashes as password storage. Benchmark legitimate login cost in a bounded lab and retain algorithm/parameter metadata with stored test hashes. Follow [OWASP's password-storage guidance](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) when selecting implementation parameters.
- [ ] Distinguish online guessing controls from offline password-hash resistance. Rate limits and recovery policy protect a live service; stored-hash design addresses a different exposure.
- [ ] Inventory each key's purpose, owner, environment, identifier, creation method, storage location, permitted users/services, backup path, and rotation/revocation procedure.
- [ ] Separate environments and purposes: a test signing key should not become a production key, and an encryption key should not be reused arbitrarily as an authentication secret.
- [ ] Learn envelope encryption: data keys encrypt content, while a separately controlled key protects those data keys. Distinguish rotating a wrapping key from re-encrypting every data record.
- [ ] Explain KMS versus HSM at awareness depth, including policy, audit, availability, and key-export properties. Moving keys into a managed service does not automatically fix overbroad application access.
- [ ] Plan recovery before deletion. A lost key can make correctly encrypted data unrecoverable; a recoverable old key can keep old data decryptable after a nominal rotation. Document both desired properties.
- [ ] Distinguish routine rotation, compromise response, revocation, and secure destruction. Cached credentials, backups, replicas, and long-lived sessions can extend exposure after a central change.

### Stage 5 — Certificates and encrypted transport

- [ ] Learn certificate subject, SAN, issuer, validity period, public key, signature, key usage, and basic constraints. Distinguish the leaf certificate, intermediates, and trust anchor.
- [ ] Validate the chain, intended name, appropriate usage, and validity time as separate requirements. A certificate's presence in a response does not make its issuer trusted.
- [ ] Explain why adding a lab CA to a trust store changes what that client trusts. Prefer an application-specific trust file for exercises and remove lab trust after the exercise.
- [ ] Trace a TLS handshake at conceptual depth: negotiation, authenticated key establishment, key derivation, and protected application records. Separate the certificate's long-term key from per-connection traffic keys.
- [ ] Learn forward secrecy as protection of past session secrets against later compromise of a long-term key under the relevant protocol assumptions. TLS 1.3 has multiple modes; 0-RTT early data has replay and forward-secrecy limitations distinct from ordinary traffic. Review the [TLS 1.3 specification](https://datatracker.ietf.org/doc/html/rfc8446) before making blanket claims.
- [ ] Study revocation and certificate renewal as operational workflows with client-specific behavior. An expired or revoked credential is not repaired by disabling verification.
- [ ] Draw data access for transport encryption, full-disk encryption, application encryption, and end-to-end encryption. Mark when plaintext exists in process memory, logs, exports, backups, or administrator-controlled endpoints.
- [ ] At awareness depth, study cryptographic agility through inventories and migration plans. For post-quantum work, consult current standards and product guidance for the actual deployment; do not invent an algorithm suite from a roadmap.

## Guided labs with evidence

### Lab A — Access decisions and denied cases

**Setup:** Use a local notes application with two synthetic users and an administrator. Create separate owned records and an explicit actor/resource/action matrix.

**Actions:** Exercise permitted reads/updates and denied cross-user actions through the server API. Include a disabled account and an expired session where the application supports them. Verify that both single-record and list/export routes apply the intended rule.

**Expected observation:** Authentication success does not remove per-resource checks. An unauthorized operation should not expose data or change state, even if the UI would ordinarily hide that action.

**Evidence:** Matrix, sanitized request/response pairs, state before/after, access-decision logs where available, and a regression test for any repaired missing check.

**Repair:** Enforce the intended rule at the trusted server boundary and retest both allowed and denied actions. Avoid fixing only the button or returning a generic error after already performing the operation.

### Lab B — Authenticated encryption and lifecycle

**Setup:** Choose a maintained AEAD interface from its installed-version documentation. Use only a short synthetic message, a newly generated test key, and documented nonce handling. Store no personal data.

**Actions:** Encrypt and decrypt successfully; change one ciphertext byte, then separately alter associated data and use the wrong key. Verify that each invalid case is rejected. Add a key identifier to the record format and rehearse writing new records with a second key while reading allowed old records with the first.

**Expected observation:** Integrity checks fail on altered or mismatched inputs. Key rotation needs a deliberate policy for old data and key access; changing a key variable alone is not a complete migration.

**Evidence:** Record format, metadata lengths, key identifiers without key values, valid/invalid outcomes, and a rotation/recovery diagram.

**Repair:** Correct nonce generation/storage, associated-data construction, key lookup, or message framing as indicated. Do not suppress authentication errors or fall back to returning unchecked bytes. Remove test keys after documenting the recovery result.

### Lab C — Certificate trust, name, and time

**Setup:** Create an isolated lab CA and a leaf certificate for a synthetic local name. Keep its private keys inside the lab and use a dedicated trust file. Prepare a separate certificate or verification-time input to model expiry without changing the host clock.

**Actions:** Verify a valid chain and correct name, then test an unknown CA, a mismatched name, and an out-of-validity time. Use explicit hostname and verification-time options where supported. The [OpenSSL verification reference](https://docs.openssl.org/master/man1/openssl-verify/) documents those controls; select the documentation matching your installed release.

**Expected observation:** Chain trust, name matching, and time validity produce distinct outcomes. A command that verifies only the chain does not prove that the hostname is correct.

**Evidence:** Public certificate details, exact verification settings, error categories, and a diagram of trust anchors. Exclude private keys from screenshots, reports, and repositories.

**Repair:** Correct the name/SAN, certificate chain, trust configuration, or renewal process. Retest the intended valid case and every negative case without disabling validation.

### Lab D — Password verification and recovery boundaries

**Setup:** Build a tiny local account fixture through a maintained password-hashing facility. Use two synthetic accounts with the same test password and a third with a different password.

**Actions:** Verify correct and incorrect passwords, inspect stored metadata, and confirm that independently salted records differ. Exercise the library's parameter-upgrade path when available. Document a recovery flow and identify which old sessions or recovery tokens should become invalid after a credential change.

**Expected observation:** Verification is a library operation, not password decryption. Different stored hashes for the same password are compatible with successful verification; metadata supports future migration.

**Evidence:** Sanitized record structure, test outcomes, upgrade notes, and a recovery-state diagram. Keep actual test secrets out of shared examples even though they are synthetic.

**Repair:** Replace custom comparisons or storage with the maintained facility, correct parameter handling, and add negative/recovery tests. Do not generalize this small lab into a production authentication design without reviewing the complete framework behavior.

## Capstone rubric and retention

Deliver a security design review for your local application containing asset inventory, data-flow/trust-boundary diagram, access matrix, cryptographic-purpose table, key lifecycle, recovery plan, and evidence from the labs. For each control, state the specific property tested and one remaining limitation.

Evaluate **security reasoning**, **authorization coverage**, **primitive selection**, **tamper rejection**, **certificate validation**, and **key recovery** as missing, guided, or independent. Require independent results for the practical track. Advanced algorithm internals remain an explicit later study track rather than a reason to delay ordinary secure administration.

The next day, choose a primitive for five requirements without reading the table. Later, draw who can decrypt a record at each stage of its lifecycle. After another gap, repeat one denied-access test, one altered-ciphertext test, and one certificate-name failure. Progress to [web security](11-web-application-security.md), [API security](12-api-security-and-modern-authentication.md), and [secure code review](13-secure-code-review-and-software-delivery.md) using these properties as the basis for your tests.
