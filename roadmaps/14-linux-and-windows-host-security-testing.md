# 14. Linux and Windows host security testing

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#14-linux-and-windows-host-security-testing)

<!-- TOPIC-TOC:START -->

## Contents

- [Understand the local trust model](#understand-the-local-trust-model)
- [Linux assessment topics](#linux-assessment-topics)
- [Windows assessment topics](#windows-assessment-topics)
- [Credentials and post-access discipline](#credentials-and-post-access-discipline)
- [Lab and completion check](#lab-and-completion-check)
- [Detailed host assessment curriculum](#detailed-host-assessment-curriculum)
  - [Phase 1: establish the host's intended role](#phase-1-establish-the-hosts-intended-role)
  - [Phase 2: Linux permissions and execution](#phase-2-linux-permissions-and-execution)
  - [Phase 3: Windows effective access and privileged components](#phase-3-windows-effective-access-and-privileged-components)
  - [Phase 4: credentials, logging, and recovery](#phase-4-credentials-logging-and-recovery)
- [Scenario labs](#scenario-labs)
  - [Lab A: Linux service configuration boundary](#lab-a-linux-service-configuration-boundary)
  - [Lab B: Windows service directory boundary](#lab-b-windows-service-directory-boundary)
  - [Lab C: remote share and secret exposure](#lab-c-remote-share-and-secret-exposure)
- [Troubleshooting and common assessment errors](#troubleshooting-and-common-assessment-errors)
- [Repeatable capstone and pass rubric](#repeatable-capstone-and-pass-rubric)

<!-- TOPIC-TOC:END -->



**Priority:** Core working knowledge; deeper practice for infrastructure testers. **Prerequisites:** 04–10.

## Understand the local trust model

- [ ] Distinguish remote service access, local interactive access, service identities, administrator/root authority, and kernel authority.
- [ ] Inventory users, groups, privileges, processes, listening sockets, services, installed packages, jobs, mounts, and security policies.
- [ ] Trace which identity reads, writes, or executes a file, and who can change its parent directory, configuration, dependencies, or startup parameters.
- [ ] Understand least privilege, credential storage, secret rotation, patching, logging, host firewalls, application control, and security baselines.
- [ ] Learn privilege escalation as a broken boundary between an ordinary identity and a more privileged action. Identify the misconfiguration and its preconditions before considering validation.
- [ ] Separate intended administrative capability from a vulnerability. An administrator being able to administer is not, by itself, a security finding.

## Linux assessment topics

- [ ] User/group permissions, ACLs, ownership, writable parent directories, symbolic links, and unsafe temporary-file handling.
- [ ] `sudo` policy, SUID/SGID programs, Linux capabilities, privileged helper programs, and the implications of permitted commands.
- [ ] Service accounts, systemd units and timers, cron jobs, startup scripts, environment variables, PATH handling, and trusted executable locations.
- [ ] SSH authentication, host keys, authorized keys, key protection, remote root policy, and forwarding settings.
- [ ] Secrets in configuration, backups, histories, process environments, logs, and deployment artifacts; account for who can actually read them.
- [ ] NFS exports, file shares, local sockets, database accounts, backup agents, web-service identities, and permission boundaries between applications.
- [ ] Mount flags, namespaces, containers, privileged container settings, exposed runtime sockets, and access to host resources.
- [ ] SELinux/AppArmor, seccomp, audit logs, package provenance, patch state, and version backports.
- [ ] Kernel vulnerabilities at a conceptual level: architecture/version requirements, stability risks, patched configurations, and why a configuration fix may be safer to validate first.

## Windows assessment topics

- [ ] Access tokens, SIDs, group membership, integrity levels, privileges, UAC behavior, and the difference between local and domain accounts.
- [ ] NTFS and registry ACLs, inherited permissions, ownership, share permissions, and effective access across both share and filesystem layers.
- [ ] Service executable/configuration permissions, service accounts, scheduled tasks, startup locations, and unsafe executable search paths.
- [ ] Registry and application configuration, installer behavior, DLL search order, signed binaries, and trusted update mechanisms.
- [ ] RDP, WinRM, SMB settings, authentication requirements, firewall scope, remote administration, and administrative share exposure.
- [ ] Password policy, local administrator reuse, Windows LAPS concepts, credential isolation, and managed service-account use.
- [ ] Credential storage architecture and protection boundaries: DPAPI, credential vaults, cached authentication, and why memory containing secrets needs careful handling.
- [ ] Microsoft Defender, attack surface reduction, application control, patch state, event logs, and auditing policy. Evaluate controls using agreed test cases.
- [ ] Backup operators, software deployment identities, service permissions, and management agents as privileged components.

## Credentials and post-access discipline

- [ ] Understand online versus offline password auditing, password hashing versus protocol challenge/response, lockout thresholds, MFA, and rate limiting.
- [ ] Use synthetic credentials and specifically authorized datasets in labs. Measure the effect of password length, common patterns, salts, and work factors without collecting real users' passwords.
- [ ] Learn at a conceptual level how credential reuse, token exposure, and excessive delegation can extend access; pair each with prevention and observable telemetry.
- [ ] After any approved access change, inventory what changed, capture minimal proof, avoid unrelated data, and restore the system.
- [ ] Treat persistence, lateral movement, and data-access simulations as separately scoped activities with clear stop and cleanup requirements.

## Lab and completion check

Build one Linux and one Windows VM with a deliberately misconfigured service or file permission. From an ordinary test account, explain the affected trust boundary, validate the problem with harmless synthetic artifacts, repair the permission or service identity, and repeat the test. Capture both host logs and effective permissions before and after.

**Ready to move on:** You can assess a host without blindly running an escalation script, explain three different privilege-boundary failures, and verify their fixes without breaking legitimate administration.

## Detailed host assessment curriculum

The core goal is to reason about identities, effective permissions, privileged execution, remote exposure, and repair. Kernel exploitation, credential extraction techniques, and complex post-access operations are later specialist subjects with separate lab requirements. You can demonstrate strong host-assessment ability by finding and repairing configuration failures without attempting those advanced activities.

### Phase 1: establish the host's intended role

- [ ] Record operating system edition/build, package source, installed roles, owner, workload, sensitivity, patch policy, and management method. Identify whether it is a workstation, application server, domain member, jump host, or container node.
- [ ] Inventory local identities, group membership, interactive logon rights, service identities, scheduled execution, listeners, installed software, storage, and remote management paths.
- [ ] Distinguish the permissions of your test account from those of the assessment tools. An administrative inventory can reveal configuration but does not prove an ordinary user can reach a risky operation.
- [ ] Record normal application behavior and a safe recovery method. Snapshot a disposable lab and confirm you can restore it before changing services or ACLs.
- [ ] Build a privileged-execution table: component, execution identity, executable, configuration, parent directories, dependencies, startup trigger, and users who can modify each input.
- [ ] Check collection completeness. Missing privilege, disabled auditing, inaccessible mounts, or unavailable logs should become limitations rather than assumed secure results.

**Deliverable:** a host diagram and a table of five trust boundaries, including at least one file boundary, one service boundary, one remote-management boundary, and one secret-storage boundary.

### Phase 2: Linux permissions and execution

- [ ] Resolve effective access across user/group IDs, supplementary groups, mode bits, POSIX ACLs, directory traversal rights, ownership, and mount behavior. Practice explaining why file permissions alone are insufficient when a parent directory is writable.
- [ ] Inspect service units, timers, cron definitions, executable paths, environment files, working directories, and configuration ownership. Include scripts and libraries loaded by privileged processes.
- [ ] Read permitted administrative operations as capabilities: which executable runs, as which identity, with which arguments/environment, and which user-controlled files it consumes.
- [ ] Study SUID/SGID and capabilities through documented benign examples. Explain the specific privileged action granted rather than assuming every special permission is automatically exploitable.
- [ ] Inspect temporary files, symbolic links, predictable names, and atomic file creation in a local training program. Use harmless sentinel files to understand filesystem races conceptually before any advanced experimentation.
- [ ] Review SSH keys and configuration, service-account login permissions, agent/port forwarding policy, credential file ownership, and access from permitted management networks.
- [ ] Compare discretionary permissions with SELinux/AppArmor policy and service sandboxing. A denial may originate in a mandatory control even when ordinary permissions allow access.
- [ ] Examine package provenance, running process versions, distribution security fixes, audit configuration, and log protection. Separate an installed update from the binary actually running.

**Phase gate:** explain a denied and an allowed file operation from the complete permission path, and show a service running with only the rights required by its task.

### Phase 3: Windows effective access and privileged components

- [ ] Learn how SIDs, local/domain groups, access tokens, integrity levels, user rights, and inherited ACLs influence effective access. Refresh sessions when testing membership changes that affect tokens.
- [ ] Compare share permissions with NTFS permissions. Test from the intended remote perspective and inspect the resulting effective access rather than reviewing one ACL in isolation.
- [ ] Review a service's execution identity, executable path, directory ACLs, service-control permissions, configuration, and dependency locations. Distinguish the ability to start a service from the ability to change what it executes.
- [ ] Inspect scheduled tasks, startup entries, update services, management agents, and software deployment mechanisms. Identify which ordinary identities can influence their privileged inputs.
- [ ] Study executable and DLL search behavior in a purpose-built local program. Use benign logging markers, and verify the relevant search and loading rules for the exact application/runtime.
- [ ] Review registry ACLs and application configuration alongside filesystem permissions. An immutable executable can still consume a writable privileged configuration.
- [ ] Examine remote access policy for RDP, WinRM, and SMB, including authentication, allowed groups, host firewall scope, and network placement.
- [ ] Review local administrator management, service-account use, credential isolation, application control, and audit policy. Assess their configuration and observable behavior through agreed benign checks.

**Phase gate:** demonstrate that an ordinary account cannot alter a privileged service's inputs, while the designated administrator can maintain it through the intended path.

### Phase 4: credentials, logging, and recovery

- [ ] Use fictional credentials to understand password hashing, salts, work factors, online throttling, and lockout behavior. Keep online and offline assessment permissions distinct.
- [ ] Identify where applications store secrets and who can read them: files, registry, environment, process metadata, logs, backups, and deployment artifacts. Record exposure without retaining the secret value.
- [ ] Learn platform secret-protection concepts and their trust boundaries. Encryption at rest does not remove the need to protect the identity or process authorized to decrypt.
- [ ] Define expected telemetry for logon, failed authentication, group changes, service changes, task changes, file access, and policy changes. Verify the selected auditing configuration actually emits the events you need.
- [ ] Consider recovery authority: backup access, restore operations, emergency administration, and recovery keys can cross important boundaries. Review their protection and documented use.
- [ ] Keep a change ledger for every lab mutation and verify service state, permissions, test accounts, temporary files, and logs after cleanup.

## Scenario labs

### Lab A: Linux service configuration boundary

**Setup:** a disposable Linux VM with a benign service that reads a configuration file and writes a synthetic status report. Deliberately give an ordinary lab group unnecessary write access to that configuration.

**Action:** inspect effective permissions and modify only a harmless report label to prove the influence path. **Expected result:** demonstrate ordinary-user influence over privileged configuration without executing a privileged payload. **Evidence:** identity, ACL/mode, service configuration, benign output, and logs. **Control:** authorized maintenance remains possible. **Fix:** correct ownership and parent-directory permissions, reduce service privileges where feasible, and verify the ordinary user can no longer modify the input.

### Lab B: Windows service directory boundary

**Setup:** a Windows VM with a benign training service and a writable configuration or dependency directory. **Action:** inspect service and directory permissions, then use a harmless configuration marker to establish which identity controls the service's input. **Expected result:** accurately describe the boundary and prerequisite rights. **Evidence:** service identity, effective ACLs, changed marker, and service events. **Control:** normal startup and administrator maintenance still work. **Fix:** narrow ACLs, use appropriate service identity, and retest from a fresh ordinary-user session.

### Lab C: remote share and secret exposure

**Setup:** synthetic team data, a fake credential file, separate team/administrator identities, and a local file share. **Action:** compare remote and local access, including inherited permissions and group membership. **Expected result:** only authorized identities reach each class of data. **Evidence:** share and filesystem settings, access outcomes, and audit records. **Control:** permitted team collaboration remains functional. **Fix:** remove the excessive grant, move secrets to an appropriate protected facility, and document rotation using a disposable credential.

## Troubleshooting and common assessment errors

A denied operation may be caused by permissions, mandatory policy, integrity level, share restrictions, authentication context, or a read-only mount. Identify the actual enforcement point. A newly changed group membership may not affect an existing session immediately. A patched package may coexist with an old running process. A command executed with administrative assessment privileges does not demonstrate an ordinary-user escalation. A powerful administrative feature becomes a finding only when unintended identities can use or influence it.

Avoid blanket hardening changes without application tests. Removing a service right can break backups or scheduled jobs; broadening it again can restore the original weakness. Identify the smallest legitimate permission set and test the workload explicitly.

## Repeatable capstone and pass rubric

Prepare one Linux and one Windows host with three seeded issues across permissions, remote exposure, and credential storage. Starting from ordinary accounts, write hypotheses, collect read-only configuration evidence, and perform only harmless agreed validation. Repair each root cause, repeat the ordinary-user check, and verify the intended service function.

Pass when each conclusion names the controlling identity, affected object, exact permission or configuration error, preconditions, observed effect, repair, and residual limitation. Include one dismissed observation, one logging gap, and a complete cleanup ledger. A second learner should be able to restore the snapshots and reproduce your conclusions using the described evidence rather than an unexplained automated escalation report.