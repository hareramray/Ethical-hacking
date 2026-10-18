# Tutorial: Desktop clients, macOS, privacy, and architecture

[Index](../README.md) | [Full source curriculum](../curriculum/specializations/22-07-desktop-clients-macos-privacy-and-architecture.md) | [Original roadmap](../../roadmaps/specializations/22-07-desktop-clients-macos-privacy-and-architecture.md)

## Follow a note from the interface to every copy

Review a fictional desktop application named `Local Notes Lab`. It stores synthetic notes for two accounts, exports a selected note, and checks a training update manifest. Begin with a component and data-flow model. Use an ordinary account in a disposable VM for runtime experiments. On a platform you do not have, perform a clearly labeled design review instead of claiming a successful platform test.

The learning goal is to connect each risk to a design decision, owner, evidence, and practical correction. Desktop applications combine local files, operating-system privileges, embedded browsers, background helpers, and remote services. “It runs locally” does not make all input trustworthy, and successful operating-system sign-in does not authorize access to every backend account.

## 1. Inventory processes and lifecycle transitions

List the main process, renderer or embedded browser, helper service, installer, updater, local database, plugins, background tasks, crash reporter, and backend API. Record their operating-system identities and privileges. For each privileged helper, write the specific feature requiring elevation. An updater that installs only into a user-owned application directory may have different needs from a machine-wide installer.

Trace installation, first launch, sign-in, normal editing, export, update, repair, logout, account switching, and removal. Record where user-selected files differ from application-managed state. Uninstalling application caches should not remove an unrelated document simply because a user once imported it.

| Component | Input source | Intended effect | Boundary to validate |
|---|---|---|---|
| Renderer | Synthetic note text | Display and edit note | Text cannot invoke arbitrary native work |
| Native bridge | Structured export request | Export selected owned note | Caller, account, note ID, destination |
| Local database | Application writes | Persist note state | Account partition and file permissions |
| Backend | Authenticated API request | Sync authorized note | Server-side ownership |
| Updater | Training manifest and package | Replace application version | Publisher, integrity, version, compatibility |
| Crash reporter | Diagnostic event | Record useful failure data | Minimize note text and tokens |

Map named pipes, sockets, XPC services, shared files, and custom URL schemes to actual callers and operations. Loopback binding and an obscure endpoint name are not caller authorization. Record the application and OS versions because IPC and platform protection behavior are version-specific.

## 2. Design a narrow native bridge

Suppose the renderer needs to export one note. A broad `write_any_file(path, bytes)` interface exposes far more capability than the feature requires. Define `export_note(note_id, destination_token)` instead. The native component resolves the note under the active account, obtains a destination through the intended user selection flow, validates state, and performs the write.

Use this in-memory validation exercise before filesystem access:

```python
notes = {"N1": {"owner": "alice", "text": "SYNTHETIC-AMBER"},
         "N2": {"owner": "bob", "text": "SYNTHETIC-BIRCH"}}

def export_request(caller, account, message):
    if caller != "trusted-notes-ui":
        return "denied_caller"
    if set(message) != {"operation", "note_id"}:
        return "invalid_schema"
    if message["operation"] != "export_note":
        return "unknown_operation"
    if not isinstance(message["note_id"], str):
        return "invalid_note_id"
    note = notes.get(message["note_id"])
    if note is None or note["owner"] != account:
        return "not_available"
    return {"export_text": note["text"]}

print(export_request("trusted-notes-ui", "alice",
                     {"operation": "export_note", "note_id": "N1"}))
print(export_request("trusted-notes-ui", "alice",
                     {"operation": "export_note", "note_id": "N2"}))
```

Expect Alice's synthetic text for N1 and `not_available` for N2. Test an unknown operation, extra field, integer note ID, and untrusted caller. The caller string is a simulation; a real IPC implementation must derive peer identity from an appropriate platform mechanism, not accept a caller label inside the message. Backend requests still require independent authorization.

Follow file imports through selection, parsing, storage, preview, and export. Extensions do not prove content format. Archive extraction needs destination containment and appropriate handling of links and special entries. Temporary files need correct ownership. Symbolic links, ambiguous paths, and changes between validation and use can undermine a path check. Prefer APIs that operate on the intended opened resource and follow documented platform guarantees.

For embedded browsers, distinguish renderer sandboxing, context separation, bridge APIs, navigation policy, external URL opening, and content security controls. A compromised renderer should not receive an arbitrary native execution primitive. Electron's guidance addresses these boundaries and cautions about privileged functionality exposed to renderer content. [Electron security guidance](https://www.electronjs.org/docs/latest/tutorial/security)

## 3. Understand macOS protections separately

