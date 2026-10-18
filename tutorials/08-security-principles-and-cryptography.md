# 08. Test security properties and use cryptographic interfaces correctly

[Index](README.md) | [Complete source curriculum](curriculum/08-security-principles-and-cryptography.md) | [Original roadmap](../roadmaps/08-security-principles-and-cryptography.md)

## Prerequisites and outcome

Complete networking, operating-system basics, and introductory programming. Use synthetic local records only. Python examples require an isolated project environment; the encryption and password examples additionally require maintained `cryptography` and `argon2-cffi` packages installed according to their documentation. The certificate example targets OpenSSL 3.x in a disposable Linux guest. Record installed versions and consult matching references. No example deploys a production authentication system.

You will build an access matrix, verify denied cases, reject altered ciphertext, compare password verification outcomes, and distinguish certificate trust, name, and time failures. Explain what each control establishes and what remains outside its protection.

## 1. Convert broad security goals into claims

For a local invoice application, confidentiality means only authorized actors can read invoices; integrity means unauthorized changes cannot alter them; availability means authorized users can obtain service when needed. Authenticity concerns the claimed origin/identity, accountability connects actions to attributable records, privacy governs appropriate collection/use/disclosure, and resilience includes recovery under failure. Encrypting a database does not automatically establish all seven.

An asset is something valuable. A threat is a potential harmful actor/event. A vulnerability is a weakness; exposure is reachability or accessibility; an exploit is a means of using a weakness. A control changes the likelihood or consequence. A finding is an evidenced assessment result, an incident is an actual adverse occurrence under the organization's definition, and risk combines uncertain likelihood and consequences in context. A severity score is a decision aid with assumptions, not automatically a measured probability.

Draw users, browser, API, identity provider, database, queue/worker, administrator, logs, and backups. Mark trust boundaries and label data, credentials, and control messages crossing each. Dependency trust extends the attack surface: a secure handler can still consume an unsafe upstream decision. Write an abuse case as actor, prerequisites, action, protected asset, and expected control, then choose the smallest test capable of falsifying the intended behavior.

| Principle | Concrete application |
| --- | --- |
| Least privilege / least functionality | A worker receives only required data actions; unused interfaces are absent |
| Secure defaults / fail-safe behavior | Unknown roles and failed checks deny access without performing the operation |
| Complete mediation | Single-record, list, export, batch, and background paths all enforce policy |
| Separation of duties | A sensitive action requires distinct responsibilities where the policy demands it |
| Defense in depth | Server authorization, narrow database rights, monitoring, and recovery address different failures |
| Compensating control / residual risk | A temporary restriction reduces exposure while the underlying defect remains tracked |

Preventive controls block, detective controls reveal, corrective controls repair, and recovery controls restore. Validate each with evidence. Minimize data collection and bound requests so privacy and availability are part of test design, not afterthoughts.

## 2. Separate identity from resource authorization

Identification says which account is claimed. Authentication verifies credentials or another proof. Authorization decides whether that actor may perform this action on this resource in this context. Accounting records the result. Authentication success never implies unrestricted object access.

RBAC uses role membership; ABAC evaluates attributes such as tenant or context; ownership/relationship checks connect actor to record. Combining them can be necessary: two customers share a role yet must not read each other's invoices. Privileged and service identities need explicit rules too.

This pure local function models one narrowly stated read policy:

```python
def can_read(actor, record):
    if actor is None or not actor.get("enabled") or not actor.get("session_valid"):
        return False
    if actor.get("tenant") != record["tenant"]:
        return False
    if actor.get("role") == "tenant_admin":
        return True
    return actor.get("role") == "customer" and actor.get("id") == record["owner"]

alice = {"id": "a", "role": "customer", "tenant": "t1",
         "enabled": True, "session_valid": True}
own = {"owner": "a", "tenant": "t1"}
other = {"owner": "b", "tenant": "t1"}
assert can_read(alice, own)
assert not can_read(alice, other)
assert not can_read(None, own)
assert not can_read({**alice, "enabled": False}, own)
assert not can_read({**alice, "session_valid": False}, own)
assert not can_read({**alice, "role": "unknown"}, own)
assert not can_read({**alice, "role": "tenant_admin", "tenant": "t2"}, own)
print("seven policy cases passed")
```

