# Tutorial: IoT, embedded systems, and hardware

[Index](../README.md) | [Full source curriculum](../curriculum/specializations/22-02-iot-embedded-systems-and-hardware.md) | [Original roadmap](../../roadmaps/specializations/22-02-iot-embedded-systems-and-hardware.md)

## Start with a device you can explain and recover

Use an emulator for the practical exercise below. It requires no physical wiring and makes update state transitions visible. An owned low-voltage development board is a later extension after reading its schematic, processor manual, bootloader guide, pinout, power limits, and errata. The goal is to connect firmware evidence to runtime behavior and then demonstrate a recoverable update design.

A microcontroller commonly combines a processor, memory, and peripherals for dedicated control. A system-on-chip, or SoC, integrates multiple computing functions; an application processor typically supports a richer operating system. These categories overlap. Flash stores persistent firmware, RAM holds working state, ROM may contain immutable startup code, and memory-mapped peripheral registers make hardware functions accessible through addresses.

Reset starts a defined boot path: initial ROM or boot code, bootloader, firmware initialization, interrupt setup, scheduler or main loop, then peripheral activity. An interrupt temporarily transfers execution to a handler. A watchdog expects periodic service and can reset an unresponsive system. A memory map tells you which ranges refer to executable code, RAM, device registers, or reserved regions. It does not prove that every range has equal access protection.

Before touching hardware, distinguish voltage, current, and power. Logic interfaces depend on documented voltage levels and a common reference; incompatible levels can damage components. Pull-ups establish a default signal state. Continuity checking belongs on an appropriately unpowered circuit using the instrument's documented method. Follow electrostatic-discharge handling guidance. Do not connect an unknown header based on wire color or an online photo. Keep mains circuits and unknown powered equipment outside beginner practice.

## 1. Build an interface inventory

Imagine a training temperature sensor named `SIM-17`. It has a debug console, a sensor bus, a local configuration screen, and a cloud-style message interface implemented entirely in local memory. Describe each interface before proposing a vulnerability:

| Interface | Intended use | Input and output | Boundary to verify |
|---|---|---|---|
| UART console | Development diagnostics | Boot log, optional commands | Does output expose synthetic secrets? |
| JTAG or SWD | Processor debugging | Memory and execution control | Is availability consistent with lifecycle policy? |
| SPI sensor | Synchronous peripheral traffic | Commands and readings | Which code validates returned lengths? |
| I2C sensor | Addressed bus transactions | Register selection and values | How are timeout and absent-device states handled? |
| Companion app | Account and configuration | Enrollment, preferences | Who owns this device? |
| Cloud connector | Telemetry and commands | Topic or resource messages | Which identity can publish or read? |

UART output is not automatically an authenticated administration interface. JTAG and SWD provide debugging capabilities that differ from an application protocol. SPI typically uses chip selection and clocked transfers; I2C uses addressing, clocking, and acknowledgments. Decode a saved training trace into command, address, data, and result. For example, an I2C register read returning `00 19` may mean 25 units in your fictional encoding; the bytes alone do not establish a real sensor's units or authentication.

Include removable storage, wireless connections, local services, factory programming fixtures, and manufacturing provisioning in the inventory even when the emulator omits them. A sensor value becomes a firmware decision, then a telemetry message, then a dashboard value. At every conversion ask who can change the input and how errors are represented.

## 2. Review firmware as a reproducible software artifact

Create a disposable directory containing `manifest.json`, `application.bin` with invented bytes, and `config.json`. Record where each file originated and compute a SHA-256 hash using `Get-FileHash -Algorithm SHA256` in PowerShell or a standard Python hashing function. Hashes identify artifacts; a hash obtained alongside an untrusted download does not establish publisher authenticity.

Inspect packaging before extracting content. Identify manifest metadata, compression, partition descriptions, filesystem images, application components, and bootloader components. Build an evidence table linking an artifact hash to a component, a build option, and an observed runtime path. A library filename is evidence of presence, not proof that a vulnerable function is reachable. A key-shaped string may be a public certificate, test fixture, or unused example; classify its purpose before calling it a secret.

Read a small C input parser from your own training firmware. Mark buffer lengths, signed and unsigned integer conversions, ownership of allocated memory, and state shared with interrupt handlers. A 16-bit length promoted into a different type can change range assumptions. A variable accessed both in the main loop and an interrupt needs a synchronization design appropriate to the processor and compiler; `volatile` alone is not a general race fix.

Inventory third-party components with an SBOM, including versions, provenance, build configuration, and whether they are shipped or merely used during building. Review development credentials, debug logging, default configuration, and device-specific provisioning separately. Zephyr's official security material links secure coding, threat modeling, hardening, and vulnerability handling; use the documentation matching a chosen build. [Zephyr security documentation](https://docs.zephyrproject.org/latest/security/index.html)

## 3. Distinguish boot and update guarantees

Secure boot makes a policy decision about permitted executable software. Measured boot records measurements that another component may use for evaluation; recording a hash alone does not prevent execution. Draw the trust anchor, verifier, signing authority, protected version state, and every executable stage. Configuration can remain unprotected even when one application image is signed.

For an update, separate authenticity, integrity, freshness, compatibility, and recoverability. A correctly signed older image can violate rollback policy. A valid image for another board can be incompatible. A verified download can still leave a device unusable if installation loses power halfway through. Real designs need an authenticated manifest and a documented trust-anchor lifecycle; the following model deliberately abstracts cryptography to supplied boolean test results.

