# 21. Tutorial: human and physical security assessments

[Index](README.md) | [Complete source curriculum](curriculum/21-human-and-physical-security-assessments.md) | [Original roadmap](../roadmaps/21-human-and-physical-security-assessments.md)

Prerequisites: scope, identity, privacy-aware evidence, and reporting. Complete this chapter as a fictional tabletop or a specifically agreed walkthrough. An application assessment does not implicitly include contacting employees, impersonating staff, entering buildings, or manipulating security equipment.

## Lesson 1: examine the decision, evidence, and pressure

Consider a mock help desk receiving “I lost my device; reset my account.” The claimed identity is an assertion. A contact detail taken from the same request is not independent evidence. The decision must use an approved verification route and a clear authority to grant the requested access.

Draw `request → verified identity → authorization check → action → audit → notification`. Add an exception branch for unavailable evidence. Repeat the model for payment destination changes, supplier changes, onboarding, offboarding, visitor admission, and badge replacement. Each workflow has distinct consequences: recovering an ordinary account and changing a privileged account need not have identical approval requirements.

Ask where a worker can find trusted contact details, who owns exceptions, and what happens outside ordinary hours. Time pressure, inaccessible instructions, confusing screens, understaffing, authority cues, or an absent supervisor can make an apparently simple rule unusable. The finding should identify that control failure rather than describe a person as careless.

## Lesson 2: recognize deception without constructing a campaign

| Category | Claim to question | Control to practice in a closed exercise |
| --- | --- | --- |
| Phishing/email | Sender identity or requested action | Report through the known channel and verify the transaction independently. |
| Smishing/SMS | Urgent link or identity | Navigate through the established application/contact route. |
| Vishing/voice | Claimed authority | Call back using an approved directory entry, not a supplied number. |
| QR-code deception | Hidden destination | Treat the decoded address as untrusted input; use a known service route. |
| Impersonation/synthetic media | Familiar appearance or voice | Require transaction-specific independent evidence and authorization. |

SPF, DKIM, and DMARC help evaluate email sending/domain relationships. Their success does not prove the sender's requested payment is authorized; a legitimate account can be compromised. Filtering, domain monitoring, phishing-resistant authentication, callbacks, and dual approval address different parts of the workflow. None turns visual branding into trustworthy proof.

After a report, trace acknowledgement, triage, ownership, escalation, feedback, and immediate protective steps. A report button whose queue has no owner is an incomplete control. Practice with an obvious fictional message stored in the training packet; do not collect credentials or send a live campaign to learn the process.

## Lesson 3: prepare an exercise people can use

Write a charter naming sponsor, process owner, facilitator/controller, observer, participants, permitted locations/channels, start/end, objective, synthetic artifacts, data collected, retention, and stop route. Define what distinguishes a genuine incident from exercise activity. Participants need an accessible withdrawal/escalation path; pressure to violate policy would undermine the test.

Use culturally appropriate, accessible wording and review scenario assumptions with the process owner. Specify concrete stop conditions: participant distress, an actual incident, a request beyond the agreed scope, or any safety concern. The facilitator stops the exercise and uses the agreed escalation route rather than treating those events as more test material.

Prepare a mock directory with invented names and internal extension labels, a recovery form, an evidence policy, and three scenario cards:

1. An ordinary user can complete the documented independent check.
2. The requester lacks required evidence and supplies a new callback number.
3. A privileged-account request is urgent while the usual approver is unavailable.

For each, ask the participant to locate the rule, select evidence, identify the authorizer, and explain the next step. The correct outcome is ordinary recovery, a safe pending/escalated case, and a privileged exception owned by the designated authority. Urgency alone is not evidence. A legitimate user also needs a viable alternative; a permanently unusable recovery process is not a successful design.

Record decisions, ambiguities, and elapsed time at the process level. Revise the form to distinguish trusted directory details from request-supplied details, add an exception owner, and provide an accessible alternative channel. Repeat the same cases plus one new case. Improvement means both unauthorized changes are prevented and legitimate recovery remains possible.

## Lesson 4: walk through physical access as a lifecycle

A coordinated walkthrough follows visitor registration, identity checks, temporary badge issuance, escort assignment, door access, expiration, departure, and record handling. For staff and contractors, add role changes, lost badges, periodic access review, and offboarding. Inspect the documented workflow with the facilities owner; practical lock, surveillance, alarm, and access-control testing belongs to approved training equipment or a qualified supervised evaluation.

| Area | Useful observation | Corrective outcome to verify |
| --- | --- | --- |
| Reception and doors | Who notices a held-open door and who responds? | A clear, usable response path with owner and timing. |
| Server rooms | Who approves, escorts, and logs access? | Access aligns with role and expires when no longer needed. |
| Equipment/repair/deliveries | How are custody and authorized movement recorded? | Records connect items, owners, vendors, and return/disposal. |
| Documents and screens | Printing, clean-desk practice, screen lock, visibility | Sensitive material is handled through a workable protected process. |
| Unattended devices/removable media | Ownership, storage, and permitted use | Clear handling policy and authorized support escalation. |
| Disposal | Data sanitization and custody documentation | Owner can verify the stated disposition without relying on appearance. |

Physical access controls must coexist with emergency egress, accessibility, and safety requirements. Record a concern for the responsible specialist; do not improvise changes to exits or alarms. Photographing badges, people, restricted layouts, or screens is a separate evidence-collection decision, not an automatic part of a walkthrough.

## Lesson 5: interpret outcomes with useful metrics

Suppose eight of ten tabletop scenarios reached the correct verification route. Report `8/10 scenarios`, not “80% of staff are secure.” Include which scenarios were eligible, whether participants had advance notice, observation effects, and the small sample. Click rate alone ignores reports, escalation speed, transaction verification, technical control outcomes, and recovery usability.

Distinguish process failure, unclear ownership, inaccessible instructions, training gaps, technical defects, and exercise confusion. Collect context in a nonpunitive debrief. Aggregate results so small groups do not identify participants indirectly. Retain only the evidence needed for the improvement decision and remove it according to the agreed schedule. The [NIST Privacy Framework](https://www.nist.gov/privacy-framework) provides a structure for thinking about exercise data and its lifecycle; actual workplace and safety rules need the responsible owners' review.

**Worked finding:** “The mock recovery form accepts requester-supplied callback details as independent identity evidence.” Evidence is the form and scenario decision trace. Repair is a trusted-directory verification route with an owned exception path. Retest ordinary recovery, missing evidence, unavailable approver, and the accessible alternative. No real password or personal record is needed.

**Answer checks:** A familiar voice does not establish transaction authority. A completed badge revocation request does not prove the access system applied it. A high report count can indicate a working reporting culture rather than more susceptibility. Pass with a charter, process diagram, anonymized results, an owned improvement, a successful legitimate case, a controlled insufficient-evidence case, and a debrief/cleanup record.
