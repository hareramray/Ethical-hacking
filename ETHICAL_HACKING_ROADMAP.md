# Ethical Hacking Roadmap: From Beginner to Professional Practice

**Prepared:** 18 October 2026  
**Format:** A practical syllabus, progress checklist, lab plan, and reference guide.  
**Starting assumption:** You are beginning from basic computer use. Demonstrate an existing skill and skip its introductory exercises if you already know it.

**Expanded topic files:** [Open the detailed roadmap collection](roadmaps/README.md) | [Track your progress](roadmaps/PROGRESS.md).

## 00. How to use this roadmap

Ethical hacking means assessing security with authorization, establishing what a weakness actually allows, and helping the owner fix it. The outcome is a defensible assessment and a safer system.

This roadmap covers the major foundations, professional practices, and specialization areas. No finite document can include every product, vulnerability, research paper, or future technique. Treat this as a comprehensive map of what to learn; use the linked documentation to deepen each subject and update your notes as systems change.

### Learning order

1. Complete authorization and lab setup: **01–02**.
2. Build the technical foundation: **03–08**.
3. Learn the assessment workflow: **09–10**. Start writing findings using **23** immediately.
4. Learn applications and infrastructure: **11–16**. Everyone needs working familiarity; choose one area for deeper practice.
5. Add defensive visibility: **20**. Use it alongside every practical exercise.
6. Choose one primary specialization: **17–19, 21–22**, or deepen **11–16**.
7. Complete independent projects and assessments: **24–25**.
8. Keep **26–27** open as your resource and template library.

**Core** means essential for a general security tester. **Track** means depth needed for your chosen role. **Awareness** means recognize the subject, its risks, and when specialist help is needed. You do not need expert ability in every track before applying for a junior position.

For every topic, work through this loop:

> Explain normal behavior → build a small example → identify a trust boundary → test a controlled failure → collect evidence → implement a fix → retest → explain the result to someone else.

For practical core or track topics, tick a checkbox after you can explain the idea without reading, demonstrate it in your lab, and save evidence. For awareness topics, completion means explaining the concept, recognizing its prerequisites, and analyzing a suitable example; practical mastery comes later if you select that track. Watching a video alone is preparation. For topic groups containing several ideas, split the checkbox into smaller tasks in your own notes.

### Navigation

