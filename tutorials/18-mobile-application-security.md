# 18. Tutorial: mobile application security

[Index](README.md) | [Complete source curriculum](curriculum/18-mobile-application-security.md) | [Original roadmap](../roadmaps/18-mobile-application-security.md)

Prerequisites: HTTP/API security, basic programming, identity, and cryptography. Start with a dedicated emulator and an app you build or a deliberately vulnerable training build. An iOS practical assessment requires its supported development environment and appropriate device access; a desktop simulation does not establish iOS platform security.

## Lesson 1: model four cooperating systems

A mobile application is installed software, a device/OS security context, a backend, and third-party dependencies. Draw a note flowing from UI to local cache, network client, API authorization, database, analytics, and notification service. Label where identities and data ownership change. A well-sandboxed app can still use an API with missing ownership checks.

Packaging and code signing associate executable content with a publisher/update identity. They do not prove business logic is correct. Installation, first launch, foreground/background transitions, process death, restart, upgrade, and removal have different storage and lifecycle effects. Record package identifier, build variant, signing identity, OS/device version, and debug configuration for each observation.

Read one Kotlin/Java flow from UI event to storage/network call, then one Swift/Objective-C equivalent when the platform is available. In Flutter, React Native, or hybrid software, follow the native plugin boundary as well as the shared-language code: a wrapper can invoke privileged native behavior.

## Lesson 2: read the platform boundary map

| Platform concept | Meaning and a useful review question |
| --- | --- |
| Android activity/service/receiver/provider | UI entry, background work, event receiver, or shared-data interface. Which external callers may invoke it? |
| Manifest, exported components, permissions | Declarations help define reachability and required rights. Compare declarations with runtime enforcement for the target platform version. |
| Intents and pending intents | Messages request actions; a pending intent can delegate a future operation under its creator's identity. Validate destination, action, mutable inputs, and delegated authority. |
| iOS sandbox, entitlements, provisioning | Sandbox restrictions and signed capabilities govern access; provisioning enables the intended app/device distribution relationship. An entitlement is not a backend role. |
| App groups and extensions | Shared containers or cooperating processes widen data access; identify every participant and retained file. |
| URL schemes/universal links | External navigation reaches an app. Ownership verification and input handling matter; a link parameter is not proof of authorization. |
| Data protection classes | Storage availability depends on device/key state and selected protection; explicitly test the expected locked/unlocked/restart condition. |

For a declared entry point, fill four columns: caller, accepted input, required identity, effect. Example: a notes link accepts an opaque note ID, requires a current app session, and retrieves content through an ownership-enforcing backend. Test missing ID, malformed ID, signed-out state, and another user's ID. Expected result: a clear rejection or authorized navigation, without untrusted parameters silently changing an account or privileged destination.

