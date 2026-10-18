# 22.3 OT, ICS, and cyber-physical systems

[All topic roadmaps](../README.md) | [Specialization overview](../22-advanced-specialization-map.md)

<!-- TOPIC-TOC:START -->

## Contents

- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1: Understand the process before the network](#stage-1-understand-the-process-before-the-network)
  - [Stage 2: Model architecture and operational dependencies](#stage-2-model-architecture-and-operational-dependencies)
  - [Stage 3: Learn industrial communications through observation](#stage-3-learn-industrial-communications-through-observation)
  - [Stage 4: Design controls around operational constraints](#stage-4-design-controls-around-operational-constraints)
  - [Stage 5: Practice incident coordination and restoration](#stage-5-practice-incident-coordination-and-restoration)
- [Worked lab: fictional tank monitoring and recovery](#worked-lab-fictional-tank-monitoring-and-recovery)
- [Debugging blind spots and study boundaries](#debugging-blind-spots-and-study-boundaries)

<!-- TOPIC-TOC:END -->



**Prerequisites:** Networking, defensive monitoring, industrial-process basics, and safety engineering awareness.

- [ ] Learn PLCs, HMIs, historians, engineering workstations, safety systems, zones/conduits, and industrial protocol trust assumptions.
- [ ] Understand availability, deterministic timing, equipment lifecycles, maintenance windows, vendor dependencies, and the difference between cyber impact and physical consequences.
- [ ] Study asset inventory, passive visibility, remote-access governance, segmentation, backup/recovery, change control, and incident coordination with operators.

**Project:** Use a simulator with an entirely fictional process to review architecture and monitor benign traffic. **Pass:** Explain hazards and stop conditions and propose controls that respect operational requirements. Use [NIST OT security guidance](https://csrc.nist.gov/pubs/sp/800/82/r3/final) and [CISA ICS recommended practices](https://www.cisa.gov/resources-tools/resources/ics-recommended-practices). Never substitute a production controller for a training simulator.

## Detailed learning sequence

### Stage 1: Understand the process before the network

Start with a completely fictional process such as a simulated tank level displayed on a screen. Learn sensor values, actuator commands, setpoints, control loops, interlocks, alarms, and operating modes. Explain which values describe reality, which represent operator intent, and which determine an automatic action. Keep the process disconnected from physical pumps, heaters, motors, or other actuators.

- [ ] Describe the role of a PLC, HMI, historian, engineering workstation, remote terminal unit, and supervisory server.
- [ ] Distinguish basic process control from independent safety functions.
- [ ] Read a simple process diagram and identify normal ranges, unsafe states, and recovery states.
- [ ] Understand scan cycles, deterministic timing, latency, jitter, and why ordinary IT assumptions can fail.
- [ ] Name the operator and engineering knowledge needed to interpret each process alarm.
- [ ] Explain the difference between losing visibility, losing control, and losing the underlying process.

### Stage 2: Model architecture and operational dependencies

Create zones for enterprise systems, industrial operations, engineering access, remote maintenance, and the fictional process. Draw every permitted conduit and its business purpose. Include identity, DNS, time, backup, remote access, vendor support, and removable-media dependencies. Architectural layers help organize reasoning, but a diagram does not prove separation.

Study long equipment lifecycles, vendor-certified configurations, maintenance windows, licensing, unsupported operating systems, spare parts, and recovery dependencies. Assess how a proposed control changes operator workload, timing, troubleshooting, or emergency response. Security recommendations must fit the actual process and be reviewed by its responsible specialists.

### Stage 3: Learn industrial communications through observation

Use supplied traces or a simulator to identify request/response patterns, function categories, register or object models, polling rates, and device roles. Study protocol authentication and integrity assumptions, but do not infer a live system's exposure from a protocol name alone. Gateways, secure variants, isolation, and application controls alter the trust model.

Map an observed network value to its engineering meaning in the simulator. Distinguish routine reads, configuration changes, control operations, and maintenance activity. Establish a benign baseline: peers, expected protocols, frequencies, timing ranges, and ordinary exceptions. Passive observation is a starting technique; it still needs approved collection points and evidence-handling rules in real environments.

### Stage 4: Design controls around operational constraints

Review asset inventory, access ownership, segmentation, remote session approval, administrator separation, application allowlisting where appropriate, backup integrity, and logging. Explore time-limited vendor access, controlled file transfer, documented maintenance sessions, and session termination. Define responsibility for evaluating an advisory when an immediate patch is not feasible.

For each control, list the protected property, the failure mode it addresses, the operational dependency, the validation method, and the recovery path. Discuss compensating controls with operators rather than assuming one generic hardening baseline fits every device. Include spare-device configuration, firmware compatibility, engineering project files, certificates, and licensing in recovery planning.

### Stage 5: Practice incident coordination and restoration

Write a tabletop plan that brings together operations, engineering, safety, cybersecurity, communications, and vendor support. Define who can change process state, isolate a connection, restore a project, or approve return to service. Record stop conditions and escalation paths before any exercise.

Study evidence sources such as engineering change records, historian data, HMI alarms, remote-access logs, network observations, and operator notes. Correlate them carefully: a process upset may have mechanical, instrumentation, operational, or cyber causes. Avoid claiming a cyber cause from a single anomalous packet. Recovery includes verifying trusted configuration and safe process state, not merely booting a controller.

## Worked lab: fictional tank monitoring and recovery

**Setup:** Create a software-only process model with a level value, an HMI-like display, a historian-like log, and a simulated controller. Use a private virtual network with no physical outputs and no connections to operational networks. Define normal operating ranges and a safe paused state within the model. Save the controller logic and all configuration as versioned training artifacts.

**Actions:** Observe a normal run and record its expected traffic. Change a simulated operator setpoint through the approved interface and verify the audit trail. Introduce a missing telemetry source and a delayed historian event as test conditions. Conduct a tabletop in which a fictional engineering workstation must be isolated, then restore the model from saved configuration.

**Expected behavior:** Monitoring distinguishes changed setpoints from lost visibility; the operator can identify the simulated safe state; restoration uses the correct project version; event timing is interpreted with stated uncertainty; no action affects a physical process.

**Evidence:** Deliver the process diagram, asset and dependency inventory, conduit table, benign traffic profile, alarm timeline, decision log, configuration hashes, and restored-state comparison. Document which behaviors are simplified by the simulator.

**Correction:** Repair missing ownership, overly broad simulated access, incomplete backups, or ambiguous alarms. Repeat the relevant scenario and demonstrate that the operator can follow the revised procedure without guessing.

## Debugging blind spots and study boundaries

A quiet device may communicate only during a specific cycle. A historian can show delayed or transformed data. An HMI display can be stale while the controller continues operating. A known device model may have a different firmware, function, or safety role at another site. Network reachability does not establish permission to interrogate a device.

Never validate simulator findings by scanning production controllers or issuing experimental process commands. The next stage of professional work requires process-specific supervision, documented engineering review, vendor guidance, and explicit authorization. Simulation results should state exactly which physical and timing behaviors were omitted.

- [ ] Explain the fictional process, its normal state, and its modeled hazards.
- [ ] Map every permitted communication path to an operational purpose.
- [ ] Identify monitoring blind spots and alternative explanations for anomalies.
- [ ] Demonstrate restoration of logic, configuration, identity, and monitoring.
- [ ] Produce an incident tabletop with named decision owners and clear stop conditions.
- [ ] Defend one proposed control in terms of both security and operational usability.

**Primary reading:** Use [NIST SP 800-82 Rev. 3](https://csrc.nist.gov/pubs/sp/800/82/r3/final) for OT architecture, threats, and controls, alongside the CISA practices linked above. Check the publication page for revision status when beginning a real engagement. Obtain protocol and device behavior from the relevant official specification and manufacturer documentation.

