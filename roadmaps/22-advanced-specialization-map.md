# 22. Advanced specialization map

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#22-advanced-specialization-map)

<!-- TOPIC-TOC:START -->

## Contents

- [22.1 AI, LLM, RAG, and agent security](#221-ai-llm-rag-and-agent-security)
- [22.2 IoT, embedded systems, and hardware](#222-iot-embedded-systems-and-hardware)
- [22.3 OT, ICS, and cyber-physical systems](#223-ot-ics-and-cyber-physical-systems)
- [22.4 Telecom and radio-frequency security](#224-telecom-and-radio-frequency-security)
- [22.5 Browser, kernel, and virtualization research](#225-browser-kernel-and-virtualization-research)
- [22.6 Blockchain and smart-contract security](#226-blockchain-and-smart-contract-security)
- [22.7 Desktop clients, macOS, privacy, and architecture](#227-desktop-clients-macos-privacy-and-architecture)
- [22.8 Adversary emulation and red/purple-team planning](#228-adversary-emulation-and-redpurple-team-planning)
- [Choose and navigate a specialization](#choose-and-navigate-a-specialization)
  - [A practical selection process](#a-practical-selection-process)
  - [Shared research standards](#shared-research-standards)

<!-- TOPIC-TOC:END -->



These tracks extend the core curriculum. Choose one or two for deep practice; maintain conceptual awareness of the others. Each track requires ongoing study because platforms, threat models, and techniques change.

## 22.1 AI, LLM, RAG, and agent security

**Prerequisites:** Web/API security, Python, identity, data pipelines, and basic machine learning.

- [ ] Learn model training versus inference, tokens, context windows, embeddings, vector stores, retrieval-augmented generation, tools, agents, memory, and evaluation datasets.
- [ ] Trace trust boundaries across user input, documents, retrieved content, tool responses, system instructions, identities, and external actions.
- [ ] Study direct/indirect prompt injection, sensitive-data exposure, excessive permissions, unsafe output handling, poisoned retrieval data, supply-chain risks, resource exhaustion, and incorrect claims.
- [ ] Test tenant isolation, retrieval authorization, document provenance, connector scopes, secret handling, tool argument validation, action approvals, memory retention, and auditability.
- [ ] Understand model limitations and non-determinism; maintain repeatable evaluation cases and measure both security failures and legitimate-task success.

**Project:** Build a local assistant over synthetic documents with mock tools. Evaluate whether untrusted document content can cause unauthorized actions, then enforce boundaries outside the model and retest. **Pass:** Demonstrate tenant separation, limited tool permissions, traceable actions, and a regression suite. Use the [OWASP GenAI Security Project](https://genai.owasp.org/) for its evolving application and agent guidance.

## 22.2 IoT, embedded systems, and hardware

**Prerequisites:** C, Linux, networking, electronics fundamentals, and safe handling of low-voltage equipment.

- [ ] Study microcontrollers, SoCs, bootloaders, memory maps, embedded operating systems, firmware formats, UART/JTAG/SWD concepts, SPI/I2C, and debug-interface exposure.
- [ ] Review firmware provenance, signing, secure/measured boot, rollback protection, update recovery, device identity, key provisioning, secure storage, and end-of-support behavior.
- [ ] Assess companion apps, local services, device-to-cloud authorization, MQTT/CoAP concepts, fleet management, reset behavior, and disposal.
- [ ] Understand SBOMs, third-party components, manufacturing trust, physical access assumptions, and side-channel/fault-injection concepts as advanced research areas.

**Project:** Review firmware for an owned development board or emulator and threat-model its update path. **Pass:** Produce an interface inventory, reproducible findings, and a verified update/recovery design without interacting with deployed third-party devices.

## 22.3 OT, ICS, and cyber-physical systems

**Prerequisites:** Networking, defensive monitoring, industrial-process basics, and safety engineering awareness.

- [ ] Learn PLCs, HMIs, historians, engineering workstations, safety systems, zones/conduits, and industrial protocol trust assumptions.
- [ ] Understand availability, deterministic timing, equipment lifecycles, maintenance windows, vendor dependencies, and the difference between cyber impact and physical consequences.
- [ ] Study asset inventory, passive visibility, remote-access governance, segmentation, backup/recovery, change control, and incident coordination with operators.

**Project:** Use a simulator with an entirely fictional process to review architecture and monitor benign traffic. **Pass:** Explain hazards and stop conditions and propose controls that respect operational requirements. Use [NIST OT security guidance](https://csrc.nist.gov/pubs/sp/800/82/r3/final) and [CISA ICS recommended practices](https://www.cisa.gov/resources-tools/resources/ics-recommended-practices). Never substitute a production controller for a training simulator.

## 22.4 Telecom and radio-frequency security

**Prerequisites:** Networking, authentication, signal basics, and the applicable authorization rules for your location.

- [ ] Learn cellular architecture, SIM/eSIM identity, roaming, signaling trust, VoIP/SIP/RTP, software-defined radio concepts, modulation, and spectrum boundaries.
- [ ] Study protocol threat models, privacy implications, lawful test arrangements, and emergency-service dependencies.

**Project:** Analyze supplied recordings or a fully simulated protocol exchange; any radio transmission requires the appropriate approved environment. **Pass:** Explain trust boundaries and monitoring controls without interacting with public carrier infrastructure or third-party communications.

## 22.5 Browser, kernel, and virtualization research

**Prerequisites:** Advanced operating systems, C/C++, assembly, debugging, fuzzing, and mitigation knowledge.

- [ ] Study browser process models, sandboxing, JavaScript engines, JIT compilation, extension permissions, IPC, and origin isolation.
- [ ] Study kernel interfaces, drivers, memory ownership, synchronization, device interfaces, hypervisors, virtual devices, and guest/host boundaries.
- [ ] Learn harness engineering, reproducibility, root-cause analysis, patch verification, coordinated disclosure, and careful management of untrusted inputs.

**Project:** Fuzz a small open-source parser or toy interface in a disposable local environment. **Pass:** Deliver a minimized bug report, patch or mitigation analysis, and regression evidence. Advance to complex targets only after demonstrating reliable isolation and debugging.

## 22.6 Blockchain and smart-contract security

**Prerequisites:** Programming, cryptography concepts, distributed systems, and transaction semantics.

- [ ] Learn accounts, keys, signatures, transactions, gas, contract execution, events, storage, oracles, and upgrade/proxy models.
- [ ] Study access control, reentrancy, arithmetic/rounding, signature replay, initialization, oracle assumptions, front-running concepts, economic invariants, and privileged administration.
- [ ] Learn unit, property, invariant, and fuzz testing; distinguish code correctness from protocol-economic assumptions.

**Project:** Audit a toy contract on a local development chain or designated testnet with valueless assets. **Pass:** State invariants, reproduce a controlled failure, repair it, and verify the invariant. Consult [Solidity security considerations](https://docs.solidity.org/en/latest/security-considerations.html); do not use mainnet funds as learning material.

## 22.7 Desktop clients, macOS, privacy, and architecture

**Prerequisites:** Operating systems, programming, authentication, and threat modeling.

- [ ] Review thick-client local storage, IPC, installer privileges, auto-update integrity, backend authorization, embedded browsers, Electron trust boundaries, and unsafe local file handling.
- [ ] For macOS, learn app signing, notarization, Gatekeeper, TCC permissions, sandboxing, entitlements, Keychain, XPC, launch services, and endpoint telemetry.
- [ ] Study security architecture: trust boundaries, least privilege, defense in depth, fail-safe behavior, resilience, secure defaults, tenant isolation, and dependencies.
- [ ] Study privacy engineering: data inventory, purpose limitation, minimization, retention, deletion, re-identification risks, consent boundaries, and privacy threat modeling.
- [ ] Explore cryptographic protocol review, HSM/TPM design, key lifecycle, post-quantum migration planning, and side-channel resistance as separate advanced tracks requiring deeper mathematics and specialist review.

**Project:** Threat-model a small desktop application and its update service, then review its data lifecycle. **Pass:** Connect each significant risk to a design decision, validation evidence, an owner, and a practical remediation plan.

## 22.8 Adversary emulation and red/purple-team planning

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

## Choose and navigate a specialization

The detailed topic roadmaps below expand every specialization in this map. Choose by the systems you can study responsibly, the prerequisites you can already demonstrate, and the type of evidence you enjoy producing. Complete a small project before committing to a larger laboratory or paid equipment.

| Detailed roadmap | Foundation to demonstrate first | First useful portfolio result |
| --- | --- | --- |
| [AI, LLM, RAG, and agent security](specializations/22-01-ai-llm-rag-and-agent-security.md) | API authorization, Python, data flow diagrams | Tenant-isolation and mock-tool evaluation suite |
| [IoT, embedded systems, and hardware](specializations/22-02-iot-embedded-systems-and-hardware.md) | C, Linux, low-voltage electronics | Firmware/update trust review for an owned board |
| [OT, ICS, and cyber-physical systems](specializations/22-03-ot-ics-and-cyber-physical-systems.md) | Networking, monitoring, process safety concepts | Simulated process architecture and recovery exercise |
| [Telecom and radio-frequency security](specializations/22-04-telecom-and-radio-frequency-security.md) | Protocols, authentication, basic signal mathematics | Analysis of a supplied trace or simulated exchange |
| [Browser, kernel, and virtualization research](specializations/22-05-browser-kernel-and-virtualization-research.md) | C/C++, assembly, debugging, fuzzing | Minimized local defect with a verified regression fix |
| [Blockchain and smart-contract security](specializations/22-06-blockchain-and-smart-contract-security.md) | Programming, signatures, distributed state | Local contract invariant suite and audit report |
| [Desktop clients, macOS, privacy, and architecture](specializations/22-07-desktop-clients-macos-privacy-and-architecture.md) | OS permissions, application identity, threat modeling | Update-service review and data-lifecycle assessment |
| [Adversary emulation and red/purple-team planning](specializations/22-08-adversary-emulation-and-redpurple-team-planning.md) | Assessment reporting, identity, detection engineering | Harmless three-action exercise with measured results |

### A practical selection process

1. Read the prerequisites and first project for two candidate tracks. List missing knowledge and available lab resources. Prefer a track where you can observe both the vulnerable behavior and the corrected behavior.
2. Complete one small prerequisite demonstration: debug an owned binary, trace an API permission decision, map a simulated industrial process, or validate a detection fixture.
3. Define a four-part research question: the system, the trust boundary, the expected property, and the evidence needed to evaluate it.
4. Run a bounded pilot and write a short report. Decide whether the work interests you enough to repeat with greater depth.
5. Keep the other tracks as awareness topics. Cross-training becomes useful when a real boundary crosses disciplines, such as an IoT companion app or an AI agent using enterprise identity.

### Shared research standards

Every specialist project needs a reproducible environment, synthetic or appropriately authorized data, a stated observation limit, preserved evidence, and a reset procedure. Record platform versions and build identifiers with results. A laboratory finding supports claims about the tested environment; generalization requires additional evidence.

Use a progression of understanding, reproduction, explanation, repair, and independent verification. Time spent watching demonstrations does not substitute for these outcomes. Record unresolved questions as a future-study backlog rather than silently marking a topic complete. When a specialist system requires expertise you do not yet have, use simulation and source review while building that prerequisite knowledge.

**Completion gate:** Deliver one reviewed capstone in your chosen track, demonstrate a corrected behavior, explain a plausible alternative cause for the original observation, and document the boundaries of your conclusion. The original checklist remains the coverage map; the linked files provide the ordered work needed to build evidence for it.

