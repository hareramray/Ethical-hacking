# Ethical Hacking: Detailed Topic Roadmaps

**Updated:** 18 October 2026  
**Collection:** 28 main-topic roadmaps and 8 separate advanced-specialization roadmaps.

This collection expands every numbered topic in the [original master roadmap](../ETHICAL_HACKING_ROADMAP.md). Each main-topic file retains its original curriculum and adds its own learning sequence, exercises, evidence requirements, troubleshooting, and completion criteria. Specialist files extend the eight tracks introduced in section 22.

Start with [00 — how to use the roadmap](00-how-to-use-this-roadmap.md), [01 — authorization](01-authorization-scope-and-professional-conduct.md), and [02 — lab setup](02-build-a-safe-repeatable-lab.md). Track your work in [PROGRESS.md](PROGRESS.md). Use the [coverage map](COVERAGE.md) to see how the collection maps back to the source.

## Recommended learning order

1. **Preparation:** 00–02. Establish scope, a recoverable lab, and a learning workflow.
2. **Common foundation:** 03–08. Learn computers, networking, operating systems, programming, security principles, and cryptography.
3. **Assessment method:** 09–10. Learn how to choose tests, interpret evidence, and validate findings.
4. **Applications and infrastructure:** 11–16. Build working familiarity, then deepen the subjects relevant to your role.
5. **Detection and reporting throughout:** 20 and 23. Correlate each exercise with logs and write useful findings.
6. **Specialization:** 17–19, 21, or one of the eight section-22 tracks. Follow the prerequisites and select one primary track initially.
7. **Independent work:** 24–25. Complete capstones, review evidence, and adapt your schedule.
8. **Reference support:** 26–27. Select tools deliberately and reuse the templates.

Core topics require practical competence; awareness topics initially require explanation and analysis; chosen tracks require deeper independent work. The scheduling example covers core study and an initial specialization, not expert mastery of every optional branch. No finite roadmap can enumerate every product, future vulnerability, or research result; update your notes as the underlying systems change.

## Main topic files

| Topic | Phase | What the expanded file covers |
| --- | --- | --- |
| [00. How to use this roadmap](00-how-to-use-this-roadmap.md) | Orientation | Learning order, skill levels, prerequisite mapping, study workflow, and self-review. |
| [01. Authorization, scope, and professional conduct](01-authorization-scope-and-professional-conduct.md) | Preparation | Ownership, written scope, operating conditions, evidence handling, and disclosure. |
| [02. Build a safe, repeatable lab](02-build-a-safe-repeatable-lab.md) | Preparation | Hardware planning, virtualization, isolated networks, reset/recovery, and troubleshooting. |
| [03. Computing and study foundations](03-computing-and-study-foundations.md) | Foundation | Architecture, data representation, OS execution, and technical learning foundations. |
| [04. Networking and Internet protocols](04-networking-and-internet-protocols.md) | Foundation | Ethernet, IP/IPv6, routing, DNS, transports, HTTP/TLS, and packet analysis. |
| [05. Linux administration](05-linux-administration.md) | Foundation | Shells, files, identities, services, networking, logs, maintenance, and hardening. |
| [06. Windows administration](06-windows-administration.md) | Foundation | Windows architecture, ACLs, PowerShell, services, logs, and enterprise foundations. |
| [07. Programming and automation](07-programming-and-automation.md) | Foundation | Python, Bash, PowerShell, JavaScript, SQL, C, debugging, Git, and safe automation. |
| [08. Security principles and cryptography](08-security-principles-and-cryptography.md) | Foundation | Security reasoning, IAM, cryptographic primitives, certificates, and key lifecycle. |
| [09. Assessment methodology, reconnaissance, and enumeration](09-assessment-methodology-reconnaissance-and-enumeration.md) | Assessment method | Scope-to-test workflow, passive discovery, service enumeration, and evidence. |
| [10. Vulnerability assessment and research](10-vulnerability-assessment-and-research.md) | Assessment method | Advisories, vulnerability triage, scanner limits, research, reproduction, and fixes. |
| [11. Web application security](11-web-application-security.md) | Applications | Application mapping, access control, injection, browser security, caches, and logic. |
| [12. API security and modern authentication](12-api-security-and-modern-authentication.md) | Applications | REST, GraphQL, gRPC, WebSockets, OAuth/OIDC, SAML, tokens, and account lifecycle. |
| [13. Secure code review and software delivery](13-secure-code-review-and-software-delivery.md) | Applications | Code/data-flow review, analysis tools, tests, dependencies, CI/CD, and build integrity. |
| [14. Linux and Windows host security testing](14-linux-and-windows-host-security-testing.md) | Infrastructure | Linux/Windows host boundaries, services, permissions, credentials, and remediation. |
| [15. Active Directory and enterprise identity](15-active-directory-and-enterprise-identity.md) | Infrastructure | AD administration, Kerberos, delegation, certificates, identity paths, and hybrid SaaS. |
| [16. Cloud, containers, and Kubernetes](16-cloud-containers-and-kubernetes.md) | Infrastructure | AWS, Azure, Google Cloud, workload identity, containers, Kubernetes, and logging. |
| [17. Wireless and network appliance security](17-wireless-and-network-appliance-security.md) | Specialist track | Wi-Fi, enterprise authentication, Bluetooth, appliances, and segmentation. |
| [18. Mobile application security](18-mobile-application-security.md) | Specialist track | Android/iOS models, local storage, transport, IPC, backend controls, and mobile review. |
| [19. Reverse engineering, exploit development, and malware analysis](19-reverse-engineering-exploit-development-and-malware-analysis.md) | Specialist track | Binary analysis, memory errors, debugging, fuzzing, exploit concepts, and sample analysis. |
| [20. Detection engineering, incident response, and forensics](20-detection-engineering-incident-response-and-forensics.md) | Defensive practice | Telemetry, detections, hunting, incident handling, evidence acquisition, and forensics. |
| [21. Human and physical security assessments](21-human-and-physical-security-assessments.md) | Specialist track | Approved simulations, identity-verification workflows, facilities, and human factors. |
| [22. Advanced specialization map](22-advanced-specialization-map.md) | Specialist overview | Prerequisites and selection guidance for eight separately expanded specialist roadmaps. |
| [23. Reporting, remediation, and retesting](23-reporting-remediation-and-retesting.md) | Professional practice | Evidence, reproducibility, severity, developer guidance, report QA, and retesting. |
| [24. Capstones, portfolio, and career direction](24-capstones-portfolio-and-career-direction.md) | Projects and career | Project ladder, independent assessments, portfolio quality, role choice, and credentials. |
| [25. Study schedules and readiness checks](25-study-schedules-and-readiness-checks.md) | Study planning | Time budgeting, study blocks, retrieval practice, readiness, and adaptive planning. |
| [26. Tools and learning resources](26-tools-and-learning-resources.md) | Reference library | Tool selection, evidence interpretation, safe automation, and learning-resource strategy. |
| [27. Reusable templates and glossary](27-reusable-templates-and-glossary.md) | Templates and glossary | Reusable learning, scope, finding, test, evidence, change, and retest templates. |

