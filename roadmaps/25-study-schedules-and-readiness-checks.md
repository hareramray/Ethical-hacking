# 25. Study schedules and readiness checks

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#25-study-schedules-and-readiness-checks)

<!-- TOPIC-TOC:START -->

## Contents

- [A realistic time budget](#a-realistic-time-budget)
- [Weekly routine: example for 10 hours](#weekly-routine-example-for-10-hours)
- [Your first 30 days](#your-first-30-days)
- [Assessment questions](#assessment-questions)
- [Common mistakes and corrections](#common-mistakes-and-corrections)
- [Keep the roadmap current](#keep-the-roadmap-current)
- [Expanded planning method: adapt the schedule to evidence](#expanded-planning-method-adapt-the-schedule-to-evidence)
  - [Step 1: Measure capacity before setting dates](#step-1-measure-capacity-before-setting-dates)
  - [Step 2: Plan one block at a time](#step-2-plan-one-block-at-a-time)
  - [Step 3: Use a session contract](#step-3-use-a-session-contract)
  - [Step 4: Track proficiency separately from activity](#step-4-track-proficiency-separately-from-activity)
  - [Step 5: Schedule retrieval and integration](#step-5-schedule-retrieval-and-integration)
- [Example four-week block with adaptable workload](#example-four-week-block-with-adaptable-workload)
- [Replanning decisions](#replanning-decisions)
- [Monthly and quarterly reviews](#monthly-and-quarterly-reviews)

<!-- TOPIC-TOC:END -->



## A realistic time budget

The following **900-hour planning example** covers foundational ability, broad core exposure, and one initial specialization. It is an estimate created for this roadmap, not a guarantee of mastery or employment. Extensive specialist research, repeated failed labs, and learning basic programming from scratch can require substantially more time.

| Phase | Focus | Suggested hours | Evidence required before moving on |
| --- | --- | ---: | --- |
| A | Authorization, lab, computing foundations: 01–03 | 40 | Scope document, recoverable lab, basic troubleshooting. |
| B | Networking and OS administration: 04–06 | 150 | Network diagram, packet analysis, Linux/Windows configuration labs. |
| C | Programming and security principles: 07–08 | 130 | Tested scripts, small app, authentication/crypto explanations. |
| D | Assessment process and research: 09–10 | 70 | Inventory, coverage matrix, correctly triaged findings. |
| E | Web, API, and code review: 11–13 | 180 | Independent application assessment and verified fixes. |
| F | Hosts and enterprise identity: 14–15 | 100 | Host review and a small identity assessment. |
| G | Cloud and container basics: 16 | 60 | Deployment, permissions review, logs, teardown. |
| H | Detection/reporting/capstones: 20, 23–24 | 90 | End-to-end report, retest, monitored lab exercise. |
| I | One selected specialization: 17–19, 21–22, or deeper core | 80 | One focused project and a plan for further depth. |
| **Total** | **Core plus initial specialization** | **900** | **Evidence-based review of strengths and remaining gaps.** |

Reporting and defensive visibility should be practiced throughout; their hours above include focused consolidation and capstones. The 80-hour specialist block is an introduction, especially for exploit research, embedded systems, or industrial security.

| Sustainable study time | Approximate time for 900 focused hours |
| --- | --- |
| 5 hours/week | 180 weeks, about 3.5 years. |
| 10 hours/week | 90 weeks, about 21 months. |
| 15 hours/week | 60 weeks, about 14 months. |
| 20 hours/week | 45 weeks, about 10–11 months. |

Allow extra calendar time for breaks, work, exams, and revisiting gaps. Someone with strong IT or development experience may demonstrate existing competencies and shorten the route.

## Weekly routine: example for 10 hours

- **2 hours:** Read or watch one tightly scoped topic and make retrieval questions.
- **4 hours:** Build and test it in a lab; reserve part of this time for troubleshooting.
- **2 hours:** Write findings, implement a fix, and retest.
- **1 hour:** Review previous topics without notes or repeat a weak exercise.
- **1 hour:** Review official documentation, update the tracker, and plan the next week.

Every fourth week, substitute an unfamiliar integrated exercise for some new material. If you used a walkthrough, repeat the exercise later without it and change one condition so you must reason again.

## Your first 30 days

| Week | Focus | Concrete output |
| --- | --- | --- |
| 1 | Read 00–02; set up one Linux VM or hosted lab; practice files, terminals, and help pages. | Lab inventory, scope statement, backup/restore evidence, study log. |
| 2 | Start 04; learn addresses, subnets, DNS, ports, TCP, and the browser request path. | Annotated diagram and a capture of your own harmless HTTP/DNS activity. |
| 3 | Start 05–06; users, permissions, processes, services, logs, and basic administration. | Two short configuration labs with before/after observations. |
| 4 | Start 07; Python basics, Git, structured data, simple tests, and input handling. | A small log parser or inventory script with a README and error cases. |

This month starts the foundations; it does not finish them. Continue according to the phase exit criteria rather than rushing to an arbitrary calendar date.

## Assessment questions

Before advancing from the core, demonstrate that you can:

- [ ] Explain a browser request from DNS through TLS, HTTP, application logic, and database access.
- [ ] Troubleshoot a routing, DNS, service, or permission problem without assuming it is a vulnerability.
- [ ] Use Linux and Windows terminals, inspect logs, and determine effective permissions.
- [ ] Write and debug a short script that handles errors, structured data, and secrets responsibly.
- [ ] Explain authentication, authorization, sessions, encryption, hashing, signatures, and key management.
- [ ] Scope an assessment and identify third-party or excluded systems.
- [ ] Distinguish discovery, suspicion, confirmed weakness, and demonstrated impact.
- [ ] Manually verify application access controls with multiple synthetic users and roles.
- [ ] Explain a host or identity access path and repair its underlying permission issue.
- [ ] Read basic cloud permissions and identify a workload's identity and accessible resources.
- [ ] Connect an approved test action to logs and explain a missing signal.
- [ ] Write a reproducible finding and verify remediation with positive and negative cases.
- [ ] Complete an unfamiliar scoped lab with a useful report and cleanup record.
- [ ] State the limits of your knowledge and identify what additional evidence or expertise you need.

For a junior role, aim for independent core work with review from a more experienced practitioner. Advanced domains require mentorship and repeated practice; do not imply expert ability because you completed a topic list.

## Common mistakes and corrections

| Mistake | Better practice |
| --- | --- |
| Collecting tools before understanding systems | Learn the protocol and produce one manual observation first. |
| Copying walkthrough commands | Explain each action, vary the environment, and repeat unaided later. |
| Treating scanner results as final findings | Verify prerequisites, compare control cases, and preserve uncertainty. |
| Studying only popular web vulnerabilities | Include authorization, identity lifecycle, business logic, deployment, and reporting. |
| Trying every specialization at once | Complete the common core and choose one primary track. |
| Chasing certificates without artifacts | Produce reports, code, fixes, and retest evidence alongside study. |
| Ignoring defensive visibility | Identify the logs and controls that should show each exercise. |
| Publishing secrets in learning notes | Use synthetic data, inspect repository history, and review before publishing. |
| Learning exploit behavior without remediation | Repair the cause and test the secure behavior before finishing the lab. |
| Assuming a CTF flag proves professional readiness | Add scope management, false-positive handling, business impact, and a complete report. |

## Keep the roadmap current

Each month, revisit one weak foundation and one current vendor advisory relevant to your track. Each quarter, review official project documentation, replace stale links in your notes, update your lab images, and perform an unfamiliar capstone. Keep a changelog of new concepts and what they change in your testing method.

## Expanded planning method: adapt the schedule to evidence

### Step 1: Measure capacity before setting dates

Choose a weekly study commitment you can maintain alongside existing responsibilities. Use the first two weeks to compare planned and actual focused time. Separate active work from passive watching, installation delays, and interruptions; all may be necessary, but they contribute differently to skill development.

Build calendar estimates from remaining focused hours divided by your observed sustainable rate. Treat the 900-hour plan above as one initial model. Do not add every optional specialization to that total and still expect the same finish date. A new track creates additional work; demonstrating an existing prerequisite can remove redundant introductory work.

### Step 2: Plan one block at a time

For the next four weeks, select a primary topic, two or three observable outcomes, and a capstone-sized check. Break each outcome into lessons that fit your available sessions. A networking block might end with explaining a request path and diagnosing three distinct faults. The lessons can cover addresses, routes, DNS, sockets, and packet evidence.

Reserve buffer for environment problems and review. The plan should survive an unexpectedly difficult concept without forcing you to skip it. Keep a stretch task available for easy weeks, but do not treat a stretch goal as a requirement that invalidates the core learning.

### Step 3: Use a session contract

At the start of a session, write one objective, the starting state, the expected artifact, and a stopping point. For example: “Compare owner and non-owner read access in the local API; save two request traces and explain the result.” Prepare the exact lab and documentation needed before branching into more material.

At the end, record the result, actual time, help used, mistakes, and next action. If the task is unfinished, leave a restart note stating the current state and the next test. This reduces the need to rediscover what you were doing in the next session.

### Step 4: Track proficiency separately from activity

Maintain three different measures: practice completed, evidence produced, and independent proficiency. Completing many labs can represent productive repetition or memorization; review unfamiliar variants to distinguish them. A long study streak does not prove that a security boundary is understood.

Use the 0–4 scale consistently. Level 1 requires a correct explanation. Level 2 requires guided execution. Level 3 requires independent work and defensible evidence. Level 4 requires extension, review, or robust regression work. Awareness topics need an appropriate explanation initially, rather than the same practical depth as your primary track.

### Step 5: Schedule retrieval and integration

Revisit a concept after a delay without opening the answer first. Explain its mechanism, predict a changed scenario, and only then consult notes. If recall fails, identify whether terminology, mechanism, or execution was missing and practice that part.

After several related lessons, run an integrated exercise with no announced failure category. A broken web request may result from DNS, routing, TLS, authentication, authorization, or application state. Your task is to discriminate among them. Keep the assessment bounded and document the result, including a valid “no confirmed vulnerability” outcome.

## Example four-week block with adaptable workload

| Week | Main objective | Minimum evidence | Optional extension |
| --- | --- | --- | --- |
| 1 | Explain an authenticated request and its identity context. | Sequence diagram and annotated request. | Compare session and bearer-token handling. |
| 2 | Define object access rules for two users and two tenants. | Permission matrix with expected outcomes. | Add sharing, suspended users, or background work. |
| 3 | Test one deliberately incorrect rule and repair it. | Minimal reproduction, code/config change, regression checks. | Test another transport or bulk endpoint. |
| 4 | Review a new access path independently. | Findings or negative-result report and remaining coverage. | Peer review or additional variant testing. |

Adjust the block size when the prerequisites are missing. The objective is reliable understanding; an exercise that spans two blocks can still be successful learning.

## Replanning decisions

| Observation | Interpretation to investigate | Practical adjustment |
| --- | --- | --- |
| Repeatedly need the same hint | The mechanism may not be understood. | Rebuild a smaller example and explain it without tools. |
| Many setup failures | Environment knowledge or reproducibility is weak. | Revisit lab setup and write a clean rebuild guide. |
| Can solve announced labs but not unknown ones | Recognition is stronger than method selection. | Add mixed diagnostic cases and hypothesis logs. |
| Good technical work, weak reports | Evidence organization needs practice. | Allocate a dedicated writing/reproduction review session. |
| Little progress despite long hours | Task scope or switching cost may be too high. | Reduce active topics and define smaller outputs. |
| Existing experience makes lessons trivial | Introductory work may be redundant. | Attempt the exit task and advance if evidence supports it. |

## Monthly and quarterly reviews

Each month, review one strong artifact and one weak artifact. Look for a recurring error pattern and plan a focused correction. Compare your estimated and actual time without turning the estimate into a judgment of ability.

Each quarter, assess an unfamiliar scenario, review the primary resources for your track, inspect whether your lab images and notes still match, and reconsider your specialization. Update the tracker with concrete next actions. Keep a small record of subjects deliberately deferred so they are not mistaken for completed coverage.

**Planning completion check:** You can show a sustainable schedule, current evidence-linked tracker, one delayed review, one integrated assessment, and a documented adjustment based on what the results revealed. The schedule supports the learning rather than replacing its assessment.
