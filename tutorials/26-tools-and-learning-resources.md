# 26. Tutorial: choose tools, interpret output, and use learning resources

[Index](README.md) | [Complete source curriculum](curriculum/26-tools-and-learning-resources.md) | [Original roadmap](../roadmaps/26-tools-and-learning-resources.md)

Start with a question that can be answered from an observation: “Which process listens on this local port?” is better than “Which scanner should I install?” Record what a tool accepts, requires, sends or changes, outputs, misses, and how to stop it. This chapter covers every tool family in the source; the family-specific chapters provide deeper mechanics.

## Lesson 1: connect process, listener, request, and event

Run the [portable API](examples/README.md) in server mode. In another Windows PowerShell terminal, use read-only observations:

```powershell
Get-NetTCPConnection -LocalPort 8765 -State Listen
Get-Process -Id (Get-NetTCPConnection -LocalPort 8765 -State Listen).OwningProcess
curl.exe -i -H 'Authorization: Bearer alice-lab' http://127.0.0.1:8765/notes/n1
Get-Help Get-NetTCPConnection
```

Expect a listener at `127.0.0.1`, a Python process, and an HTTP 200 containing synthetic data. Exact process IDs vary. On Linux, `ss -lntp` and `ps` provide analogous observations; process details may require permission. A configuration file describes intent, while a listener describes runtime state. A service that has not reloaded can disagree with its configuration.

Stop the fixture with Ctrl+C and repeat the client request. Expect connection failure instead of an HTTP authorization denial. Do not modify the host firewall merely to complete this example. In a disposable VM, add a separately scoped blocked-listener scenario and compare client, host listener, and firewall evidence. A timeout alone does not identify which component dropped traffic.

## Lesson 2: learn a small network and browser toolkit

| Tool family | What it can establish | Important limit and practice |
| --- | --- | --- |
| `ip`/`ipconfig`, socket tools | Interface, route, address, listener, and process context | An address does not prove reachability. Correlate a local request with the active route/listener. |
| DNS query clients | Resolver, record type, answer, and response metadata | Cached answers and split DNS can differ. Compare the intended resolver and record type explicitly. |
| `curl` | Transport/application response under selected request settings | It does not enforce browser CORS behavior. Compare a successful owner request with a forbidden non-owner request. |
| Wireshark/tcpdump | Traffic visible at the chosen capture point | Encryption/offload/capture position affect evidence. Annotate one owned exchange and its missing visibility. |
| Nmap | Reachable services and protocol-dependent inventory observations | States/guesses require interpretation. Reconcile a bounded owned-target inventory with server listeners. |
| Browser developer tools | Requests, DOM, storage, JavaScript errors, redirects | Browser state can change identity and caching. Use separate test profiles and inspect request initiators. |
| Burp Suite or ZAP | Proxy history, request editing/replay, controlled observation | Proxy trust and active features change behavior. Learn one benign replay before enabling automation. |

