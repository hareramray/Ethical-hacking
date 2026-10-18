# 14. Tutorial: Linux and Windows host security testing

[Index](README.md) · [Complete source curriculum](curriculum/14-linux-and-windows-host-security-testing.md) · [Original roadmap](../roadmaps/14-linux-and-windows-host-security-testing.md)

## Assess who controls each privileged input

A host boundary fails when an unintended identity can influence an action reserved for a more trusted identity. A writable service configuration may matter even when its executable is protected. Conversely, a documented administrator's ability to administer is expected. This chapter teaches effective access, service boundaries, remote exposure, credential protection, logging, repair, and recovery through harmless artifacts.

Prerequisites are tutorials 04–10 and basic administration. Prepare disposable Linux and Windows VMs, an ordinary test account, an administrator account, synthetic files, and a tested restore point. Use the guest OS specified beside each command. Do not apply deliberately weak permissions to your daily computer. No credential extraction, kernel exploitation, persistence, or lateral-movement exercise is needed to complete this tutorial.

## Lesson 1: establish the host's intended role

Record OS edition/build, package source, owner, workload, sensitivity, installed roles, patch policy, and management method. A workstation, application server, jump host, domain member, and container node have different intended access. Distinguish remote service access, local interactive access, service identity, administrator/root, and kernel authority.

Inventory users/groups, logon rights, processes, listeners, services, packages, tasks/jobs, mounts, and security policies. Record the collection identity: privileged inventory can reveal a weak ACL but does not prove an ordinary user can use it. Missing rights or auditing become limitations.

Create a privileged-execution table with component, execution identity, executable, configuration, dependencies, parent directories, environment, startup trigger, and identities able to modify each. Include backups, deployment agents, scheduled work, and update services. Establish normal application behavior and restoration steps before changes.

Read-only examples on a Linux VM:

```bash
id
uname -a
ss -lnt
systemctl list-units --type=service --state=running
findmnt
```

Read-only examples in Windows PowerShell:

```powershell
whoami /all
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber
Get-CimInstance Win32_Service | Select-Object Name, StartName, State, PathName
Get-NetTCPConnection -State Listen | Select-Object LocalAddress, LocalPort, OwningProcess
Get-ScheduledTask | Select-Object TaskName, TaskPath, State
```

Availability and visibility vary with privileges and OS edition. Save only fields relevant to the lab. A listening port establishes exposure on that interface, not remote reachability or administrative authorization. Compare host firewall, network placement, authentication, and intended groups separately.

## Lesson 2: reason through Linux effective access