- [00. How to use this roadmap](#00-how-to-use-this-roadmap)
- [01. Authorization, scope, and professional conduct](#01-authorization-scope-and-professional-conduct)
- [02. Build a safe, repeatable lab](#02-build-a-safe-repeatable-lab)
- [03. Computing and study foundations](#03-computing-and-study-foundations)
- [04. Networking and Internet protocols](#04-networking-and-internet-protocols)
- [05. Linux administration](#05-linux-administration)
- [06. Windows administration](#06-windows-administration)
- [07. Programming and automation](#07-programming-and-automation)
- [08. Security principles and cryptography](#08-security-principles-and-cryptography)
- [09. Assessment methodology, reconnaissance, and enumeration](#09-assessment-methodology-reconnaissance-and-enumeration)
- [10. Vulnerability assessment and research](#10-vulnerability-assessment-and-research)
- [11. Web application security](#11-web-application-security)
- [12. API security and modern authentication](#12-api-security-and-modern-authentication)
- [13. Secure code review and software delivery](#13-secure-code-review-and-software-delivery)
- [14. Linux and Windows host security testing](#14-linux-and-windows-host-security-testing)
- [15. Active Directory and enterprise identity](#15-active-directory-and-enterprise-identity)
- [16. Cloud, containers, and Kubernetes](#16-cloud-containers-and-kubernetes)
- [17. Wireless and network appliance security](#17-wireless-and-network-appliance-security)
- [18. Mobile application security](#18-mobile-application-security)
- [19. Reverse engineering, exploit development, and malware analysis](#19-reverse-engineering-exploit-development-and-malware-analysis)
- [20. Detection engineering, incident response, and forensics](#20-detection-engineering-incident-response-and-forensics)
- [21. Human and physical security assessments](#21-human-and-physical-security-assessments)
- [22. Advanced specialization map](#22-advanced-specialization-map)
- [23. Reporting, remediation, and retesting](#23-reporting-remediation-and-retesting)
- [24. Capstones, portfolio, and career direction](#24-capstones-portfolio-and-career-direction)
- [25. Study schedules and readiness checks](#25-study-schedules-and-readiness-checks)
- [26. Tools and learning resources](#26-tools-and-learning-resources)
- [27. Reusable templates and glossary](#27-reusable-templates-and-glossary)

### What to record

Use a private Git repository for learning notes and sanitized code. Keep client material, credentials, tokens, and sensitive lab artifacts outside public repositories. Maintain one skill tracker with: topic, status, evidence link, last practiced date, mistakes, and next exercise.

Use these levels consistently:

| Level | What you can demonstrate |
| --- | --- |
| 0 — New | You have not studied the topic. |
| 1 — Explain | You can describe normal behavior and the security boundary. |
| 2 — Guided | You can complete a lab with hints and explain the result. |
| 3 — Independent | You can assess an unfamiliar lab, document evidence, and recommend a working fix. |
| 4 — Extend | You can handle edge cases, review another tester's reasoning, and create a reliable regression check. |

For the core, target level 3. For awareness topics, level 1 is initially enough. A specialization requires sustained level 3 work and selected level 4 capabilities.

## 01. Authorization, scope, and professional conduct

**Priority:** Core, before any active testing.

### Understand the boundaries

- [ ] Distinguish vulnerability scanning, vulnerability assessment, penetration testing, adversary emulation, red teaming, purple teaming, configuration review, and compliance auditing. Each has a different objective and evidence standard.
- [ ] Understand ownership, written authorization, acceptable-use conditions, data sensitivity, confidentiality, and coordinated disclosure. An accessible system or a public IP address is not permission to test.
- [ ] Identify the person who can authorize the assessment and all relevant asset owners. A customer's permission does not automatically cover its hosting provider, payment processor, identity provider, employees' personal devices, or another tenant.
- [ ] Learn to read a bug bounty or vulnerability disclosure policy: exact asset list, exclusions, allowed techniques, rate limits, disclosure rules, report channel, and any safe-harbor wording. Policies are specific to the program.
- [ ] Learn the difference between a legal requirement, a contract requirement, a platform policy, and an organizational preference. For an actual engagement, have the responsible owner or qualified adviser resolve jurisdiction and contract questions.

### Produce rules of engagement

- [ ] Record target domains, IP ranges, applications, accounts, tenant/project IDs, environments, and explicitly excluded dependencies.
- [ ] Set objectives, success conditions, dates, testing windows with time zones, source systems, allowed methods, maximum rates, and resource limits.
- [ ] Define approval gates for disruptive tests, credential testing, social engineering, physical access, persistence simulations, and any movement beyond the initial host. Separate authorization is necessary when these are outside the agreed assessment.
- [ ] Specify test identities, synthetic data, backup/recovery readiness, change ownership, escalation contacts, and an immediate stop mechanism.
- [ ] Agree how to handle an accidental discovery outside scope, real sensitive data, a live incident, service degradation, or a potentially critical finding.
- [ ] Define evidence encryption, access, retention, deletion, report delivery, and permission for any later public write-up.
- [ ] Establish cleanup and retesting responsibilities. Log every temporary account, configuration change, file, scheduled task, and access rule created during testing.

Cloud providers publish additional testing conditions. Review the current [AWS penetration testing policy](https://aws.amazon.com/security/penetration-testing/) or [Microsoft Azure testing guidance](https://learn.microsoft.com/en-us/azure/security/fundamentals/pen-testing) when those platforms are involved. Recheck the rules before each engagement; do not treat a cached summary as authorization.

### Lab and completion check

Write a one-page assessment agreement for a fictional company using your own lab assets. Include an in-scope host, an excluded host, a maintenance window, a stop contact, a data-handling rule, and a restoration plan. Given five example actions, explain which are allowed, disallowed, or require clarification.

**Ready to move on:** You can determine whether an action is in scope before running it, stop safely, and explain how evidence will be protected.

## 02. Build a safe, repeatable lab

**Priority:** Core. Start small; add components only when a phase needs them.

### Hardware and platform planning

These are planning estimates, not software minimum requirements:

| Available resources | Practical starting approach |
| --- | --- |
| Limited machine or about 8 GB RAM | Browser-hosted training labs; one lightweight Linux VM at a time; small local development exercises. |
| About 16 GB RAM and SSD storage | A Linux workstation and one or two small targets, adjusting allocations to leave room for the host. |
| About 32 GB RAM or more | A small Windows domain, Linux target, and log collector running together, depending on VM sizing. |
| No suitable local hardware | Provider-hosted training environments; postpone multi-VM enterprise labs. |

- [ ] Learn CPU virtualization, host/guest terminology, resource allocation, virtual disks, snapshots, cloning, and checkpoints.
- [ ] Select a supported hypervisor for your host: Hyper-V, VirtualBox, VMware, or KVM are examples. Read its current requirements and networking documentation before installing.
- [ ] Use an ordinary Linux distribution for administration practice. A security distribution such as Kali can be a later tool workstation; its tool collection does not replace the foundations.
- [ ] Use appropriately licensed Windows and Windows Server images. Check evaluation terms rather than assuming an image remains valid indefinitely.
- [ ] Understand that WSL, containers, and virtual machines provide different isolation properties. WSL is useful for development but is not a substitute for every networking, Windows-domain, kernel, or malware-analysis lab.

### Network isolation and recovery

```text
Personal host
  └── Hypervisor
        ├── Isolated virtual network
        │     ├── Tester workstation
        │     ├── Deliberately vulnerable target
        │     └── Optional log collector / test domain
        └── Controlled update access when required

No unsolicited inbound route from the Internet to vulnerable targets.
```

- [ ] Learn bridged, NAT, host-only, and internal virtual networking. Host-only networks still include the host; NAT does not make an intentionally vulnerable workload harmless.
- [ ] Prefer an internal isolated network for vulnerable targets. Disable forwarding into personal, office, or public networks; verify the actual routes and firewall rules.
- [ ] Keep any Internet-facing update path temporary and controlled. Do not expose a vulnerable training application on a cloud public IP just to make access convenient.
- [ ] Verify the application's listening address and any container port publishing. A container's default exposure may differ from what you intended.
- [ ] Use dedicated browser profiles and lab accounts. Install interception certificates only in the lab browser or device, then remove them when finished.
- [ ] Disable unnecessary shared folders, clipboard integration, USB passthrough, and host mounts. Never reuse real passwords or synchronize lab secrets to personal accounts.
- [ ] Take a known-good snapshot before each exercise. Keep separate backups of important notes: snapshots are not independent backups.
- [ ] Test restoration, verify time synchronization for log correlation, and record software versions.
- [ ] For cloud labs, create a separate project/account, use MFA, set billing alerts and resource limits, and document teardown. A budget alert may notify you without stopping expenditure.

### Build in stages

1. **Starter lab:** Linux workstation, a browser, editor, Git, Python, packet analyzer, and local test web service.
2. **Application lab:** Deliberately vulnerable training app, proxy, database with synthetic records, and application logs.
3. **Infrastructure lab:** Linux target, Windows target, service accounts, file shares, and host logs.
4. **Enterprise lab:** Domain controller, member workstation, member server, dedicated synthetic identities, and centralized logs.
5. **Cloud/container lab:** Disposable tenant/project and a local container/cluster setup when you reach that phase.
6. **Specialist lab:** Mobile emulator, small hardware board, or isolated reverse-engineering VM according to your track.

Keep an inventory containing hostname, purpose, OS/image version, IP address, network, credentials location, snapshot, and owner. Learn to rebuild targets from a short setup document or automation script.

**First deliverable:** A network diagram, inventory, isolation check, and demonstrated snapshot restoration. Confirm that the training app is reachable only by intended lab systems before testing it.

## 03. Computing and study foundations

**Prerequisites:** None. **Priority:** Core. Understand the systems you will later assess before installing security tools.

### Computer architecture and data

- [ ] Identify CPU, RAM, persistent storage, network interfaces, motherboard firmware, and peripherals; distinguish volatile from persistent information.
- [ ] Understand bits, bytes, binary, hexadecimal, signed integers, overflow, Boolean operations, endianness, and the difference between a value and its representation.
- [ ] Recognize ASCII, Unicode, UTF-8, newline conventions, URL encoding, hexadecimal encoding, and Base64. Encoding does not provide secrecy.
- [ ] Understand files, directories, extensions, actual file formats, metadata, compression, archives, checksums, file signatures, and why an extension can misrepresent content.
- [ ] Understand BIOS/UEFI, bootloaders, operating-system startup, Secure Boot concepts, disk partitions, filesystems, and disk encryption at an introductory level.

### Operating systems and application execution

- [ ] Explain kernel space versus user space, processes versus threads, executable files versus running programs, and the role of system calls.
- [ ] Learn scheduling, virtual memory, address spaces, stack and heap, file handles/descriptors, shared libraries, interprocess communication, and signals/events conceptually.
- [ ] Distinguish administrator privileges, application permissions, hardware access, and network access. Installing a program does not automatically give it every permission.
- [ ] Understand clients, servers, services, databases, caches, queues, APIs, and the difference between local and remote execution.
- [ ] Compare virtual machines, containers, and compatibility layers. Learn host/guest boundaries, virtual disks, snapshots, resource limits, and shared-folder risks.
- [ ] Learn availability basics: CPU load, memory pressure, disk space, latency, backups, restoration, and why snapshots alone are not a complete backup plan.
- [ ] **Advanced:** Study interrupts, direct memory access, kernel modules/drivers, memory mapping, executable loaders, and hardware-assisted virtualization when specializing in systems security.

### Learning workflow and technical communication

- [ ] Use a text editor, terminal, browser developer tools, Markdown, a password manager, and a structured note directory.
- [ ] Read a manual page or official reference; identify supported versions, defaults, prerequisites, limitations, and whether an example is safe in your environment.
- [ ] Practice hypothesis-driven troubleshooting: observation → possible cause → smallest discriminating test → result → revised explanation.
- [ ] Keep notes containing date, objective, environment/version, actions, evidence, interpretation, remediation, and retest. Separate confirmed observations from assumptions.
- [ ] Learn basic probability, percentages, orders of magnitude, and rates; distinguish correlation from causation and statistical confidence from certainty.
- [ ] Explain a technical issue twice: once to another engineer and once to a nontechnical stakeholder. Record what could not be tested.
- [ ] Use active recall, spaced review, and reconstruction from memory; measure successful independent tasks rather than videos watched.

### Safe practice and exit criteria

**Labs:** Inventory your own computer; create a disposable VM; install an ordinary application; inspect its process and files; take a snapshot; make a harmless configuration change; restore it. Compare a text file's displayed content, encoding, bytes, metadata, and checksum. Break and repair a local application's configuration while recording evidence.

**Exit gate:** Rebuild the VM from written instructions, explain how a program reaches memory and accesses a file, distinguish encoding from encryption, and troubleshoot one failure without blindly reinstalling everything.

**Common gaps:** Memorizing commands without understanding output; confusing a terminal with an operating system; using screenshots without written reproduction steps; treating a successful restore as proof that every backup works.

## 04. Networking and Internet protocols

**Prerequisites:** Section 03 and basic command-line use. **Priority:** Core; deeper routing engineering is a specialization.

### Network models, addressing, and delivery

- [ ] Use OSI and TCP/IP models to explain encapsulation, headers, payloads, and where switches, routers, firewalls, proxies, and applications operate.
- [ ] Understand Ethernet frames, MAC addresses, ARP, broadcast domains, switches, VLANs, trunks, and the distinction between physical and logical topology.
- [ ] Calculate IPv4 network ranges using CIDR and subnet masks. Recognize private, public, loopback, link-local, multicast, and special-purpose addresses.
- [ ] Explain default gateways, routing tables, longest-prefix matching, static routing, NAT/PAT, connection tracking, and why NAT is not a complete security policy.
- [ ] Learn IPv6 notation, prefixes, global and link-local addresses, multicast, Neighbor Discovery, Router Advertisements, SLAAC, DHCPv6, and dual-stack operation.
- [ ] Understand MTU, fragmentation, path-MTU discovery, ICMP/ICMPv6, packet loss, jitter, bandwidth, throughput, and asymmetric routing.
- [ ] Distinguish stateful/stateless firewall behavior, allow/deny rules, inbound/outbound controls, segmentation, and application-layer filtering.
- [ ] **Advanced:** Understand STP, link aggregation, dynamic routing, BGP trust relationships, overlays, SDN, load balancing, and high-availability designs.

For the IPv6 protocol itself, use the [IETF IPv6 specification](https://www.rfc-editor.org/rfc/rfc8200) as a reference after learning the basic vocabulary.

### Transport and infrastructure services

- [ ] Explain TCP handshakes, sequence/acknowledgment numbers, retransmission, flow/congestion control, connection teardown, ports, and sockets.
- [ ] Explain UDP tradeoffs and that UDP applications can implement reliability themselves. Recognize QUIC's relationship to UDP and TLS.
- [ ] Understand DNS resolvers, authoritative servers, recursion, caching, TTLs, delegation, forward/reverse lookups, and A/AAAA/CNAME/MX/TXT/NS/SOA/SRV records.
- [ ] Distinguish DNSSEC validation from encrypted DNS transport; understand split DNS and why resolver choice affects results.
- [ ] Understand DHCP leases/options, time synchronization, and why incorrect clocks break authentication, certificates, and evidence correlation.
- [ ] Recognize the purpose and trust boundaries of SSH, SMB, LDAP, Kerberos, RDP, SNMP, NTP, SMTP, IMAP, and POP. Learn normal traffic before assessing weaknesses.
- [ ] Distinguish a service's conventional port from proof of its actual identity; a service can use a different port.

### Web traffic, encrypted connections, and remote access

- [ ] Trace a URL through DNS, connection establishment, TLS, HTTP request, application processing, response, and browser rendering.
- [ ] Learn HTTP methods, status codes, headers, cookies, sessions, content types, caching, compression, redirects, proxies, and HTTP/1.1, HTTP/2, and HTTP/3 at a conceptual level.
- [ ] Understand TLS certificates, hostname checks, certificate chains, trust stores, negotiation, and why encrypted transport still requires endpoint authentication.
- [ ] Learn VPN tunneling, split/full tunneling, remote-access versus site-to-site designs, reverse proxies, CDNs, and the visibility each intermediary has.
- [ ] Recognize WebSockets, server-sent events, and long-lived API connections; understand that browser traffic is broader than page downloads.

### Safe practice and exit criteria

**Labs:** Draw a two-VM network; calculate its address range; run a local web service; inspect only your lab traffic with a packet analyzer. Identify DNS, TCP, TLS, and HTTP stages. Introduce separate DNS, route, firewall, and application failures and diagnose each. Compare IPv4 and IPv6 connectivity. Capture a local unencrypted demonstration request and explain which fields an observer can read.

**Exit gate:** Annotate one connection's packet sequence, subnet a small lab correctly, distinguish name-resolution failure from service failure, and explain where encryption starts and ends.

**Common gaps:** Ignoring IPv6; assuming ping failure proves a host is down; treating a listening port as a vulnerability; reading packet-analyzer summaries without inspecting fields; overlooking proxy behavior, clock skew, or encrypted DNS.

## 05. Linux administration

**Prerequisites:** Sections 03–04. **Priority:** Core. Start with one general-purpose distribution and learn its normal administration before relying on a security distribution.

### Shell, files, and permissions

- [ ] Navigate absolute/relative paths; inspect, copy, move, compare, archive, search, and edit files. Understand hidden files, links, mount points, case sensitivity, and the filesystem hierarchy.
- [ ] Use command help, manual pages, tab completion, history, environment variables, exit codes, standard input/output/error, pipes, and redirection.
- [ ] Learn quoting, escaping, globbing, command substitution, and argument boundaries. Understand why untrusted text must not become shell syntax.
- [ ] Read file ownership, user/group/other permission bits, directory permissions, umask, ACLs, special permission bits, and effective permissions.
- [ ] Manage users, groups, sudo policy, account lifecycle, SSH keys, and service accounts using least privilege.
- [ ] Understand hard versus symbolic links, inode metadata, file timestamps, open-but-deleted files, and the difference between filename permissions and file-content permissions.

### Services, networking, and maintenance

- [ ] Inspect processes, parent/child relationships, signals, background jobs, resource use, and which process owns a listening socket.
- [ ] Manage services and scheduled jobs; understand startup configuration and the service manager used by your distribution.
- [ ] Read system/application/authentication logs; learn journal queries, log rotation, time zones, retention, and the need to preserve original evidence.
- [ ] Configure interfaces, routes, DNS, hostnames, local firewalls, and secure remote administration. Verify effective configuration rather than merely editing a file.
- [ ] Install, update, and remove packages; understand repositories, package signatures, dependency resolution, configuration changes, and trusted software sources.
- [ ] Manage disks, partitions, mounts, swap, quotas, backups, restoration, patching, and disk-space failures.
- [ ] Configure an ordinary web service with a dedicated account, limited file access, intentional network exposure, and useful logs.

### Internals and hardening

- [ ] Understand process credentials, environment inheritance, shared libraries, search paths, dynamic loading, and how configuration ownership affects trust.
- [ ] Learn `/proc` and `/sys` as interfaces to system information; distinguish reported configuration from observed runtime behavior.
- [ ] Recognize Linux capabilities, PAM, SSH configuration, SELinux/AppArmor policies, kernel parameters, and audit facilities.
- [ ] **Advanced:** Study namespaces, cgroups, seccomp, container isolation, kernel modules, boot integrity, filesystem capabilities, and service sandboxing.
- [ ] Compare a secure baseline with a running system; document exceptions, operational impact, rollback steps, and verification.

The [Linux kernel administrator's guide](https://docs.kernel.org/admin-guide/) is a deeper reference for kernel-facing behavior; use your distribution's documentation for its package and service-management conventions.

### Safe practice and exit criteria

**Labs:** Build a Linux VM from scratch; create a normal user and a restricted service account; configure a local web service; collect its logs; back up its configuration and data; restore to a fresh VM. Deliberately misconfigure a lab file permission, service path, and DNS setting, then repair each with evidence.

**Exit gate:** Administer the VM without a desktop interface, explain why an access attempt succeeds or fails, identify the account behind a service, and restore that service from your documented backup.

**Common gaps:** Using root for every task; treating containers as equivalent to VMs; changing permissions broadly to silence errors; deleting logs during troubleshooting; confusing package signatures with proof that software has no vulnerabilities.

## 06. Windows administration

**Prerequisites:** Sections 03–04. **Priority:** Core for general security work; deeper enterprise administration is essential for internal assessments.

### Windows architecture and permissions

- [ ] Understand Windows editions, supported builds, update channels, firmware boot, kernel/user mode, processes, threads, drivers, and services.
- [ ] Navigate NTFS, system/user directories, environment variables, registry hives, executable formats, DLLs, and application installation locations.
- [ ] Learn security identifiers (SIDs), local/domain accounts, groups, access tokens, privileges, integrity levels, and User Account Control.
- [ ] Understand NTFS ACLs, inheritance, explicit permissions, effective access, ownership, and how share permissions combine with filesystem permissions.
- [ ] Recognize service accounts, scheduled-task identities, startup mechanisms, and the distinction between an interactive user's rights and a background service's rights.
- [ ] Understand local security policy, audit policy, Credential Manager, certificate stores, and protected operating-system components conceptually.

### Administration and observability

- [ ] Use PowerShell discovery/help, object pipelines, properties, filtering, structured output, error handling, and approved remoting practices.
- [ ] Use Event Viewer, Task Manager, Resource Monitor, Services, Task Scheduler, and built-in system information to investigate normal behavior.
- [ ] Learn Windows Event Log channels, event timestamps, authentication events, service changes, PowerShell logging, and centralized collection concepts.
- [ ] Configure network profiles, DNS, routes, host firewall rules, SMB shares, RDP restrictions, and secure administrative access in your lab.
- [ ] Understand patch management, Microsoft Defender, BitLocker, Secure Boot, recovery keys, recovery environments, system restore limitations, and tested backups.
- [ ] Distinguish application allowlisting, antivirus detection, endpoint telemetry, and privilege management; understand each control's purpose.
- [ ] Learn WSL and virtualization boundaries; verify which host files, network interfaces, and credentials a development environment can access.

Use [Microsoft's PowerShell overview](https://learn.microsoft.com/en-us/powershell/scripting/overview) to understand its administration model, then practice with the help available in your installed version.

### Enterprise foundations

- [ ] Distinguish workgroups, Active Directory Domain Services, and cloud identity; understand that a domain join and a cloud registration are different relationships.
- [ ] Learn domains, forests, organizational units, domain controllers, directory objects, trusts, DNS dependencies, and Group Policy processing.
- [ ] Explain the broad roles of Kerberos, LDAP, SMB, NTLM, certificate services, and time synchronization without yet attempting attack techniques.
- [ ] **Advanced:** Study delegated administration, group-managed service accounts, privileged access models, local administrator password management, and identity lifecycle controls.

### Safe practice and exit criteria

**Labs:** Create two local users in a Windows VM; build a shared test folder with distinct permissions; predict and verify each user's access. Install a harmless service, identify its account and events, and restore its configuration. In a separately isolated enterprise lab, join a client to your own test domain and trace an ordinary sign-in.

**Exit gate:** Explain effective access to a shared file, identify a service's security context, correlate a local configuration change with logs, and distinguish local, domain, and cloud identities.

**Common gaps:** Assuming membership in Administrators means every process is elevated; ignoring share permissions; treating registry presence as execution evidence; disabling protective controls instead of understanding a failure.

## 07. Programming and automation

**Prerequisites:** Section 03 plus basic Linux/Windows command-line skills. **Priority:** Python and shell basics are core; learn other languages to the depth required by your chosen systems.

### Common programming foundations

- [ ] Learn variables, types, control flow, functions, modules, data structures, exceptions, input/output, recursion, and basic algorithmic complexity.
- [ ] Understand bytes versus text, parsing versus validation, serialization formats, regular-expression limits, dates/time zones, and integer/length boundaries.
- [ ] Use a debugger: breakpoints, stepping, call stacks, local variables, and tracebacks. Reproduce a bug with the smallest useful input.
- [ ] Write readable code with explicit configuration, structured logs, useful errors, timeouts, resource limits, and safe cancellation.
- [ ] Understand dependencies, virtual environments, lockfiles, package provenance, version pinning, and updating vulnerable components.

### Languages and development skills

- [ ] **Python — core:** Collections, comprehensions, files, `pathlib`, JSON/CSV, regex, exceptions, logging, argument parsing, virtual environments, HTTP clients, sockets conceptually, and unit tests. Add concurrency only after understanding rate limits and shared state.
- [ ] **Bash — core:** Variables, arrays, conditionals, loops, functions, pipelines, exit-status handling, quoting, temporary files, and safe handling of filenames with spaces. Understand when a Python program is clearer than a shell script.
- [ ] **PowerShell — core:** Objects, cmdlets, functions, modules, parameter validation, errors, CSV/JSON, event queries, and repeatable administration. Understand Windows PowerShell versus modern PowerShell compatibility.
- [ ] **JavaScript/HTML — core for web:** DOM, forms, events, scope, closures, objects/prototypes, promises, async/await, fetch, JSON, browser storage, cookies, and client/server trust boundaries. Read enough CSS to navigate and inspect interfaces.
- [ ] **SQL — core:** Tables, keys, joins, filtering, aggregation, transactions, indexes, permissions, and parameterized queries. Understand relational constraints and why application validation cannot replace database integrity controls.
- [ ] **C — systems foundation:** Compilation/linking, types, pointers, arrays, strings, allocation/freeing, memory ownership, structs, integer conversion, and undefined behavior. Use warnings and sanitizers in your own small programs.
- [ ] **Advanced/specialization:** Assembly and calling conventions for binary analysis; Java/C# for enterprise applications; Go/Rust for relevant tooling; PHP/Ruby or framework-specific languages when the target codebase requires them.

Start with the [official Python tutorial](https://docs.python.org/3/tutorial/) and use [MDN's web-development curriculum](https://developer.mozilla.org/en-US/docs/Learn_web_development) for browser and JavaScript foundations.

### Software engineering and secure automation

- [ ] Use Git commits, branches, diffs, merges, conflict resolution, ignore files, and reviews. Keep credentials, private evidence, and generated secrets out of repositories.
- [ ] Write tests for boundary cases, invalid inputs, authorization decisions, parsing failures, and expected behavior after a fix.
- [ ] Understand HTTP APIs, pagination, authentication, status codes, retry/backoff, idempotency, rate limits, and response validation.
- [ ] Use explicit target allowlists, dry-run modes, bounded concurrency, timeouts, and output directories in assessment helpers; prevent accidental work outside the lab.
- [ ] Avoid constructing shell commands or database queries from untrusted strings; prefer structured APIs and parameterization.
- [ ] Learn code review, basic static analysis, dependency checks, CI concepts, and reproducible installation instructions.

### Safe practice and exit criteria

**Labs:** Write a parser that summarizes synthetic authentication logs; a configuration checker for your own VMs; and a local CRUD application with two user roles and a database. Add negative authorization tests. Repair a parsing bug with a debugger and a regression test. Compile a small C program and use a sanitizer to identify and fix a self-created memory error.

**Exit gate:** Read unfamiliar short code, explain its input-to-output path, change it safely, test failures, and package a documented script someone else can run in a clean environment.

**Common gaps:** Copying code without understanding dependencies; trusting AI-generated scripts; suppressing all exceptions; mixing byte/text encodings; logging secrets; using retries without bounds; considering a working demo production-ready.

## 08. Security principles and cryptography

**Prerequisites:** Networking, operating-system basics, and introductory programming. **Priority:** Core concepts for everyone; cryptographic engineering is an advanced specialty.

### Security reasoning and architecture

- [ ] Explain confidentiality, integrity, availability, authenticity, accountability, privacy, and resilience using concrete system examples.
- [ ] Distinguish assets, threats, vulnerabilities, exposures, exploits, controls, findings, incidents, and risk. A severe-sounding weakness needs evidence and context.
- [ ] Apply least privilege, least functionality, secure defaults, complete mediation, separation of duties, defense in depth, and fail-safe behavior.
- [ ] Draw data flows and trust boundaries; identify what crosses each boundary, who controls it, and where authorization must occur.
- [ ] Understand attack surface, threat modeling, abuse cases, dependency trust, compensating controls, residual risk, and defense validation.
- [ ] Consider availability and privacy when designing a test; collect only evidence needed to demonstrate the issue.

### Identity and access management

- [ ] Distinguish identification, authentication, authorization, and accounting; understand that valid login does not grant access to every object.
- [ ] Learn password storage, unique salts, password-derived key functions, rate limiting, recovery flows, account lifecycle, and session expiration/revocation.
- [ ] Compare RBAC, ABAC, ownership checks, tenant isolation, service identities, and privileged access. Trace authorization from identity to resource to action.
- [ ] Understand MFA factors, phishing-resistant authentication concepts, passkeys/WebAuthn, device enrollment, recovery, and the risk introduced by weaker fallback paths.
- [ ] Learn OAuth 2.0 authorization, OpenID Connect authentication, SAML federation, access/refresh tokens, scopes, audience, issuer, signatures, and expiry at a conceptual level.
- [ ] Distinguish browser sessions, bearer tokens, API keys, certificates, and workload identities; understand their storage, exposure, rotation, and revocation needs.

### Cryptographic building blocks and operational use

- [ ] Distinguish encoding, hashing, password hashing, message authentication codes, encryption, key exchange, and digital signatures.
- [ ] Understand symmetric versus asymmetric cryptography, authenticated encryption, nonces/IVs, salts, cryptographic randomness, key derivation, and replay protection.
- [ ] Learn why strong algorithms still fail through weak keys, nonce reuse, missing authentication, incorrect validation, exposed secrets, or broken protocols.
- [ ] Understand certificate subjects, subject alternative names, certificate authorities, chains, hostname validation, trust anchors, expiry, and revocation concepts.
- [ ] Compare encryption in transit, at rest, and end to end; identify which endpoints and administrators can still access plaintext.
- [ ] Learn key generation, distribution, storage, access restrictions, rotation, revocation, destruction, backups, and recovery. Recognize KMS/HSM roles.
- [ ] Use maintained cryptographic libraries and established protocols; understand that writing an algorithm from scratch is an educational exercise, not a deployment plan.
- [ ] **Advanced:** Study entropy estimation, protocol composition, padding/oracle concepts, side channels, forward secrecy, cryptographic agility, and post-quantum migration considerations using current standards.

For implementation-oriented reading, use the [OWASP cryptographic-storage guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html), checking its current recommendations before building a real system.

### Safe practice and exit criteria

**Labs:** Build an access-control matrix for your local application and verify allowed and denied cases. Use a maintained library to encrypt synthetic data, then show that modified ciphertext fails authentication. Create lab certificates and observe trusted, untrusted, expired, and hostname-mismatch outcomes. Inspect a toy password-storage implementation and replace insecure storage with a maintained password-hashing facility. Document a key-rotation and recovery exercise with test secrets.

**Exit gate:** Explain which cryptographic primitive solves a stated problem; reject encoding as secrecy and ordinary fast hashing as password storage; identify a missing authorization check; and describe who can decrypt data throughout its lifecycle.

**Common gaps:** Confusing OAuth with authentication; believing signatures hide content; assuming encrypted data is safe when the key is beside it; validating tokens without checking audience/issuer; treating MFA as protection against every account-compromise scenario.

## 09. Assessment methodology, reconnaissance, and enumeration

**Priority:** Core. **Prerequisites:** 01–08 at a working level.

### Build a repeatable assessment process

- [ ] Translate the business objective into security questions: who should access which records, which systems should communicate, and which operations require additional approval?
- [ ] Distinguish black-box, gray-box, and white-box assessments. Document what access and information you were given, and the resulting limitations.
- [ ] Define the test perspective: unauthenticated Internet user, ordinary application user, internal workstation, administrator, or source-code reviewer.
- [ ] Map assets, identities, data flows, entry points, dependencies, and trust boundaries before choosing tests.
- [ ] Create hypotheses with expected secure behavior, minimal test actions, likely evidence, potential impact, and a stop condition.
- [ ] Prioritize reachable, business-critical boundaries. Keep a backlog for other observations instead of repeatedly trying the same favorite technique.
- [ ] Maintain a timestamped activity log and a coverage matrix. Label results as tested, passed, finding, inconclusive, not applicable, or not tested, with reasons.
- [ ] Use control cases: compare an authorized user to an unauthorized user, a valid input to an invalid one, and the vulnerable state to the fixed state.
- [ ] Separate discovery, safe validation, impact analysis, reporting, remediation, retesting, and cleanup. Record uncertainty rather than converting a suspicion into a confirmed vulnerability.

### Passive reconnaissance and asset ownership

- [ ] Learn public DNS records, certificate transparency, RDAP/registration information, IP allocation and ASNs, published documentation, repositories, and archived pages.
- [ ] Separate externally observed facts from guesses. A certificate name or shared IP is evidence to investigate ownership, not an automatic scope expansion.
- [ ] Track source, timestamp, confidence, ownership, environment, and whether an asset may be stale or shared.
- [ ] Review deliberately public artifacts for configuration exposure and accidental secrets using synthetic examples. If a real secret appears during authorized work, follow the agreed handling process; do not use it merely to see what it accesses.
- [ ] Understand the privacy implications of OSINT. Use organizational information needed for the assessment; avoid collecting personal details unrelated to the objective.
- [ ] Learn how modern applications depend on CDNs, reverse proxies, SaaS, identity providers, DNS providers, and managed storage. Confirm which dependencies you can test.

### Active discovery and service enumeration

- [ ] Learn host discovery limitations: filtered probes, sleeping devices, IPv6, cloud security groups, proxies, and NAT can all change observations.
- [ ] Distinguish TCP connection behavior from UDP ambiguity. An unanswered probe is not proof that a service does not exist.
- [ ] Understand open, closed, filtered, and uncertain port states; service identification is a hypothesis until corroborated.
- [ ] Learn the effects of scan timing, retries, parallelism, packet loss, authentication, and fragile services. Start conservatively and use the agreed rate limits.
- [ ] Read what a scanner script does before enabling it. Labels such as discovery or safe are not a guarantee that the action fits your target or scope.
- [ ] Enumerate the configuration and access model of relevant services: HTTP(S), SSH, SMB, RDP, WinRM, DNS, LDAP, Kerberos, NFS, SNMP, SMTP, databases, message brokers, and administrative interfaces.
- [ ] For every service, ask: why is it reachable; who can authenticate; what can an ordinary identity do; where is encryption enforced; what is logged; who maintains it?
- [ ] Learn segmentation assessment, IPv4/IPv6 parity, management-plane separation, VPN exposure, and remote-access policy review using owned lab networks.
- [ ] Learn the purpose and risks of tunnels, proxies, and pivoting in segmented labs. Document exact permitted routes; broader reachability never enlarges authorization.

Use the [Nmap reference guide](https://nmap.org/book/man.html) to understand options and output, and [Wireshark documentation](https://www.wireshark.org/docs/) to correlate a tool's result with the actual network exchange.

### Lab sequence

1. Inventory a small isolated environment from its design documents.
2. Discover its reachable services from two allowed network positions.
3. Compare discovered services with the inventory and explain every discrepancy.
4. Inspect one service using its native client, a packet capture, and its server logs.
5. Change a firewall rule or authentication setting, repeat the observation, and record the difference.
6. Produce a coverage matrix showing what remains unknown and what access would resolve it.

**Ready to move on:** You can create an accurate asset/service map, justify every test, explain ambiguous results, and avoid mistaking a port number for a confirmed product or weakness.

## 10. Vulnerability assessment and research

**Priority:** Core. **Prerequisites:** 08–09.

### Understand vulnerability information

- [ ] Distinguish a weakness class (CWE), a specific vulnerability record (CVE), a vendor advisory, an affected-version range, and an exploit demonstration.
- [ ] Read prerequisites: feature enabled, deployment mode, permissions, platform, architecture, authentication state, network access, and user interaction.
- [ ] Learn why banners can be misleading: backported fixes, customized packages, proxy headers, disabled features, and inaccurate version detection.
- [ ] Compare technical severity with business risk. Reachability, exposed data, compensating controls, asset criticality, and recovery cost change prioritization.
- [ ] Learn CVSS vector interpretation and the version used by the engagement. Record the vector and reasoning, not just a numeric score. [FIRST CVSS v4.0 guide](https://www.first.org/cvss/v4.0/user-guide).
- [ ] Understand exploitation likelihood information such as EPSS, evidence of known exploitation, and local exposure. None alone proves that your asset is vulnerable. [FIRST EPSS](https://www.first.org/epss/).
- [ ] Distinguish a vendor-supported fix, configuration mitigation, compensating control, and accepted risk; record residual risk and who owns it.

### Use scanners critically

- [ ] Learn authenticated and unauthenticated checks, credential privilege requirements, plugin/feed updates, exclusions, maintenance windows, and scan limits.
- [ ] Compare tools such as Greenbone/OpenVAS or a commercial vulnerability scanner by required coverage and operational constraints, rather than installing every product.
- [ ] Learn when a scanner can inspect package state or configuration and when it only infers a weakness from externally visible behavior.
- [ ] Check false positives manually and explain false negatives caused by missing credentials, reachability, rate limits, or unsupported technology.
- [ ] Deduplicate instances by root cause while retaining the list of affected assets. Do not combine unrelated weaknesses just because a scanner gives them the same label.
- [ ] Record scan time, configuration, tool/feed version, credentials role, tested assets, and any unavailable checks.

### Research and reproduce safely

- [ ] Prefer vendor advisories, upstream patches, official documentation, and original research over copied exploit descriptions.
- [ ] Read patch differences and identify the missing validation or incorrect assumption. Build a small mental model before attempting reproduction.
- [ ] Review unfamiliar proof-of-concept code as untrusted software: dependencies, network destinations, subprocesses, file writes, destructive behavior, and credential access.
- [ ] Use a disposable, isolated copy of the affected software and synthetic data. Pin versions so another learner can reproduce the observation.
- [ ] Start with the least invasive proof that establishes the security boundary failure. Demonstrating access to a single synthetic record can establish an authorization flaw without extracting a database.
- [ ] Separate a crash from code execution, information disclosure from authenticated access, and a weak setting from demonstrated business impact.
- [ ] Reproduce on the vulnerable version and verify the patched version no longer exhibits the behavior. Record conditions that prevent reproduction.
- [ ] Learn basic coordinated vulnerability disclosure: confidential report, reproducibility, vendor communication, agreed publication, and handling of third-party affected components.

### Lab and completion check

Select three training findings: one real vulnerable version, one configuration issue, and one deliberately misleading version banner. Produce a triage sheet with evidence, prerequisites, confidence, severity reasoning, remediation, and verification results. At least one initially suspicious finding should be correctly dismissed or marked inconclusive.

**Ready to move on:** You can explain why a finding exists, what evidence confirms it, what remains unproven, and how the owner can verify the fix.

## 11. Web application security

**Priority:** Core: application mapping, access control, sessions, common injection, browser boundaries, business logic, and reporting. Track depth: unusual interpreters, desynchronization, advanced cache interactions, and framework-specific behavior. Treat advanced items as a continuing study backlog rather than requiring expert ability before every junior role.

**Prerequisites:** TCP/IP, DNS, TLS, HTTP, HTML/CSS/JavaScript, cookies, SQL, one server-side language, Git, and an isolated application you can reset. First build a small application with registration, login, two user roles, two tenants, a database, uploads, and a background task. Understanding normal behavior is part of testing it.

**Study method:** For every flaw below, record the trust boundary, root cause, preconditions, smallest harmless verification, affected security property, durable remediation, and a regression test. Use your own applications or explicitly provided training environments. Keep synthetic identities and data throughout. The assignments and completion thresholds here are suggested learning targets.

### 11.1 Map the application before testing

- [ ] Trace browser → CDN/cache → reverse proxy → application → database → queue/worker → third-party service. Mark where identity, authorization, decoding, validation, and logging happen.
- [ ] Learn request methods, status codes, headers, content types, redirects, compression, multipart bodies, URL encoding, Unicode normalization, HTTP/1.1 framing, HTTP/2 streams, and HTTP/3 concepts.
- [ ] Distinguish origin from site; understand same-origin policy, CORS, credentialed requests, browser storage, cookie scope, and the difference between a browser restriction and a server authorization decision.
- [ ] Inventory routes, parameters, hidden fields, forms, JavaScript bundles, API calls, file handlers, administrative features, exports, search, webhooks, alternate formats, and asynchronous jobs.
- [ ] Make a role–resource–action matrix covering anonymous, ordinary, privileged, suspended, and deleted users; add a tenant dimension. Include read, create, update, delete, share, bulk operations, and background processing.
- [ ] Record feature prerequisites and business invariants: who owns an object, whether a discount is single-use, which state transitions are legal, and which actions require fresh authentication.
- [ ] Practice browser developer tools, an intercepting proxy, request comparison, application logs, debugger breakpoints, and database inspection. Learn tool scope controls and request budgets before using automation.

Use the [OWASP Web Security Testing Guide](https://owasp.org/projects/web-security-testing-guide) to organize assessment coverage and [OWASP ASVS](https://owasp.org/projects/asvs) to select verifiable security requirements. Record the version used because requirement identifiers and content can change.

### 11.2 Identity, authorization, and session weaknesses

- [ ] Authentication: account enumeration, inconsistent login paths, weak registration verification, recovery flows, reset-token lifecycle, email changes, MFA enrollment/reset, recovery codes, remembered devices, and passwordless login.
- [ ] Sessions: unpredictable identifiers, fixation, rotation after authentication or privilege changes, cookie flags, idle and absolute timeout, logout, revocation, concurrent sessions, device lists, and session handling after account suspension.
- [ ] Access control: horizontal and vertical privilege boundaries, insecure direct object references, function-level checks, object-property restrictions, tenant isolation, ownership transfers, invitation acceptance, and shared-link permissions.
- [ ] Check authorization again in exports, search results, nested resources, batch operations, downloads, workers, caches, and alternative API versions. Hiding a control in the interface does not enforce access.
- [ ] CSRF: identify browser-supplied ambient credentials, state-changing actions, login CSRF, anti-CSRF token validation, origin checks, and SameSite limitations. Understand how XSS can undermine browser-side defenses.

**Lab:** Create two users in separate tenants and one administrator. Demonstrate one missing ownership check using a single synthetic record. Add centralized authorization, then test owner, non-owner, other tenant, administrator, anonymous, and suspended identities. Verify both content and side effects: a denied response alone is insufficient if a worker still performs the action.

### 11.3 Injection, interpretation, and unsafe server behavior

- [ ] SQL injection: query construction, prepared statements, ORM escape hatches, dynamic identifiers, second-order data, and database privilege boundaries. Learn why parameterization and business validation solve different problems.
- [ ] NoSQL, LDAP, XPath, expression-language, and log injection: recognize the interpreter and grammar involved instead of assuming every injection behaves like SQL.
- [ ] OS command and argument injection: shell invocation, unsafe process construction, option interpretation, executable allowlists, and least-privilege workers.
- [ ] Server-side template injection: user-controlled templates versus ordinary template data, dangerous rendering helpers, and sandbox limitations.
- [ ] Path traversal and local/remote file inclusion: canonicalization, alternate separators, symbolic links, archive extraction, working directories, and storage-root enforcement.
- [ ] SSRF: URL-fetching features, redirects, parser discrepancies, DNS resolution, private/internal destinations, service credentials, allowed schemes, egress controls, and response handling. Verify only against a local mock service you own.
- [ ] XML external entities and unsafe XML processing: external resource resolution, DTD behavior, parser defaults, schema validation, and resource exhaustion safeguards.
- [ ] Unsafe deserialization: automatic object construction, untrusted type metadata, framework signing assumptions, schema-based formats, and unsafe convenience methods. Separate integrity protection from safe parsing.
- [ ] File uploads: extension/MIME/content agreement, generated filenames, authorization, executable content, storage outside served code paths, image/document processing, size limits, archive handling, and safe download headers.
- [ ] Type confusion and parser differences: duplicate parameters, parameter pollution, duplicate JSON keys, content-type mismatch, numeric coercion, null handling, Unicode ambiguity, and mismatched validation across layers.
- [ ] Header injection/response splitting, unsafe redirects, and generated-content injection in CSV exports, email, PDFs, and documents. Follow data into the next interpreter, including a spreadsheet opened by an administrator.
- [ ] Resource exhaustion: inefficient regular expressions, large/recursive documents, decompression, expensive queries, unbounded pagination, and uncontrolled job creation. Study limits through bounded local tests, not service disruption.

**Lab:** Choose three different interpreters or parsers. For each, trace untrusted input to its dangerous use, verify a harmless observable effect, replace the unsafe construction with a safe API or strict schema, and add tests for valid input, rejected input, encoding variants, and downstream behavior.

### 11.4 Browser, frontend, and content security

- [ ] Reflected, stored, and DOM-based XSS; context-sensitive output encoding; HTML sanitization; safe DOM APIs; framework escape bypasses; and third-party script trust.
- [ ] DOM sources and sinks, `postMessage` origin/source checks, DOM clobbering, JavaScript prototype pollution, dynamic script loading, JSONP/legacy integrations, and unsafe client-side routing.
- [ ] CORS origin matching, credential behavior, preflight handling, exposed headers, and why permitted browser reads must match the application's intended trust relationship.
- [ ] Clickjacking, framing policy, opener relationships, cross-origin information leaks, referrer leakage, mixed content, open redirects, and sensitive information in URLs.
- [ ] Content Security Policy, nonces/hashes, Trusted Types where supported, HSTS, MIME handling, Permissions Policy, and cross-origin isolation. Treat headers as supporting controls, with compatibility and deployment tests.
- [ ] Service workers, cache storage, local/session storage, IndexedDB, source maps, browser extensions, analytics scripts, and frontend build-time variables. Determine which data persists after logout or account switching.
- [ ] Server-side rendering, hydration, static generation, incremental revalidation, and server components: identify which code runs where and where privileged data can enter a public response.

**Lab:** Repair one stored-content flaw and one DOM data-flow flaw in your own application. Verify the intended formatted content still works, unsafe input stays inert, private data does not appear in public output, and the relevant browser policy is enforced without breaking legitimate pages.

### 11.5 HTTP intermediaries, caches, and application logic

- [ ] Request smuggling/desynchronization: inconsistent message boundaries, normalization, HTTP/2-to-HTTP/1 translation, connection reuse, and frontend/backend disagreement. Practice only in a dedicated proxy/backend lab with no unrelated users.
- [ ] Host and forwarded-header trust, absolute URL generation, proxy identity headers, redirect construction, and trusted-proxy configuration.
- [ ] Alternative HTTP methods, method overrides, routing inconsistencies, path normalization, and access controls that differ between the edge, framework router, and application handler.
- [ ] Cache poisoning and cache deception: cache keys, unkeyed inputs, `Vary`, personalized responses, authentication state, path normalization, query handling, CDN rules, and purge behavior.
- [ ] Business logic: skipped workflow steps, price/quantity/currency trust, rounding, coupon reuse, refunds, entitlements, trials, referral systems, invitations, consent, account linking, and administrative overrides.
- [ ] Races and state transitions: check-then-act flaws, duplicate redemption, transaction isolation, unique constraints, locking, atomic updates, idempotency keys, retry semantics, and partial failure recovery.
- [ ] Information exposure and configuration: debug pages, verbose errors, backup artifacts, test endpoints, directory indexes, weak security defaults, public object storage links, and secrets in application logs.
- [ ] Reliability as a security property: fail-open checks, inconsistent authorization during outages, stale caches, delayed revocation, queue retries, and incomplete cleanup after failed transactions.

The [PortSwigger topic catalog](https://portswigger.net/web-security/all-topics) provides practice across server, browser, and advanced web topics. Its [race-condition material](https://portswigger.net/web-security/race-conditions) is useful when studying concurrent state changes.

**Lab:** Implement a synthetic single-use coupon and test bounded concurrent requests locally. Enforce the invariant with an atomic database operation or transaction, then verify retries, duplicate requests, and worker processing cannot create a second redemption. Separately configure a local cache and prove that two accounts never receive one another's personalized response.

### 11.6 Practice sequence and exit criteria

The [CORS preflight lesson](labs/browser_security/CORS_PREFLIGHT.md), [CSP worker/reporting lesson](labs/browser_security/CSP_WORKERS_REPORTING.md), and [local OAuth/OIDC flow](labs/browser_security/OAUTH_OIDC.md) add observed browser-protocol behavior. Keep request permission, handler effects, response visibility, worker execution, report receipt, and identity-flow validation as separate evidence.

Runnable companion lessons now cover [personalized cache isolation](labs/browser_security/CACHE_ISOLATION.md), [authorization during queued exports](labs/browser_security/QUEUED_AUTHORIZATION.md), and [browser return-URL validation](labs/browser_security/OPEN_REDIRECTS.md). Compare vulnerable/fixed decisions and repeat the successful allowed controls. The cache and queue lessons use disposable application models; the redirect lesson follows real HTTP navigation between the two local origins.

1. Build and document the small application; perform a manual walkthrough before scanning.
2. Complete at least 25 training exercises spanning identity, access control, injection, browser security, files, SSRF, logic, and intermediaries. Revisit five without walkthroughs after a delay.
3. Assess a local [OWASP Juice Shop](https://owasp.org/projects/juice-shop) or [WebGoat](https://owasp.org/projects/webgoat) deployment and distinguish verified findings from scanner suggestions.
4. Produce at least eight concise finding records and remediate four in source code, with positive and negative regression tests.
5. Pass a fresh application review: explain coverage gaps, detect a planted authorization defect, identify an unsafe input-to-sink path, and propose a fix that preserves intended behavior.

**Exit evidence:** application map; role/tenant matrix; repeatable notes; eight findings across at least five root causes; four verified repairs; and a checklist explaining tested, untested, and inapplicable controls.

## 12. API security and modern authentication

**Priority:** Core: REST/JSON, object/function/property authorization, lifecycle controls, and OAuth/OIDC concepts. Track depth: implement and assess the additional protocols used by your target systems, including SAML, gRPC, advanced GraphQL, and WebAuthn details.

**Prerequisites:** Section 11, JSON/XML, API clients, TLS, asymmetric cryptography concepts, and the ability to read a protocol sequence diagram. Begin with an API you implement and a local identity provider or documented test tenant.

### 12.1 API design and attack-surface coverage

- [ ] REST: resource models, methods, status codes, pagination, filtering, partial updates, content negotiation, idempotency, schema validation, and version compatibility.
- [ ] Inventory documented and undocumented endpoints, deprecated versions, administrative routes, mobile-specific APIs, partner interfaces, exports, batch methods, and background consumers. Compare implementation with OpenAPI or equivalent contracts.
- [ ] Authorization at object, function, and property levels; mass assignment; excessive returned fields; nested-resource ownership; tenant context; and authorization on every bulk item.
- [ ] Resource consumption limits across page size, batch size, upload volume, search complexity, paid integrations, concurrency, and asynchronous jobs. Include account- and tenant-level accounting.
- [ ] Sensitive workflows: purchase, reservation, invitation, password recovery, content publication, and inventory allocation. Define misuse-resistant state transitions before evaluating automation controls.
- [ ] Third-party API consumption: transport trust, schema/length checks, credential scope, timeouts, retries, redirects, unexpected error content, and trust in partner-supplied identifiers.
- [ ] Webhooks: signing, timestamp/replay handling, key rotation, delivery authentication, destination validation, idempotency, event ordering, and dead-letter recovery.

Use the [OWASP API Security Top 10 project](https://owasp.org/projects/api-security-project) as an awareness checklist; supplement it with endpoint-specific contracts and authorization requirements rather than treating ten categories as complete coverage.

### 12.2 Protocol-specific learning

- [ ] GraphQL: schema, queries, mutations, subscriptions, resolvers, node identifiers, aliases, batching, field-level authorization, nested relationship access, depth/cost limits, and error leakage. Introspection visibility alone does not establish a vulnerability.
- [ ] gRPC: Protocol Buffers, services/methods, metadata, unary and streaming calls, deadlines, message limits, interceptors, transport security, service identity, reflection exposure, and per-method/per-message authorization.
- [ ] WebSockets: handshake origin validation, authentication, subscription scope, message schemas, reconnection, token expiration, session revocation, message size/frequency limits, and authorization after initial connection.
- [ ] Event-driven APIs: producer/consumer identity, queue/topic permissions, message provenance, schema evolution, replay, duplicate delivery, tenant routing, and delayed authorization decisions.

**Lab:** Expose the same synthetic object through REST and either GraphQL, gRPC, or WebSockets. Test a cross-tenant read, prohibited property update, and expired identity on each interface. Fix the shared policy, then verify equivalent denial and permitted behavior across transports.

### 12.3 Identity protocols and credential lifecycle

- [ ] Distinguish authentication, authorization, federation, provisioning, and session management. Diagram resource owner, client, authorization server, identity provider, resource server, and relying party.
- [ ] OAuth: authorization-code flow, PKCE, confidential/public clients, redirect URI validation, scopes, resource/audience restrictions, state binding, consent, client authentication, token exchange, and refresh-token rotation/reuse handling.
- [ ] Study implicit and password-grant flows as legacy review concerns; consult the security guidance when selecting implementations. Understand code interception, issuer mix-up, replay, and redirect trust at the design level. Use [RFC 9700](https://www.rfc-editor.org/info/rfc9700/) as the OAuth security reference.
- [ ] OpenID Connect: discovery, ID versus access tokens, issuer/audience verification, nonce, subject identifiers, UserInfo, authentication freshness, account linking, and logout. Validate tokens for their intended purpose; an ID token is not a substitute for API authorization. Reference [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html).
- [ ] JWT/JWS/JWE: encoding versus signing versus encryption, trusted algorithms and keys, signature verification, expiration/not-before, issuer/audience, key IDs, JWKS retrieval/rotation, token-type separation, and revocation tradeoffs. Decoding a token does not validate it.
- [ ] SAML: service/identity providers, metadata trust, assertions, signatures, audience, recipient, destination, request correlation, time windows, replay prevention, XML parsing, signature-wrapping concepts, and certificate rollover.
- [ ] WebAuthn/passkeys: registration and authentication ceremonies, relying-party ID/origin, challenges, user presence/verification, credential records, authenticator options, recovery, device loss, synchronization considerations, and enrollment protection. Study the [W3C WebAuthn specification](https://www.w3.org/TR/webauthn-3/) alongside your platform's supported implementation.
- [ ] Full lifecycle: invitation → registration → verification → enrollment → login → elevation → recovery → revocation → deletion. Include MFA resets, lost devices, changed emails, disabled employees, service accounts, API keys, and SCIM provisioning/deprovisioning.
- [ ] Storage and logging: prevent tokens in URLs, analytics, crash reports, browser-accessible storage without a deliberate design, and debugging output. Separate production and testing identities, issuers, keys, and audiences.

**Lab:** Implement code flow with PKCE through an established library. Test wrong issuer/audience, expired credentials, invalid state/nonce, replayed completion, recovery, and revoked sessions using only your test accounts. Add regression tests at the component responsible for each validation.

**Exit evidence:** a complete identity sequence diagram; an API inventory; at least 20 authorization/lifecycle test cases across two tenants; a cross-protocol policy test; a key-rotation exercise; and documented behavior when users, sessions, refresh credentials, or signing keys are revoked.

## 13. Secure code review and software delivery

**Priority:** Core: read a small application's data flows, identify unsafe operations, understand dependencies/secrets, and verify fixes. Track depth: complex codebases, advanced fuzzing, full pipeline assessment, build provenance, and release-integrity engineering.

**Prerequisites:** proficiency in one language/framework, debugging, tests, Git, dependency management, basic build tooling, and Sections 11–12. Learn one stack deeply, then transfer the principles to a second stack with different parsing and type behavior.

### 13.1 Read code as a system

- [ ] Start with architecture, assets, trust boundaries, entry points, authentication middleware, authorization policies, data models, external integrations, and deployment configuration.
- [ ] Trace sources → transformations → validation → sensitive sinks. Sources include HTTP, files, messages, database records, environment settings, and partner data; stored data can remain untrusted.
- [ ] Recognize sinks: queries, process execution, template rendering, deserialization, filesystem access, network fetches, redirects, logging, cryptography, authorization decisions, and serialization to clients.
- [ ] Distinguish validation, escaping, encoding, canonicalization, sanitization, parameterization, and authorization. Check their order, context, completeness, and whether alternate paths bypass them.
- [ ] Follow control flow through middleware, decorators, callbacks, exceptions, feature flags, workers, retries, and administrative jobs. Review denial behavior and partial side effects.
- [ ] Inspect business invariants and transactional boundaries, permission changes, identifier reuse, stale caches, and object ownership. Many important defects are absent from pattern-based scanner rules.
- [ ] Review crypto usage: approved libraries, secure randomness, password hashing, authenticated encryption, nonce handling, key separation/rotation, certificate verification, and error handling. Avoid custom cryptographic designs.
- [ ] Review language hazards: dynamic evaluation, coercion, unsafe reflection, unsafe native interfaces, integer boundaries, memory ownership, concurrency, filesystem races, and framework-specific insecure defaults.

**Lab:** Review a small codebase without scanning first. Draw three complete data flows, write explicit security hypotheses, inspect tests and configuration, and then compare your findings with static analysis. For every warning, document reachability, attacker control, mitigating checks, and actual impact.

### 13.2 Verification tools and secure changes

- [ ] Understand SAST, software composition analysis, secret scanning, DAST, interactive analysis, fuzzing, and manual review: inputs required, classes detected, false positives, blind spots, and operational cost.
- [ ] Learn dependency reachability and advisory interpretation; distinguish an installed vulnerable package from a reachable vulnerable behavior while still tracking required updates.
- [ ] Practice unit, integration, property-based, contract, and end-to-end security tests. Use positive cases so a repair cannot pass simply by disabling the feature.
- [ ] Use bounded fuzzing against a local parser or handler with time/memory limits, reproducible seeds, crash minimization, and triage. Fix the underlying invariant rather than one discovered input.
- [ ] Add review checks to pull requests, define justified severity thresholds, document exceptions with owners/expiry, and keep suppression narrowly scoped.
- [ ] Check patch completeness across alternate routes, encodings, types, API versions, workers, tenant contexts, and duplicated implementations.

The [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) provides focused guidance for implementation topics such as authorization, secure code review, secret management, and CI/CD security. Use the relevant language/framework documentation to confirm the exact behavior of your chosen APIs.

### 13.3 Dependencies, builds, and delivery infrastructure

- [ ] Dependency graph: direct/transitive, production/development/build dependencies, lockfiles, integrity hashes, private registries, namespace confusion, abandoned packages, lifecycle scripts, and update ownership.
- [ ] SBOM: generate a machine-readable inventory, record versions/components/relationships, connect it to the built artifact, and use it to answer whether an advisory affects a released build. Learn SPDX/CycloneDX concepts and VEX limitations.
- [ ] Source controls: protected branches, review requirements, identity protection, least-privilege tokens, repository access reviews, release-tag integrity, and auditability.
- [ ] CI/CD trust: untrusted pull requests, workflow permissions, reusable actions, pinned dependencies, third-party integrations, runner isolation, workspace cleanup, cache/artifact trust, environment approvals, and fork behavior.
- [ ] Secrets: creation, storage, injection, scope, rotation, revocation, redaction, and incident response. Prefer short-lived workload credentials where supported; removing a committed secret does not revoke it.
- [ ] Build integrity: isolated build environments, immutable inputs, reproducibility concepts, provenance, artifact digests, signing, verification policy, trusted builders, and protection of signing identities. A valid signature must still be connected to an authorized producer and expected build.
- [ ] Use the [SLSA specification](https://slsa.dev/spec/) to study supply-chain integrity and provenance requirements; identify which evidence a consumer actually verifies before trusting an artifact.
- [ ] Infrastructure as code: versioned configuration, plan review, module/provider trust, remote-state confidentiality, policy checks, least-privilege deployment credentials, environment separation, and drift detection.
- [ ] Packaging and release: minimal runtime images, non-root execution where appropriate, patch cadence, artifact promotion, migration safety, staged rollout, rollback, and retention of release evidence.
- [ ] Post-release loop: telemetry, vulnerability intake, dependency advisories, patch verification, emergency access, key compromise response, and feedback into design requirements.

### 13.4 Delivery capstone and exit criteria

Create a small repository containing the lab application, tests, dependency lockfile, deployment configuration, and CI workflow. Seed a harmless mock secret and an intentionally insecure local code path; use dedicated test fixtures so no genuine credential or vulnerable service is published.

**Root cause → verification → repair → regression:** trace the insecure source-to-sink flow; demonstrate its harmless local effect; replace the unsafe behavior; and prove both rejection and legitimate use. For the mock secret, verify detection, remove it, and document the revocation process using a disposable test credential.

**Exit evidence:** two manual code reviews; four confirmed and fixed defects; ten meaningful security assertions; a triaged scanner report; an SBOM tied to a build digest; verified build provenance/signature where your tooling supports them; a least-privilege CI workflow; and a tested rollback procedure. Be able to explain which security properties each artifact demonstrates and what remains unproven.

## 14. Linux and Windows host security testing

**Priority:** Core working knowledge; deeper practice for infrastructure testers. **Prerequisites:** 04–10.

### Understand the local trust model

- [ ] Distinguish remote service access, local interactive access, service identities, administrator/root authority, and kernel authority.
- [ ] Inventory users, groups, privileges, processes, listening sockets, services, installed packages, jobs, mounts, and security policies.
- [ ] Trace which identity reads, writes, or executes a file, and who can change its parent directory, configuration, dependencies, or startup parameters.
- [ ] Understand least privilege, credential storage, secret rotation, patching, logging, host firewalls, application control, and security baselines.
- [ ] Learn privilege escalation as a broken boundary between an ordinary identity and a more privileged action. Identify the misconfiguration and its preconditions before considering validation.
- [ ] Separate intended administrative capability from a vulnerability. An administrator being able to administer is not, by itself, a security finding.

### Linux assessment topics

- [ ] User/group permissions, ACLs, ownership, writable parent directories, symbolic links, and unsafe temporary-file handling.
- [ ] `sudo` policy, SUID/SGID programs, Linux capabilities, privileged helper programs, and the implications of permitted commands.
- [ ] Service accounts, systemd units and timers, cron jobs, startup scripts, environment variables, PATH handling, and trusted executable locations.
- [ ] SSH authentication, host keys, authorized keys, key protection, remote root policy, and forwarding settings.
- [ ] Secrets in configuration, backups, histories, process environments, logs, and deployment artifacts; account for who can actually read them.
- [ ] NFS exports, file shares, local sockets, database accounts, backup agents, web-service identities, and permission boundaries between applications.
- [ ] Mount flags, namespaces, containers, privileged container settings, exposed runtime sockets, and access to host resources.
- [ ] SELinux/AppArmor, seccomp, audit logs, package provenance, patch state, and version backports.
- [ ] Kernel vulnerabilities at a conceptual level: architecture/version requirements, stability risks, patched configurations, and why a configuration fix may be safer to validate first.

### Windows assessment topics

- [ ] Access tokens, SIDs, group membership, integrity levels, privileges, UAC behavior, and the difference between local and domain accounts.
- [ ] NTFS and registry ACLs, inherited permissions, ownership, share permissions, and effective access across both share and filesystem layers.
- [ ] Service executable/configuration permissions, service accounts, scheduled tasks, startup locations, and unsafe executable search paths.
- [ ] Registry and application configuration, installer behavior, DLL search order, signed binaries, and trusted update mechanisms.
- [ ] RDP, WinRM, SMB settings, authentication requirements, firewall scope, remote administration, and administrative share exposure.
- [ ] Password policy, local administrator reuse, Windows LAPS concepts, credential isolation, and managed service-account use.
- [ ] Credential storage architecture and protection boundaries: DPAPI, credential vaults, cached authentication, and why memory containing secrets needs careful handling.
- [ ] Microsoft Defender, attack surface reduction, application control, patch state, event logs, and auditing policy. Evaluate controls using agreed test cases.
- [ ] Backup operators, software deployment identities, service permissions, and management agents as privileged components.

### Credentials and post-access discipline

- [ ] Understand online versus offline password auditing, password hashing versus protocol challenge/response, lockout thresholds, MFA, and rate limiting.
- [ ] Use synthetic credentials and specifically authorized datasets in labs. Measure the effect of password length, common patterns, salts, and work factors without collecting real users' passwords.
- [ ] Learn at a conceptual level how credential reuse, token exposure, and excessive delegation can extend access; pair each with prevention and observable telemetry.
- [ ] After any approved access change, inventory what changed, capture minimal proof, avoid unrelated data, and restore the system.
- [ ] Treat persistence, lateral movement, and data-access simulations as separately scoped activities with clear stop and cleanup requirements.

### Lab and completion check

Build one Linux and one Windows VM with a deliberately misconfigured service or file permission. From an ordinary test account, explain the affected trust boundary, validate the problem with harmless synthetic artifacts, repair the permission or service identity, and repeat the test. Capture both host logs and effective permissions before and after.

**Ready to move on:** You can assess a host without blindly running an escalation script, explain three different privilege-boundary failures, and verify their fixes without breaking legitimate administration.

## 15. Active Directory and enterprise identity

**Priority:** Core awareness; track depth for internal assessments. **Prerequisites:** Windows, DNS, networking, authentication, and host permissions.

### Learn administration before assessment

- [ ] Domains, forests, organizational units, sites, domain controllers, replication, global catalogs, and trust relationships.
- [ ] Users, computers, groups, nested groups, service accounts, managed service accounts, and privileged administrative identities.
- [ ] AD-integrated DNS, time synchronization, directory naming, LDAP queries, Group Policy, and domain join.
- [ ] Kerberos principals, tickets, ticket-granting services, service principal names, lifetimes, and delegation; compare NTLM at an architectural level.
- [ ] Access-control entries, inheritance, object ownership, delegated administration, and effective rights over directory objects.
- [ ] AD CS certificate authorities, templates, enrollment rights, certificate authentication, revocation, and private-key protection.
- [ ] Trust direction versus access direction, transitivity, authentication boundaries, and forest-level considerations.
- [ ] Distinguish on-premises AD DS from Microsoft Entra ID. Learn hybrid synchronization and federation as additional trust relationships, not interchangeable products.

The [Microsoft AD DS overview](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview) is an entry point to the official administration documentation.

### Assess identity attack paths

- [ ] Map ordinary-user capabilities before privileged ones. Inventory privilege-bearing groups and indirect paths created by group nesting or delegated rights.
- [ ] Review excessive directory permissions, stale users/computers, unused trusts, service-account privileges, and inconsistent account lifecycle processes.
- [ ] Review Kerberos service-account exposure and password strength. Understand ticket-related attack classes and their prerequisites in a synthetic domain.
- [ ] Recognize Kerberoasting and AS-REP roasting as credential-auditing study topics; compare their prerequisites and account controls. Understand pass-the-hash and pass-the-ticket as distinct forms of credential-material reuse, with prevention and logging considerations.
- [ ] Study NTLM relay and name-resolution spoofing as protocol/control interactions; learn the roles of signing, channel binding, authentication policy, and network placement.
- [ ] Review constrained, unconstrained, and resource-based delegation concepts, and distinguish legitimate service behavior from unsafe trust.
- [ ] Review certificate template and enrollment permissions, issuance requirements, authentication uses, and certificate-based privilege boundaries.
- [ ] Understand credential reuse, privileged sessions on lower-trust machines, and administrative tier separation.
- [ ] Review GPO editing rights, SYSVOL content access, software deployment, backup infrastructure, and management platforms.
- [ ] Model trust edges using manually collected inventory before introducing graph tools. An apparent path requires validation of permissions, current state, and preconditions.
- [ ] Learn the importance of domain-controller backups, recovery plans, restricted administration, and protected management access.
- [ ] Recognize high-impact capabilities such as directory replication abuse or authentication-ticket forgery conceptually; reserve any practical validation for purpose-built domains with explicit scope.
- [ ] Connect common research terminology such as DCSync and forged authentication tickets to the specific permissions, key material, and trust assumptions involved; avoid treating a technique name as proof that its prerequisites exist.

### Hybrid identity and SaaS

- [ ] Tenant roles, application registrations, enterprise applications, consent, service principals, workload identities, and secret/certificate lifetimes.
- [ ] Federation, provisioning, SCIM, synchronization agents, external guests, cross-tenant relationships, and deprovisioning delays.
- [ ] MFA enrollment and recovery, conditional access, session policies, legacy authentication, and emergency access account controls.
- [ ] SaaS sharing settings, OAuth application access, email forwarding policy, audit availability, and retention.
- [ ] Compare an application's local role model with the identity provider's claims; verify that removing a group or permission eventually removes access as intended.

### Lab and completion check

Build a small isolated domain with a controller, member server, workstation, ordinary users, one service identity, and delegated administrators. Document normal authentication. Introduce two excessive-permission relationships, map their impact using test identities, and remediate them. Add a logging view showing the relevant identity events. If hardware is limited, use a dedicated hosted enterprise lab.

**Ready to move on:** You can explain an identity access path from its permissions and prerequisites, fix the underlying delegation issue, and demonstrate that legitimate work still succeeds.

## 16. Cloud, containers, and Kubernetes

**Priority:** Core concepts; track depth in one provider first. **Prerequisites:** networking, IAM, APIs, Linux, and basic application deployment.

### Cloud concepts that transfer between providers

- [ ] Shared responsibility for IaaS, PaaS, SaaS, and serverless; control plane versus workload/data plane.
- [ ] Organizations, accounts/subscriptions/projects, regions, resource hierarchies, management groups, and separation of development from production.
- [ ] Human and workload identities, role assumption, federated login, temporary credentials, trust policies, resource policies, and inherited permissions.
- [ ] Explicit deny, policy conditions, role scope, privilege boundaries, organization controls, and the interaction of identity and resource policies.
- [ ] Virtual networks, subnets, routes, security groups/firewalls, private endpoints, public exposure, egress, DNS, load balancers, and administrative access.
- [ ] Object storage, managed databases, message queues, compute instances, serverless functions, secrets services, and key management.
- [ ] Instance/workload metadata concepts, service-account credentials, default permissions, and the relationship between application flaws and cloud identity.
- [ ] Audit logging, data-access logging, retention, centralized collection, alerting, and who can disable or delete evidence.
- [ ] Encryption keys, backup ownership, snapshots, image sharing, replication, and data lifecycle.
- [ ] Infrastructure as code, configuration drift, deployment identities, state-file sensitivity, and destructive-change review.

### Choose one provider, then translate

| Area | AWS vocabulary to learn | Azure vocabulary to learn | Google Cloud vocabulary to learn |
| --- | --- | --- | --- |
| Organization | Organizations, accounts, SCPs | Tenants, management groups, subscriptions | Organizations, folders, projects, organization policy |
| Identity | IAM roles/policies, STS | Entra identities, Azure RBAC, managed identities | IAM roles/policies, service accounts, workload identity |
| Networking | VPC, security groups, endpoints | VNet, NSG, Private Link | VPC, firewall policies, private access |
| Compute | EC2, Lambda, ECS/EKS | VMs, Functions, App Service, AKS | Compute Engine, Cloud Run, GKE |
| Storage and secrets | S3, KMS, Secrets Manager | Storage accounts, Key Vault | Cloud Storage, Cloud KMS, Secret Manager |
| Visibility | CloudTrail and relevant service logs | Activity, sign-in, and resource logs | Cloud Audit Logs and service logs |

The names organize your study; they do not imply identical behavior. Read the documentation for the service and policy type actually in use. Provider introductions: [AWS documentation](https://docs.aws.amazon.com/), [Azure documentation](https://learn.microsoft.com/en-us/azure/), and [Google Cloud security](https://cloud.google.com/security).

### Cloud assessment skills

- [ ] Inventory resources and effective permissions using a dedicated read-only review identity wherever possible.
- [ ] Identify excessive roles, unsafe trust relationships, long-lived keys, unowned service identities, public data, and unmanaged exposure.
- [ ] Review CI/CD-to-cloud federation, claim restrictions, workload identity scope, and the difference between deployment and runtime permissions.
- [ ] Test cross-account/tenant boundaries using two accounts you own or are explicitly permitted to use, with synthetic objects.
- [ ] Review serverless triggers, event-source permissions, environment configuration, dependencies, and function identity.
- [ ] Assess managed database access, backup sharing, secret retrieval permissions, signed URLs, and object lifecycle.
- [ ] Correlate a permitted test action with provider audit logs. Record which actions need additional data-plane logging.
- [ ] Review provider testing policies, cost constraints, and teardown before launching vulnerable cloud training environments.

### Containers

- [ ] Images versus containers, layers, registries, tags versus digests, build contexts, runtime configuration, and image provenance.
- [ ] Linux namespaces and cgroups, root inside a container versus host authority, user namespaces, rootless operation, and capabilities.
- [ ] Privileged mode, host networking/PID sharing, writable host mounts, runtime sockets, device access, and security profiles.
- [ ] Non-root workloads, read-only filesystems where practical, minimal images, dependency patching, secret injection, and resource limits.
- [ ] Image scanning versus runtime configuration review: a clean package scan does not prove safe privileges or trustworthy code.
- [ ] Registry access, signing/verification, build secrets, sensitive layers, and reproducible deployment.

### Kubernetes

- [ ] Control-plane components, API server, etcd, kubelets, namespaces, pods, deployments, services, ingress, and network plugins.
- [ ] Authentication, RBAC roles/bindings, service accounts, workload identity, token handling, and effective permissions.
- [ ] Pod Security admission, security contexts, capabilities, host access, admission controls, and trusted image policy.
- [ ] NetworkPolicy enforcement depends on the installed network plugin; namespaces alone do not create full tenant isolation.
- [ ] Secrets storage and encryption, configuration exposure, audit policy, control-plane access, backups, and node lifecycle.
- [ ] Helm charts, operators, custom resources, controllers, and the permissions granted to installed extensions.
- [ ] Multi-tenancy assumptions, cluster-admin access paths, managed-service boundaries, and container/host isolation limitations.

Use the [Kubernetes security checklist](https://kubernetes.io/docs/concepts/security/security-checklist/) to select applicable checks and then verify their behavior in your actual cluster.

### Lab and completion check

Deploy a small application with synthetic records in a disposable cloud project or account. Draw its network and identity paths. Correct one excessive workload permission and one unintended exposure. Produce before/after evidence and audit logs. Separately, deploy a local containerized application, document its privileges, and reduce them while preserving function. Add a local Kubernetes cluster only after you understand containers.

**Ready to move on:** You can distinguish application, identity, network, and platform responsibility; explain effective access; demonstrate a cloud or container fix; and remove all billable lab resources using a checked teardown inventory.

## 17. Wireless and network appliance security

**Prerequisites:** TCP/IP, Ethernet, subnetting, routing, packet analysis, authentication, certificates, and network segmentation. Start with equipment you own and an isolated network. Radio signals can extend beyond a room; owning an access point does not authorize interacting with nearby clients.

### Knowledge and skill checklist

- [ ] Explain radio frequencies, channels, interference, signal strength, antenna behavior, and the difference between visibility and permission to test.
- [ ] Read 802.11 management, control, and data frames; understand discovery, association, authentication, roaming, and the relationship between a wireless client and the wired network.
- [ ] Compare open networks, obsolete WEP/TKIP, WPA2, WPA3, Personal versus Enterprise deployments, SAE, protected management frames, and transition-mode tradeoffs. Learn mechanisms and configuration implications rather than treating every protocol version as equivalent.
- [ ] Understand 802.1X, EAP methods, RADIUS, certificate chains, server identity validation, client certificates, enrollment, revocation, and failure behavior.
- [ ] Assess guest isolation, client isolation, management VLANs, access-point administration, onboarding, WPS exposure, captive portals, device inventory, and trusted certificate deployment.
- [ ] Identify rogue access-point and lookalike-network risks conceptually; understand how inventory, certificate validation, monitoring, and user education reduce them.
- [ ] Inspect wireless configuration exports, update policies, controller access, administrator roles, logging, and recovery procedures. Treat configuration backups as sensitive because they may contain secrets.
- [ ] Study Bluetooth Classic and BLE architecture, pairing versus bonding, GATT services, discoverability, authentication, encryption, and privacy. Use your own development peripherals for practical work.
- [ ] Understand NFC/RFID identification versus authentication and where cloning resistance, reader trust, and backend authorization differ. Keep experiments to training tags and readers.
- [ ] Review routers, switches, firewalls, VPN gateways, proxies, load balancers, DNS appliances, and storage appliances as management-plane and data-plane systems.
- [ ] Assess administrative exposure, AAA, SNMP versions, SSH/TLS configuration, unused services, firmware support, configuration drift, backup integrity, centralized logs, and time synchronization.
- [ ] Validate firewall and segmentation policy using a permitted source/destination/service matrix, including IPv6, rather than assuming an IPv4 rule protects every path.
- [ ] Understand routing-protocol authentication, DHCP protections, ARP-related controls, switch port configuration, high availability, and the operational consequences of configuration changes.

### Safe projects and evidence

1. Build a guest and trusted network on a spare router. Document intended flows, test only your clients, and show that guest access cannot reach the administration interface.
2. Compare two wireless security configurations using settings, client behavior, and your own traffic captures. Record compatibility limitations without performing disruptive radio tests.
3. Review a sample appliance configuration and produce a prioritized hardening plan with backup and rollback steps.

**Exit criteria:** Explain an enterprise wireless authentication flow, interpret your own connection capture, demonstrate segmentation with positive and negative tests, and produce reproducible configuration findings. Use [NIST WLAN guidance](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=910174) for lifecycle and monitoring foundations; it is older guidance, so supplement it with the current documentation for the exact device and wireless features you study.

## 18. Mobile application security

**Prerequisites:** Web/API testing, HTTP/TLS, programming, authentication, cryptography basics, and Linux familiarity. Learn Android first if that matches available hardware; add iOS when a supported development environment and device are available.

### Knowledge and skill checklist

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

### Safe projects and evidence

1. Build a small app that authenticates to your local API and stores a synthetic token. Diagram the complete data flow before testing.
2. Assess an intentionally vulnerable training app or your own test build. Record device/OS/app versions, tested controls, evidence, and limitations.
3. Repair one storage issue, one deep-link or IPC issue, and one backend authorization issue; retest the same scenarios.

**Exit criteria:** Produce a mobile report that distinguishes device, application, and backend findings; demonstrate both static and dynamic evidence; explain where emulator results require physical-device confirmation. Use the [OWASP MASVS/MASTG overview](https://mas.owasp.org/MASTG/0x03-Overview/) to connect security requirements with testing, and consult [Apple Platform Security](https://support.apple.com/guide/security/welcome/web) for Apple-specific protection models.

## 19. Reverse engineering, exploit development, and malware analysis

**Prerequisites:** C, memory management, operating-system internals, assembly basics, Python, debugging, and disciplined isolation. These are separate specialist skills; start with binaries you compile yourself before studying untrusted samples.

### Knowledge and skill checklist

- [ ] Understand hexadecimal, endianness, registers, instructions, addressing modes, stack frames, calling conventions, virtual memory, system calls, linking, loading, and process/thread behavior.
- [ ] Compare x86-64 and ARM64; understand PE, ELF, and Mach-O layouts, symbols, imports/exports, sections, relocations, debug information, and compiler optimizations.
- [ ] Follow control flow and data flow; label functions and structures; distinguish a decompiler's approximation from observed machine behavior.
- [ ] Use breakpoints, watchpoints, register/memory inspection, stack traces, crash dumps, and deterministic reproduction. Separate an initial symptom from its root cause.
- [ ] Recognize out-of-bounds access, stack/heap corruption, use-after-free, double-free, integer conversion mistakes, format-string problems, race conditions, and unsafe deserialization.
- [ ] Understand exploitability assessment: attacker-controlled input, reachable code, privilege boundary, confidentiality/integrity consequences, preconditions, and environmental assumptions. A crash alone does not establish code execution.
- [ ] Study mitigations conceptually: ASLR, DEP/NX, stack canaries, PIE, RELRO, control-flow integrity, sandboxing, pointer authentication, memory tagging, and memory-safe language approaches.
- [ ] Learn exploit-development vocabulary: control-flow versus data-only corruption, read/write primitives, return-to-library and return/jump-oriented code reuse, calling-convention constraints, and reliability across builds. Study these in supervised toy-binary exercises and connect each to the relevant mitigation and root-cause fix.
- [ ] Learn coverage-guided fuzzing, harness design, input corpora, structured inputs, sanitizers, time/resource limits, crash minimization, deduplication, regression testing, and coverage interpretation.
- [ ] Understand patch comparison and variant analysis as methods for identifying root causes and verifying fixes; avoid assuming every changed function is security-relevant.
- [ ] Learn symbolic execution and taint analysis concepts, constraint limitations, path explosion, and when manual reasoning is more productive.
- [ ] For malware analysis, study file triage, hashes, signatures, metadata, strings, imports, embedded resources, packing indicators, and confidence limits.
- [ ] Learn behavioral observation: process trees, file/registry changes, scheduled activity, network destinations, configuration data, and host indicators. Analyze persistence and evasion mechanisms to recognize and remediate them, without building deployment or bypass workflows.
- [ ] Understand sample provenance, evidence handling, reproducible analysis notes, false attribution risks, and why an antivirus label is not definitive identification.
- [ ] Learn isolation boundaries: snapshots, restricted networking, disabled shared folders/clipboard, no personal credentials, controlled sample storage, and a tested reset procedure. A virtual machine alone does not guarantee containment.

### Safe projects and evidence

1. Compile a small C parser with debug information, inspect it in a debugger and disassembler, then repeat with optimization enabled and explain the differences.
2. Fuzz your own parser with a sanitizer, minimize one failure, fix its root cause, and retain the input as a regression test. Record coverage and the bounded testing budget.
3. Reverse engineer a benign challenge binary and write a function-level behavioral explanation validated against execution.
4. Analyze an instructor-provided synthetic sample or sanitized trace; create an evidence-based behavioral report and a detection hypothesis. Live malware work belongs in a properly supervised specialist lab.

**Exit criteria:** Explain a crash from input to defective operation, produce a minimal nonweaponized reproducer for a toy program, implement a fix, and verify it. Distinguish observed facts, inferred behavior, and unresolved questions. Use [Ghidra's official project](https://github.com/NationalSecurityAgency/ghidra) for reverse-engineering tooling and [LLVM's libFuzzer documentation](https://www.llvm.org/docs/LibFuzzer.html) for coverage-guided fuzzing concepts and harnesses.

## 20. Detection engineering, incident response, and forensics

**Prerequisites:** Networking, Windows/Linux administration, scripting, authentication, basic cloud concepts, and evidence documentation. Offensive assessment becomes more useful when you can show what defenders could observe and how to improve response.

### Knowledge and skill checklist

- [ ] Understand logs, metrics, traces, alerts, incidents, indicators, behaviors, baselines, and threat hypotheses. Distinguish an unusual event from confirmed malicious activity.
- [ ] Collect and interpret Windows security and service logs, PowerShell telemetry, Sysmon, Linux authentication/audit/service logs, application logs, and endpoint detection events.
- [ ] Learn process identity, parent/child relationships, command lines, user/logon context, file hashes, network connections, DNS, and identity-provider events. Identify missing fields before writing detections.
- [ ] Understand network telemetry: packet capture, flow records, DNS, proxy, firewall, VPN, IDS/IPS, TLS metadata, and the limitations imposed by encryption and sensor placement.
- [ ] Learn cloud control-plane audit logs, identity sign-ins, role changes, object-storage access, network flow logs, container/Kubernetes audit events, and SaaS audit trails.
- [ ] Verify time synchronization, UTC conversion, event delay, clock skew, parsing, normalization, deduplication, retention, integrity, access controls, and dropped-event monitoring.
- [ ] Learn one SIEM query language well, then understand how its field mappings and query behavior differ from other platforms.
- [ ] Write Sigma rules with explicit log sources, fields, conditions, exclusions, severity, assumptions, references, and expected false positives. Validate the translated rule in the target backend.
- [ ] Write YARA rules for controlled file collections; learn meaningful strings or byte patterns, conditions, metadata, performance, and false-positive testing. A pattern match requires interpretation.
- [ ] Study rule lifecycle: threat hypothesis, necessary telemetry, logic, positive/negative test data, review, staging, tuning, deployment, ownership, and retirement.
- [ ] Measure precision, recall where labeled data permits, false-positive burden, detection latency, investigation effort, and known blind spots. An ATT&CK mapping does not prove comprehensive coverage.
- [ ] Practice threat hunting as a bounded hypothesis-driven investigation with a documented dataset, queries, findings, and follow-up actions.
- [ ] Learn incident preparation, triage, severity, scope determination, stakeholder roles, containment choices, eradication, recovery validation, communication, and lessons learned.
- [ ] Understand when containment can destroy volatile evidence or disrupt business; rehearse decision points with system owners before emergencies.
- [ ] Learn evidence acquisition, write protection where appropriate, chain of custody, cryptographic hashing, original versus working copies, timestamps, and reproducible analysis.
- [ ] Understand disk, memory, browser, email, endpoint, network, identity, and cloud evidence; distinguish live acquisition from offline analysis and document collection limitations.
- [ ] Build event timelines and correlate independent sources. Know that deleted records, encrypted storage, missing logs, and retention limits constrain conclusions.
- [ ] Learn threat-intelligence reliability, indicator expiry, enrichment, sharing permissions, and confidence ratings; avoid identifying an actor solely from a reused tool or IP address.

### Safe projects and evidence

1. Centralize logs from one Windows VM, one Linux VM, and a local application. Generate benign sign-ins, administration changes, and file events; confirm their arrival and timestamps.
2. Create five detection hypotheses, each with matching and nonmatching test fixtures, an investigation note, and a documented telemetry dependency.
3. Use a synthetic incident dataset to build a timeline and determine affected accounts, hosts, and data; clearly mark uncertainty.
4. Run a collaborative purple-team exercise with harmless predefined actions: agree the action, expected evidence, detection, response, and success criteria before execution.
5. Conduct a recovery tabletop covering credential rotation, restoration from a clean backup, renewed monitoring, and a retest of the original weakness.

**Exit criteria:** Demonstrate that a detection fires for intended test data and stays quiet on realistic benign data; explain at least one blind spot; deliver an incident timeline and a defensible evidence log. Consult [Microsoft Sysmon documentation](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon), [Sigma rule documentation](https://sigmahq.io/docs/basics/rules.html), and [YARA rule documentation](https://yara.readthedocs.io/en/stable/writingrules.html). Align incident-response planning with [NIST SP 800-61 Rev. 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final).

## 21. Human and physical security assessments

**Prerequisites:** Assessment scoping, privacy, reporting, authentication, and communication. This track requires explicit agreement on participants, locations, scenarios, messages, information collected, and stop conditions. Technical authorization alone does not automatically include people or buildings.

### Knowledge and skill checklist

- [ ] Understand how workflow pressure, confusing interfaces, authority cues, and weak verification processes create risk. Focus findings on systems and processes instead of blaming individuals.
- [ ] Learn approved simulation design, stakeholder review, participant safeguards, accessibility, cultural sensitivity, and measurement that supports learning.
- [ ] Assess identity verification for account recovery, help-desk changes, payment instructions, supplier changes, onboarding, and offboarding through approved tabletop scenarios.
- [ ] Understand phishing, smishing, vishing, QR-code deception, impersonation, and synthetic-media risks at a recognition and control-design level.
- [ ] Study email authentication and filtering, domain monitoring, reporting channels, phishing-resistant authentication, callback procedures, and dual approval for sensitive changes.
- [ ] Measure reporting behavior, time to escalation, clarity of verification steps, and process resilience; click rate alone is an incomplete measure.
- [ ] Learn facility risk assessment: visitor management, escorts, badge issuance/revocation, door monitoring, reception procedures, server-room access, equipment storage, and secure disposal.
- [ ] Review clean-desk policies, screen locking, unattended devices, removable-media policies, printing, document handling, and visibility of sensitive information.
- [ ] Understand physical safety, emergency egress, accessibility requirements, incident escalation, and coordination with facilities/security teams.
- [ ] Treat locks, access-control systems, surveillance, and alarms as specialist systems; practical work uses training equipment or supervised, explicitly approved evaluations.
- [ ] Learn data minimization, anonymized reporting, retention limits, debriefing, and how to communicate findings without publishing personal information.

### Safe projects and evidence

1. Design a tabletop account-recovery exercise using fictional people, accounts, and documents; evaluate identity verification and escalation.
2. Create a training message and reporting workflow in a closed training environment using synthetic identifiers. Do not collect real passwords or tokens.
3. Conduct an agreed walkthrough with a facilities owner and document process improvements without bypassing locks, tailgating, or interfering with safety systems.

**Exit criteria:** Produce a reviewed exercise plan, privacy-aware metrics, a nonpunitive debrief, and specific control improvements. Explain which actions are outside the agreed scope and when the exercise must stop. Successful learning improves verification and reporting processes, not the humiliation of participants.

## 22. Advanced specialization map

These tracks extend the core curriculum. Choose one or two for deep practice; maintain conceptual awareness of the others. Each track requires ongoing study because platforms, threat models, and techniques change.

### 22.1 AI, LLM, RAG, and agent security

**Prerequisites:** Web/API security, Python, identity, data pipelines, and basic machine learning.

- [ ] Learn model training versus inference, tokens, context windows, embeddings, vector stores, retrieval-augmented generation, tools, agents, memory, and evaluation datasets.
- [ ] Trace trust boundaries across user input, documents, retrieved content, tool responses, system instructions, identities, and external actions.
- [ ] Study direct/indirect prompt injection, sensitive-data exposure, excessive permissions, unsafe output handling, poisoned retrieval data, supply-chain risks, resource exhaustion, and incorrect claims.
- [ ] Test tenant isolation, retrieval authorization, document provenance, connector scopes, secret handling, tool argument validation, action approvals, memory retention, and auditability.
- [ ] Understand model limitations and non-determinism; maintain repeatable evaluation cases and measure both security failures and legitimate-task success.

**Project:** Build a local assistant over synthetic documents with mock tools. Evaluate whether untrusted document content can cause unauthorized actions, then enforce boundaries outside the model and retest. **Pass:** Demonstrate tenant separation, limited tool permissions, traceable actions, and a regression suite. Use the [OWASP GenAI Security Project](https://genai.owasp.org/) for its evolving application and agent guidance.

### 22.2 IoT, embedded systems, and hardware

**Prerequisites:** C, Linux, networking, electronics fundamentals, and safe handling of low-voltage equipment.

- [ ] Study microcontrollers, SoCs, bootloaders, memory maps, embedded operating systems, firmware formats, UART/JTAG/SWD concepts, SPI/I2C, and debug-interface exposure.
- [ ] Review firmware provenance, signing, secure/measured boot, rollback protection, update recovery, device identity, key provisioning, secure storage, and end-of-support behavior.
- [ ] Assess companion apps, local services, device-to-cloud authorization, MQTT/CoAP concepts, fleet management, reset behavior, and disposal.
- [ ] Understand SBOMs, third-party components, manufacturing trust, physical access assumptions, and side-channel/fault-injection concepts as advanced research areas.

**Project:** Review firmware for an owned development board or emulator and threat-model its update path. **Pass:** Produce an interface inventory, reproducible findings, and a verified update/recovery design without interacting with deployed third-party devices.

### 22.3 OT, ICS, and cyber-physical systems

**Prerequisites:** Networking, defensive monitoring, industrial-process basics, and safety engineering awareness.

- [ ] Learn PLCs, HMIs, historians, engineering workstations, safety systems, zones/conduits, and industrial protocol trust assumptions.
- [ ] Understand availability, deterministic timing, equipment lifecycles, maintenance windows, vendor dependencies, and the difference between cyber impact and physical consequences.
- [ ] Study asset inventory, passive visibility, remote-access governance, segmentation, backup/recovery, change control, and incident coordination with operators.

**Project:** Use a simulator with an entirely fictional process to review architecture and monitor benign traffic. **Pass:** Explain hazards and stop conditions and propose controls that respect operational requirements. Use [NIST OT security guidance](https://csrc.nist.gov/pubs/sp/800/82/r3/final) and [CISA ICS recommended practices](https://www.cisa.gov/resources-tools/resources/ics-recommended-practices). Never substitute a production controller for a training simulator.

### 22.4 Telecom and radio-frequency security

**Prerequisites:** Networking, authentication, signal basics, and the applicable authorization rules for your location.

- [ ] Learn cellular architecture, SIM/eSIM identity, roaming, signaling trust, VoIP/SIP/RTP, software-defined radio concepts, modulation, and spectrum boundaries.
- [ ] Study protocol threat models, privacy implications, lawful test arrangements, and emergency-service dependencies.

**Project:** Analyze supplied recordings or a fully simulated protocol exchange; any radio transmission requires the appropriate approved environment. **Pass:** Explain trust boundaries and monitoring controls without interacting with public carrier infrastructure or third-party communications.

### 22.5 Browser, kernel, and virtualization research

**Prerequisites:** Advanced operating systems, C/C++, assembly, debugging, fuzzing, and mitigation knowledge.

- [ ] Study browser process models, sandboxing, JavaScript engines, JIT compilation, extension permissions, IPC, and origin isolation.
- [ ] Study kernel interfaces, drivers, memory ownership, synchronization, device interfaces, hypervisors, virtual devices, and guest/host boundaries.
- [ ] Learn harness engineering, reproducibility, root-cause analysis, patch verification, coordinated disclosure, and careful management of untrusted inputs.

**Project:** Fuzz a small open-source parser or toy interface in a disposable local environment. **Pass:** Deliver a minimized bug report, patch or mitigation analysis, and regression evidence. Advance to complex targets only after demonstrating reliable isolation and debugging.

### 22.6 Blockchain and smart-contract security

**Prerequisites:** Programming, cryptography concepts, distributed systems, and transaction semantics.

- [ ] Learn accounts, keys, signatures, transactions, gas, contract execution, events, storage, oracles, and upgrade/proxy models.
- [ ] Study access control, reentrancy, arithmetic/rounding, signature replay, initialization, oracle assumptions, front-running concepts, economic invariants, and privileged administration.
- [ ] Learn unit, property, invariant, and fuzz testing; distinguish code correctness from protocol-economic assumptions.

**Project:** Audit a toy contract on a local development chain or designated testnet with valueless assets. **Pass:** State invariants, reproduce a controlled failure, repair it, and verify the invariant. Consult [Solidity security considerations](https://docs.solidity.org/en/latest/security-considerations.html); do not use mainnet funds as learning material.

### 22.7 Desktop clients, macOS, privacy, and architecture

**Prerequisites:** Operating systems, programming, authentication, and threat modeling.

- [ ] Review thick-client local storage, IPC, installer privileges, auto-update integrity, backend authorization, embedded browsers, Electron trust boundaries, and unsafe local file handling.
- [ ] For macOS, learn app signing, notarization, Gatekeeper, TCC permissions, sandboxing, entitlements, Keychain, XPC, launch services, and endpoint telemetry.
- [ ] Study security architecture: trust boundaries, least privilege, defense in depth, fail-safe behavior, resilience, secure defaults, tenant isolation, and dependencies.
- [ ] Study privacy engineering: data inventory, purpose limitation, minimization, retention, deletion, re-identification risks, consent boundaries, and privacy threat modeling.
- [ ] Explore cryptographic protocol review, HSM/TPM design, key lifecycle, post-quantum migration planning, and side-channel resistance as separate advanced tracks requiring deeper mathematics and specialist review.

**Project:** Threat-model a small desktop application and its update service, then review its data lifecycle. **Pass:** Connect each significant risk to a design decision, validation evidence, an owner, and a practical remediation plan.

### 22.8 Adversary emulation and red/purple-team planning

**Prerequisites:** Independent assessment/reporting skills, enterprise or cloud identity, detection engineering, and experience working under formal rules of engagement.

- [ ] Choose a business-relevant threat scenario using credible threat information; explain why its objective and assumptions fit the organization's environment.
- [ ] Map the scenario to observable behaviors using [MITRE ATT&CK](https://attack.mitre.org/). Select a small justified set; a technique checklist alone is not an exercise objective.
- [ ] Define the starting access, allowed identities/assets, synthetic objective, permitted transitions, stop conditions, and safe substitutes for actions that would otherwise expose data or disrupt operations.
- [ ] Create an exercise plan with action owners, expected telemetry, prerequisites, evaluation criteria, rollback, and a control-team contact able to stop the exercise.
- [ ] Learn the distinction between a transparent purple-team exercise and a controlled exercise with limited defender foreknowledge. Agree the visibility model in advance.
- [ ] Study command-and-control, persistence, collection, and exfiltration as behavior and telemetry categories. Use harmless simulations and synthetic data where these categories matter to the approved objective.
- [ ] Correlate the action timeline with alerts, triage, escalation, and response. Measure time and quality of detection, evidence availability, decision-making, and containment.
- [ ] Debrief collaboratively, identify root causes for missed signals, assign improvements, repeat relevant tests, and verify complete cleanup.

**Project:** Design a three-action simulation in your own monitored lab, using harmless test events and a synthetic objective. **Pass:** Produce the approved exercise plan, action/evidence timeline, measured detection results, improvement backlog, and verified cleanup. Start with transparent collaboration before pursuing more complex operational exercises.

## 23. Reporting, remediation, and retesting

**Priority:** Core. Begin this section with your first lab, not at the end of your studies.

### Evidence and reasoning

- [ ] Keep timestamps and time zones, target identifiers, test account roles, prerequisites, tool versions, relevant requests/responses, and host or application logs.
- [ ] Capture enough evidence for another authorized tester to reproduce the observation. A screenshot alone often misses identity, context, or the action that caused the result.
- [ ] Redact secrets and personal data while preserving the parts needed to assess the finding. Store unredacted evidence only when needed and under the agreed controls.
- [ ] Distinguish observed impact, reasonably supported potential impact, and untested speculation. Explain assumptions explicitly.
- [ ] Identify the root cause: missing authorization, excessive privilege, unsafe parsing, exposed secret, weak lifecycle control, or another specific failure.
- [ ] Use CWE and applicable testing/verification references when helpful. Include the standard version so future readers can understand the mapping.
- [ ] Rate severity using the agreed method. Explain business consequences and affected scope alongside technical scores.
- [ ] Preserve negative results and test limitations. State what you could not test because of access, time, safety, or environment differences.

### A useful assessment report

1. **Executive summary:** Objective, tested environment, main risks, strengths, and the most important corrective actions in plain language.
2. **Scope and constraints:** Assets, dates, perspectives, accounts, exclusions, dependencies, and material limitations.
3. **Methodology and coverage:** Applicable tests, depth, tools where relevant, and what remained untested.
4. **Findings overview:** IDs, titles, severity, affected systems, owners, and status.
5. **Detailed findings:** Expected behavior, actual behavior, prerequisites, minimal reproduction, evidence, impact, cause, and remediation.
6. **Remediation plan:** Immediate containment, durable fixes, systemic improvements, owners, priorities, and dependencies.
7. **Retest results:** What changed, exact evidence, remaining variants, and final status.
8. **Appendices:** Sanitized inventory, coverage matrix, terminology, and supporting technical details.

### Remediation that developers and administrators can use

- [ ] Explain where the control belongs. For example, object authorization belongs on the server for each relevant operation, not only in the interface.
- [ ] Recommend a specific class of fix that addresses the cause, and explain any compatibility or operational tradeoff.
- [ ] Distinguish a temporary mitigation from a durable change. Specify remaining exposure and a follow-up owner.
- [ ] Look for repeated patterns across endpoints, repositories, identities, or environments. One missing authorization check may indicate a shared architectural problem.
- [ ] Add a regression test that fails before the fix and passes after it, plus a control proving legitimate behavior still works.
- [ ] Retest adjacent variants: another role, record owner, HTTP method, API version, tenant, deployment, or authentication flow as appropriate.
- [ ] Use meaningful statuses: open, partially remediated, remediated and verified, risk accepted by owner, or not retested. A developer saying fixed is not verification.
- [ ] Confirm removal of test accounts, temporary files, certificates, access rules, and synthetic data according to the cleanup agreement.

### Communication skills

- [ ] Explain the same finding to an engineer in technical terms and to a business owner in terms of affected operations and data.
- [ ] Ask precise clarification questions, give a reproducible example, and respond to disagreement with evidence.
- [ ] Escalate an urgent finding through the agreed channel while preserving a written record.
- [ ] Learn clear status updates, handover notes, meeting preparation, time estimation, and respectful peer review.
- [ ] Understand assessment quality assurance: a second reviewer checks reproducibility, scope, severity, redaction, and whether the fix addresses the cause.

**Practice:** Write a report containing three real lab findings, one rejected false positive, a coverage matrix, an executive summary, and a retest appendix. Ask someone to reproduce one finding using only your report.

**Ready to move on:** Your report lets an owner understand the problem, an engineer fix it, and another tester verify the result without guessing.

## 24. Capstones, portfolio, and career direction

### Project ladder

Complete the first four projects, then one project aligned with your primary track. These are recommended practice targets, not industry certification requirements.

| Project | Build and assess | Evidence to produce | Pass condition |
| --- | --- | --- | --- |
| 1. Small network | Two owned systems and a local service; configure routing/firewalls and troubleshoot one deliberate fault. | Diagram, inventory, packet capture commentary, before/after rules. | Explain the full request path and why the broken case failed. |
| 2. Secure application | Small CRUD app with accounts, roles, database, uploads or another sensitive workflow. | Threat model, access matrix, three security test cases, fixes and regression tests. | Unauthorized cases fail while legitimate operations work. |
| 3. Host review | Linux and Windows configuration assessments. | Service/permission inventory, prioritized findings, hardening changes and logs. | Demonstrate the corrected boundary and successful normal administration. |
| 4. End-to-end assessment | An unfamiliar training environment with a defined scope and time limit. | Rules of engagement, activity log, coverage matrix, report, cleanup record. | Another person can follow the evidence and distinguish confirmed findings from uncertainty. |
| 5A. Web/API track | Multi-user or multi-tenant app with sessions and an API. | Role/tenant matrix, business-logic analysis, manual tests and automated regressions. | Verify object, function, and workflow boundaries across more than one endpoint. |
| 5B. Enterprise track | Isolated AD environment with ordinary and delegated identities. | Identity graph, two validated lab weaknesses, corrections and detection evidence. | Remove the unsafe permission paths while preserving intended administration. |
| 5C. Cloud track | Disposable cloud app with workload identity and storage. | Architecture/IAM review, least-privilege changes, audit evidence, teardown. | Prove permitted and denied actions and verify resource cleanup. |
| 5D. Mobile track | Owned training app plus its test backend. | Storage/network/IPC analysis, API boundary tests, fixes. | Explain client and server responsibilities with reproducible evidence. |
| 5E. Research track | Small parser or toy binary you compile. | Crash reproduction, root-cause analysis, patch, regression corpus. | Explain the defect without claiming more impact than you established. |
| 5F. Purple-team track | Controlled activity against a monitored lab. | Hypothesis, telemetry map, detection logic, false-positive evaluation, response note. | Detect the exercise reliably and document visibility gaps. |

### Build a portfolio with substance

- [ ] Publish sanitized lab reports, a small useful automation tool, a threat model, and at least one fix with its regression test.
- [ ] Include setup, dependencies, limitations, reproducibility steps, and what you learned. State when a result came from a guided exercise.
- [ ] Show reasoning: the initial hypothesis, observations, rejected explanations, final root cause, and verified remediation.
- [ ] Keep challenge write-ups consistent with the platform's publication rules. Do not publish active exam content or client findings without permission.
- [ ] Prefer a few clear artifacts over a large collection of copied tool outputs. Maintain your work so another learner can actually run it.
- [ ] Practice a five-minute explanation of one project and a deeper technical walkthrough of a second.

### Select a direction

| Direction | Deepest subjects | Typical work sample |
| --- | --- | --- |
| Web/API penetration tester | 11–13, authentication, reporting | Application assessment and verified fixes. |
| Infrastructure/internal tester | 04–06, 09–10, 14–15 | Network/host/identity assessment with clear access reasoning. |
| Application security engineer | 07–08, 11–13, architecture | Secure design review, code change, pipeline control and regression tests. |
| Cloud security assessor | 12–13, 15–16, cloud logging | IAM/network review with deployment and audit evidence. |
| Detection or purple-team practitioner | 09, 14–16, 20, 23 | Measured detection exercise and response improvement. |
| Mobile/embedded/research specialist | 18–19 or selected 22 topics | Focused technical research with reproducible validation. |

Security operations, IT support, system administration, networking, QA, and software development can also provide relevant experience. Read actual role descriptions and map your evidence to the work required. The [NIST NICE Framework](https://www.nist.gov/itl/applied-cybersecurity/nice/nice-framework-resource-center) provides a vocabulary for describing cybersecurity tasks and capabilities.

### Optional credentials

Credentials can structure study or satisfy a particular employer's requirements. They do not replace the ability to assess, explain, and report. Choose after completing foundational labs and reviewing current job requirements in your target market.

- **Early practical assessment:** Compare [INE eJPT](https://ine.com/security/certifications/ejpt-certification) with your present networking, host, and web skills.
- **Broader practical development:** Compare relevant [HTB Academy paths and certifications](https://academy.hackthebox.com/) or [OffSec PEN-200](https://www.offsec.com/courses/pen-200/) with your desired role and available study time.
- **Specialization:** Consider a web, cloud, mobile, defensive, or research credential only when the subject matches work you want to do.

Before paying, verify the current syllabus, prerequisites, total access cost, exam format, allowed tools, reporting expectations, retake terms, renewal rules, and accessibility requirements. Prices and course names can change. Completing every certificate is not a prerequisite for employment.

### Bug bounty as a separate practice route

- [ ] Start with training labs and report writing. Bug bounty work is open-ended research and has no guaranteed payout.
- [ ] Read one program's current policy thoroughly; document exact scope and permitted behavior before testing.
- [ ] Learn duplicate handling, impact expectations, disclosure timelines, triage communication, and remediation verification.
- [ ] Prefer deep understanding of one application and its workflows to indiscriminate automation across many targets.
- [ ] Track time, useful learning, report quality, and confirmed results. A bounty total is not a complete measure of skill.

## 25. Study schedules and readiness checks

### A realistic time budget

The following **900-hour planning example** covers foundational ability, broad core exposure, and one initial specialization. It is an estimate created for this roadmap, not a guarantee of mastery or employment. Extensive specialist research, repeated failed labs, and learning basic programming from scratch can require substantially more time.

| Phase | Focus | Suggested hours | Evidence required before moving on |
| --- | --- | ---: | --- |
| A | Authorization, lab, computing foundations: 01–03 | 40 | Scope document, recoverable lab, basic troubleshooting. |
| B | Networking and OS administration: 04–06 | 150 | Network diagram, packet analysis, Linux/Windows configuration labs. |
| C | Programming and security principles: 07–08 | 130 | Tested scripts, small app, authentication/crypto explanations. |
| D | Assessment process and research: 09–10 | 70 | Inventory, coverage matrix, correctly triaged findings. |
| E | Web, API, and code review: 11–13 | 180 | Independent application assessment and verified fixes. |
| F | Hosts and enterprise identity: 14–15 | 100 | Host review and a small identity assessment. |
| G | Cloud and container basics: 16 | 60 | Deployment, permissions review, logs, teardown. |
| H | Detection/reporting/capstones: 20, 23–24 | 90 | End-to-end report, retest, monitored lab exercise. |
| I | One selected specialization: 17–19, 21–22, or deeper core | 80 | One focused project and a plan for further depth. |
| **Total** | **Core plus initial specialization** | **900** | **Evidence-based review of strengths and remaining gaps.** |

Reporting and defensive visibility should be practiced throughout; their hours above include focused consolidation and capstones. The 80-hour specialist block is an introduction, especially for exploit research, embedded systems, or industrial security.

| Sustainable study time | Approximate time for 900 focused hours |
| --- | --- |
| 5 hours/week | 180 weeks, about 3.5 years. |
| 10 hours/week | 90 weeks, about 21 months. |
| 15 hours/week | 60 weeks, about 14 months. |
| 20 hours/week | 45 weeks, about 10–11 months. |

Allow extra calendar time for breaks, work, exams, and revisiting gaps. Someone with strong IT or development experience may demonstrate existing competencies and shorten the route.

### Weekly routine: example for 10 hours

- **2 hours:** Read or watch one tightly scoped topic and make retrieval questions.
- **4 hours:** Build and test it in a lab; reserve part of this time for troubleshooting.
- **2 hours:** Write findings, implement a fix, and retest.
- **1 hour:** Review previous topics without notes or repeat a weak exercise.
- **1 hour:** Review official documentation, update the tracker, and plan the next week.

Every fourth week, substitute an unfamiliar integrated exercise for some new material. If you used a walkthrough, repeat the exercise later without it and change one condition so you must reason again.

### Your first 30 days

| Week | Focus | Concrete output |
| --- | --- | --- |
| 1 | Read 00–02; set up one Linux VM or hosted lab; practice files, terminals, and help pages. | Lab inventory, scope statement, backup/restore evidence, study log. |
| 2 | Start 04; learn addresses, subnets, DNS, ports, TCP, and the browser request path. | Annotated diagram and a capture of your own harmless HTTP/DNS activity. |
| 3 | Start 05–06; users, permissions, processes, services, logs, and basic administration. | Two short configuration labs with before/after observations. |
| 4 | Start 07; Python basics, Git, structured data, simple tests, and input handling. | A small log parser or inventory script with a README and error cases. |

This month starts the foundations; it does not finish them. Continue according to the phase exit criteria rather than rushing to an arbitrary calendar date.

### Assessment questions

Before advancing from the core, demonstrate that you can:

- [ ] Explain a browser request from DNS through TLS, HTTP, application logic, and database access.
- [ ] Troubleshoot a routing, DNS, service, or permission problem without assuming it is a vulnerability.
- [ ] Use Linux and Windows terminals, inspect logs, and determine effective permissions.
- [ ] Write and debug a short script that handles errors, structured data, and secrets responsibly.
- [ ] Explain authentication, authorization, sessions, encryption, hashing, signatures, and key management.
- [ ] Scope an assessment and identify third-party or excluded systems.
- [ ] Distinguish discovery, suspicion, confirmed weakness, and demonstrated impact.
- [ ] Manually verify application access controls with multiple synthetic users and roles.
- [ ] Explain a host or identity access path and repair its underlying permission issue.
- [ ] Read basic cloud permissions and identify a workload's identity and accessible resources.
- [ ] Connect an approved test action to logs and explain a missing signal.
- [ ] Write a reproducible finding and verify remediation with positive and negative cases.
- [ ] Complete an unfamiliar scoped lab with a useful report and cleanup record.
- [ ] State the limits of your knowledge and identify what additional evidence or expertise you need.

For a junior role, aim for independent core work with review from a more experienced practitioner. Advanced domains require mentorship and repeated practice; do not imply expert ability because you completed a topic list.

### Common mistakes and corrections

| Mistake | Better practice |
| --- | --- |
| Collecting tools before understanding systems | Learn the protocol and produce one manual observation first. |
| Copying walkthrough commands | Explain each action, vary the environment, and repeat unaided later. |
| Treating scanner results as final findings | Verify prerequisites, compare control cases, and preserve uncertainty. |
| Studying only popular web vulnerabilities | Include authorization, identity lifecycle, business logic, deployment, and reporting. |
| Trying every specialization at once | Complete the common core and choose one primary track. |
| Chasing certificates without artifacts | Produce reports, code, fixes, and retest evidence alongside study. |
| Ignoring defensive visibility | Identify the logs and controls that should show each exercise. |
| Publishing secrets in learning notes | Use synthetic data, inspect repository history, and review before publishing. |
| Learning exploit behavior without remediation | Repair the cause and test the secure behavior before finishing the lab. |
| Assuming a CTF flag proves professional readiness | Add scope management, false-positive handling, business impact, and a complete report. |

### Keep the roadmap current

Each month, revisit one weak foundation and one current vendor advisory relevant to your track. Each quarter, review official project documentation, replace stale links in your notes, update your lab images, and perform an unfamiliar capstone. Keep a changelog of new concepts and what they change in your testing method.

## 26. Tools and learning resources

Choose tools to answer a defined question. Start with the operating system's utilities, a browser, Wireshark, one web proxy, Python, and Git. Add specialized tools when their prerequisites appear in your roadmap. For every run, record the version, scope, settings, time, observations, limitations, and verification. Tool output becomes evidence only after you interpret and validate it.

### Tool-role matrix

The examples below are alternatives or additions by task, not a requirement to install everything. Use lab targets and the controls specified in the authorization and lab sections.

| Category and examples | Purpose | Knowledge required first | Evidence to produce |
|---|---|---|---|
| Network CLI: `ip`/`ipconfig`, `ss`, DNS clients, `curl` | Diagnose addressing, listeners, resolution, and HTTP connectivity. | IP addressing, routing, DNS, sockets, HTTP. | A justified diagnosis supported by relevant configuration and response fields. |
| Packet analysis: [Wireshark](https://www.wireshark.org/docs/), tcpdump | Explain observed protocol exchanges. | Encapsulation, protocol fields, capture position, filtering. | Annotated lab capture showing a connection and its boundaries. |
| Service inventory: [Nmap](https://nmap.org/book/man.html) | Identify reachable services inside an explicit target scope. | TCP/UDP behavior, filtering, timing, service identification limits. | Scoped inventory with uncertain results and manual confirmation. |
| Browser developer tools | Inspect requests, DOM changes, storage, scripts, and errors. | HTTP, JavaScript, origins, sessions. | A minimal request/response or execution trace supporting a finding. |
| Intercepting proxy: Burp Suite or [ZAP](https://www.zaproxy.org/docs/) | Examine and repeat authorized web requests. | TLS interception, HTTP semantics, application sessions. | Sanitized before/after requests with a reproducible behavioral difference. |
| Vulnerability scanner: [Greenbone Community Edition](https://greenbone.github.io/docs/latest/) | Compare system exposure with vulnerability checks. | Asset identity, authenticated checks, scan impact, false positives. | Validated findings; include scan coverage, feed dates, and limitations. |
| Automation: Python and Git | Parse evidence, check configurations, maintain repeatable scripts. | Programming, input validation, error handling, version control. | Reviewed code, sample inputs, bounded execution, and meaningful tests. |
| Linux inspection: journal, process, file, and permission utilities | Explain host state and configuration. | Services, credentials, filesystems, logs. | A timeline or access explanation tied to actual host observations. |
| Windows inspection: [Sysinternals](https://learn.microsoft.com/en-us/sysinternals/) | Inspect processes, handles, startup entries, and system activity. | Windows processes, tokens, registry, services. | An annotated process or event trace with relevant context. |
| Identity graph analysis: [BloodHound](https://bloodhound.specterops.io/) | Explore relationships and potential privilege paths in your test directory. | AD/cloud identity, ACLs, groups, delegation. | A path whose prerequisites and permissions you independently validate. Limit collection scope and protect directory exports. |
| Password auditing: [hashcat](https://hashcat.net/hashcat/) or [John the Ripper](https://www.openwall.com/john/) | Study password-storage resistance using synthetic, explicitly authorized lab hashes only. | Hash formats, salts, key derivation, resource limits. | A controlled comparison and storage recommendations; keep recovered test values private. |
| Controlled vulnerability validation: [Metasploit](https://docs.rapid7.com/metasploit/) | Understand a known vulnerability's conditions in an isolated lab using approved modules. | Protocol, vulnerability mechanics, module behavior, cleanup. | Preconditions, observed effect, relevant logs, and confirmed restoration. |
| HTTP fuzzing: [ffuf](https://github.com/ffuf/ffuf) | Explore response differences on a purpose-built application you own. | HTTP, input boundaries, response baselines, throttling. | A small reproducible test case; explain noise and false positives. |
| Reverse engineering: [Ghidra](https://github.com/NationalSecurityAgency/ghidra), debugger | Understand a self-written or licensed training binary. | C, assembly basics, memory, executable formats. | Annotated control/data flow and a defensible interpretation. |
| Mobile assessment: [MobSF](https://mobsf.github.io/Mobile-Security-Framework-MobSF/), [adb](https://developer.android.com/tools/adb) | Inspect your training application and emulator behavior. | Android architecture, manifests, permissions, app storage. | Manually verified static observations and relevant runtime evidence. |
| Cloud and infrastructure: provider CLI, IaC inspection | Inventory your sandbox and review configuration changes. | Cloud IAM, account boundaries, billing, state files. | Resource/policy inventory and reviewed configuration differences; protect secrets in state. |
| Container orchestration: [kubectl](https://kubernetes.io/docs/reference/kubectl/) | Inspect your local cluster's workloads and permissions. | Kubernetes objects, contexts, RBAC, networking. | A scoped workload/permission assessment with the selected context recorded. |
| Log detections: [Sigma](https://sigmahq.io/docs/), native log queries | Express and test suspicious-event detection. | Log schemas, event sources, time, backend query behavior. | Positive/negative test events, matching results, and false-positive notes. |
| File/content rules: [YARA](https://virustotal.github.io/yara/) | Match patterns in harmless test files or approved samples. | File formats, strings/bytes, rule conditions. | Test corpus, expected matches, misses, and collision analysis. |

### Learning resources by starting level

**Starting from basic computer use — free resources:** Work through [OverTheWire Bandit](https://overthewire.org/wargames/bandit/) after learning terminal navigation and SSH. Use its authorized game environment and document the Linux concept behind each solution. Revisit the official Python, Microsoft, and MDN references linked in the foundations sections when a prerequisite is missing.

**Learning web security — free resources:** [PortSwigger Web Security Academy](https://portswigger.net/web-security) provides structured explanations and interactive labs. Pair a topic with a request trace, a written explanation, and remediation. Progress from guided exercises to exercises where the vulnerability category is not announced.

**Running your own application lab — free/open-source projects:** Use [OWASP WebGoat](https://owasp.org/projects/webgoat) for guided vulnerability lessons and [OWASP Juice Shop](https://owasp.org/projects/juice-shop) for broader application challenges. Run deliberately vulnerable applications locally with isolation and restore procedures. Do not expose them on public cloud interfaces or a shared network.

**Building deeper systems skills — free learning:** [pwn.college](https://pwn.college/) offers hands-on material for computing and security foundations through deeper systems topics. Match modules to your current prerequisites; advanced binary exercises should follow C, memory, and debugging practice.

**Wanting a guided general curriculum — mixed access:** [TryHackMe](https://tryhackme.com/) and [Hack The Box Academy](https://academy.hackthebox.com/) provide structured training with differing access arrangements. Inspect the current syllabus and free material first. Choose one path that fills a demonstrated skill gap; confirm current access terms before paying.

### How to consume resources without getting stuck collecting them

1. Select one roadmap topic and its exit gate.
2. Read one explanation and the relevant official reference.
3. Complete one guided lab, noting why each action matters.
4. Repeat independently, then change one assumption or configuration.
5. Explain the result, remediation, and detection evidence in your own words.
6. Revisit after a delay; move on when you can reproduce and explain it.

Use hints progressively. After reading a full solution, rebuild the exercise later without it. Keep a small backlog of missing prerequisites instead of continually switching courses.

### Download provenance and maintenance

- [ ] Obtain tools from the official project/vendor or a trusted distribution repository; follow official links to release artifacts.
- [ ] Check release notes, supported platforms, signatures/checksums where provided, and signing-key provenance. A matching checksum alone does not establish a trustworthy publisher.
- [ ] Inspect installation scripts and requested privileges; isolate unfamiliar software and use test credentials.
- [ ] Record versions and dependency changes so exercises are reproducible. Avoid random repackaged bundles, credential-stealing imitations, and blindly pasted installation commands.
- [ ] Treat extensions, templates, community modules, and scanner rules as executable or security-relevant dependencies requiring their own review.

**Exit gate:** Select the smallest suitable toolset, explain what each tool can and cannot establish, and turn its output into a verified finding or a documented negative result.

## 27. Reusable templates and glossary

### Learning note template

```markdown
# Topic / exercise title

Date and time zone:
Roadmap section:
Objective and prerequisite:
Authorized lab assets:
Software versions and snapshot:

## Normal behavior
What should happen, and which security boundary should hold?

## Hypothesis and test
What observation would support or disprove the hypothesis?
Actions, inputs, expected result, rate/resource limits, stop condition.

## Evidence and interpretation
Sanitized requests, output, logs, timestamps, and artifact locations.
Observed facts:
Alternative explanations:
Uncertainty and untested conditions:

## Fix and retest
Root cause:
Change made:
Negative test (unauthorized behavior is blocked):
Positive test (legitimate behavior still works):
Remaining variants:

## Cleanup and reflection
Restored/removed artifacts:
Mistakes and lessons:
Next independent exercise:
Current skill level (0–4):
```

### Scope and rules-of-engagement template

```markdown
# Assessment scope

Owner and written authorization reference:
Objective and success criteria:
Dates, time zone, and approved testing windows:
In-scope assets and exact identifiers:
Excluded assets and third-party dependencies:
Test accounts, roles, tenants, and synthetic data:
Permitted methods and source systems:
Rate/resource limits and prohibited actions:
Disruptive/special activities requiring separate agreement:
Stop conditions, emergency contact, and escalation channel:
Backup, restoration, and change owners:
Evidence storage, access, retention, and deletion:
Report recipients and delivery method:
Cleanup and retest responsibilities:
Publication/disclosure terms:
```

### Finding template

```markdown
# FIND-001: Precise title describing the failed control

Status and severity:
Affected assets / versions / endpoints:
Affected identities or roles:
First observed and last verified:
Confidence and prerequisites:

## Summary and root cause
Expected behavior:
Observed behavior:
Underlying cause:

## Minimal reproduction
1. Establish the documented lab/test state.
2. Perform the minimum agreed test action.
3. Compare actual behavior with the control case.

## Evidence
Sanitized artifacts, timestamps, and references.

## Impact and severity reasoning
Demonstrated impact:
Potential impact and assumptions:
CVSS version/vector if required:
Business context and affected scope:

## Remediation
Immediate mitigation:
Durable fix:
Owner and dependencies:
Regression tests and related areas to review:

## Retest
Date and environment:
Change reviewed:
Positive/negative test results:
Remaining issues and final status:
```

### Example of a precise lab finding

**Title:** Ordinary users can read another user's synthetic invoice because the API omits an ownership check.

**Expected:** User A can read invoices assigned to A. User B cannot read A's invoices.

**Observed:** In the owned training application, B's authenticated session received A's synthetic invoice when requesting that record. Both users had the same ordinary role; the test did not use an administrator account.

**Evidence:** Record the two test identities, the invoice's expected owner, a sanitized request/response, and the corresponding server log. Retrieve only the synthetic test record needed to establish the failure.

**Cause and fix:** Authentication was present, but the server did not enforce record ownership for the read operation. Apply an ownership or explicit shared-access rule at the server's data-access boundary.

**Retest:** A still reads A's record; B is denied A's record; B still reads B's record; an unauthenticated request is denied; list/search/export paths obey the same rule. Record what was tested rather than claiming every possible path is fixed.

### Coverage and progress templates

| Test ID | Asset / feature | Role / perspective | Expected boundary | Result | Evidence / limitation |
| --- | --- | --- | --- | --- | --- |
| AUTHZ-01 | Synthetic invoice read | Ordinary user B | Cannot read A's private record | Not started | — |
| AUTHZ-02 | Synthetic invoice read | Record owner A | Can read own record | Not started | — |

| Topic | Target level | Current level | Evidence | Last practiced | Next action |
| --- | ---: | ---: | --- | --- | --- |
| DNS troubleshooting | 3 | 0 | — | — | Explain resolution, then diagnose a local fault. |
| Object authorization | 3 | 0 | — | — | Build a two-user ownership matrix. |
| Kernel research | 1 initially | 0 | — | — | Explain user/kernel boundaries before deeper study. |

### Command and interface vocabulary to practice

Learn what each command accepts, what it changes, how failure is reported, and how to get help. These are study prompts; adapt syntax to your installed OS and version.

- **Linux navigation and text:** `pwd`, `ls`, `cd`, `file`, `stat`, `less`, `head`, `tail`, `find`, `rg`/`grep`, `sort`, `uniq`, `cut`, `awk`, `sed`, and `diff`.
- **Linux administration:** `id`, `groups`, `chmod`, `chown`, `getfacl`, `ps`, `top`, `systemctl`, `journalctl`, `ip`, `ss`, and your distribution's package manager.
- **Windows/PowerShell:** `Get-Help`, `Get-Command`, `Get-ChildItem`, `Get-Content`, `Get-Process`, `Get-Service`, `Get-WinEvent`, `Get-Acl`, `Get-NetIPConfiguration`, `Get-NetTCPConnection`, and `Resolve-DnsName`.
- **Network/application observation:** `curl`, a DNS query client, Wireshark display filters, browser Network/Storage/Console panels, and a proxy's request editor.
- **Development:** `git status`, `git diff`, `git log`, Python virtual environments, debugger controls, your language's test runner, and structured log queries.

Practice reads and observation first; learn the scope and rollback of commands that modify permissions, services, files, accounts, or networking.

### Glossary

| Term | Meaning in this roadmap |
| --- | --- |
| Asset | A system, application, identity, data store, or other resource being protected or assessed. |
| Attack surface | The reachable interfaces and interactions through which a system can be influenced. |
| Trust boundary | A point where identity, privilege, ownership, or confidence in data changes. |
| Threat model | A structured explanation of valuable assets, potential adversaries, failure scenarios, and controls. |
| Authentication / authorization | Establishing an identity / deciding what that identity may do. |
| Session | State associating a sequence of interactions with an authenticated or otherwise identified client. |
| Principal / service account | An identity that can receive permissions / an identity used by a workload or service. |
| Least privilege | Granting only the access needed for the intended task. |
| RBAC / ABAC | Access decisions based on roles / attributes and conditions. |
| ACL | Access-control list specifying permissions for an object. |
| Tenant | A separately managed customer or organizational security context in a shared service. |
| Vulnerability / exploit | A security weakness / a method that takes advantage of a weakness. |
| Proof of concept | A limited demonstration of a behavior or security failure under stated conditions. |
| CWE / CVE | A weakness classification / an identifier for a specific disclosed vulnerability. |
| CVSS / EPSS | A severity scoring system / an estimate of exploitation probability over its defined horizon. |
| False positive / false negative | A reported problem that is not present / a real problem the method misses. |
| IOC / behavior | An observable indicator associated with activity / the action or pattern being performed. |
| TTP | Tactic, technique, or procedure used to describe adversary behavior. |
| ROE | Rules of engagement defining authorized assessment boundaries and operating conditions. |
| OSINT | Analysis of publicly available information for a defined purpose. |
| SAST / DAST / SCA | Static code analysis / testing a running application / analysis of software components and dependencies. |
| SBOM | Software bill of materials describing components in a software artifact. |
| IaC | Infrastructure as code: configuration describing infrastructure in a versionable form. |
| CI/CD | Automated integration and delivery/deployment workflows for software changes. |
| IdP / federation | Identity provider / trust allowing one system to rely on another system's identity assertions. |
| OAuth / OIDC / SAML | An authorization framework / an identity layer over OAuth / an assertion-based federation standard. |
| JWT | A token format carrying claims; security depends on correct validation and context. |
| MFA / passkey | Authentication using distinct factor categories / a public-key credential used through supported authentication protocols. |
| PKI / KMS / HSM | Public-key infrastructure / key management service or system / hardware security module. |
| Hash / MAC / signature | A digest / a keyed integrity check / a public-key-verifiable authenticity and integrity mechanism. |
| SSRF / XSS / CSRF | Server-side request forgery / cross-site scripting / cross-site request forgery. |
| IDOR / BOLA | Insecure direct object reference / broken object-level authorization; naming differs, but object access must be checked. |
| Race condition / TOCTOU | Behavior depending on competing timing / a check and later use occurring under changed conditions. |
| Privilege escalation | Crossing from a lower-authority context to greater authority through an unintended path. |
| Lateral movement | Moving from one system or identity context to another within an environment. |
| Control plane / data plane | Management and configuration interfaces / interfaces carrying workload traffic or data operations. |
| SIEM / EDR | Centralized security-event analysis / endpoint detection and response capabilities. |
| Fuzzing | Exercising a target with varied inputs to discover unexpected behavior. |
| RAG / prompt injection | Retrieval-augmented generation / untrusted content attempting to alter an AI system's behavior. |
| Remediation / retest | Correcting the underlying issue / checking that the correction works under defined conditions. |

### Personal starting checklist

- [ ] Choose a sustainable weekly study time and create a skill tracker.
- [ ] Read the authorization section and establish an isolated practice environment.
- [ ] Complete the first networking, Linux, Windows, and programming exercises.
- [ ] Write one useful lab note every week.
- [ ] Revisit weak prerequisites instead of skipping them.
- [ ] Complete an independent assessment and report before claiming practical proficiency.
- [ ] Choose one specialization based on the work you enjoy and can demonstrate.
