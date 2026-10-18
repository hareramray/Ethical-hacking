# 05. Administer and repair an understandable Linux service

[Index](README.md) | [Complete source curriculum](curriculum/05-linux-administration.md) | [Original roadmap](../roadmaps/05-linux-administration.md)

## Prerequisites and working boundary

Complete networking and lab setup. Use one disposable general-purpose Linux VM, a normal account, console recovery, Bash, Python 3, and its installed documentation. Commands involving system accounts or services require a separate privileged administration step inside that guest. Do not apply them to a personal or organizational server. Distribution package, network, and service managers differ; record yours instead of assuming every example fits.

## 1. Become exact about shell arguments

First identify where you are:

```bash
pwd
id
uname -a
cat /etc/os-release
type printf
```

`pwd` identifies the working directory, `id` the process identity/groups, and release information the platform. A terminal is an interface to a shell; the shell interprets commands and launches programs. Aliases, functions, builtins, and executable files can share names; `type` helps distinguish them. Use `help` for Bash builtins, `man` for manual pages, and supported `--help` options. Read exit-status and side-effect descriptions.

An absolute path starts at `/`; a relative path starts from the working directory. `/etc` normally holds configuration, `/var` variable data/logs, `/home` user data, `/usr` installed user-space software, `/tmp` temporary files, `/run` runtime state, and `/proc`/`/sys` live kernel interfaces. Dot-prefixed names are conventionally hidden from default listings. Case sensitivity, mounts, and links affect path resolution.

Practice harmless argument printing:

```bash
item='two words'
printf '<%s>\n' "$item"     # one argument
printf '<%s>\n' $item       # normally two after splitting
printf '<%s>\n' '$item'     # literal dollar sign and name
printf '<%s>\n' "$(printf '%s' demo)"
```

Double quotes preserve argument boundaries while permitting expansions; single quotes preserve literal content. Globs expand matching filenames, and command substitution inserts command output. Untrusted text must remain data rather than becoming `eval` or shell syntax. For arrays use `"${array[@]}"` to preserve each element. Filenames with spaces, Unicode, glob characters, or a leading dash reveal weak quoting; supported `--` marks the end of options.

Create a practice tree, then inspect/copy/compare it with `ls`, `stat`, `file`, `cp`, `cmp`, `diff`, and a pager. Search content with `rg` or `grep`, locate names with `find`, and use structured parsers for JSON/CSV. Do not parse human-formatted `ls` output as a reliable filename list.

```bash
mkdir -p "$HOME/linux-lab/files"
printf '%s\n' 'synthetic' > "$HOME/linux-lab/files/two words.txt"
cat -- "$HOME/linux-lab/files/missing.txt" > "$HOME/linux-lab/stdout.txt" 2> "$HOME/linux-lab/stderr.txt"
status=$?
printf 'exit=%s\n' "$status"
```

Expect nonzero status and a saved error. Standard input, output, and error are separate streams. A pipeline's default status reflects its last command; `pipefail` changes that in Bash, and `set -e` has contextual exceptions. Check important failures explicitly. Background jobs, `jobs`, `fg`, and `wait` concern shell jobs; prefer Ctrl+C or graceful application shutdown before forced termination.

## 2. Predict filesystem access

An account has a numeric UID, primary GID, and supplementary groups. A process carries credentials from its session; group changes may require a fresh login. Names are labels for numeric identities, important when restoring to another guest.

Mode bits select owner, group, or other access. For ordinary files, read reads content, write changes content, and execute allows execution subject to other controls. For directories, read lists names, execute traverses known entries, and write permits entry changes when combined with required traversal. Deleting a file generally depends on its containing directory, not whether the file's content is writable; sticky-bit rules and other controls can add restrictions.

Create a local prediction exercise:

```bash
mkdir -p "$HOME/linux-lab/project"
printf '%s\n' 'lab invoice' > "$HOME/linux-lab/project/invoice.txt"
chmod 750 "$HOME/linux-lab/project"
chmod 640 "$HOME/linux-lab/project/invoice.txt"
ls -ld "$HOME/linux-lab/project"
stat "$HOME/linux-lab/project/invoice.txt"
```