Application signing connects code to a signing identity and integrity checks. Designated requirements help express expected code identity. Notarization and Gatekeeper participate in the platform's distribution and launch assessment. The App Sandbox restricts resources according to its model and entitlements. TCC manages access decisions for categories of protected user data. Keychain stores credentials under access policies. XPC supports communication between processes. None of these replaces the application's business authorization. [Apple Platform Security](https://support.apple.com/guide/security/welcome/web)

For a documentation worksheet, map one note feature to each relevant protection. Importing a user-selected document, reading an address book, and launching a helper have different requirements. Entitlements describe capabilities; review whether each is justified. Launch Services and custom URL handlers affect how documents and URLs reach the app. System extensions and endpoint telemetry have separate platform constraints and deployment considerations.

On an actual supported macOS test environment, record initial permission state, request a permission through the normal UI, deny it, and verify graceful failure. Then grant it and verify the feature. Change it later and inspect background behavior. Repeat the relevant scenario after an application update. Document development signing or relaxed test settings because distribution behavior may differ.

For XPC, review both helper identity and caller validation using the APIs supported by the target OS. A trusted caller can still submit an unauthorized resource identifier, so peer validation and argument authorization remain distinct. Record which controls were directly observed and which were inferred from documentation; do not report a Windows-only review as a macOS runtime test.

## 4. Review the complete update chain

Draw discovery, metadata retrieval, package download, verification, staging, installation, restart, and recovery. Identify publisher identity, signing key lifecycle, permitted version, platform compatibility, destination, and installer privilege. TLS protects a transport relationship; it does not by itself establish that a downloaded package is the intended application release.

Create four synthetic manifest fixtures:

| Fixture | Publisher check | Integrity check | Compatibility | Expected outcome |
|---|---|---|---|---|
| Version 3, intended platform | Pass | Pass | Pass | Stage and install |
| Modified package | Pass | Fail | Pass | Reject before replacement |
| Other-platform package | Pass | Pass | Fail | Reject with clear reason |
| Interrupted staging | Not complete | Not complete | Pending | Preserve recoverable installed state |

The checks in this worksheet are modeled outcomes, not a cryptographic implementation. In a real training updater, use its documented package-signature mechanism and fresh test keys. Preserve package hashes, manifest, decision logs, old version, and recovery instructions.

Check whether update parameters can turn the helper into a general privileged file writer. Fixed installation destinations and validated package structure reduce this risk. Define rollback and revocation policy: recovering from a broken release must not silently permit any older vulnerable release or unknown signer. Exercise interruption in the disposable environment and verify application state after recovery.

## 5. Audit the data lifecycle and architecture

Build an inventory with data type, purpose, source, recipients, storage, access, retention, deletion, and user controls. Include notes, attachment names, persistent device IDs, account IDs, crash records, telemetry, caches, temporary files, backups, and exports. Security asks whether collected data is protected; privacy also asks whether collecting and retaining it serves an appropriate purpose.

For a crash report, compare two designs. Design A records the entire note and access token. Design B records an error category, application version, and a short synthetic request identifier. If B supports diagnosis, collecting A adds unnecessary exposure. Data minimization can improve both privacy and incident impact. The NIST Privacy Framework organizes privacy-risk management separately from a narrow access-control checklist. [NIST Privacy Framework](https://www.nist.gov/privacy-framework)

Privacy threat modeling also examines inferred attributes and re-identification. A pseudonymous device ID combined with exact activity times can link events across datasets even when names are absent. Ask whether that linkage serves the stated purpose, whether precision can be reduced, and whether separate uses require separate consent or controls. Test the actual exported diagnostics against those decisions rather than relying only on policy text.

Trace deletion through the local database, sync queue, backend, search index, caches, backups, and processors. Introduce a pending sync item in the model, delete the note, then restart. If the job recreates it, deletion is incomplete even though the UI initially looked correct. Define tombstones or another consistent deletion policy and test its lifecycle. Document backup retention and restoration behavior honestly.

Switch from Alice to Bob without restarting. Bob must not see Alice's note titles, previews, recent-file list, or cached exports. Repeat after restart. Shared computers and lost devices make session state, local permissions, encryption, and token revocation relevant. Consent boundaries should reflect actual features and data uses rather than blanket permission for unrelated collection.

Write two architecture alternatives: a privileged general helper versus a narrow user-level exporter. Compare privilege, feature coverage, auditability, failure handling, recovery, and operational complexity. Least privilege, defense in depth, secure defaults, tenant isolation, and fail-safe behavior become concrete design properties when connected to these alternatives. For example, an unavailable authorization service should not cause the backend to return every tenant's notes.

## 6. Place cryptography research behind explicit questions

Advanced protocol review asks about participants, threat model, message authentication, freshness, key confirmation, and failure behavior. Begin by inventorying algorithms, keys, certificates, owners, storage, rotation, revocation, recovery, and dependencies. An HSM or TPM can protect key operations under a defined model, but does not authorize every application request automatically.

Post-quantum migration planning starts with where cryptographic dependencies exist, how long confidentiality must last, and whether algorithms and protocols can be replaced. Do not invent a new protocol or claim migration complete after changing one library. Side-channel resistance requires implementation-specific evidence and specialist analysis. These are separate deeper tracks, not conclusions established by the notes-client lab.

## Questions with answer guidance

1. **Can a signed, notarized app have a cross-account flaw?** Yes. Publisher and launch checks do not prove local or backend authorization correctness.
2. **Why validate both IPC caller and resource ID?** A legitimate component may request an operation beyond the current account's authority.
3. **What proves deletion?** Evidence across all managed copies and background jobs, with explicit retention exceptions and delays.
4. **What should a recovery test verify?** Intended software, correct account state, data integrity, and normal operation—not just that the process starts.

Deliver the component map, privilege inventory, IPC contract, lifecycle trace, data inventory, update results, design comparison, and retest record. Each finding needs an owner and a measurable correction, such as “Bob's account cannot retrieve Alice's note through UI, cache, or API after switching and restarting.” Preserve platform-specific limitations beside the evidence.
