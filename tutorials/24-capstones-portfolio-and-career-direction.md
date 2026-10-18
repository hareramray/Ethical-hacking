# 24. Tutorial: capstones, portfolio, and career direction

[Index](README.md) | [Complete source curriculum](curriculum/24-capstones-portfolio-and-career-direction.md) | [Original roadmap](../roadmaps/24-capstones-portfolio-and-career-direction.md)

Prerequisites: a recoverable lab, basic technical foundations, and the reporting method in chapter 23. This chapter turns learning into reproducible work. A completed guided challenge is useful practice; an unfamiliar assessment tests whether you can choose the method yourself.

## Lesson 1: write a project brief with a finish condition

“Learn cloud security” has no useful stopping point. “Demonstrate that one workload identity can read one synthetic storage location and cannot read another, with audit evidence and teardown” is testable. State owner, users, assets, boundary, scope, prerequisites, deliverables, review method, effort range, and recovery.

Divide the project into build, observe, assess, repair, retest, and document. Keep a change log because the final environment often differs from the initial diagram. Reserve reporting and cleanup time before exploration begins. A project that ends with unorganized observations has not produced an assessment another person can use.

For your first brief, use the shared API fixture: explain Alice/Bob ownership, inspect requests locally, demonstrate the disabled-check function's failure, verify enforcement, and package the evidence. Label it a guided synthetic exercise. The fixture is a starting component, not a finished CRUD application or a production authentication system.

## Lesson 2: climb the project ladder

| Project | Concrete construction and test | Finish condition |
| --- | --- | --- |
| 1. Network | Two owned systems, a local service, diagram, routing/firewall rules, and one deliberately changed fault | Diagnose the fault from client/server/packet evidence and restore normal reachability. |
| 2. Secure application | Build a small CRUD app with accounts, roles, database, and one sensitive workflow such as upload | Threat model, permission matrix, three security cases, corrected controls, and regressions. |
| 3. Hosts | Review Linux and Windows service identities, permissions, remote exposure, and logs | Explain each access path and verify repairs without breaking legitimate administration. |
| 4. Unfamiliar assessment | Fresh training target with written scope and a fixed time budget | Inventory, hypotheses, coverage, report, false-positive handling, and complete cleanup. |
| 5A. Web/API | Multiple users/tenants and more than one endpoint | Verify object, function, tenant, and workflow rules, including legitimate operations. |
| 5B. Enterprise identity | Isolated directory with ordinary/delegated identities | Independently validate two permission weaknesses and remove unintended paths while keeping intended delegation. |
| 5C. Cloud | Disposable isolated environment with workload identity and storage | Allowed/denied policy tests, audit evidence, billing/resource inventory, and verified teardown. |
| 5D. Mobile | Owned app and its backend | Storage/transport/IPC analysis plus server boundary tests and fixes. |
| 5E. Research | Self-built parser or toy binary | Minimal failure, exact cause, patch, regression corpus, and limited impact claim. |
| 5F. Purple team | Monitored lab and harmless predefined actions | Tested hypotheses, collection evidence, measured outcomes, false-positive evaluation, and response improvement. |

Complete the first four and one primary-track project. The other tracks remain available as deliberate later work, with their checklist entries marked accordingly. Choosing a track does not mean silently dropping its alternatives from the curriculum.

## Lesson 3: build three artifacts that reinforce each other

Use one environment to produce a network/data-flow diagram, a small useful script or configuration checker, and a short assessment report with a verified correction. The diagram explains context; the script makes observations repeatable; the report connects evidence to action.

Give each artifact purpose, setup, dependencies/versions, synthetic inputs, expected output, limits, recovery/reset, and attribution. Include at least one failed hypothesis and explain what evidence disproved it. Screenshots help when they show behavior, but raw tool output without interpretation does not show judgment.

A useful bundle can use this structure:

```text
project/
  README.md          purpose, setup, run, expected results, limitations
  model.md           system and trust boundaries
  src/               original helper code
  fixtures/          synthetic data and labeled cases
  report.md          evidence-linked assessment and verified repairs
  evidence/          sanitized observations only
```

Ask a reviewer to rebuild it using only the README. Every clarification you must give becomes a documentation improvement. If they cannot reproduce due to a missing private dependency, provide a synthetic substitute or narrow the reproducibility claim.

## Lesson 4: assess without an announced vulnerability category

Select a fresh authorized training environment. Define assets, accounts, exclusions, time budget, stop conditions, and report delivery. Start with expected behavior and inventory, then choose tests based on evidence. Keep a hypothesis log with supported, rejected, and unresolved outcomes.

At the planned exploration cutoff, prioritize the strongest findings, resolve material ambiguities where feasible, and write the report. State access/time/environment limitations. A justified “no confirmed weakness in the tested cases” is valid; manufacturing a finding to make a portfolio more exciting damages its value.

In a specialization, do a construction project and a separate assessment project. Build an ownership model, then review an unfamiliar one; configure delegation, then assess a new graph; collect telemetry, then evaluate rules against fresh labeled cases. This checks transfer of knowledge rather than recall of one fixture.

## Lesson 5: choose roles using evidence from actual work

| Direction | Evidence to emphasize |
| --- | --- |
| Web/API tester | Scoped application assessment, access-control reasoning, reproducible findings, and verified fixes. |
| Infrastructure/internal tester | Network diagnosis, Linux/Windows host permissions, directory access paths, and administration-preserving repairs. |
| Application security engineer | Design/code review, a meaningful code correction, tests, and software delivery controls. |
| Cloud assessor | Workload identity, effective policy/network review, audit trails, and lifecycle/teardown. |
| Detection/purple practitioner | Collection validation, hypothesis-based rules, labeled evaluation, and response improvement. |
| Mobile/embedded/research specialist | A tightly scoped technical study with reproducible evidence and limitations. |

IT support, administration, networking, QA, operations, and development can provide related experience. Do not label a personal lab as production work. When making a job decision, collect several current postings in your intended market and map recurring tasks to artifacts and proficiency levels; this tutorial does not assume a fixed hiring market.

Credentials may structure learning or satisfy an actual role requirement. The source curriculum names INE eJPT, HTB Academy paths, OffSec PEN-200, and specialist credentials as comparison candidates, not a required sequence. Before spending money, verify the current syllabus, prerequisites, total costs/access window, exam/tool/report requirements, retakes, renewal, and accessibility. Compare what the course adds to your existing practice. No credential or bounty income guarantees employment.

## Lesson 6: release responsibly and explain your work

Label work personal, guided, simulated, academic, or professional with permission. Review files, screenshots, captures, metadata, repository history, and tool projects for secrets and personal information. Removing a secret from the latest file does not remove it from Git history; exposed real credentials also need revocation through their owner. Respect challenge/exam/publication conditions and credit sources.

Bug bounty is a separate open-ended research practice. Start with labs and reports, then read a program's current scope and permitted behavior. Understand exclusions, duplicates, impact evidence, triage, disclosure, and retesting. Deep workflow knowledge is more useful than indiscriminate automation; payouts are uncertain, so track time and learning as well as confirmed outcomes.

Practice a two-minute owner explanation, a five-minute project overview, and a deeper technical walkthrough. Be ready to describe a mistake, a false positive, a tool limitation, and what additional evidence would change your conclusion. **Exit deliverables:** three reproducible artifacts, one unfamiliar scoped assessment, one specialist build/review pair, and a second iteration improved by reviewer feedback. Publishing is optional; private review can establish the same learning evidence.
