# 06. Windows administration

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#06-windows-administration)

<!-- TOPIC-TOC:START -->

## Contents

- [Windows architecture and permissions](#windows-architecture-and-permissions)
- [Administration and observability](#administration-and-observability)
- [Enterprise foundations](#enterprise-foundations)
- [Safe practice and exit criteria](#safe-practice-and-exit-criteria)
- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1 — Identify the environment and execution context](#stage-1--identify-the-environment-and-execution-context)
  - [Stage 2 — Reason about Windows access decisions](#stage-2--reason-about-windows-access-decisions)
  - [Stage 3 — Administer through objects and evidence](#stage-3--administer-through-objects-and-evidence)
  - [Stage 4 — Maintain services, network boundaries, and recovery](#stage-4--maintain-services-network-boundaries-and-recovery)
  - [Stage 5 — Prepare for enterprise identity](#stage-5--prepare-for-enterprise-identity)
- [Guided labs with evidence](#guided-labs-with-evidence)
  - [Lab A — Local versus shared-folder access](#lab-a--local-versus-shared-folder-access)
  - [Lab B — Service and event correlation](#lab-b--service-and-event-correlation)
  - [Lab C — Recover a usable configuration](#lab-c--recover-a-usable-configuration)
- [Capstone rubric and retention](#capstone-rubric-and-retention)

<!-- TOPIC-TOC:END -->



**Prerequisites:** Sections 03–04. **Priority:** Core for general security work; deeper enterprise administration is essential for internal assessments.

## Windows architecture and permissions

- [ ] Understand Windows editions, supported builds, update channels, firmware boot, kernel/user mode, processes, threads, drivers, and services.
- [ ] Navigate NTFS, system/user directories, environment variables, registry hives, executable formats, DLLs, and application installation locations.
- [ ] Learn security identifiers (SIDs), local/domain accounts, groups, access tokens, privileges, integrity levels, and User Account Control.
- [ ] Understand NTFS ACLs, inheritance, explicit permissions, effective access, ownership, and how share permissions combine with filesystem permissions.
- [ ] Recognize service accounts, scheduled-task identities, startup mechanisms, and the distinction between an interactive user's rights and a background service's rights.
- [ ] Understand local security policy, audit policy, Credential Manager, certificate stores, and protected operating-system components conceptually.

## Administration and observability

- [ ] Use PowerShell discovery/help, object pipelines, properties, filtering, structured output, error handling, and approved remoting practices.
- [ ] Use Event Viewer, Task Manager, Resource Monitor, Services, Task Scheduler, and built-in system information to investigate normal behavior.
- [ ] Learn Windows Event Log channels, event timestamps, authentication events, service changes, PowerShell logging, and centralized collection concepts.
- [ ] Configure network profiles, DNS, routes, host firewall rules, SMB shares, RDP restrictions, and secure administrative access in your lab.
- [ ] Understand patch management, Microsoft Defender, BitLocker, Secure Boot, recovery keys, recovery environments, system restore limitations, and tested backups.
- [ ] Distinguish application allowlisting, antivirus detection, endpoint telemetry, and privilege management; understand each control's purpose.
- [ ] Learn WSL and virtualization boundaries; verify which host files, network interfaces, and credentials a development environment can access.

Use [Microsoft's PowerShell overview](https://learn.microsoft.com/en-us/powershell/scripting/overview) to understand its administration model, then practice with the help available in your installed version.

## Enterprise foundations

- [ ] Distinguish workgroups, Active Directory Domain Services, and cloud identity; understand that a domain join and a cloud registration are different relationships.
- [ ] Learn domains, forests, organizational units, domain controllers, directory objects, trusts, DNS dependencies, and Group Policy processing.
- [ ] Explain the broad roles of Kerberos, LDAP, SMB, NTLM, certificate services, and time synchronization without yet attempting attack techniques.
- [ ] **Advanced:** Study delegated administration, group-managed service accounts, privileged access models, local administrator password management, and identity lifecycle controls.

## Safe practice and exit criteria

**Labs:** Create two local users in a Windows VM; build a shared test folder with distinct permissions; predict and verify each user's access. Install a harmless service, identify its account and events, and restore its configuration. In a separately isolated enterprise lab, join a client to your own test domain and trace an ordinary sign-in.

**Exit gate:** Explain effective access to a shared file, identify a service's security context, correlate a local configuration change with logs, and distinguish local, domain, and cloud identities.

**Common gaps:** Assuming membership in Administrators means every process is elevated; ignoring share permissions; treating registry presence as execution evidence; disabling protective controls instead of understanding a failure.

## Detailed learning sequence

Build the **practical track** in a disposable Windows VM: identities, effective access, PowerShell inspection, services, logs, networking, updates, and recovery. Enterprise identity starts at **awareness depth** unless you have a separate owned domain lab and sufficient resources. Check the installed edition and build before following administration instructions; available features and policy interfaces differ.

### Stage 1 — Identify the environment and execution context

- [ ] Record operating-system edition, build, architecture, update state, virtualization platform, and PowerShell edition/version. Distinguish the VM name, local computer name, signed-in identity, and any domain or cloud relationship.
- [ ] Navigate the Windows, Program Files, ProgramData, and user profile directories. Distinguish machine-wide application data from per-user data and temporary files. Use environment-variable expansion deliberately rather than hardcoding another user's profile path.
- [ ] Learn drive letters, volumes, NTFS, junctions, and symbolic links. Treat reparse points as a reason to verify resolved paths before recursive operations; a displayed folder can redirect elsewhere.
- [ ] Explain executable files, DLL loading, processes, threads, handles, services, and drivers at a diagram level. Inspect an ordinary application's process tree and executable location before investigating suspicious-looking names.
- [ ] Learn registry hives and scopes, value types, and 32-bit/64-bit application considerations. Export only the synthetic setting you are changing in a lab; an arbitrary registry export is not a complete system backup.
- [ ] Compare an ordinary terminal with an elevated terminal. Inspect identity and privileges in each and explain why the same account can have different effective capabilities in different processes.

### Stage 2 — Reason about Windows access decisions

- [ ] Distinguish a local account from a domain account that has the same displayed name. Use the account authority and SID when identifying a principal.
- [ ] Learn security descriptors, DACLs, SACLs, access-control entries, inheritance, and ownership. Explain that a DACL governs access while a SACL contributes audit policy; auditing does not itself grant permission. Use [Microsoft's access-control model](https://learn.microsoft.com/en-us/windows/win32/secauthz/access-control-components) as the conceptual reference.
- [ ] Predict effective access using the requested operation, the actual process token, group membership, and applicable entries. Avoid reducing all ACL evaluation to the slogan “deny always wins”; entry ordering and inherited versus explicit entries matter.
- [ ] Distinguish object permissions from user rights and privileges, such as permitted logon types or privileged backup operations. Learn integrity levels and UAC as additional parts of the model rather than synonyms for an ACL.
- [ ] Create task-oriented groups and assign folder permissions to those groups. Compare read, write, modify, and full control. Understand why granting ownership or permission-changing rights is broader than granting content editing.
- [ ] For SMB, verify both share permissions and NTFS permissions. Network access is constrained by both; a direct local-path test does not exercise the share permission check.
- [ ] Learn inheritance changes by inspecting a small synthetic directory tree. Record explicit and inherited entries before changing inheritance so the intended outcome can be restored.
- [ ] Understand when a new sign-in or service restart is needed for token-related changes to take effect. Do not assume a group edit changes every already-running process immediately.

### Stage 3 — Administer through objects and evidence

- [ ] Start PowerShell with `Get-Command`, `Get-Help`, and `Get-Member`. Inspect objects with `Select-Object`; filter with `Where-Object`; format only for final display. Formatting output early can discard the structured properties later steps need.
- [ ] Use read-only inventory examples such as `Get-Process`, `Get-Service`, `Get-ComputerInfo`, `Get-NetIPConfiguration`, and `Get-NetTCPConnection` where available. Read help and note required privileges or module limitations.
- [ ] Understand properties, arrays, pipelines, parameter binding, providers, and the distinction between a PowerShell cmdlet and a native executable. A native program's exit code needs its own handling.
- [ ] Query Event Logs with `Get-WinEvent` using a bounded time range and provider/channel filters. Export selected events or an appropriate EVTX record while retaining timestamps and event XML fields where needed.
- [ ] Compare Task Manager, Resource Monitor, Services, Task Scheduler, and Event Viewer views of one normal workload. Correlate process ID, service name, identity, timestamps, and executable path rather than matching only a display label.
- [ ] Distinguish an installed service, running service, scheduled task definition, and an observed task execution. A registry startup entry or task definition establishes configuration, not proof that it ran successfully.
- [ ] Understand terminating and nonterminating PowerShell errors. Write scripts that preserve error details and stop when continuing would produce misleading results; avoid globally hiding errors.
- [ ] Export structured inventory to CSV/JSON with explicit fields and encoding. Remove secrets and unnecessary personal data from evidence before sharing it.

### Stage 4 — Maintain services, network boundaries, and recovery

- [ ] Inspect a service's logon identity, start mode, executable path, dependencies, and recovery actions. Separate the interactive user's access from the service's access to local files and remote resources.
- [ ] Configure a harmless scheduled task with a predictable output file. Compare interactive versus background execution, working directory, environment, and logon requirements. Use synthetic data and a dedicated account where appropriate.
- [ ] Inspect addresses, DNS servers, routes, network profiles, firewall rules, and listeners. Understand why a rule scoped to one profile may not apply after the active network profile changes.
- [ ] Create a narrow inbound rule for one lab service, one protocol/port, and the lab subnet. Verify that the service is reachable as intended and that an unrelated port remains closed.
- [ ] Learn SMB share creation and removal, administrative-share awareness, and secure remote-administration restrictions. Keep RDP or management services reachable only within the intended lab boundary.
- [ ] Inspect Defender health, update status, and ordinary security events. When a control blocks the lab application, read the evidence and correct the application or configuration instead of disabling protection globally.
- [ ] Explain Secure Boot, full-volume encryption, recovery keys, and startup recovery as different controls. Practice recovery with disposable guest data; keep the recovery material separately accessible before altering boot or encryption settings.
- [ ] Distinguish restore points, VM checkpoints, file backup, and a recoverable system image. Verify a restore in the lab; a backup job reporting success does not demonstrate that an application can run from its restored data.
- [ ] For WSL or containers, inventory mounted host paths, network exposure, environment variables, and credential access. A separate shell or filesystem view does not automatically imply a complete isolation boundary.

### Stage 5 — Prepare for enterprise identity

- [ ] Draw workgroup, AD DS domain, and cloud identity relationships separately. Distinguish a device join, registration, user sign-in, and access to a remote application.
- [ ] Learn forest, domain, OU, domain controller, computer object, group, and trust. Explain administrative delegation and why OU organization is not itself a network boundary.
- [ ] Explain DNS dependency, domain-controller discovery, time synchronization, Kerberos ticket roles, LDAP directory queries, SMB file access, and Group Policy distribution at awareness depth.
- [ ] Learn Group Policy scope, inheritance, filtering, processing, and resulting policy. Inspect the effective result rather than assuming a linked policy reached every machine.
- [ ] Understand service identities, managed service accounts, local administrator password management, account lifecycle, and privileged administration as separate design topics. Select implementation details from current Microsoft documentation for the exact lab platform.
- [ ] Only then build a separate isolated domain lab: one owned server, one client, synthetic users, a test OU, and one harmless policy. Keep credentials and domain names distinct from any workplace environment.

## Guided labs with evidence

### Lab A — Local versus shared-folder access

**Setup:** Create two ordinary users and two task groups in a Windows VM. Create a synthetic folder tree and, if available, a second owned client on an isolated virtual network. Record a baseline ACL export and share configuration.

**Actions:** Give one group read access and another modify access. Predict read, create, edit, delete, and permission-change outcomes. Test from actual user sessions and repeat relevant cases through SMB using the intended identities. Change one share restriction and compare local and network results.

**Expected observation:** The same file can have different outcomes through a local path and a share because the network path has additional checks. Existing sessions and token state can affect which identity is actually used.

**Evidence:** Account authority/SID, group membership, ACLs, share permissions, path used, expected/observed outcomes, and exact error messages.

**Repair:** Check active identity, inherited entries, share scope, and existing SMB sessions. Correct the specific entry and repeat both allowed and denied cases. Avoid taking ownership of unrelated system folders.

### Lab B — Service and event correlation

**Setup:** Use a harmless lab service or scheduled status-report task that writes a timestamp to a synthetic file. Record its identity, execution path, working directory, and log channels.

**Actions:** Trigger a successful run, then set an incorrect output path within the synthetic lab tree and trigger a failure. Restore the path and run again. Query events for the bounded period, recording provider, channel, event identifier, and relevant fields.

**Expected observation:** Configuration, launch, and successful work are distinct observations. Some events appear only if their logging or audit policy is enabled.

**Evidence:** A small timeline connecting configuration, process/task execution, file output, failure message, correction, and successful retest.

**Repair:** Compare execution identity and folder permissions before changing the account. If no event appears, verify the provider, channel, time filter, and enabled audit settings rather than asserting that no action occurred.

### Lab C — Recover a usable configuration

**Setup:** Back up the synthetic application's data, configuration, and documented ACL/share requirements. Keep a clean VM checkpoint as a separate convenience, not the sole recovery mechanism.

**Actions:** Restore into a fresh lab directory or clean guest. Recreate groups and task/service definitions, apply intended permissions, and test with both allowed and restricted users. Use the isolated domain lab only for the optional enterprise extension.

**Expected observation:** Restored bytes, service identity, and effective policy must agree for recovery to succeed. Recreated local accounts can have different SIDs even when their names match.

**Evidence:** Restore procedure, identity mapping, configuration comparison, test results, and unresolved dependencies.

**Repair:** Resolve stale SID entries, missing profiles, absent dependencies, and network-profile mismatches explicitly. Repeat the restore after updating the runbook.

## Capstone rubric and retention

Produce a Windows service-and-access runbook: environment inventory, identity diagram, local/share access matrix, bounded event queries, maintenance procedure, backup and recovery, and three repaired failures. Evaluate **identity accuracy**, **effective-access prediction**, **event interpretation**, **network scope**, and **restore repeatability** as missing, guided, or independent. All practical criteria should be independent before internal-assessment work.

The next day, predict a folder-access case from its ACL and token information. Later, repeat it through SMB and explain any difference. The following week, diagnose a changed network profile or scheduled-task path without reopening the solution. Revisit enterprise terms through diagrams until they are needed in [Active Directory and identity testing](15-active-directory-and-enterprise-identity.md), checking that topic's prerequisites before progressing.
