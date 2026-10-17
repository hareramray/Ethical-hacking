# 05. Linux administration

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#05-linux-administration)

<!-- TOPIC-TOC:START -->

## Contents

- [Shell, files, and permissions](#shell-files-and-permissions)
- [Services, networking, and maintenance](#services-networking-and-maintenance)
- [Internals and hardening](#internals-and-hardening)
- [Safe practice and exit criteria](#safe-practice-and-exit-criteria)
- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1 — Become precise at the shell](#stage-1--become-precise-at-the-shell)
  - [Stage 2 — Predict effective filesystem access](#stage-2--predict-effective-filesystem-access)
  - [Stage 3 — Run an understandable service](#stage-3--run-an-understandable-service)
  - [Stage 4 — Maintain storage, packages, and network state](#stage-4--maintain-storage-packages-and-network-state)
  - [Stage 5 — Add hardening with measurable effects](#stage-5--add-hardening-with-measurable-effects)
- [Guided labs with evidence](#guided-labs-with-evidence)
  - [Lab A — A permission prediction table](#lab-a--a-permission-prediction-table)
  - [Lab B — Service diagnosis without broad privilege](#lab-b--service-diagnosis-without-broad-privilege)
  - [Lab C — Rebuild from backup](#lab-c--rebuild-from-backup)
- [Capstone rubric and spaced practice](#capstone-rubric-and-spaced-practice)

<!-- TOPIC-TOC:END -->



**Prerequisites:** Sections 03–04. **Priority:** Core. Start with one general-purpose distribution and learn its normal administration before relying on a security distribution.

## Shell, files, and permissions

- [ ] Navigate absolute/relative paths; inspect, copy, move, compare, archive, search, and edit files. Understand hidden files, links, mount points, case sensitivity, and the filesystem hierarchy.
- [ ] Use command help, manual pages, tab completion, history, environment variables, exit codes, standard input/output/error, pipes, and redirection.
- [ ] Learn quoting, escaping, globbing, command substitution, and argument boundaries. Understand why untrusted text must not become shell syntax.
- [ ] Read file ownership, user/group/other permission bits, directory permissions, umask, ACLs, special permission bits, and effective permissions.
- [ ] Manage users, groups, sudo policy, account lifecycle, SSH keys, and service accounts using least privilege.
- [ ] Understand hard versus symbolic links, inode metadata, file timestamps, open-but-deleted files, and the difference between filename permissions and file-content permissions.

## Services, networking, and maintenance

- [ ] Inspect processes, parent/child relationships, signals, background jobs, resource use, and which process owns a listening socket.
- [ ] Manage services and scheduled jobs; understand startup configuration and the service manager used by your distribution.
- [ ] Read system/application/authentication logs; learn journal queries, log rotation, time zones, retention, and the need to preserve original evidence.
- [ ] Configure interfaces, routes, DNS, hostnames, local firewalls, and secure remote administration. Verify effective configuration rather than merely editing a file.
- [ ] Install, update, and remove packages; understand repositories, package signatures, dependency resolution, configuration changes, and trusted software sources.
- [ ] Manage disks, partitions, mounts, swap, quotas, backups, restoration, patching, and disk-space failures.
- [ ] Configure an ordinary web service with a dedicated account, limited file access, intentional network exposure, and useful logs.

## Internals and hardening

- [ ] Understand process credentials, environment inheritance, shared libraries, search paths, dynamic loading, and how configuration ownership affects trust.
- [ ] Learn `/proc` and `/sys` as interfaces to system information; distinguish reported configuration from observed runtime behavior.
- [ ] Recognize Linux capabilities, PAM, SSH configuration, SELinux/AppArmor policies, kernel parameters, and audit facilities.
- [ ] **Advanced:** Study namespaces, cgroups, seccomp, container isolation, kernel modules, boot integrity, filesystem capabilities, and service sandboxing.
- [ ] Compare a secure baseline with a running system; document exceptions, operational impact, rollback steps, and verification.

The [Linux kernel administrator's guide](https://docs.kernel.org/admin-guide/) is a deeper reference for kernel-facing behavior; use your distribution's documentation for its package and service-management conventions.

## Safe practice and exit criteria

**Labs:** Build a Linux VM from scratch; create a normal user and a restricted service account; configure a local web service; collect its logs; back up its configuration and data; restore to a fresh VM. Deliberately misconfigure a lab file permission, service path, and DNS setting, then repair each with evidence.

**Exit gate:** Administer the VM without a desktop interface, explain why an access attempt succeeds or fails, identify the account behind a service, and restore that service from your documented backup.

**Common gaps:** Using root for every task; treating containers as equivalent to VMs; changing permissions broadly to silence errors; deleting logs during troubleshooting; confusing package signatures with proof that software has no vulnerabilities.

## Detailed learning sequence

The **practical track** is ordinary administration of one disposable Linux VM: shell use, identities, permissions, packages, services, logs, networking, and recovery. The **awareness track** introduces kernel interfaces and confinement mechanisms; configure these only after you can explain the unconfined service's normal behavior. Record the distribution and release because package names, network managers, and service managers vary.

### Stage 1 — Become precise at the shell

- [ ] Orient yourself using `pwd`, `id`, `uname`, and your distribution's release information. Know whether the terminal is on the host, guest, remote system, or inside a container before making changes.
- [ ] Navigate and inspect using `cd`, `ls`, `stat`, `file`, and a pager. Learn the roles of `/etc`, `/var`, `/home`, `/usr`, `/tmp`, `/run`, `/proc`, and `/sys` without assuming every distribution puts every component in exactly the same place.
- [ ] Practice copying and comparing synthetic files with spaces, leading dashes, and Unicode in their names. Learn `--` where a command supports it, quote paths, and distinguish a glob pattern from a literal filename.
- [ ] Use `man`, command `--help`, and shell `help` for builtins. Read the exit-status and warning sections, not just the first example. Distinguish shell aliases, functions, builtins, and executable programs with command-discovery tools.
- [ ] Predict what single quotes, double quotes, backslashes, variable expansion, command substitution, and globbing do to an argument list. Use a harmless argument-printing exercise rather than experimenting with destructive commands.
- [ ] Separate standard output, standard error, and exit status. Redirect them into separate lab files and observe that a command can print an error while a later pipeline component succeeds.
- [ ] Practice `rg` or `grep`, `find`, sorting, counting, and structured parsers. Do not parse human-oriented `ls` output when an API or filename-safe traversal is available.
- [ ] Learn terminal jobs, foreground/background execution, and orderly cancellation. Prefer a graceful application stop or termination signal before considering forced termination.

**Checkpoint:** Explain the exact arguments received by a command containing a path with spaces. Reproduce a failed file read while preserving both its error message and status.

### Stage 2 — Predict effective filesystem access

- [ ] Learn user IDs, primary and supplementary groups, account records, and the difference between an account name and its numeric identity. Understand that new group membership may require a new login session before it appears in a process.
- [ ] Read owner/group/other mode bits and apply them to a particular identity. For directories, distinguish listing names, traversing known names, and creating/removing entries; directory permissions govern operations on names.
- [ ] Explain why deleting a file generally depends on permissions on its containing directory, with additional rules such as the sticky bit, rather than merely whether the file's contents are writable.
- [ ] Calculate an intended initial mode using `umask`, remembering that applications request a creation mode and the mask removes permissions rather than adding executable bits.
- [ ] Compare a hard link with a symbolic link using inode information. Move a target, follow the resulting behavior, and explain why a symlink has its own pathname while a hard link refers to the same underlying file object.
- [ ] Introduce ACLs after mode bits. Inspect named entries and the ACL mask; predict effective access rather than reading one entry in isolation.
- [ ] Recognize setuid, setgid, and sticky bits. Study their legitimate administrative purposes and audit them conceptually; do not create privileged executables as a beginner permissions exercise.
- [ ] Create separate interactive and service identities. Give the service only the directories and operations it requires. Review `sudo` policy with its validation tool and keep recovery console access before changing administrative access.

### Stage 3 — Run an understandable service

- [ ] Install one ordinary service from the distribution's configured trusted repositories. Record package origin, version, configuration locations, data directories, and how to remove or restore it.
- [ ] For systemd-based systems, distinguish service enablement from running state. Inspect the unit, drop-ins, execution user, working directory, environment, restart policy, dependencies, and standard-output destination. On another service manager, identify the equivalent controls.
- [ ] Identify the process ID, parent, user, executable path, open sockets, and command line. Compare the service manager's intended configuration with the actual process and listener.
- [ ] Learn reload versus restart, configuration validation, and dependency ordering. Validate a new configuration before applying it, then verify runtime behavior rather than treating a successful edit as completion.
- [ ] Query a bounded time range of service and authentication logs. Learn boot identifiers, time zones, journal persistence, rotation, and application log destinations. Absence of an event is inconclusive if the relevant logging was never enabled.
- [ ] Learn cron, timers, and other scheduled mechanisms at awareness depth, then create a harmless scheduled status report under a limited account. Record environment differences from your interactive shell.
- [ ] Explain SSH server versus client configuration, host keys versus user keys, and server identity verification. Keep a working console while testing restricted remote administration and validate a fresh login before closing the old session.

### Stage 4 — Maintain storage, packages, and network state

- [ ] Inspect filesystems, mount options, block devices, free blocks, and inode use. Learn why a filesystem can refuse new files when byte capacity still appears available.
- [ ] Compare apparent file size with allocated storage, and understand open-but-deleted files at awareness depth. Diagnose disk use with bounded inspection rather than recursively deleting directories whose purpose you do not know.
- [ ] Practice mounting a small disposable virtual disk by a stable identifier; test its configuration before relying on it at boot. Keep the original guest disk and host drives outside this exercise.
- [ ] Separate application data, configuration, secrets, and generated cache. Choose a backup method that preserves required ownership and permissions and produces an application-consistent copy.
- [ ] Learn repository metadata, signed package trust, dependencies, and upgrade configuration prompts. Read proposed changes before accepting them and verify service health after updates.
- [ ] Inspect interface addresses, routes, resolver state, and sockets using the tools supplied by the distribution. Learn which manager owns persistent configuration so that a manual change is not silently overwritten later.
- [ ] Configure a narrow firewall rule for the lab service and test both allowed and denied access from another owned VM. Confirm IPv4 and IPv6 separately when both are enabled.

### Stage 5 — Add hardening with measurable effects

- [ ] Map trust in executable search paths, writable configuration, environment variables, shared libraries, and service working directories. Ask which account can modify each input a more privileged process consumes.
- [ ] Inspect selected `/proc` information for your own process and distinguish live interfaces from ordinary stored files. At awareness depth, use `/sys` to understand device and kernel settings without changing unfamiliar values.
- [ ] Learn capabilities as individually named privileges, PAM as a framework for authentication-related policy, and SELinux/AppArmor as additional access-control layers. A mode-bit allow does not prove every other control allows the action.
- [ ] When a confined service fails, inspect the denial evidence and intended policy. Fix the minimum required rule or application path; disabling confinement is not a diagnosis.
- [ ] For specialization, map namespaces, cgroups, seccomp, container mounts, and service sandboxing to the resources they restrict. Explain what each fails to isolate before stacking controls.
- [ ] Write a baseline with an operational reason, verification command, exception owner, and rollback for each setting. A copied hardening checklist can break legitimate workloads when its assumptions differ from yours.

## Guided labs with evidence

### Lab A — A permission prediction table

**Setup:** Create two unprivileged test users and one project group in a disposable guest. Use only a new synthetic project directory. Keep an independent administrative session available.

**Actions:** Create a group-readable file and a group-writable directory. Predict each account's ability to list, traverse, read, modify, and remove entries. Verify from separate sessions as the actual users. Change one mode or ACL entry, repeat predictions, and observe a newly created file under a chosen `umask`.

**Expected observation:** File access and directory-entry operations differ; group membership and ACL masks affect the result. Tests made as root do not represent an ordinary user's access.

**Evidence:** Identity output, directory/file metadata, ACL output when used, predicted/observed matrix, and the final intended permissions.

**Repair:** If access differs from prediction, walk every parent directory, inspect current process groups, and read ACLs or confinement denials. Correct one cause and retest the denied case as well as the permitted case.

### Lab B — Service diagnosis without broad privilege

**Setup:** Run a static synthetic web service under a dedicated account on the isolated lab network. Record its working configuration, service definition, ports, log locations, and test request.

**Actions:** Introduce an incorrect content path, then an unreadable synthetic content file, then a narrowly scoped firewall denial, restoring baseline between cases. Use service status, journal/application logs, process identity, socket inspection, local request, and remote request to locate the failing layer.

**Expected observation:** A running process does not guarantee healthy content delivery. Local success with remote failure suggests a different investigation from a process that exits during startup.

**Evidence:** Three short incident records with exact symptom, diagnostic steps, corrected setting, and positive/negative retest. Keep original logs and append interpretations separately.

**Repair:** Correct the path, targeted permission, or rule. Avoid making the service run as root or granting world write merely to eliminate an error.

### Lab C — Rebuild from backup

**Setup:** Back up the service's data, configuration, required secret references, and account/permission requirements. Document dependencies and service startup instructions.

**Actions:** Create a fresh guest or a clean clone, install dependencies, recreate the service identity, restore files, and validate behavior. Compare hashes of static synthetic content and verify that access restrictions survived restoration.

**Expected observation:** A usable backup requires both recoverable data and enough system knowledge to run it. Matching file bytes alone does not prove correct ownership, policy, or application behavior.

**Evidence:** Restore log, missing dependency list, request results, permission checks, and a documented rollback. Preserve the original VM until the restored instance passes.

**Repair:** Resolve numeric ownership mismatches, missing packages, absent certificates, and changed paths explicitly. Repeat the restore from amended notes so the improvement is demonstrated.

## Capstone rubric and spaced practice

Deliver a minimal service runbook containing installation, user/group model, directory permissions, network exposure, log queries, updates, backups, and recovery. Include three fault reports and an ordinary maintenance change with rollback. Score each area **unexplained**, **works with notes**, or **independently reproducible**; core identity, access, logging, and restore tasks must reach the final level.

After a day, reproduce one permission prediction without notes. After several days, diagnose a different service failure. Later, restore into a clean guest and explain every privileged action used. Review one manual page whenever a command's behavior surprises you. Continue to [automation](07-programming-and-automation.md) only when you can perform the administrative operation manually and explain its side effects.
