# Tutorial: OT, ICS, and cyber-physical systems

[Index](../README.md) | [Full source curriculum](../curriculum/specializations/22-03-ot-ics-and-cyber-physical-systems.md) | [Original roadmap](../../roadmaps/specializations/22-03-ot-ics-and-cyber-physical-systems.md)

## Begin with a fictional process

This lesson uses a software tank with no physical outputs. Its purpose is to teach process interpretation, architecture, monitoring, and restoration. No controller, public service, radio, pump, heater, or operational network is required. The essential prerequisite is understanding networking and logs well enough to distinguish an observed packet from an interpretation of its effect.

Operational technology monitors or influences physical conditions. A cyber event matters partly because of the process consequence it could cause. An unavailable payroll screen and an unavailable operator display may both be application failures, but their timing, recovery priorities, and consequences differ. NIST OT guidance explicitly considers performance, reliability, and safety alongside security. As checked on 18 October 2026, the Revision 3 publication page also links an initial public draft of Revision 4; use the final or draft status deliberately. [NIST SP 800-82 Rev. 3 publication page](https://csrc.nist.gov/pubs/sp/800/82/r3/final)

Name the fictional process `Tank-Lab`. Its level is a number from 0 to 100. Normal operation is 35–65. The operator requests a setpoint of 50. The simulated controller adjusts an invented inflow variable. A modeled high-level interlock changes the simulated mode to paused at 80. These values are training assumptions, not engineering guidance for real tanks.

## 1. Distinguish process roles and states

A programmable logic controller, or PLC, reads inputs, evaluates logic, and updates outputs in a recurring cycle. An HMI displays process state and accepts authorized operator input. A historian stores time-series observations. An engineering workstation edits project logic and configuration. A remote terminal unit serves remote monitoring or control roles. A supervisory server coordinates higher-level visibility or control. Independent safety functions have their own requirements and should not be assumed to exist merely because a display has an alarm.

A sensor value describes an observation. A setpoint expresses desired behavior. An actuator command requests a physical effect. An interlock prevents or changes an operation under defined conditions. An alarm calls attention to a state requiring interpretation. Manual, automatic, maintenance, and paused modes alter the meaning of commands and limits.

Draw this process flow in a text file:

```text
Invented level -> simulated controller -> invented inflow -> model update
       |                  ^
       v                  |
HMI display <---- authorized operator setpoint
       |
       v
historian log with event time and arrival time
```

Label every value with units and ownership. Losing the HMI display is losing visibility; the controller may continue. Losing the ability to issue commands is losing control. Neither necessarily means the simulated level itself has stopped changing. Keep those distinctions in the incident record.

The controller's scan interval, communication latency, and jitter affect when a change is observed. Deterministic timing means behavior meets defined timing expectations, not that every event has zero delay. An ordinary IT control that adds unpredictable delay can change process behavior. Operators and engineers must explain what each alarm means in its actual operating mode.

## 2. Run a small model and interpret telemetry loss

Save this as a local Python exercise. It has no networking or physical-device code:

```python
level, setpoint = 50.0, 50.0
last_hmi = None
history = []
for tick in range(8):
    if tick == 2:
        setpoint = 60.0
    command = 2.0 if level < setpoint else 0.0
    mode = "paused" if level >= 80 else "automatic"
    if mode == "automatic":
        level = min(100.0, max(0.0, level + command - 1.0))
    telemetry_present = tick not in {4, 5}
    if telemetry_present:
        last_hmi = (tick, level)
        history.append({"event_time": tick, "level": level})
    age = None if last_hmi is None else tick - last_hmi[0]
    print(tick, "actual", level, "display", last_hmi,
          "age", age, "mode", mode)
```

First predict the output manually. At tick 4 the model still advances while the display retains its tick-3 value. Tick 5 makes that display older. At tick 6 fresh telemetry resumes. The correct observation is “visibility stale for two modeled intervals,” not “controller stopped.” This model simplifies process dynamics and contains no independent safety system.

Add an alarm when display age exceeds one interval. Then distinguish the alarm from the process interlock: stale telemetry warns the operator about evidence quality, while high level changes simulated control mode. Save the original and revised outputs. Deliberately delay one historian event by three ticks and keep both event time and arrival time. Sorting only by arrival time produces a misleading process sequence.

## 3. Map zones, conduits, and dependencies

Create zones for enterprise reporting, industrial operations, engineering, remote maintenance, and the fictional process. A conduit is an explicitly justified communication path between zones. Architecture labels are useful reasoning aids but do not prove enforcement.

| Source and destination | Purpose | Permitted direction | Evidence of enforcement |
|---|---|---|---|
| HMI to controller model | Read level; approved setpoint | Defined local API | Contract and authorization log |
| Historian to model | Read telemetry | Read only | No write operation exposed |
| Engineering to model | Approved version deployment | Maintenance state only | Change record and version hash |
| Enterprise to reporting copy | View summaries | No process command path | Separate copied dataset |
| Vendor role to maintenance service | Time-limited support | Approved window only | Expiry and session log |

List identity, DNS, time, certificates, backup storage, remote access, vendor support, and removable-media dependencies. A controller configuration backup that needs an unavailable license server may not be immediately restorable. A remote-maintenance account that remains enabled outside the window changes the trust model. A diagram omitting these dependencies will overstate independence.

Long equipment lifecycles make supported versions, spare parts, certified configurations, and maintenance windows relevant to remediation. Write a change proposal that includes the protected property, expected failure prevented, operational cost, validation method, rollback, and owner. For example, time-limited vendor access reduces unattended exposure but requires an available approver and a documented emergency support path.

## 4. Learn communications from a benign trace

Use the model's saved events as a supplied trace. Represent reads, setpoint changes, and project updates as distinct operation categories. Identify peers, polling intervals, request/response relationships, expected values, and error states. In a real industrial protocol, register or object numbers must be mapped using authoritative device documentation; a numeric address alone does not reveal engineering meaning.

Create ten normal read records at one-second modeled intervals and one approved setpoint change at tick 2. Your baseline contains routine reads, an authorized write, and known gaps at ticks 4 and 5. A rule that calls every write malicious is wrong because normal operation includes approved changes. A rule that calls every gap an outage ignores collection failure and timing variation.

Authentication and integrity properties depend on the actual protocol variant, gateways, configuration, and application controls. Do not infer an entire deployment's exposure from a protocol name. Passive observation can reduce interaction, but collection points and data handling still require approval in real environments. For this lesson all observations are generated locally.

Annotate each unusual event with alternatives. A delayed historian record may be a queueing issue. A quiet device may act only during a particular cycle. A transformed historian value may use a scaling function. A discrepancy between displayed and recorded values may be clock skew, stale telemetry, calibration, or a processing defect. These hypotheses guide the next evidence request.

## 5. Design controls that operators can use

Create an asset register containing role, software or firmware version, project version, owner, critical dependencies, recovery source, and observed communication paths. Review segmentation, administrator separation, access ownership, remote-session approval, controlled file transfer, and appropriate application allowlisting. Record who evaluates vendor advisories when patching cannot happen immediately.

For the fictional engineering endpoint, require a dedicated training administrator and a maintenance-mode flag before installing a project. Log old and new configuration hashes. Test the same action as a read-only observer: it should fail without changing the active version. Repair authorization in the model if it does not. Then repeat a permitted maintenance update to show that normal engineering remains possible.

Recovery material includes more than firmware. Preserve controller logic, configuration, certificates, role assignments, HMI mappings, historian interpretation, supported firmware combinations, licensing information, and spare-device instructions. Backups need integrity, confidentiality where relevant, and restoration evidence. A file existing in storage does not prove it can restore service.

## 6. Conduct a restoration tabletop

Assign named fictional roles: Mira as operator, Dev as engineer, Sana as safety lead, Chen as cyber analyst, and Ravi as exercise controller. Operations owns the simulated process-state decision. Engineering owns project restoration. Cybersecurity supplies evidence and communication recommendations. The controller can stop the exercise.

1. Start from a recorded normal baseline and save project and configuration hashes.
2. Inject “engineering workstation unavailable” as a written scenario. Do not attack or disconnect a real workstation.
3. Ask which approved maintenance conduit would be paused and how ongoing operator visibility is preserved.
4. Introduce the stale HMI reading from the earlier model. The operator must recognize uncertainty rather than assume the last value remains current.
5. Restore a clean copy of the model using the documented version. Verify identity, configuration, logic, display mapping, historian timestamps, and normal setpoint changes.
6. Compare restored state with the baseline and record every difference, owner, and explanation.

Stop the exercise if a proposed action would reach a physical device, expose unrelated data, exceed the fictional scope, or require an unavailable decision owner. In real work, stop conditions and process-specific engineering review must precede testing. A simulator never grants permission to probe a production controller.

Correlate engineering change records, HMI alarms, historian events, remote-access logs, network observations, and operator notes. State timestamp uncertainty. A single anomalous packet does not establish a cyber cause: mechanical faults, instrumentation problems, operator actions, and collection artifacts may explain the same symptom.

## Questions with answer guidance

1. **The HMI is stale but the model keeps changing. What failed?** Visibility failed; evidence does not yet show loss of control or loss of the process.
2. **Why might immediate patching be inappropriate?** Compatibility, timing, certified configurations, and availability requirements may require a validated maintenance plan and interim controls.
3. **Why is a restored controller insufficient?** Correct process state, trusted logic, identities, monitoring, and operator procedures also need validation.
4. **What makes a conduit defensible?** A specific operational purpose, narrow permitted operations, identified owners, and verified enforcement and recovery behavior.

Your completion package should contain the process diagram, modeled hazards, dependency inventory, conduit table, benign baseline, alarm timeline, decision log, hashes, and restored-state comparison. Record that physics, equipment wear, actual scan timing, real safety functions, and vendor-specific behavior were omitted. A good result explains both the security improvement and why an operator can carry it out without guessing.