The expected message confirms these seven cases, not all possible policies. In an application, actor state must come from a trusted authentication/session boundary, and record ownership from trusted storage. A client-supplied `enabled=true` is not proof. Run equivalent tests through every relevant server route and verify state remains unchanged after denial. Hiding a button or rejecting after mutation does not enforce the intended boundary.

## 3. Treat authentication as a lifecycle

Sessions are created, renewed, expired, revoked, and ended. Removing a browser cookie does not necessarily invalidate a stolen server-side session. Sensitive changes may need reauthentication. Enrollment, password change, recovery, device replacement, and deprovisioning can be weaker than ordinary sign-in; test the state transitions and old-session/recovery-token invalidation policy.

MFA combines different factor categories, not two passwords. Passkeys/WebAuthn use public-key credentials bound to relying-party context, supporting phishing resistance under the protocol's assumptions. Device enrollment, account recovery, compromised endpoints, and weaker fallback remain important. [W3C Web Authentication specification](https://www.w3.org/TR/webauthn-3/)

| Credential/mechanism | What to trace |
| --- | --- |
| Browser session | Cookie/storage, server authority, expiry, logout, revocation |
| Bearer access token | Whoever possesses it can generally present it; scope, audience, lifetime matter |
| Refresh token | Authority to obtain new access tokens; rotation/reuse/revocation policy differs |
| API key | Service/client identity or capability according to design; storage and restriction matter |
| Client certificate / proof of possession | Demonstrates key possession under protocol rules; identity mapping still matters |
| Workload identity | Issuance and permissions for software rather than a human user |

OAuth 2.0 provides delegated authorization involving client, authorization server, resource server, scopes, and grants. OpenID Connect adds an identity layer with ID tokens and validation rules. SAML federation communicates signed assertions between identity and service providers, with issuer, audience, recipient, time, and trust checks. Consent is not a blanket authorization for every resource. [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)

Decoding a token only displays its representation. Validation can require an allowed algorithm, trusted key, issuer, audience, time claims, and application-specific constraints. A valid signature still does not authorize every action. Redirect handling and protocol-state binding matter because the response must belong to the initiating transaction and intended client.

## 4. Select a primitive by the property required

| Mechanism | Supplies | Does not supply alone |
| --- | --- | --- |
| Base64 / hexadecimal / URL encoding | Reversible representation | Secrecy or integrity |
| Cryptographic hash | Fixed-size content digest | Trusted origin if an attacker supplies both data and digest |
| Password hashing / password KDF | Costly password verification/derivation with salt and parameters | Protection against unlimited guessing of a weak password |
| MAC / HMAC | Integrity/authenticity among shared-secret holders | Which particular holder authored it, or confidentiality |
| Symmetric AEAD | Confidentiality and integrity under a secret key | Authorization of anyone who gains the key |
| Digital signature | Public verification under a trusted public key | Confidentiality or proof of a human's intention |
| Authenticated key agreement | Shared key establishment with identity when supplied by the protocol | Correct downstream access policy |

A preimage attack seeks an input matching a specified digest; a second-preimage attack seeks another input matching a given input's digest; a collision seeks any distinct pair with equal digests. Toy hashes illustrate these goals but say nothing about practical attack cost against modern hashes. Equal numerical key lengths across symmetric and asymmetric families do not imply equal strength.

Keys must remain secret. Salts can be public and distinguish password derivations. Nonces/IVs have algorithm-specific uniqueness/randomness requirements. Associated data is authenticated but unencrypted. Cryptographically secure randomness is intended for secrets; a simulation PRNG is not a substitute. Password-derived keys need an appropriate KDF rather than raw password bytes or invented hash concatenations.

Signatures authenticate bytes, so serialization, canonicalization, context, and public-key identity determine meaning. A valid old message can still be replayed; freshness/counters/nonces and application state must prevent unwanted repeated actions. Strong algorithms fail when protocols compose them incorrectly or keys/validation are mishandled.

## 5. Prove authenticated-encryption failure behavior

Run this small Python example with `cryptography` available. It generates a fresh test key, does one encryption, and never prints key material:

```python
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

key = AESGCM.generate_key(bit_length=256)
box = AESGCM(key)
nonce = os.urandom(12)
aad = b"lab-record:v1:tenant=t1"
ciphertext = box.encrypt(nonce, b"synthetic invoice", aad)
assert box.decrypt(nonce, ciphertext, aad) == b"synthetic invoice"
changed = bytes([ciphertext[0] ^ 1]) + ciphertext[1:]
cases = [
    (box, changed, aad),
    (box, ciphertext, b"lab-record:v1:tenant=t2"),
    (AESGCM(AESGCM.generate_key(bit_length=256)), ciphertext, aad),
]
for decoder, data, context in cases:
    try:
        decoder.decrypt(nonce, data, context)
    except InvalidTag:
        print("rejected")
    else:
        raise AssertionError("invalid input accepted")
```

Expect `rejected` three times. Altered ciphertext, wrong associated data, and wrong key must not produce usable plaintext. The same nonce here is used to check the same encrypted message; never reuse a nonce for a new encryption under the same AES-GCM key. Random generation in a tiny demo does not solve high-volume persistent nonce management. Production designs need documented generation, collision/usage limits, concurrency, restart, and rotation handling. [Cryptography stable AEAD documentation](https://cryptography.io/en/stable/hazmat/primitives/aead/)

If decryption fails unexpectedly, compare key identifier, nonce bytes, associated data construction, record framing, and ciphertext—not secret values in shared logs. Do not return unchecked bytes or silently disable authentication. A record format needs version, key ID, nonce, ciphertext/tag, and authenticated context with a defined serialization.

For rotation, create key K2, encrypt new synthetic records under K2 with new nonces, and retain authorized read access to K1 records according to policy. Restore a K1 record from a test backup, then demonstrate that denying K1 access prevents recovery. This shows why “change the current key variable” is not a migration. Keep identifiers and results in evidence, never keys.

## 6. Verify passwords and lifecycle changes

With `argon2-cffi` in the isolated environment:

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

hasher = PasswordHasher()
test_password = "synthetic-example-only"
first = hasher.hash(test_password)
second = hasher.hash(test_password)
assert first != second
assert hasher.verify(first, test_password)
try:
    hasher.verify(first, "wrong-synthetic-password")
except VerifyMismatchError:
    print("wrong password rejected")
print("rehash needed:", hasher.check_needs_rehash(first))
```

Independent salts make stored records differ while both verify the same password. Verification is not decryption. The encoded format retains algorithm/parameter metadata; after successful authentication, a library-supported rehash path upgrades outdated parameters. Defaults in this exercise are not a production tuning recommendation: benchmark bounded legitimate verification cost and follow current framework/library guidance. [argon2-cffi password workflow](https://argon2-cffi.readthedocs.io/en/stable/howto.html)

Ordinary fast SHA-256 hashing is not suitable password storage. Password-hash cost resists offline guessing; live-service rate limits and recovery controls address online attempts. Salt does not turn a weak password into a strong one. Use a maintained authentication framework for an actual service and test invalid input, credential change, recovery, logout, disabled account, and old-session invalidation.

Maintain a key inventory: purpose, owner, environment, identifier, generation method, storage, permitted identities, distribution, backup, rotation, revocation, and destruction. Separate development and production keys and separate purposes. Envelope encryption uses data keys for records and a wrapping key for those keys; rotating a wrapping key need not mean re-encrypting every record. KMS provides managed key operations/policy/audit, while HSM hardware protects key operations/material under its design. Neither fixes overbroad application permissions automatically. Cached keys, replicas, backups, and old sessions affect compromise response and secure destruction.

## 7. Separate certificate chain, name, and time

A leaf certificate binds a public key to subject information including SAN names and permitted usage. Issuers sign certificates; intermediates connect to a configured trust anchor. Basic constraints distinguish CA certificates; key usage and extended key usage constrain purpose. Validation needs appropriate chain, name, usage, and time checks. Revocation/renewal are operational workflows with client-specific behavior.

In a new Linux guest directory, use these OpenSSL 3.x commands. Stop if the directory already exists rather than overwriting old keys. Private test keys remain inside this directory and are never added to a global trust store:

```bash
umask 077
mkdir crypto-cert-lab
cd crypto-cert-lab
openssl req -x509 -newkey rsa:2048 -noenc -keyout ca.key -out ca.crt -days 2 -subj '/CN=Local Tutorial CA' -addext 'basicConstraints=critical,CA:TRUE' -addext 'keyUsage=critical,keyCertSign,cRLSign'
openssl req -new -newkey rsa:2048 -noenc -keyout leaf.key -out leaf.csr -subj '/CN=invoice.test'
cat > leaf.ext <<'EOF'
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:invoice.test
EOF
openssl x509 -req -in leaf.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out leaf.crt -days 1 -extfile leaf.ext
openssl verify -CAfile ca.crt -purpose sslserver -verify_hostname invoice.test leaf.crt
openssl verify -CAfile ca.crt -purpose sslserver -verify_hostname wrong.test leaf.crt
future_time=$(python3 -c 'import time; print(int(time.time()) + 3*86400)')
openssl verify -CAfile ca.crt -attime "$future_time" -verify_hostname invoice.test leaf.crt
```

The valid check should return `leaf.crt: OK`; mismatched hostname and future-time checks should fail for their respective reasons. Test untrusted issuance by verifying without the lab `-CAfile` in the guest's ordinary trust context, provided that CA was never installed there. Inspect `openssl x509 -in leaf.crt -noout -text` to connect SAN, issuer, validity, and constraints to results. Dedicated trust files localize the experiment. [OpenSSL request reference](https://docs.openssl.org/3.0/man1/openssl-req/), [certificate command](https://docs.openssl.org/3.0/man1/openssl-x509/), [verification controls](https://docs.openssl.org/3.0/man1/openssl-verify/)

Do not change the host clock to simulate expiry and do not “repair” failure by disabling verification. Correct SAN, issuer chain, trust configuration, or renewal, then rerun positive and negative cases. Preserve public certificate metadata and commands; remove the disposable private-key artifacts through your lab cleanup process when recovery exercises are finished.

## 8. Map encryption boundaries and advanced concepts

TLS negotiates parameters, authenticates key establishment according to its mode, derives traffic keys, and protects application records. Long-term certificate keys differ from per-connection traffic keys. Forward secrecy concerns protection of earlier session secrets after later long-term-key compromise under the relevant mode. Early data/0-RTT has replay and forward-secrecy limitations; do not make a blanket claim that every TLS mode supplies identical properties. [TLS 1.3 specification](https://datatracker.ietf.org/doc/html/rfc9846)

Transport encryption ends at TLS endpoints; a terminating proxy can see plaintext. Disk encryption protects locked storage, while a running authorized application can see decrypted data. Application encryption restricts access according to key placement; end-to-end encryption aims to limit plaintext to intended endpoints. Logs, exports, process memory, backups, and administrator-controlled endpoints remain part of the data-flow analysis.

Entropy measures uncertainty under a model; the length of a predictable string is not its security strength. Padding/oracle problems arise when observable differences reveal protected-message validity information. Side channels can expose secrets through timing, cache behavior, power, or other observations. Protocol composition requires context binding and compatible assumptions, not merely a list of strong algorithms. Cryptographic agility begins with an inventory and migration/recovery plan. Post-quantum migration should follow current standards and actual product support, rather than an invented suite; use NIST's maintained program as the starting reference. [NIST post-quantum cryptography program](https://csrc.nist.gov/projects/post-quantum-cryptography)

## Completion and answer guidance

Deliver asset/data-flow inventory, trust boundaries, access matrix, allowed/denied server tests, primitive-purpose table, tamper rejection, password outcomes, certificate failure matrix, and a key recovery/rotation record. For each control, name one limitation.

If ciphertext changes but decrypts, check whether authentication is actually enforced. If a valid token reads another user's record, repair authorization rather than token decoding. If a signature verifies, do not claim secrecy. If a file is encrypted and its key is beside it with the same access, analyze who can obtain both. Repeat one denied read, one altered-message case, and one hostname failure after a delay; the lesson is complete when you can explain and repair each result independently.
