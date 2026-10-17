# 26. Tools and learning resources

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#26-tools-and-learning-resources)

<!-- TOPIC-TOC:START -->

## Contents

- [Tool-role matrix](#tool-role-matrix)
- [Learning resources by starting level](#learning-resources-by-starting-level)
- [How to consume resources without getting stuck collecting them](#how-to-consume-resources-without-getting-stuck-collecting-them)
- [Download provenance and maintenance](#download-provenance-and-maintenance)
- [Expanded tool-learning roadmap](#expanded-tool-learning-roadmap)
  - [Stage 1: Learn observation before automation](#stage-1-learn-observation-before-automation)
  - [Stage 2: Learn a small network toolkit](#stage-2-learn-a-small-network-toolkit)
  - [Stage 3: Add a browser and one intercepting proxy](#stage-3-add-a-browser-and-one-intercepting-proxy)
  - [Stage 4: Evaluate scanners and code-analysis tools](#stage-4-evaluate-scanners-and-code-analysis-tools)
  - [Stage 5: Add specialist tools only when their model is understood](#stage-5-add-specialist-tools-only-when-their-model-is-understood)
  - [Stage 6: Automate repeated, understood work](#stage-6-automate-repeated-understood-work)
- [Resource selection and reading strategy](#resource-selection-and-reading-strategy)
- [Tool competence assessment](#tool-competence-assessment)

<!-- TOPIC-TOC:END -->



Choose tools to answer a defined question. Start with the operating system's utilities, a browser, Wireshark, one web proxy, Python, and Git. Add specialized tools when their prerequisites appear in your roadmap. For every run, record the version, scope, settings, time, observations, limitations, and verification. Tool output becomes evidence only after you interpret and validate it.

## Tool-role matrix

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

## Learning resources by starting level

**Starting from basic computer use — free resources:** Work through [OverTheWire Bandit](https://overthewire.org/wargames/bandit/) after learning terminal navigation and SSH. Use its authorized game environment and document the Linux concept behind each solution. Revisit the official Python, Microsoft, and MDN references linked in the foundations sections when a prerequisite is missing.

**Learning web security — free resources:** [PortSwigger Web Security Academy](https://portswigger.net/web-security) provides structured explanations and interactive labs. Pair a topic with a request trace, a written explanation, and remediation. Progress from guided exercises to exercises where the vulnerability category is not announced.

**Running your own application lab — free/open-source projects:** Use [OWASP WebGoat](https://owasp.org/projects/webgoat) for guided vulnerability lessons and [OWASP Juice Shop](https://owasp.org/projects/juice-shop) for broader application challenges. Run deliberately vulnerable applications locally with isolation and restore procedures. Do not expose them on public cloud interfaces or a shared network.

**Building deeper systems skills — free learning:** [pwn.college](https://pwn.college/) offers hands-on material for computing and security foundations through deeper systems topics. Match modules to your current prerequisites; advanced binary exercises should follow C, memory, and debugging practice.

**Wanting a guided general curriculum — mixed access:** [TryHackMe](https://tryhackme.com/) and [Hack The Box Academy](https://academy.hackthebox.com/) provide structured training with differing access arrangements. Inspect the current syllabus and free material first. Choose one path that fills a demonstrated skill gap; confirm current access terms before paying.

## How to consume resources without getting stuck collecting them

1. Select one roadmap topic and its exit gate.
2. Read one explanation and the relevant official reference.
3. Complete one guided lab, noting why each action matters.
4. Repeat independently, then change one assumption or configuration.
5. Explain the result, remediation, and detection evidence in your own words.
6. Revisit after a delay; move on when you can reproduce and explain it.

Use hints progressively. After reading a full solution, rebuild the exercise later without it. Keep a small backlog of missing prerequisites instead of continually switching courses.

## Download provenance and maintenance

- [ ] Obtain tools from the official project/vendor or a trusted distribution repository; follow official links to release artifacts.
- [ ] Check release notes, supported platforms, signatures/checksums where provided, and signing-key provenance. A matching checksum alone does not establish a trustworthy publisher.
- [ ] Inspect installation scripts and requested privileges; isolate unfamiliar software and use test credentials.
- [ ] Record versions and dependency changes so exercises are reproducible. Avoid random repackaged bundles, credential-stealing imitations, and blindly pasted installation commands.
- [ ] Treat extensions, templates, community modules, and scanner rules as executable or security-relevant dependencies requiring their own review.

**Exit gate:** Select the smallest suitable toolset, explain what each tool can and cannot establish, and turn its output into a verified finding or a documented negative result.

## Expanded tool-learning roadmap

### Stage 1: Learn observation before automation

Start with your operating system's process, socket, file, identity, and log utilities. Use one local application to connect these observations: a process runs as an account, listens on an address, reads configuration, handles a request, and writes an event. Predict what each tool should reveal before running it.

Create a tool notebook with purpose, inputs, required privileges, outputs, side effects, limitations, and a small verified example. Include how to obtain help and how to stop the tool. Learn the distinction between reading configuration and observing runtime behavior; both can be necessary when a service has not reloaded a changed file.

### Stage 2: Learn a small network toolkit

Use a DNS client to compare a requested name, resolver answer, record type, and cache behavior. Use a connection or HTTP client to distinguish resolution, transport, TLS, and application failures. Use a packet analyzer to verify the exchange at the capture position you actually selected.

Introduce service-discovery tools after you can explain basic TCP/UDP behavior. Record exact target scope, timing, output format, and uncertainty. Compare the inventory with server-side listening sockets and firewall configuration. A scanner's guess is a lead to validate, not a substitute for identifying the real service.

**Lab:** Present one service in three states: not listening, listening but blocked, and reachable. Compare the tool outputs and logs. Explain which observation distinguishes each case and where uncertainty remains.

### Stage 3: Add a browser and one intercepting proxy

Learn request history, scope filters, request editing, comparisons, authentication state, and certificate handling. Identify which actions send traffic and which only inspect stored data. Separate test accounts and label sessions so an administrator's browser state cannot invalidate an ordinary-user test.

Practice replaying one benign request in your own app, then change exactly one relevant field. Record the expected effect before interpreting the response. Learn how automatic retries, redirects, anti-CSRF token refresh, and expired sessions can change what you are observing. Keep request budgets bounded and avoid enabling every scanning feature before understanding its behavior.

### Stage 4: Evaluate scanners and code-analysis tools

Choose a scanner for a documented coverage need. Read how credentials, plugins, excluded assets, and authentication failures affect results. Preserve configuration and feed dates. Triaging five findings correctly is more valuable than exporting a large unreviewed report.

For code tools, distinguish static analysis, dependency analysis, secret detection, runtime testing, and fuzzing. Supply a small codebase with known true and false cases, then observe what each tool finds and misses. Record whether the tool understands framework authorization and whether a dependency warning proves reachable behavior or only component presence.

**Lab:** Build a triage worksheet with finding, tool claim, local conditions, manual verification, status, and remediation. Include at least one confirmed issue, false positive, and unresolved result caused by insufficient evidence.

### Stage 5: Add specialist tools only when their model is understood

Before a directory graph tool, learn permissions and relationships. Before a debugger, learn processes, memory, and calling conventions. Before a cloud CLI, learn account selection and effective permissions. Before a mobile analyzer, learn packaging, permissions, and backend responsibilities.

Tools can concentrate sensitive data. A proxy project may contain tokens; an identity export may expose privilege relationships; a crash dump may include secrets; an IaC state file may preserve credentials. Define storage and deletion practices for the tool's artifacts, not only for the final report.

### Stage 6: Automate repeated, understood work

Automate parsing, comparison, inventory, and bounded verification after performing the task manually. Prefer structured output and APIs to fragile terminal-text parsing when available. Add explicit target selection, dry-run behavior, cancellation, timeouts, conservative concurrency, useful errors, and log redaction.

Test the helper against empty results, invalid input, denied access, interrupted operations, timeouts, and unexpectedly large responses. Treat a partial run as partial coverage. Never silently interpret an authentication failure as a clean assessment.

## Resource selection and reading strategy

Choose one primary learning source, one official reference, and one practice environment per current topic. A tutorial explains a path; reference documentation defines actual behavior; a lab tests your understanding. If the sources disagree, check dates, product versions, defaults, and whether the examples use the same deployment model.

Use the existing resource links in this file and the specialized references in each topic. Select learning platforms by syllabus fit and available access rather than maintaining simultaneous subscriptions. Check current terms before spending money or planning around a hosted exercise.

For research reading, extract the affected component, trust boundary, prerequisites, faulty assumption, observed effect, fix, and limitations. Reproduce only an appropriate owned or provided training case. Record original-source attribution instead of copying another author's explanation as your own.

## Tool competence assessment

| Question | Evidence of understanding |
| --- | --- |
| What question does the tool answer? | A precise objective and expected observation. |
| What input or privilege does it need? | Documented target, identity, scope, and permissions. |
| What does it change or send? | Knowledge of side effects, requests, files, and cleanup. |
| What can it miss? | Coverage limits and negative-result interpretation. |
| How can you verify its result? | Independent server, code, packet, or configuration evidence. |
| Can another person repeat the run? | Version, configuration, prerequisites, and sanitized test data. |

**Capstone:** Select the smallest toolkit for a local application-and-host assessment. Explain each tool's role, perform one manual verification of each important result, resolve a misleading output, and package a reproducible evidence bundle. Your report should remain understandable to someone who uses different tools.
