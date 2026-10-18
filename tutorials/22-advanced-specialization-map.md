# 22. Tutorial: choose and connect advanced specializations

[Index](README.md) | [Complete source curriculum](curriculum/22-advanced-specialization-map.md) | [Original roadmap](../roadmaps/22-advanced-specialization-map.md)

This chapter teaches how to choose a track and formulate a research project. Each of the eight tracks has a separate practical tutorial linked below. Work through the shared foundations first; recognizing a specialist term is different from being able to assess its implementation independently.

## Lesson 1: recognize the boundary each track studies

| Track and tutorial | What changes across its trust boundary | First observable experiment |
| --- | --- | --- |
| [22.1 AI, LLM, RAG, agents](specializations/22-01-ai-llm-rag-and-agent-security.md) | Untrusted prompts/documents/tool results influence model output, retrieval, memory, or actions. | Two synthetic tenants and mock tools: an unauthorized document/action must remain inaccessible regardless of generated text. |
| [22.2 IoT, embedded, hardware](specializations/22-02-iot-embedded-systems-and-hardware.md) | Firmware, physical interfaces, provisioning, and cloud identities influence device authority. | Analyze an owned board/emulator's update acceptance and recovery requirements. |
| [22.3 OT, ICS, cyber-physical systems](specializations/22-03-ot-ics-and-cyber-physical-systems.md) | Digital commands/measurements affect a process with timing, availability, and safety constraints. | Follow a fictional tank measurement through PLC/HMI/historian roles in a simulator. |
| [22.4 Telecom and RF](specializations/22-04-telecom-and-radio-frequency-security.md) | Signals, subscriber identity, roaming, signaling, and media cross administrative domains. | Analyze supplied/simulated signaling and media separately, without public infrastructure or transmission. |
| [22.5 Browser, kernel, virtualization](specializations/22-05-browser-kernel-and-virtualization-research.md) | Inputs cross origin, process, privilege, memory-lifetime, or guest/host boundaries. | Minimize and repair a bounded toy parser/lifetime failure. |
| [22.6 Blockchain and smart contracts](specializations/22-06-blockchain-and-smart-contract-security.md) | Signed transactions and external calls alter shared state under economic assumptions. | Define escrow invariants and test them locally with valueless assets. |
| [22.7 Desktop, macOS, privacy, architecture](specializations/22-07-desktop-clients-macos-privacy-and-architecture.md) | IPC, installers, updates, storage, permissions, and backend requests cross authority/data-purpose boundaries. | Review a notes client and updater plus its data lifecycle. |
| [22.8 Adversary emulation and red/purple planning](specializations/22-08-adversary-emulation-and-redpurple-team-planning.md) | A sequence of approved behaviors tests prevention, observation, decision-making, and response. | Three harmless predefined actions with expected telemetry and measured response. |

These are connected domains. An IoT companion application needs mobile/API authorization. An AI connector relies on enterprise identity. A desktop updater may require cryptographic provenance and privileged IPC review. Keep those shared controls in the core curriculum; specialization adds system-specific constraints.

## Lesson 2: prove the prerequisite before buying complexity

For AI, demonstrate Python data handling, API authorization, identity, and a retrieval pipeline; distinguish training from inference, tokens from embeddings, and model output from authorized action. For embedded work, demonstrate C, Linux, networking, low-voltage electrical handling, and interface identification. For OT/RF, explain the process/protocol and safe simulation boundary before touching equipment.

For native research, explain an allocation lifetime, calling convention, debugger trace, and fuzzing harness before choosing a complex engine. For smart contracts, demonstrate signatures, transaction state, integer units/rounding, and distributed-state assumptions. For desktop/macOS, trace processes, IPC, permissions, key storage, signing, and backend responsibilities. For emulation, produce a scoped assessment and a tested detection before planning multiple actions.

Use a simple selection worksheet: interest, demonstrated prerequisites, available environment, observable corrected behavior, mentor/reviewer access, and maintenance cost. A track with no usable evidence path is a poor immediate pilot even if its name sounds attractive. Paid hardware or subscriptions are not required for the paper/simulation pilots here.

## Lesson 3: turn a broad subject into a falsifiable question

Bad project brief: “Research all AI attacks.” Better: “In the two-tenant retrieval fixture, does server-side filtering prevent Alice from retrieving Bob's document when a retrieved passage requests that action?” Name the system, boundary, property, and evidence.

For an updater: “Does installation reject a manifest whose signed digest differs from downloaded bytes?” For a local contract: “Can withdrawal make accounted liabilities exceed available assets?” For a parser: “Does every accepted length fit the available bytes and allocated capacity?” For a purple exercise: “Does the known harmless role-change action reach an actionable alert with the required identity fields?”

Write both a positive and negative control. An updater rejecting every package is not a successful update system; it must still accept an authorized valid package. A model refusing every query does not establish useful secure assistance. Measure legitimate task success alongside the security invariant.

## Lesson 4: execute a bounded pilot

1. Choose two candidate tracks and one small prerequisite demonstration for each.
2. Preserve a reproducible environment and synthetic data. Record version/build, scope, resource limit, and reset method.
3. Predict the normal and controlled-failure outcomes before running the lesson.
4. Change one assumption, collect minimal evidence, and consider an alternative explanation.
5. Repair the boundary or identify the missing design condition. Repeat the original test and a legitimate control.
6. Write a short report stating what the result establishes and what remains untested. Select the track whose work you want to repeat more deeply.

Keep a research backlog for subtopics beyond the pilot. AI may require retrieval provenance, resource budgets, evaluation datasets, and connector scopes. Embedded work extends into secure/measured boot, rollback, fleet identity, SBOM/manufacturing trust, side channels, and fault injection. Native research adds JIT, IPC, drivers, virtual devices, synchronization, and patch variants. Smart contracts add reentrancy, initialization/proxies, replay, oracles, ordering, governance, and economic invariants. The leaf tutorials teach these concepts; a successful first exercise is not evidence that the backlog is complete.

## Lesson 5: share a defensible result

Every track needs source attribution, precise version/build, observed facts, limits, recovery, and verified remediation. Use privacy minimization, fail-safe design, least privilege, tenant separation, and dependency review across architecture work. Advanced cryptographic protocol analysis, HSM/TPM internals, post-quantum migration, and side-channel resistance require additional mathematical and implementation expertise; retain them as explicit study branches rather than quietly folding them into a basic key-storage exercise.

For emulation, choose a business-relevant scenario and a small justified behavior set. Define starting access, permitted transitions, synthetic objective, control-team stop contact, visibility model, and cleanup. Command-and-control, persistence, collection, and exfiltration are behavior categories to understand through harmless substitutes and telemetry, not requirements to deploy in every exercise.

**Completion check:** a reviewer can reproduce your selected pilot, identify the failed assumption, verify the corrected behavior, and explain one plausible alternative cause you ruled out. Answer “Which track should I choose?” with evidence from a pilot, prerequisites, and available resources, not a claim that one field universally offers the best career outcome.