Linux decisions combine user/group IDs, supplementary groups, mode bits, POSIX ACLs, directory traversal, ownership, mount behavior, and mandatory policies. A readable file behind a non-traversable directory can be inaccessible. A protected file inside a writable parent can have its directory entry influenced even when its content mode looks restrictive. Symbolic links can redirect resolution. [Linux pathname resolution](https://man7.org/linux/man-pages/man7/path_resolution.7.html).

On a selected lab path, use `ls -ld` for the file and every parent; `namei -l` when available to show the path; and `getfacl` when the ACL utility is installed. ACL masks can limit named-entry rights, so reading one ACL line alone is insufficient. A read-only mount or SELinux/AppArmor denial may reject an operation even when discretionary permissions allow it.

| Topic | What the boundary means | Review and safe verification |
| --- | --- | --- |
| `sudo` | A policy grants particular commands/identities, sometimes with argument/environment effects | Read permitted operation, inputs, and restrictions; do not equate every entry with a flaw |
| SUID/SGID, capabilities, privileged helpers | Specific executable privileges can exceed ordinary process rights | Identify the intended privileged action and who controls its inputs/dependencies |
| systemd, timers, cron, startup scripts | Scheduled or service execution trusts unit/job definitions and referenced files | Read identity, executable, environment files, working directory, PATH, and parent ownership |
| SSH | Host identity, user authentication, key files, login policy, and forwarding are separate controls | Review host/authorized keys, private-key access, remote root policy, service-account logon, agent/port forwarding |
| NFS, shares, sockets, databases | Export/share/socket access combines with application and filesystem authorization | Compare intended identities using one synthetic object or harmless request |
| Mounts, namespaces, containers | Isolation and mount options shape host-resource access | Inspect privileged settings, host mounts, devices, runtime sockets and user mappings |
| SELinux/AppArmor, seccomp | Mandatory policies and syscall restrictions add enforcement beyond mode bits | Match denied operations to policy/log evidence instead of broadly disabling controls |
| Packages and kernel | Provenance, distribution backports, architecture, running versions, and patch state affect applicability | Compare trusted package status and running process/kernel; record stability-sensitive work as a separate specialization |

Environment variables, PATH, scripts, libraries, and working directories can influence a privileged program without changing its main binary. Temporary-file safety requires appropriate unique creation and atomic operations; predictable names and link races violate assumptions. Study these with harmless sentinels and bounded local code, not an escalation script.

## Lesson 3: a reproducible Linux permission fixture

This exercise uses two **pre-created dedicated lab accounts**, `labreader` and `labservice`, and a pre-created group `lab14readers` containing both. Confirm them with `id labreader` and `id labservice`; refresh sessions after membership changes. The administrator creates a new fixture directory in the disposable VM only:

```bash
sudo install -d -o root -g lab14readers -m 0750 /srv/host14-lab
printf 'TRAINING_ORIGINAL\n' | sudo tee /srv/host14-lab/label.txt >/dev/null
sudo chown root:lab14readers /srv/host14-lab/label.txt
sudo chmod 0660 /srv/host14-lab/label.txt
sudo -u labreader sh -c 'printf "TRAINING_CHANGED\n" > /srv/host14-lab/label.txt'
sudo -u labservice cat /srv/host14-lab/label.txt
```

Expected output is `TRAINING_CHANGED`. The ordinary reader can modify a service-consumed label because the file grants group write. The parent is deliberately not group-writable, allowing the lesson to isolate one permission. This demonstrates influence over an input, not arbitrary privileged execution.

Repair the file and repeat the identical write as the same ordinary identity:

```bash
sudo chmod 0640 /srv/host14-lab/label.txt
sudo -u labreader sh -c 'printf "TRAINING_AFTER\n" > /srv/host14-lab/label.txt'
sudo -u labservice cat /srv/host14-lab/label.txt
```

Expect the write to fail with permission denied while the service identity still reads `TRAINING_CHANGED`. Capture identities, before/after mode/ACL, attempted operation, and observed output. Administrator maintenance remains possible through the documented privileged path. Restore the VM snapshot after collecting evidence; do not introduce these accounts or fixtures on unrelated machines.

For the service extension, configure an owned benign training service to read this label as data and write a synthetic status report. Inspect its unit with `systemctl cat <training-unit>` and its selected logs with `journalctl -u <training-unit>`. Review every dependency and parent directory, reduce runtime identity rights where practical, and prove both protected configuration and successful reporting. Never interpret configuration text as executable commands just to demonstrate influence.

## Lesson 4: understand Windows tokens and effective access

Windows access checks use identities represented by SIDs, group membership, token privileges, integrity information, and object security descriptors. Local and domain accounts with similar names are different identities. UAC and elevated versus ordinary tokens affect the actual operation. Inspect the token used by the test rather than assuming a saved username describes it. [Microsoft access-token documentation](https://learn.microsoft.com/en-us/windows/win32/secauthz/access-tokens).

NTFS and registry ACLs include inheritance and ownership. Share permissions apply alongside filesystem permissions for network access. Do not reduce a complex effective-access check to one visible allow entry: account for group membership, denied rights, inheritance, token state, and the requested operation. Group changes may require a new logon/session before the resource sees the intended token.

| Windows area | Review focus |
| --- | --- |
| Services | Execution identity, executable/path quoting, file and directory ACLs, configuration/dependencies, service-control permissions |
| Scheduled tasks and startup | Who edits definitions, arguments, directories, scripts, registry values, or consumed configuration |
| Installers, DLL search, signed binaries, updates | Actual loader/search behavior and writable inputs; a valid signature does not secure every dependency |
| RDP, WinRM, SMB, administrative shares | Authentication, allowed users/groups, firewall source scope, network placement, and intended remote administration |
| Passwords and service identities | Policy, shared local-admin reuse, Windows LAPS concepts, managed service accounts, lifecycle and least privilege |
| Credential protection | DPAPI, vaults, cached authentication, credential isolation, and authorized decrypting identities/processes |
| Defender, ASR, application control | Applied configuration and benign agreed behavior tests, supported by logs |
| Patches and audits | Running build/update state, event/audit policy, event retention and access |
| Privileged support systems | Backup operators, recovery, deployment identities, management agents, and emergency administration |

Being able to start a service is different from being able to change its executable or configuration. An immutable binary can still read a writable registry value. An allowed administrator action becomes a finding only when unintended identities can use or influence it. Study search paths using a purpose-built benign logging program and the exact application's loader documentation; do not assume every unquoted-looking string proves a reachable execution path.

## Lesson 5: Windows service-directory and share labs

In a disposable Windows VM, use an existing benign training service whose configuration contains only a report label. The administrator records the service account, binary, configuration path, dependencies, and directory ACL. Substitute the actual fixture path below; these commands are read-only:

```powershell
Get-CimInstance Win32_Service -Filter "Name='TrainingReport'" |
    Select-Object Name, StartName, State, PathName
Get-Acl -LiteralPath 'C:\Host14Lab' | Format-List
Get-Acl -LiteralPath 'C:\Host14Lab\label.txt' | Format-List
```

The administrator deliberately grants the dedicated ordinary lab account Modify on the **training label only**, using the Security settings dialog, and records inherited versus explicit entries. In a fresh ordinary-user session, change `TRAINING_ORIGINAL` to `TRAINING_CHANGED`. Have the authorized operator run the benign report and observe the marker. This establishes who influences the service input without replacing a binary or injecting executable content.

Remove that unnecessary write grant at its source; do not add a broad deny that breaks intended maintenance. Reopen the ordinary session and repeat the write. It should fail, while the service retains required read access and the designated administrator can maintain the label. Record service events and the effective ACL, and verify parent/dependency directories too. If the service does not exist, report this as a fixture prerequisite rather than treating an empty query as a passed assessment.

For the share extension, create a synthetic team folder and a fake credential marker `TRAINING_NOT_A_PASSWORD` in a separate administrative folder. Compare local and network access as team and administrator identities. Inspect both share settings and NTFS inheritance. Repair the excessive grant, retain team collaboration, move credential storage to an appropriate protected facility, and document rotation using a disposable test credential. Never collect a real secret value for the report.

## Lesson 6: credentials, telemetry, and recovery

Online password auditing interacts with authentication rate limits, MFA, and lockout; offline auditing studies an authorized dataset without live logons. Password hashing differs from protocol challenge/response. Use fictional values to compare length, common patterns, salts, and work factors, and keep permissions for these activities distinct. Credential reuse, exposed tokens, and excessive delegation can extend access; study prevention and telemetry without extracting credential material.

Inventory potential secret locations: configuration, registry, backups, shell histories, environments, process metadata, logs, deployment archives, and recovery records. Determine who can actually read them. Encryption at rest does not protect against an unintended identity already authorized to decrypt. Record path, class of secret, access conditions, and remediation without retaining the value.

Define expected events for logon/failure, group changes, service/task changes, file access, and policy changes. Perform one benign action and verify that the configured audit policy emits usable telemetry. Missing events can reflect disabled auditing, collection filters, privilege gaps, or retention rather than absence of activity. Protect the logs themselves from unauthorized change.

Recovery authority can cross the same boundaries as normal administration: backups, restore operators, emergency accounts, and recovery keys need protection and a tested runbook. Keep a change ledger with original setting, mutation, responsible identity, evidence, restoration, and verification. Persistence, lateral movement, or wider data-access simulations require separate explicit exercise scope; they are not implied by finding a weak permission.

## Troubleshooting and completion

A denial may originate from mode/ACL, mandatory policy, integrity level, share policy, read-only mount, or authentication context. Identify the decision point before changing settings. A patched package can coexist with an old running process. An administrator-run command does not demonstrate ordinary-user capability. Broad hardening that breaks backups or scheduled jobs is not a complete repair; identify the minimum legitimate rights and test the workload.

Finish with Linux and Windows hosts containing three seeded issues across permission, remote exposure, and secret storage. Begin as ordinary identities, collect configuration evidence, use harmless markers, repair each root cause, and repeat the intended operation. Submit five trust boundaries, three explained failure types, a dismissed observation, a logging gap, before/after service behavior, and cleanup confirmation.

**Answer-guided checks:** Why inspect parents? Directory control can undermine file assumptions. Why refresh the Windows session? Its existing token may retain old membership. Why is an unreadable secret file not automatically exposed? Reachable path and effective identity rights must be established. Why does a writable service label prove less than arbitrary execution? It demonstrates influence over that data field; further capability is unproven. Why test maintenance after repair? Least privilege must preserve authorized operation.