Owner can traverse/read/write appropriately; the owning group can traverse/list the directory and read the file; others have no access. Every parent directory must also permit traversal. Testing as root does not represent an ordinary user. In a disposable guest, have the administrator create two normal synthetic accounts and a project group using that distribution's account tools. Give only one account membership, sign in freshly as each, and verify list/traverse/read/write/create/delete outcomes. Record actual `id` output.

`umask` removes permission bits from the creation mode an application requests: commonly a requested file mode of 666 with mask 027 yields 640, while a requested directory mode of 777 yields 750. It does not add execute bits. ACLs add named entries; the ACL mask can reduce effective named-user/group rights. Use `getfacl` where available and inspect the whole decision, not one allow entry.

Hard links refer to the same underlying file/inode; symlinks contain a path to another object. Compare `ls -li` before/after creating each in the practice tree, then rename the original path. A hard link remains associated with the file; a relative/absolute symlink may become broken according to its target path. Timestamps and inode metadata describe selected events, not complete history. A process can retain an open-but-deleted file, occupying storage until its handle closes.

Setuid/setgid executable bits can affect execution credentials; directory setgid supports group inheritance; sticky directories limit entry removal. Inspect legitimate uses before modifying them. Do not create privileged executables for this beginner lab. Separate interactive and service accounts, manage account expiry/removal, and validate sudo changes with the distribution's supported validation tool while retaining console access.

## 3. Run and inspect a small service

Use the loopback Python service from tutorial 02. It runs as your normal account and has access to the files that account can read. Record its PID, parent, command line, listener, and logs:

```bash
ps -eo pid,ppid,user,comm,args
ss -ltnp
curl --max-time 3 -i http://127.0.0.1:8000/
```

For a dedicated service exercise, create a separate guest account without interactive use, place only synthetic content in its assigned directory, and use the guest's service manager. On systemd systems, a minimal service definition can express:

```ini
[Unit]
Description=Synthetic loopback lesson
After=network.target

[Service]
Type=simple
User=labweb
Group=labweb
WorkingDirectory=/srv/labweb
ExecStart=/usr/bin/python3 -m http.server 8000 --bind 127.0.0.1 --directory /srv/labweb
NoNewPrivileges=true
Restart=no

[Install]
WantedBy=multi-user.target
```

Before installing a unit, verify the interpreter path, account existence, directory ownership/traversal, port availability, and systemd applicability. Keep configuration owned by the administrator and content readable but not unnecessarily writable by the service. Save the definition as an explicitly named lab unit through the guest's normal administrative process. Inspect `systemctl cat labweb`, run `systemctl daemon-reload` after unit edits, then start the lab unit. Enabling controls startup at boot; starting controls present runtime state. They are separate operations.

Query `systemctl status labweb` and `journalctl -u labweb --since '10 minutes ago'`. Compare intended user/working directory/environment/restart policy/dependencies with actual process and socket. A running process can still serve incorrect content. Reload asks a service to reread supported settings; restart replaces its process. Validate configuration before either. Service-manager conventions and reload support are product-specific.

Scheduled jobs through cron or timers have their own identity, working directory, environment, and output handling. Create a harmless timestamp report only after its manual equivalent works; verify execution and output, not just the schedule definition. Preserve original logs, query bounded periods, and distinguish journal boot, timezone display, persistence, retention, and rotation. Missing logs may mean logging was not enabled.

## 4. Repair three independent faults

1. Set the lab service's content directory to an absent path. Observe startup/runtime behavior and logs. Correct the exact path, then request the page again.
2. Remove read permission from only the synthetic page for the actual service identity. Observe HTTP behavior and permission metadata. Restore the intended narrow permission, then verify both service read and an unrelated user's denial.
3. In a two-VM internal network, use the distribution's firewall manager to deny only the lab port/source flow. Compare local request, remote request, route, listener, and firewall counters. Restore the narrow rule and verify allowed and denied traffic. Keep console access and test IPv4/IPv6 separately.

