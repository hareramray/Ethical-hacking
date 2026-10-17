# 22.8 Adversary emulation and red/purple-team planning

[All topic roadmaps](../README.md) | [Specialization overview](../22-advanced-specialization-map.md)

<!-- TOPIC-TOC:START -->

## Contents

- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1: Define the question the exercise must answer](#stage-1-define-the-question-the-exercise-must-answer)
  - [Stage 2: Write an executable plan and rules of engagement](#stage-2-write-an-executable-plan-and-rules-of-engagement)
  - [Stage 3: Prepare the environment and instrumentation](#stage-3-prepare-the-environment-and-instrumentation)
  - [Stage 4: Run transparent purple-team iterations](#stage-4-run-transparent-purple-team-iterations)
  - [Stage 5: Measure response and translate findings into improvements](#stage-5-measure-response-and-translate-findings-into-improvements)
- [Worked lab: three harmless validation actions](#worked-lab-three-harmless-validation-actions)
- [Blind spots and completion gates](#blind-spots-and-completion-gates)

<!-- TOPIC-TOC:END -->



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

## Detailed learning sequence

### Stage 1: Define the question the exercise must answer

Start with a business-relevant defensive question: can the team identify and respond to an unauthorized change to a protected synthetic project? Describe the assets, roles, normal workflow, consequence, and available telemetry. Select a small set of behaviors relevant to that question. Treat adversary reports as evidence with provenance and confidence, not as scripts to reproduce indiscriminately.

- [ ] Distinguish vulnerability assessment, penetration testing, adversary emulation, control validation, and purple-team collaboration.
- [ ] Explain the difference between a technique label and an observable behavior in a specific environment.
- [ ] Define a synthetic objective that can demonstrate control performance without collecting real sensitive data.
- [ ] State initial access explicitly, including test accounts and privileges.
- [ ] Explain why each selected behavior contributes to the exercise question.
- [ ] Identify alternative benign events that can validate the same telemetry or response decision.

### Stage 2: Write an executable plan and rules of engagement

Document the sponsor, exercise owner, controller, operators, defenders, system owners, and emergency contact. Identify exact assets, identities, dates, allowed actions, prohibited effects, data rules, communication routes, visibility model, and termination authority. Agree how genuine incidents are handled during the exercise.

For each action, record prerequisites, expected state change, expected telemetry, detection hypothesis, measurement method, resource limit, rollback, and cleanup check. Specify whether an action is a live benign operation, a synthetic event, a replayed fixture, or a tabletop inject. These have different evidentiary strength and should not be reported as interchangeable.

Define stop conditions in observable terms: unexpected system instability, effects outside the test assets, exposure of non-synthetic data, inability to contact the controller, or an owner withdrawing the approved window. A control team must be able to stop the exercise and identify its artifacts.

### Stage 3: Prepare the environment and instrumentation

Use an owned monitored lab first. Create dedicated test identities, synthetic files, identifiable event markers, and a clean baseline. Verify time synchronization and source coverage. Confirm required logs arrive before testing detection logic. Capture the versions and configuration of the relevant controls.

Rehearse every action separately, including rollback. Ensure a harmless marker file remains harmless when scanned, synchronized, backed up, or processed by another service. Use mock endpoints for simulated collection or data movement. Do not introduce an Internet-facing command channel or durable hidden access merely to make a beginner exercise look realistic.

### Stage 4: Run transparent purple-team iterations

Begin with shared knowledge: explain the action, ask defenders to state expected evidence, execute the agreed benign behavior, and inspect results together. Separate observation from alerting, triage, escalation, and containment. A log record proves visibility; an alert proves a rule fired; neither alone proves that a responder understood the event.

Investigate failures layer by layer. Was the event generated? Collected? Parsed? Searchable? Matched? Suppressed? Routed? Understood? Acted upon? Record the actual cause rather than marking an entire technique as undetected. Tune one relevant component, then repeat the same case and a benign comparison case.

Limited-foreknowledge exercises require a distinct agreed visibility model and experienced coordination. They are not the default next step simply because transparent practice succeeded. The learning objective determines whether reduced foreknowledge adds useful evidence.

### Stage 5: Measure response and translate findings into improvements

Record action time, first observable evidence, alert time, triage start, correct interpretation, escalation, decision, and containment. Report missing timestamps explicitly. Measure detection quality and investigation completeness alongside speed. Fast containment of the wrong asset is not a successful response.

Map findings to owners and causes: telemetry configuration, rule logic, asset context, identity mapping, playbook ambiguity, missing authority, or communication delay. Write actionable improvements with testable acceptance criteria. Assign a retest that reproduces the relevant condition. Confirm that remediation does not create an unreasonable benign alert burden.

Study command-and-control, persistence, collection, and exfiltration as categories of behavior and observable evidence through documented reports and safe simulations. Keep practical work focused on approved benign events and synthetic data. Building stealth, evasion, or real data-removal capabilities is unnecessary for the training outcomes in this roadmap.

## Worked lab: three harmless validation actions

**Setup:** Use a local application with an administrator role, an endpoint sensor, and central logs. Create a fictional account and a synthetic document. Define three actions: an approved test-account role change, creation of an identifiable benign marker file, and a read of the synthetic document through the application. These actions validate different evidence sources without accessing unrelated data.

**Actions:** Rehearse each action, confirm logs, and reset. During the exercise, execute the written sequence while the controller records ground-truth timestamps. Defenders locate the events, evaluate the agreed suspicious context, and follow a mock escalation procedure. Pause if logs reveal unrelated sensitive information or the sequence affects an unexpected account.

**Expected behavior:** Each action produces its predicted evidence; correlations use the correct identity and asset; the team can explain whether the pattern warrants investigation under the training policy; response decisions are recorded; normal activity remains distinguishable.

**Evidence:** Deliver the plan, asset/identity scope, action log, relevant telemetry references, detection and response timestamps, investigation notes, gaps, and cleanup checklist. State which detections were tested through actual events and which responses were discussed only as a tabletop.

**Correction:** Repair the specific failed layer, such as missing role-change logs, an incorrect field mapping, or unclear escalation ownership. Re-run the affected action plus a legitimate negative case. Verify removal of test roles, marker files, synthetic records where appropriate, temporary configurations, and unused test credentials.

## Blind spots and completion gates

A known exercise marker can make a weak rule appear effective. A control may work only because defenders know the exact time. A successful synthetic event does not prove a production agent would emit the same fields. A technique mapping can omit prerequisites or privilege differences. Cleanup can remove visible files while leaving roles or scheduled configuration behind.

- [ ] Produce a reviewed plan with scope, stop conditions, owners, and reversible actions.
- [ ] Show evidence for every step from action to response.
- [ ] Explain at least one limitation introduced by simulation or advance notice.
- [ ] Assign improvements to root causes and verify them through focused retests.
- [ ] Demonstrate complete cleanup against the saved baseline.
- [ ] Deliver a collaborative debrief that improves controls without overstating exercise coverage.

**Primary resource:** Use [MITRE ATT&CK](https://attack.mitre.org/) to connect documented behaviors to relevant defensive questions. Read the underlying references and adapt to the environment. Pair the exercise with [Detection engineering, incident response, and forensics](../20-detection-engineering-incident-response-and-forensics.md) and [Reporting, remediation, and retesting](../23-reporting-remediation-and-retesting.md).

