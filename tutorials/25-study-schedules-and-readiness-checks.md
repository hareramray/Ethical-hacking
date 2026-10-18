# 25. Tutorial: build a sustainable study schedule

[Index](README.md) | [Complete source curriculum](curriculum/25-study-schedules-and-readiness-checks.md) | [Original roadmap](../roadmaps/25-study-schedules-and-readiness-checks.md)

This chapter turns the curriculum into a plan that changes with evidence. Time estimates describe a planning model; exit demonstrations establish readiness. You do not need to finish every research specialization before developing useful core ability.

## Lesson 1: measure capacity instead of guessing a finish date

For two weeks, record planned and actual focused minutes. Separate reading, deliberate practice, troubleshooting, reporting, retrieval review, setup, and interruption. Necessary setup still consumes calendar time, but two hours waiting for an installation is not two hours of independent protocol analysis.

Suppose you planned ten hours but sustained seven. Use seven to forecast, then reserve additional time for breaks and difficult topics. The source's 900-hour model totals these phases:

| Phase | Hours | Evidence gate |
| --- | ---: | --- |
| Authorization, lab, computing | 40 | Scope, restoration, and basic diagnosis. |
| Networking and OS administration | 150 | Request path, packet reasoning, Linux/Windows configuration. |
| Programming and security principles | 130 | Working error-handling scripts and security explanations. |
| Assessment process/research | 70 | Scoped inventory, coverage, and validated triage. |
| Web/API/code review | 180 | Application assessment, fixes, and regressions. |
| Host and enterprise identity | 100 | Effective-access reasoning and repaired identity paths. |
| Cloud/container foundations | 60 | Permission review, evidence, and teardown. |
| Detection/reporting/capstones | 90 | Integrated assessment and monitored/retested work. |
| Initial specialization | 80 | Focused introductory project and deeper-study plan. |
| Total | 900 | Broad foundations plus one initial track, not mastery of all tracks. |

At 5, 10, 15, and 20 hours per week, 900 hours means 180, 90, 60, and 45 weeks before breaks. At seven hours it is about 129 weeks. These are arithmetic forecasts, not promises about employment or proficiency. Demonstrated prior skills may remove redundant introductory work; adding another specialization adds work rather than fitting magically into the same total.

## Lesson 2: plan the next block and session

Choose one main topic for a four-week block and two or three observable outcomes. For networking: explain the request path, identify three different failures, and restore the intended connection. Divide that into address/routing, DNS, socket/service, and integrated diagnosis lessons. Keep a buffer and an optional extension rather than filling every available minute with mandatory new material.

A ten-hour illustrative week allocates two hours to focused explanation, four to practice/troubleshooting, two to repair/report/retest, one to delayed review, and one to references/planning. Scale the allocation to your actual capacity. Every fourth week replace some new content with an unfamiliar integrated exercise.

Write a session contract before opening tools:

```text
Objective: explain why Bob cannot read Alice's note.
Starting state: portable fixture, Python available, no persistent server.
Artifact: three outcomes and a paragraph about identity versus ownership.
Stop point: 45 minutes or a reproducible environment issue.
Restart note: exact state, last observation, next discriminating test.
```

At the end, record actual time, help used, result, misunderstanding, and next step. “Read API security” is too broad to diagnose when progress stalls; a concrete artifact makes the difficulty visible.

## Lesson 3: use the first month to establish foundations

| Week | Work | Minimum output |
| --- | --- | --- |
| 1 | Chapters 00–03, isolated lab, terminal/files/help, recovery | Scope, inventory, restore evidence, and first learning note. |
| 2 | Chapter 04 addressing, routes, DNS, ports, TCP, HTTP/TLS concepts | Annotated request path and your own harmless traffic observation. |
| 3 | Begin 05–06 users, permissions, services, processes, logs | Two configuration observations with identity and before/after reasoning. |
| 4 | Begin 07 Python, structured data, Git, errors, tests | A small parser/inventory helper with a README and invalid-input examples. |