Restore baseline between faults so one error does not mask another. Running everything as root, granting world write, or disabling the firewall does not explain which boundary was wrong. Keep a short record with symptom, hypothesis, discriminating test, actual cause, minimal correction, and retest.

SSH has client and server configuration. Server host keys establish server identity; user keys authenticate users. Verify host identity through the lab's known record, restrict intended accounts, validate server configuration, and test a fresh login while preserving console/old session. Do not close your only working recovery path before verifying changes.

## 5. Maintain network, packages, and storage

Inspect interface addresses, routes, DNS/resolver state, hostname, listener, and local firewall with tools owned by the distribution. Determine whether NetworkManager, systemd-networkd, another manager, or static configuration controls persistence. A manual edit can be overwritten if you modify the wrong layer.

Trusted package repositories provide signed metadata/package trust according to the distribution. Signatures support provenance, not proof of vulnerability-free code. Review repository origin, dependencies, proposed removals/upgrades, and configuration prompts. Update only through your documented process and test service health afterward. Record package versions for restoration.

Use `lsblk`, `findmnt`, `df -h`, and `df -i` for block devices, mounts, byte capacity, and inode capacity. A filesystem can have free bytes but no free inodes. Apparent size and allocated blocks differ for sparse/compressed files. Open-but-deleted files explain some gaps between directory totals and filesystem use. Diagnose before deleting anything.

Partitions, filesystem creation, mounting, swap, and quotas are distinct layers. Practice a new filesystem only on an explicitly identified disposable virtual disk. Use stable identifiers for persistent mounts, validate the configuration before reboot, and preserve recovery console access. Swap extends backing for memory pages but is not a cure for unbounded workloads; quotas constrain assigned consumption, not every possible exhaustion path.

## 6. Understand additional hardening layers

| Mechanism | What it controls | What to inspect |
| --- | --- | --- |
| Process credentials / search paths | Which identity runs which executable | Writable PATH directories, scripts, config, working directory |
| Shared libraries / dynamic loading | Code loaded by a process | Trusted ownership and configured search locations |
| `/proc` / `/sys` | Live process/kernel/device interfaces | Read selected own-process data; avoid unfamiliar writes |
| Linux capabilities | Individually named privileged operations | Whether the service needs each granted capability |
| PAM | Authentication-related policy framework | Applicable service policy and failure evidence |
| SELinux / AppArmor | Additional mandatory confinement | Denial records and minimum required path/rule |
| Namespaces / cgroups | Resource views / accounting and limits | Shared resources, limits, and container assumptions |
| seccomp | System-call filtering | Necessary calls and failure behavior |
| Audit / kernel parameters | Selected event collection and behavior | Effective settings, applicability, and rollback |
| Kernel modules / boot integrity | Privileged extensions and boot trust | Origin, loading policy, and approved baseline |
| Service sandboxing | Restrictions on one service | Read/write paths, privileges, networking, compatibility |

Mode-bit permission does not override a confinement denial. Fix the minimal policy or application-path mismatch based on evidence instead of disabling controls. The kernel administrator guide documents kernel-facing features; use distribution guidance for integration and defaults. [Linux kernel administrator guide](https://docs.kernel.org/admin-guide/)

## 7. Prove a restore

Separate configuration, data, secret references, and generated cache. Choose an application-consistent backup and preserve necessary metadata. Restore into a clean guest or fresh service directory, recreate identities, install dependencies, restore files, and verify hashes plus access rules. Numeric UID/GID mismatches need explicit mapping. Do not discard the original VM until the restored service passes.

Your runbook should cover installation, account model, permissions, network exposure, log queries, updates, backup, recovery, exceptions, owner, verification, and rollback. Repeat the restore from the amended instructions after discovering any missing dependency. Pass when you can administer without a desktop, explain an allowed and denied read, identify the service's actual account, repair the three faults, and restore useful behavior independently.
