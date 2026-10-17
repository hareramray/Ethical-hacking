# 22.2 IoT, embedded systems, and hardware

[All topic roadmaps](../README.md) | [Specialization overview](../22-advanced-specialization-map.md)

<!-- TOPIC-TOC:START -->

## Contents

- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1: Learn the electrical and computing foundations](#stage-1-learn-the-electrical-and-computing-foundations)
  - [Stage 2: Inventory interfaces and trust boundaries](#stage-2-inventory-interfaces-and-trust-boundaries)
  - [Stage 3: Analyze firmware as a software artifact](#stage-3-analyze-firmware-as-a-software-artifact)
  - [Stage 4: Study boot, identity, and updates](#stage-4-study-boot-identity-and-updates)
  - [Stage 5: Review networked behavior and fleet operation](#stage-5-review-networked-behavior-and-fleet-operation)
- [Worked lab: an update and recovery review](#worked-lab-an-update-and-recovery-review)
- [Debugging blind spots and completion gates](#debugging-blind-spots-and-completion-gates)

<!-- TOPIC-TOC:END -->



**Prerequisites:** C, Linux, networking, electronics fundamentals, and safe handling of low-voltage equipment.

- [ ] Study microcontrollers, SoCs, bootloaders, memory maps, embedded operating systems, firmware formats, UART/JTAG/SWD concepts, SPI/I2C, and debug-interface exposure.
- [ ] Review firmware provenance, signing, secure/measured boot, rollback protection, update recovery, device identity, key provisioning, secure storage, and end-of-support behavior.
- [ ] Assess companion apps, local services, device-to-cloud authorization, MQTT/CoAP concepts, fleet management, reset behavior, and disposal.
- [ ] Understand SBOMs, third-party components, manufacturing trust, physical access assumptions, and side-channel/fault-injection concepts as advanced research areas.

**Project:** Review firmware for an owned development board or emulator and threat-model its update path. **Pass:** Produce an interface inventory, reproducible findings, and a verified update/recovery design without interacting with deployed third-party devices.

## Detailed learning sequence

### Stage 1: Learn the electrical and computing foundations

Begin with a low-voltage development board or emulator that has public documentation. Read the board schematic, processor reference, pinout, power requirements, and programming guide. Learn voltage versus current, common ground, logic levels, pull-ups, continuity, electrostatic-discharge handling, and the consequences of connecting incompatible interfaces. Keep mains-powered equipment and unknown circuits outside beginner practice.

- [ ] Distinguish a microcontroller from an application processor and an SoC.
- [ ] Explain flash, RAM, ROM, memory-mapped peripherals, interrupts, watchdogs, and boot stages.
- [ ] Follow reset through bootloader, firmware initialization, task scheduling, and peripheral setup.
- [ ] Read enough C to identify buffer sizes, integer widths, ownership, and interrupt-shared state.
- [ ] Use a known-safe development connection and record the documented voltage and pin assignments.
- [ ] Establish a recovery path before changing firmware or persistent configuration.

### Stage 2: Inventory interfaces and trust boundaries

List physical interfaces, debug headers, removable storage, local network services, wireless connections, companion apps, cloud APIs, and manufacturing provisioning systems. For each, record intended users, required privilege, accepted input, exposed data, and availability during normal use. Distinguish UART console output from an authenticated management interface and JTAG/SWD debugging from an ordinary application protocol.

Study SPI and I2C at the transaction level using a documented training peripheral or saved trace. Understand chip select, addresses, clocking, command framing, and error handling. Learn that visible traffic does not reveal whether an upper layer authenticates messages. Identify trust boundaries between a sensor reading, firmware decision, network message, and cloud command.

### Stage 3: Analyze firmware as a software artifact

Obtain firmware from your own build or the board's authorized distribution channel. Record its provenance and hash. Identify packaging, metadata, compression, partitions, filesystem images, application components, and bootloader components. Distinguish strings and configuration remnants from actively used functionality.

Inspect dependency versions, build options, default settings, logging, development credentials, and device-specific provisioning. Review source where available, then verify selected behavior on the board or emulator. Do not assume every extracted key-like string is a secret or that a shared library's presence proves the vulnerable path is reachable. Maintain an evidence chain from artifact to component to runtime use.

### Stage 4: Study boot, identity, and updates

Explain secure boot as a trust decision about what may execute and measured boot as recorded evidence about what executed. Identify the trust anchor, verification stage, signing authority, and protected state. Study version counters, rollback policy, recovery images, update manifests, interrupted updates, and limited flash endurance.

Trace device identity from manufacturing through enrollment, normal authentication, credential rotation, factory reset, transfer, and disposal. Compare shared fleet credentials with per-device credentials and explain revocation scope. Identify where keys live, which processes can use them, and what physical-access assumptions the design makes.

For updates, define authenticity, integrity, freshness, compatibility, and recoverability separately. A signed image can still be wrong for the hardware or older than the allowed release. A robust update process verifies the artifact and survives interruption according to its documented recovery design.

### Stage 5: Review networked behavior and fleet operation

Build a local mock service for the device. Learn MQTT topic authorization, client identity, subscriptions, retained messages, and delivery semantics; learn CoAP resource models and constrained-network assumptions when relevant. Trace which party may publish commands, read telemetry, change configuration, or enroll new devices.

Review companion-app authorization, local discovery, account linking, reset behavior, cloud outages, time synchronization, and certificate expiration. Evaluate fleet inventory, end-of-support communication, remote disablement policy, and ownership transfer. Plan how a lost device is removed without disturbing unrelated devices. Study an SBOM as an inventory input rather than a guarantee that every component risk is understood.

## Worked lab: an update and recovery review

**Setup:** Use one owned development board with a documented bootloader or an emulator with equivalent update states. Build a harmless sensor simulator that publishes invented readings to a local mock endpoint. Preserve the baseline firmware, configuration, and recovery instructions. Use training signing keys that never protect real devices.

**Actions:** Test a valid update, an image with altered bytes, an incompatible image, and an older version against the intended policy. Model interruption at defined update stages using an emulator or the board's documented training recovery method. Reset the device and test whether its old account association persists as designed.

**Expected behavior:** Invalid or unauthorized images are rejected; valid compatible images install; rollback behavior matches the documented policy; interruption has a defined recoverable state; resetting or transferring the device follows its intended identity lifecycle.

**Evidence:** Keep hashes, image metadata, boot logs, version state, test conditions, device identity state, and recovery results. Distinguish a feature unsupported by the board from one implemented incorrectly. Record all limitations of emulated flash, timing, and hardware key storage.

**Correction:** Improve manifest checks, state transitions, key handling, credential revocation, or recovery design as indicated. Retest the failure case and a valid update. Demonstrate that recovery restores trustworthy software rather than merely restoring network connectivity.

## Debugging blind spots and completion gates

An unstable serial connection can be an electrical mismatch. A device that appears silent may have a boot failure, incorrect clock configuration, wrong interface parameters, or no application logging. A factory reset may clear user settings without removing manufacturing identity. A firmware signature may authenticate one component while leaving configuration or another boot stage unprotected.

- [ ] Explain the boot chain and each identity's purpose from evidence.
- [ ] Produce an interface inventory with physical-access assumptions.
- [ ] Reproduce one firmware or update defect safely and verify a correction.
- [ ] Demonstrate documented recovery from a controlled failed update.
- [ ] Trace enrollment, rotation, reset, transfer, and disposal for a synthetic device identity.
- [ ] Explain which side-channel or fault-injection questions require specialist equipment and expertise.

**Primary resources:** Study [Zephyr's security documentation](https://docs.zephyrproject.org/latest/security/index.html) for an embedded project perspective and [NIST SP 800-213](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-213.pdf) for device cybersecurity requirements. The board vendor's schematic, reference manual, bootloader guide, and errata are essential evidence for hardware-specific conclusions.