Use the [Android security guidance](https://developer.android.com/privacy-and-security/security-tips) and [Apple Platform Security](https://support.apple.com/guide/security/welcome/web) for the exact platform facilities you review.

## Lesson 3: make a data lifecycle table

Create synthetic examples of a session token, private note, profile identifier, diagnostic message, and exported attachment. For each, record creation, storage, readers, transmission, backup, expiration, and deletion. Include files, preferences, databases, shared storage, caches, temporary files, logs, crash reports, clipboard/pasteboard, screenshots/app-switcher previews, notifications, analytics, accessibility interfaces, and platform share flows.

Android Keystore and iOS Keychain provide different platform facilities for protecting key material or secrets; neither is simply a renamed ordinary text file. Understand access policy, device authentication, supported hardware backing, and key lifecycle. Encrypting a database while distributing its decryption secret with it provides little separation. A mobile package distributed to users cannot safely contain an unrestricted server-wide secret.

Suppose Alice logs out and Bob logs in. If the cache key is merely `note_id`, Bob may see Alice's cached content before the next network request. Bind cached records to account/tenant and implement the documented logout policy. Encryption may protect storage at rest while failing to fix this in-process identity confusion.

Test offline changes and synchronization conflicts too: a stale queued write must be reauthorized by the server when replayed. For deletion or device loss, distinguish local removal, server revocation, backup retention, and third-party copies. Do not assume app removal performs every remote lifecycle action.

## Lesson 4: inspect identity and transport as separate layers

Trace login → issuance → refresh → protected operation → logout/revocation. Add account switching, password reset, session invalidation, device binding, recent-authentication checks, concurrent sessions, and recovery. Biometrics can gate a local operation or key release; they do not independently demonstrate server permission to access an arbitrary record.

In a test build, observe requests through a dedicated proxy and test trust store. Record changes from the release build. TLS validation needs correct destination identity and trusted certificate handling, with deliberate error behavior. A proxy failure could instead be routing, a different network stack, or pinning. Cleartext fallback after a TLS error undermines the expected confidentiality.

Pinning is a design choice with rotation/recovery costs, not a universal pass/fail checkbox. When present, review update/recovery strategy and test the documented behavior. Use supported test-build instrumentation to inspect owned traffic. Removing a protection to observe requests changes the conditions of the evidence.

For embedded WebViews, review navigation allowlists, redirects, JavaScript bridges, file access, cookies, and external-app handoffs independently. A native bridge callable from untrusted content must not inherit unrestricted app privileges. In OAuth redirects, correlate the response with the initiating transaction and expected redirect handling; the presence of a callback URL alone proves neither identity nor consent.

## Lesson 5: work through the two-account exercise

Start with the portable [API example](examples/README.md) on the desktop. It supplies two synthetic owners and a fixed permission boundary. The emulator's loopback address refers to the emulator itself, so do not expect `127.0.0.1` to reach a desktop host automatically. Use the emulator's documented development routing or port-reversal mechanism within the isolated lab; do not expose the server publicly to solve routing. The API fixture uses HTTP and fixed tokens for learning, so it is unsuitable for production transport/token conclusions.

1. Create a minimal notes UI with explicit signed-out, Alice, and Bob states, an account-scoped cache, and a deep-link parser. Record the app/backend builds.
2. As Alice, read `n1`, background/restart the app, then log out. Inspect the documented cache and diagnostic locations.
3. Sign in as Bob. Request `n1` and open the equivalent deep link. Expected: no Alice content; backend denies cross-owner read. Bob's `n2` remains accessible.
4. Repeat signed out, with a discarded synthetic token, and offline. Distinguish a deliberate offline cache policy from a backend authorization result.
5. Add a harmless cache bug in a separate test copy by dropping the account key. Observe it, restore account-scoped indexing, and repeat the state sequence.
6. Save sanitized request/response evidence, cache keys, relevant code, lifecycle steps, and positive controls. Clear the test profile and remove proxy trust changes when finished.

The shared API has no refresh, token expiry, account deletion, or mobile key storage. Those require additional explicitly implemented fixtures; mark them untested rather than claiming this small lab covers them.

## Lesson 6: review the delivery chain and limitations

Compare debug and release artifacts: test endpoints, exported interfaces, logs, diagnostics, signing keys, embedded SDKs, dependency provenance, permissions, and update integrity. Trace SDK initialization and confirm that disabling collection stops its actual data flow. Evaluate secure random generation, key derivation, authenticated encryption, and rotation through established platform libraries rather than custom cryptography.

Static review reveals declarations and possible flows; dynamic observation confirms exercised behavior. Decompilers may reconstruct misleading names/types, and emulator behavior may differ for hardware-backed keys, biometrics, sensors, and platform integrity. Root/jailbreak detection, obfuscation, and tamper resistance can add friction but do not replace server controls.

**Answer checks:** A hidden delete button does not prove API enforcement. A signed app can contain an authorization defect. A clean logout screen does not prove caches or backups were purged. A denied read plus a working owner read is stronger than denial alone. Use [OWASP MASTG](https://mas.owasp.org/MASTG/) to organize test evidence, distinguish app/device/backend findings, and retain a matrix of device state, account, version, and network conditions. Finish with one repaired storage issue, one validated entry point, one server boundary test, and clearly listed physical-device gaps.
