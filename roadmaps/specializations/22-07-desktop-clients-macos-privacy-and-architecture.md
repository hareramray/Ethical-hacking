# 22.7 Desktop clients, macOS, privacy, and architecture

[All topic roadmaps](../README.md) | [Specialization overview](../22-advanced-specialization-map.md)

<!-- TOPIC-TOC:START -->

## Contents

- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1: Model a desktop application and its privileges](#stage-1-model-a-desktop-application-and-its-privileges)
  - [Stage 2: Review input and process boundaries](#stage-2-review-input-and-process-boundaries)
  - [Stage 3: Learn macOS protection mechanisms distinctly](#stage-3-learn-macos-protection-mechanisms-distinctly)
  - [Stage 4: Audit the installer and update lifecycle](#stage-4-audit-the-installer-and-update-lifecycle)
  - [Stage 5: Add privacy engineering and architecture review](#stage-5-add-privacy-engineering-and-architecture-review)
- [Worked lab: a desktop notes client and updater](#worked-lab-a-desktop-notes-client-and-updater)
- [Blind spots and completion gates](#blind-spots-and-completion-gates)

<!-- TOPIC-TOC:END -->



**Prerequisites:** Operating systems, programming, authentication, and threat modeling.

- [ ] Review thick-client local storage, IPC, installer privileges, auto-update integrity, backend authorization, embedded browsers, Electron trust boundaries, and unsafe local file handling.
- [ ] For macOS, learn app signing, notarization, Gatekeeper, TCC permissions, sandboxing, entitlements, Keychain, XPC, launch services, and endpoint telemetry.
- [ ] Study security architecture: trust boundaries, least privilege, defense in depth, fail-safe behavior, resilience, secure defaults, tenant isolation, and dependencies.
- [ ] Study privacy engineering: data inventory, purpose limitation, minimization, retention, deletion, re-identification risks, consent boundaries, and privacy threat modeling.
- [ ] Explore cryptographic protocol review, HSM/TPM design, key lifecycle, post-quantum migration planning, and side-channel resistance as separate advanced tracks requiring deeper mathematics and specialist review.

**Project:** Threat-model a small desktop application and its update service, then review its data lifecycle. **Pass:** Connect each significant risk to a design decision, validation evidence, an owner, and a practical remediation plan.

## Detailed learning sequence

### Stage 1: Model a desktop application and its privileges

Inventory the main process, helper services, embedded browser, local database, updater, installer, extensions, background tasks, and backend API. Identify the operating-system user and privilege of each process. Record who can supply files, links, IPC messages, configuration, plugins, or update metadata. Distinguish a user's local files from application-managed state and from remotely synchronized data.

- [ ] Trace installation, first launch, sign-in, update, repair, logout, and removal.
- [ ] Identify privileged helpers and explain why each requires elevated access.
- [ ] Map named pipes, sockets, XPC services, shared files, and custom URL schemes to callers and operations.
- [ ] Distinguish local authentication, operating-system identity, application identity, and backend authorization.
- [ ] Review database, cache, log, temporary-file, crash-report, and export locations.
- [ ] Record supported operating-system and application versions with every assessment.

### Stage 2: Review input and process boundaries

For every IPC endpoint, list its operation, argument schema, caller verification, authorization check, and privileged effect. Do not assume a local endpoint is trusted merely because it binds to loopback or uses a hidden name. Validate file paths, resource identifiers, ownership, and expected state at the component that performs the operation.

Study file import, archive extraction, document previews, external navigation, protocol handlers, and plugin loading. Follow a file from selection through parsing and storage. Consider symbolic links, temporary-file ownership, ambiguous paths, and race conditions where they apply. Avoid treating a file extension as proof of safe content.

For Electron or another embedded-browser framework, map renderer content to privileged native capabilities. Review sandboxing, context separation, exposed bridge APIs, navigation policy, external URL opening, and content security controls. The bridge should expose specific operations with validated arguments. Arbitrary filesystem or command access creates a much broader boundary than a single business feature requires.

### Stage 3: Learn macOS protection mechanisms distinctly

Study application signing, designated identity requirements, notarization, Gatekeeper assessment, app sandboxing, entitlements, TCC permissions, Keychain access, XPC, and system extension concepts. Explain which mechanism verifies publisher identity, which limits resources, and which controls access to protected user data. Avoid presenting any single mechanism as a complete security guarantee.

Trace a permission request through initial consent, denial, later changes, background behavior, and application upgrades. Review helper identities and XPC caller validation against the actual intended client. Learn which capabilities differ between development and distribution builds. Use Apple documentation matching the system under test and record when a test environment relaxes a normal platform protection.

### Stage 4: Audit the installer and update lifecycle

Draw the update chain: discovery, metadata, download, verification, staging, installation, restart, and recovery. Identify signing keys, authorized publishers, version policy, destination paths, installer privileges, and rollback behavior. Separate transport security from artifact authenticity. A download over TLS still needs the intended package identity and applicable integrity checks.

Test a valid local training update, an altered package, an incompatible package, and an interrupted installation using your own updater. Review whether the update component can be abused as a general privileged file writer. Record how users recover when a release is broken and how the publisher revokes or replaces signing authority under the design.

### Stage 5: Add privacy engineering and architecture review

Create a data inventory with purpose, collection source, recipients, storage location, access, retention, deletion, and user controls. Distinguish security of collected data from whether collecting it is appropriate. Consider inferred attributes, linkage across datasets, persistent identifiers, background telemetry, and sensitive data in crash reports.

Trace deletion through the local database, synchronized backend, search index, caches, backups, and third-party processors. Document exceptions and delays rather than promising instant universal removal. Evaluate whether account switching, shared computers, and lost devices reveal another user's data.

Write architecture decisions around explicit requirements and trust boundaries. Compare alternative designs by privilege, failure behavior, recovery, auditability, and operational complexity. Study key management, TPM/HSM usage, protocol analysis, and post-quantum migration as separate advanced investigations; begin with key inventory, algorithm dependencies, and replacement paths before drawing specialist cryptographic conclusions.

## Worked lab: a desktop notes client and updater

**Setup:** Build a small local client with synthetic notes, two fictional accounts, a restricted native bridge, a mock backend, and a training update service. Use an ordinary user account in a disposable VM. On macOS, use a dedicated test user or supported test environment and keep a record of platform settings.

**Actions:** Trace note creation, export, logout, account switching, deletion, and update. Submit a malformed local message to your own bridge and confirm its schema validation. Test an authorized operation and a caller without the required identity. Install a valid training update and reject an altered package. Review diagnostic output for unnecessary note contents or tokens.

**Expected behavior:** Each account sees only its intended data; the bridge exposes a narrow permitted action; the backend enforces ownership; update verification rejects incorrect artifacts; logs minimize sensitive content; deletion follows the documented lifecycle.

**Evidence:** Save the component diagram, process identities, IPC contract, data inventory, update checks, sanitized runtime records, and before/after state. State which macOS-specific controls were tested directly and which were reviewed only through documentation.

**Correction:** Reduce helper privileges, validate callers and arguments, partition account caches, remove unnecessary telemetry, or fix package verification. Retest the original failure and normal use. Verify that removal cleans intended local state without deleting unrelated user files.

## Blind spots and completion gates

A signed application can still contain vulnerable logic. Notarization does not prove correct backend authorization. A sandbox entitlement may grant more access than the feature needs. An IPC endpoint can authorize one caller but accept arguments that exceed that caller's intended authority. A privacy policy can describe deletion while a background job recreates the data.

- [ ] Explain the purpose and limitation of each platform protection you rely on.
- [ ] Trace one privileged operation from caller to effect with all authorization checks.
- [ ] Demonstrate update authenticity and a documented recovery path.
- [ ] Complete a data-lifecycle review including derived copies and telemetry.
- [ ] Compare two design alternatives using explicit security and usability tradeoffs.
- [ ] Deliver corrected tests and a clear list of platform-specific limitations.

**Primary resources:** Study [Electron's security guidance](https://www.electronjs.org/docs/latest/tutorial/security), [Apple Platform Security](https://support.apple.com/guide/security/welcome/web), and the [NIST Privacy Framework](https://www.nist.gov/privacy-framework). Use official API documentation for the precise entitlements, IPC interfaces, and data protection behavior you assess.