This starts the subjects; it does not compress complete OS/programming competence into one month. If you cannot distinguish a DNS failure from a stopped service, continue the foundation block before using a scanner to interpret security findings.

For an application block, use week 1 to trace authenticated requests, week 2 to define user/tenant access rules, week 3 to repair a controlled violation, and week 4 to assess a new path independently. Add sharing, account suspension, bulk operations, or a second transport only after the basic model is clear.

## Lesson 4: separate activity, evidence, and proficiency

Track these as different values. Activity is a completed lesson or practice session. Evidence is a reproducible artifact. Proficiency is what you can explain and do without the original walkthrough. Use 0 new, 1 explain, 2 guided, 3 independent, and 4 extend/review. A checkbox for a topic containing multiple concepts does not imply all those concepts have reached the same level.

Use [PROGRESS.md](PROGRESS.md) for chapter-level status and the full curriculum checklists for finer gaps. Awareness topics can initially target level 1, while practical core and primary-track work aims for independent evidence. Write “deferred” with the next prerequisite rather than leaving ambiguity.

Retrieve a mechanism from memory after a delay. Predict the result when one condition changes, then consult notes. If you remember a command but cannot explain why it distinguishes causes, repeat a smaller model. After a fully guided lab, rebuild later without the solution and change the input or configuration.

## Lesson 5: administer the readiness check

| Demonstration | What counts as an adequate answer |
| --- | --- |
| Browser request | Trace DNS, routing, transport, TLS, HTTP, application identity/authorization, and database behavior. |
| Troubleshooting | Distinguish routing, DNS, listener, TLS, identity, and permission faults with discriminating observations. |
| Administration | Inspect Linux/Windows identities, effective permissions, services, and relevant logs. |
| Programming | Handle valid, malformed, missing, denied, and bounded-large inputs; avoid leaking secrets. |
| Security principles | Explain authentication, authorization, sessions, encryption, hashes, signatures, and key lifecycle with examples. |
| Assessment method | Define exact scope/dependencies, separate discovery from confirmation, and preserve limitations. |
| Application controls | Use multiple synthetic users/roles and positive/negative cases; verify server-side outcomes. |
| Host/identity/cloud | Explain a principal's access path, repair excessive rights, and validate workload policy. |
| Detection | Connect a harmless action to telemetry and diagnose a missing signal. |
| Reporting | Reproduce a finding, verify repair, document coverage/cleanup, and state what remains unknown. |
| Integration | Complete an unfamiliar bounded lab with defensible decisions and a usable report. |

Do not award a pass for memorized definitions alone. A missing capability becomes a focused next block. Working with review is a reasonable professional progression; completing a syllabus does not establish expertise in every domain.

## Lesson 6: replan based on the actual failure

Repeated hints suggest a mechanism gap: shrink the example. Repeated setup failures suggest environment/recovery gaps: write and test a rebuild guide. Success only when the category is announced suggests weak diagnosis: mix failure types. Good technical work with weak reports needs a dedicated reproduction review. Long hours with little output may indicate oversized tasks or constant topic switching. Trivial lessons can be skipped after their exit task is independently demonstrated.

Avoid collecting tools/courses as a substitute for practice, copying scanner scores, studying only popular web flaws, ignoring detection, publishing secrets, ending after exploitation without repair, or equating a CTF flag with a professional assessment. The corrective habit is a small explained observation, a scoped claim, and a verified outcome.

Monthly, review a strong and a weak artifact, revisit one foundation, and examine a relevant current vendor advisory against your actual versions. Quarterly, run an unfamiliar capstone, review official documentation, refresh lab images safely, inspect stale links, and reconsider the chosen track. Keep a changelog of what changed and how it affects tests. **Exit task:** show a sustainable schedule, evidence-linked tracker, delayed retrieval result, integrated assessment, and one justified adjustment to your plan.