With a dedicated lab browser/profile, configure a proxy using its official instructions and only its test trust certificate. Confirm interception of the owned fixture, scope filtering, and account labeling. Change one request field and predict the response. Expired sessions, refreshed anti-CSRF tokens, redirects, retries, or cached responses can defeat a simplistic comparison. Remove the lab trust configuration afterward. See [Nmap's reference](https://nmap.org/book/man.html), [Wireshark documentation](https://www.wireshark.org/docs/), and [ZAP documentation](https://www.zaproxy.org/docs/).

## Lesson 3: evaluate scanner claims against conditions

A Greenbone or similar scanner compares observations with checks. Its credentials, feed date, plugin selection, exclusions, authentication success, and target reachability determine coverage. A failed authenticated check is not a clean host result. Start with a small lab inventory and manually triage a few findings.

Static analysis (SAST) reasons about code; dynamic analysis (DAST) observes a running application; component analysis (SCA) identifies dependency concerns; secret scanners look for credential-like patterns; fuzzers vary inputs. They have different coverage. A library's presence does not prove its vulnerable path is reachable, and a negative static result does not prove the framework's authorization policy is correct.

Create a worksheet with claim, asset/version, local prerequisites, manual observation, status, correction, and limitation. Include one confirmed issue, one false positive, and one inconclusive result. Inspect a distribution's patch/backport evidence before treating a banner version as vulnerable. Record the actual running process/build, not only an installed package list.

## Lesson 4: understand every specialist family before using it

| Family/examples | Prerequisite model | Safe learning artifact |
| --- | --- | --- |
| Python and Git | Structured input, errors, reproducibility, version history | A bounded log parser with fixtures and meaningful failure tests. |
| Linux inspection utilities | Processes, permissions, services, journal/audit context | An effective-access explanation and correlated event. |
| Windows Sysinternals | Tokens, handles, registry, processes, startup | An annotated benign process/activity trace with collection limits. |
| BloodHound | Directory/cloud relationships, ACLs, groups, delegation | A small synthetic/owned identity graph with independently checked edge prerequisites. |
| hashcat / John the Ripper | Hash formats, salts, password KDFs, work factors | Compare a tiny set of invented credentials under a resource/time limit; never infer real-user permission. |
| Metasploit | Vulnerability preconditions, module actions, side effects, restoration | Review an approved lab module's assumptions and explain a harmless validation outcome; do not blindly run modules. |
| ffuf | HTTP baselines, input boundaries, response comparison, throttling | A tiny owned-fixture response matrix and a manually reproduced difference. |
| Ghidra/debugger | C, memory, calling conventions, executable formats | Self-compiled function analysis validated by execution. |
| MobSF / adb | App packaging, Android permissions/storage, backend controls | Manually checked static observation plus emulator runtime evidence. |
| Provider CLI / IaC review | Account/project context, policy, resource lifecycle, state sensitivity | A scoped sandbox policy diff and resource inventory. |
| `kubectl` | Context, namespace, workloads, RBAC, networking | Read-only local-cluster inventory and explicit subject permission reasoning. |
| Sigma/native queries | Log schemas, backend mapping, timestamps | Positive/negative/near-match fixture results and a telemetry dependency. |
| YARA | File types, strings/bytes, conditions, matching limits | A harmless content corpus with intended matches and collisions. |

Tools often concentrate sensitive data: proxy projects hold tokens, directory exports hold privilege paths, dumps contain memory, and IaC state may contain secrets. Protect these artifacts as carefully as the final report. A graph path is a hypothesis until its edges and prerequisites are checked. A pattern match is a lead until the surrounding evidence supports its meaning.

## Lesson 5: verify provenance and automate only understood work

Follow official project/vendor or trusted distribution links. Check platform support, release notes, publisher/signing-key provenance, and provided signatures/checksums. A checksum published next to a tampered download can match malicious bytes; it does not independently establish a trustworthy publisher. Inspect installation scripts and requested privilege, and treat extensions, templates, plugins, scanner rules, and community modules as dependencies requiring review.

Record versions and configuration with every run. Avoid treating an installation command as timeless: use the documentation for your OS and version. A failing command may indicate a changed flag, missing privilege, wrong context, or absent prerequisite rather than a security finding.

Automate parsing and comparisons after doing a small case manually. Use explicit targets, dry-run where mutations exist, cancellation, timeouts, limited concurrency, maximum input size, and redacted logs. Prefer stable structured output over fragile human text. Test empty data, malformed input, denied access, timeout, interruption, and oversized responses. Report partial runs as partial coverage.

## Lesson 6: use resources without collecting them endlessly

Choose one explanation, one primary reference, and one practice environment for the current topic. For terminal foundations, the source identifies OverTheWire Bandit; for web practice, PortSwigger Web Security Academy, WebGoat, and Juice Shop; for deeper systems, pwn.college; for structured general paths, TryHackMe and HTB Academy. These are curriculum candidates, not a claim about their current access terms, pricing, or availability. Follow the retained source links and verify terms before planning around a hosted lab or purchasing access.

A useful sequence is explanation → guided exercise → independent repeat → changed assumption → repair/report → delayed recall. Record hints used. If sources disagree, compare versions, defaults, platform, deployment model, and publication date. In a research paper/advisory, extract component, boundary, prerequisites, faulty assumption, observed effect, fix, and limitations; cite the original rather than copying its prose as your contribution.

**Capstone:** select the smallest toolkit for one local application-and-host assessment. For each important output, provide an independent check. Explain one misleading result, preserve versions/settings and synthetic inputs, and document cleanup. You pass when the report makes sense to a reviewer using different tools, and you can explain what your chosen tools did not establish.
