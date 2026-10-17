# 18. Mobile application security

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#18-mobile-application-security)

<!-- TOPIC-TOC:START -->

## Contents

- [Knowledge and skill checklist](#knowledge-and-skill-checklist)
- [Safe projects and evidence](#safe-projects-and-evidence)
- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1: Understand the application as a distributed system](#stage-1-understand-the-application-as-a-distributed-system)
  - [Stage 2: Track data throughout its lifecycle](#stage-2-track-data-throughout-its-lifecycle)
  - [Stage 3: Evaluate entry points and identity](#stage-3-evaluate-entry-points-and-identity)
  - [Stage 4: Inspect transport and embedded web boundaries](#stage-4-inspect-transport-and-embedded-web-boundaries)
  - [Stage 5: Assess delivery and maintenance](#stage-5-assess-delivery-and-maintenance)
- [Worked lab: a two-account notes application](#worked-lab-a-two-account-notes-application)
- [Debugging and mastery gates](#debugging-and-mastery-gates)

<!-- TOPIC-TOC:END -->



**Prerequisites:** Web/API testing, HTTP/TLS, programming, authentication, cryptography basics, and Linux familiarity. Learn Android first if that matches available hardware; add iOS when a supported development environment and device are available.

## Knowledge and skill checklist

- [ ] Understand app packaging, signing, installation, updates, application lifecycle, process isolation, sandbox boundaries, and the distinction between the app, device, backend, and third-party services.
- [ ] Learn enough Kotlin/Java and Swift/Objective-C to follow security-sensitive code; recognize Flutter, React Native, and hybrid applications and their native integration boundaries.
- [ ] Read Android manifests and understand exported components, permissions, activities, services, broadcast receivers, content providers, intents, pending intents, and interprocess communication.
- [ ] Understand iOS entitlements, provisioning, sandboxing, app groups, URL schemes, universal links, extensions, and data protection classes.
- [ ] Evaluate local databases, files, caches, preferences, logs, screenshots, clipboard use, notifications, crash reports, backups, and temporary files for inappropriate sensitive data retention.
- [ ] Distinguish the Android Keystore and iOS Keychain from ordinary app storage; understand key access controls, device authentication requirements, and hardware-backed capabilities and limitations.
- [ ] Trace login, logout, token refresh, account switching, password reset, session invalidation, device binding, biometrics, and recovery workflows. Confirm that backend authorization remains effective when client assumptions fail.
- [ ] Evaluate certificate validation, cleartext communication, trust configuration, certificate pinning decisions, proxy behavior, and error handling. Learn interception through test builds or explicitly authorized instrumentation.
- [ ] Review deep-link validation, WebViews, JavaScript bridges, external navigation, file access, IPC input validation, and content handling.
- [ ] Understand secure randomness, key derivation, authenticated encryption, hardcoded secrets, key rotation, and the limits of attempting to keep a server secret inside a distributed app.
- [ ] Assess release settings, debug interfaces, dependency provenance, embedded SDKs, build secrets, signing-key protection, update integrity, and privacy-related permissions.
- [ ] Learn static analysis and dynamic observation, including decompilation limitations, runtime state, instrumentation concepts, and differences between emulators and physical devices.
- [ ] Treat root/jailbreak detection, obfuscation, and tamper resistance as context-dependent defense layers; determine whether a real server-side security boundary exists.
- [ ] Assess offline behavior, synchronization conflicts, lost-device behavior, accessibility exposure, platform-version differences, and account deletion.

## Safe projects and evidence

1. Build a small app that authenticates to your local API and stores a synthetic token. Diagram the complete data flow before testing.
2. Assess an intentionally vulnerable training app or your own test build. Record device/OS/app versions, tested controls, evidence, and limitations.
3. Repair one storage issue, one deep-link or IPC issue, and one backend authorization issue; retest the same scenarios.

**Exit criteria:** Produce a mobile report that distinguishes device, application, and backend findings; demonstrate both static and dynamic evidence; explain where emulator results require physical-device confirmation. Use the [OWASP MASVS/MASTG overview](https://mas.owasp.org/MASTG/0x03-Overview/) to connect security requirements with testing, and consult [Apple Platform Security](https://support.apple.com/guide/security/welcome/web) for Apple-specific protection models.

## Detailed learning sequence

### Stage 1: Understand the application as a distributed system

Create a component inventory covering the installation package, native code, embedded web content, operating-system services, identity provider, API, analytics SDKs, notification service, and update channel. For every component, identify its publisher, signing identity, execution privilege, data handled, and trust relationship. Learn installation, first launch, foreground/background transitions, process death, device restart, upgrade, account switching, and removal as distinct states.

- [ ] Read a simple Android application from manifest to activity, service, storage call, and network client.
- [ ] Read an iOS sample from entitlements and entry point through a view, data store, and API request.
- [ ] Explain how cross-platform frameworks delegate to native plugins and where an apparently simple API crosses into privileged platform functionality.
- [ ] Document build variant, package identifier, signing configuration, target platform, and debug features for each tested artifact.

### Stage 2: Track data throughout its lifecycle

Make a data inventory with synthetic examples: session tokens, cached messages, profile records, private files, device identifiers, and diagnostic events. For each, record creation, storage, access, transmission, backup, expiration, and deletion. Separate protection while the device is unlocked from protection after locking or restarting. Understand that encrypted storage is useful only with an appropriate key lifecycle and access policy.

Inspect private storage, shared storage, databases, temporary files, screenshots, app-switcher previews, notifications, pasteboards, logs, and crash reports. Trace exported files and platform share features. Check whether logout deletes the intended local data, whether another account inherits caches, and whether backup restoration recreates obsolete secrets. Treat analytics collection as a data flow requiring its own justification.

### Stage 3: Evaluate entry points and identity

Construct a table of exported components, deep links, universal links, URL schemes, IPC endpoints, content providers, and document import handlers. Record who can invoke each entry point, accepted input, authorization requirements, and resulting state changes. Test a legitimate invocation, malformed input, missing authentication, and a mismatched account using your own fixtures.

Distinguish local biometric confirmation from server-side authorization. Follow token issuance, refresh, revocation, device loss, recovery, and logout. Explain which operation requires recent authentication and which can safely use an existing session. Evaluate concurrent sessions and offline changes. A screen that hides an action does not prove the API enforces permission.

### Stage 4: Inspect transport and embedded web boundaries

Trace the trust decision for a TLS connection: hostname, certificate chain, trust store, debug exceptions, and error handling. Use an application you built to observe traffic through a test proxy. Record what changes in the test build and what remains representative of release behavior. If certificate pinning exists, review its operational assumptions, backup pins or equivalent recovery design, and rotation strategy rather than reporting its mere absence as a universal defect.

For WebViews, separate navigation policy, JavaScript execution, native bridges, cookie handling, and file access. For a native bridge, list each exposed operation and its caller checks. Review redirects and external-app handoffs. Analyze OAuth redirects using state and transaction correlation; do not assume that possession of a deep-link parameter proves the request belongs to the current user.

### Stage 5: Assess delivery and maintenance

Compare development and release packages for diagnostics, test endpoints, signing identity, exposed components, embedded credentials, and dependency inventory. Document build provenance, signing-key access, update approval, and rollback behavior. Learn how platform changes affect permission requests, background execution, and storage without assuming one OS release represents every supported device.

Investigate third-party SDK initialization: which permissions it requires, when it starts collecting information, how errors are logged, and whether removal disables the data flow. Maintain an assessment matrix across device state, app version, account role, and network condition.

## Worked lab: a two-account notes application

**Setup:** Build a minimal training application backed by a local API. Create Alice and Bob with invented notes, an expiring token, one deep link to a note, and optional offline caching. Use a dedicated emulator profile without personal accounts. Keep a clean installation snapshot and a reproducible debug build.

**Actions:** Map the data flow and record baseline behavior. Sign in as Alice, create a synthetic note, background the application, restart it, log out, and sign in as Bob. Test the deep link while signed out and while signed in as the other user. Review local storage and test proxy traces. Repeat with an expired token and disconnected network.

**Expected behavior:** The backend checks ownership on every note operation; a deep link opens only authorized content; logout and account switching apply the documented cache policy; expired sessions fail predictably; sensitive data does not appear in unnecessary logs or notifications.

**Evidence:** Preserve sanitized requests, storage locations, relevant code lines, app-state transitions, timestamps, and a device/build matrix. A screenshot alone is insufficient to establish server authorization. Separate reproducible evidence from emulator-specific observations.

**Correction:** Bind caches to account identity, remove unnecessary sensitive logging, validate entry-point parameters, and enforce ownership in the backend. Retest each original sequence plus a legitimate same-account sequence to detect functional regressions.

## Debugging and mastery gates

Proxy failures can reflect trust configuration, an unexpected network stack, device routing, or pinning. An empty database may mean the app uses another profile, encrypts records, or writes only after a lifecycle event. Runtime instrumentation can change timing and integrity checks. Treat test-build behavior as evidence with explicit limitations.

- [ ] Explain one security control from source code to observed runtime behavior.
- [ ] Demonstrate an unauthorized operation failing at the server even when the client submits it.
- [ ] Complete a data-retention matrix for logout, account switching, removal, backup, and restore.
- [ ] Produce one storage, one entry-point, and one authentication finding with corrected retests.
- [ ] Identify controls requiring a physical device and record untested scenarios honestly.

**Primary study sources:** Use [OWASP MASTG](https://mas.owasp.org/MASTG/) for test organization and the [Android security checklist](https://developer.android.com/privacy-and-security/security-tips) for platform implementation topics. Pair Apple-specific claims with Apple Platform Security above and the API documentation matching the device and SDK you actually assess.