```python
from dataclasses import dataclass

@dataclass
class Image:
    version: int
    board: str
    signature_ok: bool
    digest_ok: bool

def permitted(image, minimum_version):
    return (image.signature_ok and image.digest_ok
            and image.board == "training-board"
            and image.version >= minimum_version)

fixtures = {
    "valid": Image(3, "training-board", True, True),
    "altered": Image(3, "training-board", True, False),
    "incompatible": Image(3, "other-board", True, True),
    "older": Image(1, "training-board", True, True),
}
for name, candidate in fixtures.items():
    print(name, permitted(candidate, minimum_version=2))
```

Expected output is `valid True` and `False` for the other three cases. This tests decision logic only. It neither implements signatures nor proves hardware storage protects a counter. Add an unknown signer fixture when replacing booleans with a documented training signature library.

## 4. Model interrupted installation and recovery

On paper create slots A and B. Slot A contains confirmed version 2. Slot B is empty. Define states `downloaded`, `verified`, `staged`, `trial`, and `confirmed`. Installation writes the inactive slot; trial boot is confirmed only after a health check. Recovery must return to an allowed, known-good image or an explicitly authorized recovery path.

1. Save the baseline image, configuration hash, boot selection, and minimum version.
2. Stage valid version 3 without changing the active slot. Simulate interruption here: version 2 must remain bootable.
3. Mark version 3 as a trial. Simulate a failed health check: the recovery policy selects the documented fallback.
4. Repeat with a successful health check. Confirm version 3 and update protected state according to the actual design.
5. Try an altered image and verify that no boot-selection state changes.
6. Compare recovered software, configuration, identity, and monitoring against the baseline rather than checking only network availability.

Write down the difficult edge case: if the anti-rollback minimum advances before a trial is confirmed, the older fallback may become forbidden. A real bootloader must define how its recovery and rollback policies interact. Emulation exposes this design question without power-cycling hardware. Also account for finite flash endurance, storage capacity, manifest parsing failures, and compatibility between application and bootloader revisions.

## 5. Trace identity and fleet operation

Give `SIM-17` its own fictional credential. Follow manufacturing, enrollment, routine authentication, rotation, revocation, reset, transfer, and disposal. A shared fleet secret makes one compromise relevant to many devices; per-device identities permit narrower revocation. Record where keys reside, which code can use them, and what physical access assumptions apply. Secure storage reduces particular risks but does not make every caller authorized.

Factory reset may clear user preferences while preserving manufacturing identity. Ownership transfer should remove the old account association and its access according to the product design. Test old and new fictional owners against the mock service. Disposal must address credentials and retained data, not just a blank screen. End-of-support planning includes inventory, user notice, dependency support, and a defined operating or retirement policy.

For MQTT, model a topic such as `devices/SIM-17/telemetry` and a separate command topic. The device may publish its telemetry while only a designated controller publishes commands. Review subscriptions, retained messages, client identity, and duplicate delivery behavior; a retransmitted command must not accidentally repeat a non-idempotent action. MQTT delivery semantics do not replace application authorization. For CoAP, identify resources, methods, constrained transport assumptions, and the selected security mechanism from the applicable specification.

MQTT defines different quality-of-service levels, so document which level the exercise models rather than assuming all delivery is identical. A retained message also has a lifecycle: an old configuration can still be delivered to a new subscriber unless your design manages it. Verify the broker's topic policy separately from protocol delivery behavior. [OASIS MQTT 5.0 specification](https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html)

Now simulate a cloud outage, incorrect clock, expired training certificate, and lost companion-app session. Expected outcomes should include clear local status, bounded retries, and no silent fallback to unrestricted enrollment. Review remote disablement policy and how revoking one lost device avoids disrupting unrelated devices.

## Troubleshooting and completion evidence

An unreadable serial log may reflect logic-level mismatch, baud configuration, clock errors, or a boot failure. Do not keep changing wires blindly. In the emulator, silent output may simply mean logging is disabled. A signed image accepted by the model says nothing about whether a physical trust anchor can be replaced. Record emulator limitations for flash behavior, timing, physical debug locks, and key storage.

Deliver the interface inventory, firmware hashes, component inventory, update decision table, interrupted-update timeline, recovery comparison, and identity lifecycle tests. If the board lacks a feature, report it as unsupported before deciding whether that absence violates the intended requirements. Repair the demonstrated layer—manifest checks, state transitions, revocation, or configuration protection—and rerun invalid and valid updates.

Side channels infer secrets from observable effects such as timing or power. Fault injection deliberately perturbs execution. These are advanced research tracks requiring specialist equipment, physical assumptions, and expertise; this lesson uses a conceptual threat model, not physical attack procedures. Manufacturing trust and provisioning quality remain important even when firmware verification works correctly.

## Questions with answer guidance

1. **Why can a signed update be unsafe?** It may be too old, incompatible, incorrectly configured, or unrecoverable after interruption.
2. **Does a firmware string prove a credential leak?** No. Establish whether it is secret, active, reachable, and shared, then show its use with synthetic evidence.
3. **What proves recovery?** Trusted executable state, compatible configuration, intended identity, and restored monitoring—not merely a successful ping.
4. **What should an SBOM finding trigger?** A component-specific review of version, configuration, reachability, and remediation, rather than an automatic claim that every listed advisory applies.
