# 21. Human and physical security assessments

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#21-human-and-physical-security-assessments)

<!-- TOPIC-TOC:START -->

## Contents

- [Knowledge and skill checklist](#knowledge-and-skill-checklist)
- [Safe projects and evidence](#safe-projects-and-evidence)
- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1: Model the workflow that creates risk](#stage-1-model-the-workflow-that-creates-risk)
  - [Stage 2: Design an exercise people can learn from](#stage-2-design-an-exercise-people-can-learn-from)
  - [Stage 3: Assess digital verification and reporting](#stage-3-assess-digital-verification-and-reporting)
  - [Stage 4: Review physical access as a lifecycle](#stage-4-review-physical-access-as-a-lifecycle)
  - [Stage 5: Interpret results without blaming individuals](#stage-5-interpret-results-without-blaming-individuals)
- [Worked lab: account-recovery tabletop](#worked-lab-account-recovery-tabletop)
- [Mastery and review criteria](#mastery-and-review-criteria)

<!-- TOPIC-TOC:END -->



**Prerequisites:** Assessment scoping, privacy, reporting, authentication, and communication. This track requires explicit agreement on participants, locations, scenarios, messages, information collected, and stop conditions. Technical authorization alone does not automatically include people or buildings.

## Knowledge and skill checklist

- [ ] Understand how workflow pressure, confusing interfaces, authority cues, and weak verification processes create risk. Focus findings on systems and processes instead of blaming individuals.
- [ ] Learn approved simulation design, stakeholder review, participant safeguards, accessibility, cultural sensitivity, and measurement that supports learning.
- [ ] Assess identity verification for account recovery, help-desk changes, payment instructions, supplier changes, onboarding, and offboarding through approved tabletop scenarios.
- [ ] Understand phishing, smishing, vishing, QR-code deception, impersonation, and synthetic-media risks at a recognition and control-design level.
- [ ] Study email authentication and filtering, domain monitoring, reporting channels, phishing-resistant authentication, callback procedures, and dual approval for sensitive changes.
- [ ] Measure reporting behavior, time to escalation, clarity of verification steps, and process resilience; click rate alone is an incomplete measure.
- [ ] Learn facility risk assessment: visitor management, escorts, badge issuance/revocation, door monitoring, reception procedures, server-room access, equipment storage, and secure disposal.
- [ ] Review clean-desk policies, screen locking, unattended devices, removable-media policies, printing, document handling, and visibility of sensitive information.
- [ ] Understand physical safety, emergency egress, accessibility requirements, incident escalation, and coordination with facilities/security teams.
- [ ] Treat locks, access-control systems, surveillance, and alarms as specialist systems; practical work uses training equipment or supervised, explicitly approved evaluations.
- [ ] Learn data minimization, anonymized reporting, retention limits, debriefing, and how to communicate findings without publishing personal information.

## Safe projects and evidence

1. Design a tabletop account-recovery exercise using fictional people, accounts, and documents; evaluate identity verification and escalation.
2. Create a training message and reporting workflow in a closed training environment using synthetic identifiers. Do not collect real passwords or tokens.
3. Conduct an agreed walkthrough with a facilities owner and document process improvements without bypassing locks, tailgating, or interfering with safety systems.

**Exit criteria:** Produce a reviewed exercise plan, privacy-aware metrics, a nonpunitive debrief, and specific control improvements. Explain which actions are outside the agreed scope and when the exercise must stop. Successful learning improves verification and reporting processes, not the humiliation of participants.

## Detailed learning sequence

### Stage 1: Model the workflow that creates risk

Choose one process: resetting a password, replacing an access badge, changing a supplier payment destination, granting a visitor entry, or disposing of a device. Interview the process owner within the agreed exercise. Draw the normal path, exceptional path, approval steps, information sources, and records retained. Identify where the person making a decision lacks reliable evidence or faces conflicting instructions.

- [ ] Distinguish identity claims, independent identity evidence, authorization, and transaction approval.
- [ ] Identify which contact details are obtained from a trusted record and which arrive with a request.
- [ ] Record time pressure, understaffing, unclear ownership, inaccessible procedures, and unavailable escalation contacts as process factors.
- [ ] Compare written policy with observed approved workflow; neither alone describes the complete system.
- [ ] Map failure consequences to accounts, data, payments, equipment, safety, and service continuity.

### Stage 2: Design an exercise people can learn from

Write an exercise charter naming purpose, sponsor, process owner, controller, participating roles, locations, start/end time, and permitted activities. Define synthetic identities and artifacts. State what evidence will be collected and who will see it. Agree on immediate stop conditions, reporting contacts, a withdrawal path, and how genuine incidents will be distinguished from exercise events.

Use tabletop discussion first. A facilitator presents a fictional request and asks participants to describe the verification steps they would perform. Record decisions and missing information without pressuring anyone to bypass policy. Move to closed simulations only when the tabletop exposes questions that actual workflow observation can resolve. Do not interpret permission for a technical test as permission to contact employees or enter facilities.

### Stage 3: Assess digital verification and reporting

Study message authenticity, domain identity, authentication signals, attachment handling, link destinations, and the limits of visual branding. Learn SPF, DKIM, and DMARC conceptually through your networking and email material; message authentication does not establish that an authorized sender's requested transaction is appropriate. Understand how compromised legitimate accounts change the problem.

Evaluate independent callback procedures, transaction-specific verification, dual approval, help-desk recovery evidence, escalation channels, and phishing-resistant authentication. Test these controls with fictional requests in the training environment. Prefer collecting a report event or decision record over collecting message contents, credentials, or personal behavior histories.

Study the user journey after reporting: acknowledgement, triage, useful feedback, immediate protective steps, and access to support. A prominent report button is valuable only if the resulting queue has ownership and a response process.

### Stage 4: Review physical access as a lifecycle

During a coordinated walkthrough, follow visitor registration, identity verification, badge issuance, escort assignment, access expiration, departure, and record retention. For employees and contractors, trace role changes, lost badges, offboarding, exceptions, and periodic access review. Review equipment movement, deliveries, storage, repair vendors, and disposal documentation.

Separate physical access authorization from emergency egress. Security recommendations must preserve the facility's safety requirements and be reviewed by qualified owners. Observe door monitoring and alarm response through approved demonstrations; do not manipulate equipment or trigger alarms unexpectedly. For locks and access-control devices, use training equipment or a specialist's supervised demonstration.

Assess documentation and observation points: reception coverage, door-held-open handling, server-room visitor logs, camera access permissions, and escalation handoffs. Do not photograph badges, people, screens, floor plans, or restricted areas unless the exercise explicitly permits the collection and provides a protected storage location.

### Stage 5: Interpret results without blaming individuals

Define the unit of measurement before the exercise. Examples include completion of independent verification, correct escalation route, response time, successful badge revocation, or identification of missing process ownership. Explain the denominator: participants, eligible events, completed scenarios, or observed decisions. Avoid comparing small groups in ways that reveal individuals.

Record the difference between process failure, inaccessible instructions, training gaps, technical control failure, and exercise artifact confusion. Collect contextual explanations during the debrief. An employee following a poorly designed workflow is evidence for improving that workflow. Document limitations such as advance notice, observer effects, and the small sample size.

## Worked lab: account-recovery tabletop

**Setup:** Create fictional users, a mock help-desk form, a reference directory, and a test policy. Invite consenting participants in an authorized training setting. Assign a facilitator, a process owner, and an observer. Prepare three scenarios: ordinary recovery, missing evidence, and an urgent request involving a privileged account.

**Actions:** Present each scenario without requesting a real password or contacting real staff outside the exercise. Ask participants to locate approved contact details, identify required evidence, select an escalation path, and record the decision. Introduce an unavailable supervisor as a discussion condition rather than creating a real emergency.

**Expected behavior:** Ordinary recovery follows the documented path; insufficient evidence leads to a safe escalation; urgency does not silently remove required checks; participants can identify the owner of an exception. A legitimate user still has a workable recovery route.

**Evidence:** Keep anonymized decision steps, time-to-route measurements, ambiguous policy excerpts, and proposed improvements. Record observations at the process level. Remove synthetic data when the agreed retention period ends.

**Correction:** Revise the policy, directory access, ownership, and form prompts. Re-run the same scenarios and add one accessible alternative for participants unable to use the original verification channel. Confirm the change improves both security and legitimate recovery.

## Mastery and review criteria

- [ ] Produce a complete charter with participants, data collection, stop conditions, and debrief arrangements.
- [ ] Explain why a control verifies a specific claim and what it cannot prove.
- [ ] Complete a process diagram including exceptions, handoffs, and lifecycle termination.
- [ ] Recommend an improvement with an owner, effort estimate, verification method, and user-impact assessment.
- [ ] Demonstrate anonymized reporting and removal of unnecessary personal information.
- [ ] Show that a legitimate scenario succeeds after the improvement and an insufficient-evidence scenario is handled predictably.

**Primary reference:** Use the [NIST Privacy Framework](https://www.nist.gov/privacy-framework) to organize privacy-risk thinking around collected exercise data. For facility-specific procedures, use the approved site policy and the manufacturer's documentation with the facilities owner. Local legal, labor, and safety requirements need review by the responsible specialists before any real-world assessment is planned.