## Advanced specialization files

| Roadmap | Start after |
| --- | --- |
| [22.1 AI, LLM, RAG, and agent security](specializations/22-01-ai-llm-rag-and-agent-security.md) | Web/API security, identity, Python, data pipelines, and basic machine learning. |
| [22.2 IoT, embedded systems, and hardware](specializations/22-02-iot-embedded-systems-and-hardware.md) | C, Linux, networking, firmware concepts, and safe electronics handling. |
| [22.3 OT, ICS, and cyber-physical systems](specializations/22-03-ot-ics-and-cyber-physical-systems.md) | Networking, defensive monitoring, industrial-process and safety awareness. |
| [22.4 Telecom and radio-frequency security](specializations/22-04-telecom-and-radio-frequency-security.md) | Networking, authentication, signal concepts, and appropriate test authorization. |
| [22.5 Browser, kernel, and virtualization research](specializations/22-05-browser-kernel-and-virtualization-research.md) | C/C++, assembly, OS internals, debugging, and fuzzing. |
| [22.6 Blockchain and smart-contract security](specializations/22-06-blockchain-and-smart-contract-security.md) | Programming, cryptography, distributed systems, and transaction semantics. |
| [22.7 Desktop clients, macOS, privacy, and architecture](specializations/22-07-desktop-clients-macos-privacy-and-architecture.md) | OS administration, application development, authentication, and threat modeling. |
| [22.8 Adversary emulation and red/purple-team planning](specializations/22-08-adversary-emulation-and-redpurple-team-planning.md) | Independent assessment/reporting, enterprise/cloud identity, and detection engineering. |

## How to use each file

Read the prerequisites and original checklist first. Follow the expanded modules in order, build the prescribed owned/synthetic lab, predict the secure result, perform the bounded exercise, collect evidence, correct any defect, and retest. Use the exit criteria to determine what to practice next.

Keep exercise artifacts private until reviewed for sensitive data and publication permission. A completed reading or guided lab is useful preparation; independent proficiency requires an unfamiliar task and defensible evidence.

## Supporting files

- [Progress tracker](PROGRESS.md): one row per main topic and specialist track.
- [Coverage map](COVERAGE.md): source-to-file mapping and preserved original checklist counts.
- [Reusable templates](27-reusable-templates-and-glossary.md): scope, findings, hypotheses, evidence, changes, retests, and weekly reviews.
