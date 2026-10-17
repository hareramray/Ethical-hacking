# 23. Reporting, remediation, and retesting

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#23-reporting-remediation-and-retesting)

<!-- TOPIC-TOC:START -->

## Contents

- [Evidence and reasoning](#evidence-and-reasoning)
- [A useful assessment report](#a-useful-assessment-report)
- [Remediation that developers and administrators can use](#remediation-that-developers-and-administrators-can-use)
- [Communication skills](#communication-skills)
- [Expanded reporting curriculum](#expanded-reporting-curriculum)
  - [Module 1: Turn an observation into a defensible claim](#module-1-turn-an-observation-into-a-defensible-claim)
  - [Module 2: Make reproduction independent of your memory](#module-2-make-reproduction-independent-of-your-memory)
  - [Module 3: Explain severity and business consequence](#module-3-explain-severity-and-business-consequence)
  - [Module 4: Write a fix that addresses the cause](#module-4-write-a-fix-that-addresses-the-cause)
  - [Module 5: Design retesting before the fix lands](#module-5-design-retesting-before-the-fix-lands)
  - [Module 6: Produce reports for different readers](#module-6-produce-reports-for-different-readers)
- [Report quality-assurance rubric](#report-quality-assurance-rubric)
- [Final reporting capstone](#final-reporting-capstone)

<!-- TOPIC-TOC:END -->



**Priority:** Core. Begin this section with your first lab, not at the end of your studies.

## Evidence and reasoning

- [ ] Keep timestamps and time zones, target identifiers, test account roles, prerequisites, tool versions, relevant requests/responses, and host or application logs.
- [ ] Capture enough evidence for another authorized tester to reproduce the observation. A screenshot alone often misses identity, context, or the action that caused the result.
- [ ] Redact secrets and personal data while preserving the parts needed to assess the finding. Store unredacted evidence only when needed and under the agreed controls.
- [ ] Distinguish observed impact, reasonably supported potential impact, and untested speculation. Explain assumptions explicitly.
- [ ] Identify the root cause: missing authorization, excessive privilege, unsafe parsing, exposed secret, weak lifecycle control, or another specific failure.
- [ ] Use CWE and applicable testing/verification references when helpful. Include the standard version so future readers can understand the mapping.
- [ ] Rate severity using the agreed method. Explain business consequences and affected scope alongside technical scores.
- [ ] Preserve negative results and test limitations. State what you could not test because of access, time, safety, or environment differences.

## A useful assessment report

1. **Executive summary:** Objective, tested environment, main risks, strengths, and the most important corrective actions in plain language.
2. **Scope and constraints:** Assets, dates, perspectives, accounts, exclusions, dependencies, and material limitations.
3. **Methodology and coverage:** Applicable tests, depth, tools where relevant, and what remained untested.
4. **Findings overview:** IDs, titles, severity, affected systems, owners, and status.
5. **Detailed findings:** Expected behavior, actual behavior, prerequisites, minimal reproduction, evidence, impact, cause, and remediation.
6. **Remediation plan:** Immediate containment, durable fixes, systemic improvements, owners, priorities, and dependencies.
7. **Retest results:** What changed, exact evidence, remaining variants, and final status.
8. **Appendices:** Sanitized inventory, coverage matrix, terminology, and supporting technical details.

## Remediation that developers and administrators can use

- [ ] Explain where the control belongs. For example, object authorization belongs on the server for each relevant operation, not only in the interface.
- [ ] Recommend a specific class of fix that addresses the cause, and explain any compatibility or operational tradeoff.
- [ ] Distinguish a temporary mitigation from a durable change. Specify remaining exposure and a follow-up owner.
- [ ] Look for repeated patterns across endpoints, repositories, identities, or environments. One missing authorization check may indicate a shared architectural problem.
- [ ] Add a regression test that fails before the fix and passes after it, plus a control proving legitimate behavior still works.
- [ ] Retest adjacent variants: another role, record owner, HTTP method, API version, tenant, deployment, or authentication flow as appropriate.
- [ ] Use meaningful statuses: open, partially remediated, remediated and verified, risk accepted by owner, or not retested. A developer saying fixed is not verification.
- [ ] Confirm removal of test accounts, temporary files, certificates, access rules, and synthetic data according to the cleanup agreement.

## Communication skills

- [ ] Explain the same finding to an engineer in technical terms and to a business owner in terms of affected operations and data.
- [ ] Ask precise clarification questions, give a reproducible example, and respond to disagreement with evidence.
- [ ] Escalate an urgent finding through the agreed channel while preserving a written record.
- [ ] Learn clear status updates, handover notes, meeting preparation, time estimation, and respectful peer review.
- [ ] Understand assessment quality assurance: a second reviewer checks reproducibility, scope, severity, redaction, and whether the fix addresses the cause.

**Practice:** Write a report containing three real lab findings, one rejected false positive, a coverage matrix, an executive summary, and a retest appendix. Ask someone to reproduce one finding using only your report.

**Ready to move on:** Your report lets an owner understand the problem, an engineer fix it, and another tester verify the result without guessing.

## Expanded reporting curriculum

### Module 1: Turn an observation into a defensible claim

Begin with one sentence stating who can perform which unintended action on what resource under which conditions. Then separate the evidence supporting each element. A response containing an invoice does not establish cross-tenant exposure until you verify the request identity, expected invoice owner, tenant assignment, and whether intentional sharing applies.

Practice a four-column evidence ledger: observation, interpretation, supporting artifact, and uncertainty. Record alternative explanations before finalizing a finding. A cache could explain a stale response; an elevated session could explain unexpected access; a test fixture could have assigned the wrong owner. Use a small discriminating test for each plausible explanation.

**Exercise:** Start with a synthetic “user B can read user A's record” observation. Test identity, ownership, sharing, and fresh-session controls. Produce either a confirmed finding or a documented false-positive explanation. Both outcomes are useful when justified.

### Module 2: Make reproduction independent of your memory

Describe the starting state, environment, accounts by role, data prerequisites, action, expected behavior, and actual result. Use stable synthetic identifiers or explain how to create them. State whether a request is a first action, a replay, or a step in a sequence. Record relevant timing for races and asynchronous behavior without claiming a timing-sensitive result is deterministic.

Include minimal sanitized requests/responses and the fields that carry the evidence. Avoid burying the key fact in a large screenshot or full scanner export. Label artifacts and cross-reference them from the reproduction. Screenshots should show useful context, while machine-readable evidence can preserve values and sequence more precisely.

**Exercise:** Reproduce a finding from a clean browser profile and freshly seeded test accounts using only your own draft. Note every missing instruction. Ask a reviewer to follow the corrected draft without access to your terminal history.

### Module 3: Explain severity and business consequence

First determine the technical boundary and demonstrated effect. Then identify affected assets, exposed operations, data sensitivity, required privileges, user interaction, reachability, and available controls. State whether wider exposure was verified or is a plausible implication requiring further assessment.

Use the engagement's agreed scoring system. If using CVSS, record the version, vector, and reasoning for the selected metrics; distinguish base severity from additional threat/environment context. An exploitation forecast, a severe advisory, and a business priority represent different information. Document how they contribute rather than turning them into one unexplained number.

**Exercise:** Compare the same missing access check in two synthetic applications: a local training calendar and a multi-tenant billing service. Keep the technical evidence consistent and explain which contextual factors change business priority. Do not invent financial losses or regulatory conclusions without evidence.

### Module 4: Write a fix that addresses the cause

Identify the component responsible for enforcing the boundary. Explain what it must validate and when, including alternate entry points and background processing. Recommend established APIs or control patterns where appropriate. If the assessment lacks source access, describe the required behavior and assumptions rather than pretending to know the exact internal line that must change.

Separate containment, durable remediation, and systemic improvement. Restricting temporary exposure may reduce immediate risk; fixing shared authorization can address the root cause; adding a consistent access-control abstraction and regression suite can prevent recurrence. State compatibility considerations and legitimate use cases the fix must preserve.

**Exercise:** Write remediation for an ownership-check defect, an excessive service permission, and a leaked synthetic secret. The third requires considering credential revocation and replacement; merely deleting the visible string is not enough.

### Module 5: Design retesting before the fix lands

Record the vulnerable behavior, expected secure result, and positive control while the original evidence is fresh. Build a small variant matrix: identity, role, tenant, object state, endpoint, HTTP method, background operation, and deployment version where relevant. Choose variants according to the root cause and architecture; no finite set establishes every possible path is secure.

At retest, confirm that you are assessing the corrected build and intended environment. Distinguish a denial caused by the fix from a broken service, expired account, removed test record, or unrelated network block. Use logs or source review to strengthen the interpretation when available.

**Exercise:** Retest an application that now returns an error but still performs the forbidden action through a worker. Explain why a status-code-only check would have missed the remaining flaw. Confirm both the response and side effects after the complete correction.

### Module 6: Produce reports for different readers

The executive summary should answer what was assessed, which risks matter most, what action is needed, and what the assessment could not determine. Detailed findings support implementation and verification. Appendices hold useful technical depth without forcing every reader through raw output.

Practice a short verbal walkthrough: objective, strongest evidence, consequence, recommended fix, and unresolved question. Avoid theatrical language or absolute claims. When a developer disputes a finding, revisit preconditions and evidence together. A corrected finding is a quality improvement, not a failure of professionalism.

## Report quality-assurance rubric

| Review dimension | What a reviewer should be able to establish | Reason to return the draft |
| --- | --- | --- |
| Scope | Every tested asset and action was within the agreed boundary. | Unexplained target or account. |
| Reproducibility | Preconditions and minimum actions lead to the described result. | Missing state or identity context. |
| Evidence | Artifacts directly support the stated observation. | Screenshots imply more than they show. |
| Severity | Technical and business reasoning are explicit. | Scanner score copied without context. |
| Remediation | The recommendation corrects the underlying failure. | Generic “sanitize input” without context. |
| Retesting | Both forbidden and legitimate behavior were checked. | Success inferred from a single error response. |
| Privacy | Sensitive artifacts are handled according to agreement. | Tokens or unrelated personal records included. |
| Clarity | An owner and an engineer can both act on the report. | Unexpanded jargon or contradictory statuses. |

## Final reporting capstone

Create an assessment report with three distinct root causes, one inconclusive result, one dismissed false positive, and a coverage matrix. Add a prioritized remediation plan without assigning arbitrary universal deadlines. Retest two corrected findings, leave one clearly marked open, and produce an artifact cleanup record.

**Pass:** A peer reproduces one finding, understands one limitation, and verifies one fix using the report. The executive summary agrees with the detailed results; no unsupported claim becomes stronger when repeated in a summary.
