# 24. Capstones, portfolio, and career direction

[All topic roadmaps](README.md) | [Original master roadmap](../../ETHICAL_HACKING_ROADMAP.md#24-capstones-portfolio-and-career-direction)

<!-- TOPIC-TOC:START -->

## Contents

- [Project ladder](#project-ladder)
- [Build a portfolio with substance](#build-a-portfolio-with-substance)
- [Select a direction](#select-a-direction)
- [Optional credentials](#optional-credentials)
- [Bug bounty as a separate practice route](#bug-bounty-as-a-separate-practice-route)
- [Expanded project roadmap: build evidence of useful work](#expanded-project-roadmap-build-evidence-of-useful-work)
  - [Stage 1: Choose a bounded problem](#stage-1-choose-a-bounded-problem)
  - [Stage 2: Build a coherent foundation portfolio](#stage-2-build-a-coherent-foundation-portfolio)
  - [Stage 3: Add an unfamiliar assessment](#stage-3-add-an-unfamiliar-assessment)
  - [Stage 4: Specialize through a two-project sequence](#stage-4-specialize-through-a-two-project-sequence)
  - [Stage 5: Practice technical review and explanation](#stage-5-practice-technical-review-and-explanation)
- [Role comparison exercise](#role-comparison-exercise)
- [Certificate and course decision worksheet](#certificate-and-course-decision-worksheet)
- [Portfolio release checklist](#portfolio-release-checklist)

<!-- TOPIC-TOC:END -->



## Project ladder

Complete the first four projects, then one project aligned with your primary track. These are recommended practice targets, not industry certification requirements.

| Project | Build and assess | Evidence to produce | Pass condition |
| --- | --- | --- | --- |
| 1. Small network | Two owned systems and a local service; configure routing/firewalls and troubleshoot one deliberate fault. | Diagram, inventory, packet capture commentary, before/after rules. | Explain the full request path and why the broken case failed. |
| 2. Secure application | Small CRUD app with accounts, roles, database, uploads or another sensitive workflow. | Threat model, access matrix, three security test cases, fixes and regression tests. | Unauthorized cases fail while legitimate operations work. |
| 3. Host review | Linux and Windows configuration assessments. | Service/permission inventory, prioritized findings, hardening changes and logs. | Demonstrate the corrected boundary and successful normal administration. |
| 4. End-to-end assessment | An unfamiliar training environment with a defined scope and time limit. | Rules of engagement, activity log, coverage matrix, report, cleanup record. | Another person can follow the evidence and distinguish confirmed findings from uncertainty. |
| 5A. Web/API track | Multi-user or multi-tenant app with sessions and an API. | Role/tenant matrix, business-logic analysis, manual tests and automated regressions. | Verify object, function, and workflow boundaries across more than one endpoint. |
| 5B. Enterprise track | Isolated AD environment with ordinary and delegated identities. | Identity graph, two validated lab weaknesses, corrections and detection evidence. | Remove the unsafe permission paths while preserving intended administration. |
| 5C. Cloud track | Disposable cloud app with workload identity and storage. | Architecture/IAM review, least-privilege changes, audit evidence, teardown. | Prove permitted and denied actions and verify resource cleanup. |
| 5D. Mobile track | Owned training app plus its test backend. | Storage/network/IPC analysis, API boundary tests, fixes. | Explain client and server responsibilities with reproducible evidence. |
| 5E. Research track | Small parser or toy binary you compile. | Crash reproduction, root-cause analysis, patch, regression corpus. | Explain the defect without claiming more impact than you established. |
| 5F. Purple-team track | Controlled activity against a monitored lab. | Hypothesis, telemetry map, detection logic, false-positive evaluation, response note. | Detect the exercise reliably and document visibility gaps. |

## Build a portfolio with substance

- [ ] Publish sanitized lab reports, a small useful automation tool, a threat model, and at least one fix with its regression test.
- [ ] Include setup, dependencies, limitations, reproducibility steps, and what you learned. State when a result came from a guided exercise.
- [ ] Show reasoning: the initial hypothesis, observations, rejected explanations, final root cause, and verified remediation.
- [ ] Keep challenge write-ups consistent with the platform's publication rules. Do not publish active exam content or client findings without permission.
- [ ] Prefer a few clear artifacts over a large collection of copied tool outputs. Maintain your work so another learner can actually run it.
- [ ] Practice a five-minute explanation of one project and a deeper technical walkthrough of a second.

## Select a direction

| Direction | Deepest subjects | Typical work sample |
| --- | --- | --- |
| Web/API penetration tester | 11–13, authentication, reporting | Application assessment and verified fixes. |
| Infrastructure/internal tester | 04–06, 09–10, 14–15 | Network/host/identity assessment with clear access reasoning. |
| Application security engineer | 07–08, 11–13, architecture | Secure design review, code change, pipeline control and regression tests. |
| Cloud security assessor | 12–13, 15–16, cloud logging | IAM/network review with deployment and audit evidence. |
| Detection or purple-team practitioner | 09, 14–16, 20, 23 | Measured detection exercise and response improvement. |
| Mobile/embedded/research specialist | 18–19 or selected 22 topics | Focused technical research with reproducible validation. |

Security operations, IT support, system administration, networking, QA, and software development can also provide relevant experience. Read actual role descriptions and map your evidence to the work required. The [NIST NICE Framework](https://www.nist.gov/itl/applied-cybersecurity/nice/nice-framework-resource-center) provides a vocabulary for describing cybersecurity tasks and capabilities.

## Optional credentials

Credentials can structure study or satisfy a particular employer's requirements. They do not replace the ability to assess, explain, and report. Choose after completing foundational labs and reviewing current job requirements in your target market.

- **Early practical assessment:** Compare [INE eJPT](https://ine.com/security/certifications/ejpt-certification) with your present networking, host, and web skills.
- **Broader practical development:** Compare relevant [HTB Academy paths and certifications](https://academy.hackthebox.com/) or [OffSec PEN-200](https://www.offsec.com/courses/pen-200/) with your desired role and available study time.
- **Specialization:** Consider a web, cloud, mobile, defensive, or research credential only when the subject matches work you want to do.

Before paying, verify the current syllabus, prerequisites, total access cost, exam format, allowed tools, reporting expectations, retake terms, renewal rules, and accessibility requirements. Prices and course names can change. Completing every certificate is not a prerequisite for employment.

## Bug bounty as a separate practice route

- [ ] Start with training labs and report writing. Bug bounty work is open-ended research and has no guaranteed payout.
- [ ] Read one program's current policy thoroughly; document exact scope and permitted behavior before testing.
- [ ] Learn duplicate handling, impact expectations, disclosure timelines, triage communication, and remediation verification.
- [ ] Prefer deep understanding of one application and its workflows to indiscriminate automation across many targets.
- [ ] Track time, useful learning, report quality, and confirmed results. A bounty total is not a complete measure of skill.

## Expanded project roadmap: build evidence of useful work

### Stage 1: Choose a bounded problem

Select a project with a clear owner, user model, data model, security boundary, and completion condition. “Learn everything about cloud security” is too broad for a single project. “Deploy an application with a workload identity that can read one synthetic storage location and is denied another” produces a testable result.

Write a short project brief containing the problem, prerequisites, lab assets, scope, deliverables, planned review, and estimated effort range. Divide the work into build, observe, assess, repair, retest, and document. Keep a small change log so the final report describes the environment actually assessed.

### Stage 2: Build a coherent foundation portfolio

Start with three artifacts that reinforce one another. First, a network/service diagram explains how your lab application is reached. Second, a small program or configuration checker produces repeatable evidence. Third, a short assessment report identifies and fixes a synthetic weakness in the same environment.

For each artifact, include setup instructions, test data, expected output, limitations, and a recovery/reset procedure. Use screenshots only when they clarify behavior. A reviewer should understand the purpose before installing dependencies. Keep private notes and credentials separate from the publishable package.

**Exercise:** Ask another person to rebuild the project using only its README. Record where they stop, which assumptions you forgot, and which error messages would help. Update the project rather than providing an undocumented one-off explanation.

### Stage 3: Add an unfamiliar assessment

Choose a fresh training environment and define a realistic time budget. Obtain enough information to establish scope and accounts, then assess it without a vulnerability-by-vulnerability walkthrough. Track hypotheses, coverage, rejected ideas, findings, and unresolved questions.

Reserve time for reporting and cleanup. An assessment that consumes every minute collecting more observations can leave its owner with no usable result. Stop exploration at the planned point, prioritize evidence, write findings, and explicitly record the remaining gaps.

**Deliverable:** A short engagement packet containing scope, inventory, activity log, evidence references, report, and cleanup checklist. This project should show judgment under constraints as well as technical curiosity.

### Stage 4: Specialize through a two-project sequence

For your chosen track, complete one construction project and one assessment project. In web security, build an authorization model, then review an unfamiliar implementation. In enterprise identity, configure delegated administration, then assess a separate set of permissions. In detection, collect and normalize telemetry, then evaluate rules against a fresh labeled dataset.

The construction project teaches normal behavior and practical constraints. The assessment project tests whether you can transfer that knowledge without memorized answers. Keep both fixes and remaining limitations visible in the portfolio.

### Stage 5: Practice technical review and explanation

Present one project at three depths: a two-minute business explanation, a ten-minute technical walkthrough, and a written reproduction appendix. The short explanation should identify the affected operation and the change required. The deeper version should show preconditions, evidence, alternative explanations, and verification.

Prepare for questions about failure: What did you initially misunderstand? Which finding was a false positive? What would more time have allowed? What could the tool not establish? A credible answer shows the limits of the evidence and the next step needed to improve it.

## Role comparison exercise

Gather several current job descriptions in your intended location or remote-work market. Record recurring tasks, technology requirements, expected experience, communication requirements, and credentials explicitly required or preferred. These details change, so use current postings when you make a career decision rather than assuming this document predicts a hiring market.

Map each repeated requirement to a concrete artifact and skill level. Identify the smallest missing project that would improve your evidence. If the role expects production operations experience you do not yet have, consider adjacent work in IT, development, QA, or operations while continuing your security portfolio. Avoid presenting a lab exercise as production experience.

## Certificate and course decision worksheet

Before paying, compare the learning objective, prerequisite fit, practice format, feedback quality, available access time, assessment requirements, total cost, and current terms. Note what the resource adds that your existing material does not. Choose one at a time and define the artifact you will produce from the learning.

If an employer requires a particular credential, confirm the current requirement and your eligibility. If no role requires one, assess whether the structured practice and evaluation justify its cost to you. Never rely on an assumed salary increase or guaranteed job outcome.

## Portfolio release checklist

- [ ] State whether the work is personal, guided, simulated, academic, or professional with permission to publish.
- [ ] Remove real secrets and sensitive information from files, captures, images, metadata, and repository history.
- [ ] Confirm platform, challenge, and third-party content publication terms.
- [ ] Explain the security question, environment, evidence, root cause, fix, retest, and limitations.
- [ ] Provide working setup instructions and synthetic input data.
- [ ] Include dependency/version information and note which parts need maintenance.
- [ ] Give credit to original sources and clearly distinguish your contribution.

**Completion milestone:** Publish or privately present three reproducible artifacts, finish an unfamiliar scoped assessment, and explain one project under questioning. Then select a track-specific improvement from reviewer feedback and demonstrate the improvement in a second iteration.
