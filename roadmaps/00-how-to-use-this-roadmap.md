# 00. How to use this roadmap

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#00-how-to-use-this-roadmap)

<!-- TOPIC-TOC:START -->

## Contents

- [Learning order](#learning-order)
- [Navigation](#navigation)
- [What to record](#what-to-record)
- [A practical route through the separate topic files](#a-practical-route-through-the-separate-topic-files)
  - [Step 1: Establish your starting point](#step-1-establish-your-starting-point)
  - [Step 2: Build a dependency map](#step-2-build-a-dependency-map)
  - [Step 3: Convert a checklist item into a lesson](#step-3-convert-a-checklist-item-into-a-lesson)
  - [Step 4: Use hints without losing the learning](#step-4-use-hints-without-losing-the-learning)
  - [Step 5: Review evidence and choose the next action](#step-5-review-evidence-and-choose-the-next-action)
- [Completion criteria for using the learning system](#completion-criteria-for-using-the-learning-system)

<!-- TOPIC-TOC:END -->



Ethical hacking means assessing security with authorization, establishing what a weakness actually allows, and helping the owner fix it. The outcome is a defensible assessment and a safer system.

This roadmap covers the major foundations, professional practices, and specialization areas. No finite document can include every product, vulnerability, research paper, or future technique. Treat this as a comprehensive map of what to learn; use the linked documentation to deepen each subject and update your notes as systems change.

## Learning order

1. Complete authorization and lab setup: **01–02**.
2. Build the technical foundation: **03–08**.
3. Learn the assessment workflow: **09–10**. Start writing findings using **23** immediately.
4. Learn applications and infrastructure: **11–16**. Everyone needs working familiarity; choose one area for deeper practice.
5. Add defensive visibility: **20**. Use it alongside every practical exercise.
6. Choose one primary specialization: **17–19, 21–22**, or deepen **11–16**.
7. Complete independent projects and assessments: **24–25**.
8. Keep **26–27** open as your resource and template library.

**Core** means essential for a general security tester. **Track** means depth needed for your chosen role. **Awareness** means recognize the subject, its risks, and when specialist help is needed. You do not need expert ability in every track before applying for a junior position.

For every topic, work through this loop:

> Explain normal behavior → build a small example → identify a trust boundary → test a controlled failure → collect evidence → implement a fix → retest → explain the result to someone else.

For practical core or track topics, tick a checkbox after you can explain the idea without reading, demonstrate it in your lab, and save evidence. For awareness topics, completion means explaining the concept, recognizing its prerequisites, and analyzing a suitable example; practical mastery comes later if you select that track. Watching a video alone is preparation. For topic groups containing several ideas, split the checkbox into smaller tasks in your own notes.

## Navigation

- [00. How to use this roadmap](00-how-to-use-this-roadmap.md)
- [01. Authorization, scope, and professional conduct](01-authorization-scope-and-professional-conduct.md)
- [02. Build a safe, repeatable lab](02-build-a-safe-repeatable-lab.md)
- [03. Computing and study foundations](03-computing-and-study-foundations.md)
- [04. Networking and Internet protocols](04-networking-and-internet-protocols.md)
- [05. Linux administration](05-linux-administration.md)
- [06. Windows administration](06-windows-administration.md)
- [07. Programming and automation](07-programming-and-automation.md)
- [08. Security principles and cryptography](08-security-principles-and-cryptography.md)
- [09. Assessment methodology, reconnaissance, and enumeration](09-assessment-methodology-reconnaissance-and-enumeration.md)
- [10. Vulnerability assessment and research](10-vulnerability-assessment-and-research.md)
- [11. Web application security](11-web-application-security.md)
- [12. API security and modern authentication](12-api-security-and-modern-authentication.md)
- [13. Secure code review and software delivery](13-secure-code-review-and-software-delivery.md)
- [14. Linux and Windows host security testing](14-linux-and-windows-host-security-testing.md)
- [15. Active Directory and enterprise identity](15-active-directory-and-enterprise-identity.md)
- [16. Cloud, containers, and Kubernetes](16-cloud-containers-and-kubernetes.md)
- [17. Wireless and network appliance security](17-wireless-and-network-appliance-security.md)
- [18. Mobile application security](18-mobile-application-security.md)
- [19. Reverse engineering, exploit development, and malware analysis](19-reverse-engineering-exploit-development-and-malware-analysis.md)
- [20. Detection engineering, incident response, and forensics](20-detection-engineering-incident-response-and-forensics.md)
- [21. Human and physical security assessments](21-human-and-physical-security-assessments.md)
- [22. Advanced specialization map](22-advanced-specialization-map.md)
- [23. Reporting, remediation, and retesting](23-reporting-remediation-and-retesting.md)
- [24. Capstones, portfolio, and career direction](24-capstones-portfolio-and-career-direction.md)
- [25. Study schedules and readiness checks](25-study-schedules-and-readiness-checks.md)
- [26. Tools and learning resources](26-tools-and-learning-resources.md)
- [27. Reusable templates and glossary](27-reusable-templates-and-glossary.md)

## What to record

Use a private Git repository for learning notes and sanitized code. Keep client material, credentials, tokens, and sensitive lab artifacts outside public repositories. Maintain one skill tracker with: topic, status, evidence link, last practiced date, mistakes, and next exercise.

Use these levels consistently:

| Level | What you can demonstrate |
| --- | --- |
| 0 — New | You have not studied the topic. |
| 1 — Explain | You can describe normal behavior and the security boundary. |
| 2 — Guided | You can complete a lab with hints and explain the result. |
| 3 — Independent | You can assess an unfamiliar lab, document evidence, and recommend a working fix. |
| 4 — Extend | You can handle edge cases, review another tester's reasoning, and create a reliable regression check. |

For the core, target level 3. For awareness topics, level 1 is initially enough. A specialization requires sustained level 3 work and selected level 4 capabilities.

## A practical route through the separate topic files

Read this file once, then work from the [topic index](README.md) and [progress tracker](PROGRESS.md). The index maps every numbered topic in the original roadmap to its own document. The advanced-specialization overview links to eight additional standalone roadmaps. Begin with the original curriculum in each file, then follow its expanded exercises and milestones.

### Step 1: Establish your starting point

Create a private baseline note with your available weekly time, equipment, previous programming or IT experience, and one role that interests you. List observable skills instead of labels such as beginner or expert. For example: “I can create a user and explain a file permission” is more useful than “I know Linux.” If no role stands out, complete the common foundation and compare two capstones later.

Use a small diagnostic exercise: explain how a browser reaches a local web service; find the service process; identify its account; read one relevant log; make a harmless change; restore it. A missing step identifies a prerequisite, not a personal failure. Save your explanation so you can compare it with your work after several months.

### Step 2: Build a dependency map

For a difficult topic, write three columns: concept, required prior knowledge, and evidence that you have that knowledge. For API authorization, prerequisites include HTTP, identity, data ownership, and application routing. If you cannot explain HTTP request state, revisit networking and web foundations before adding more API tools.

Study closely related subjects together. Networking and packet analysis reinforce each other. Linux and Bash reinforce each other. Programming and application security become clearer when you own a small application. Reporting and defensive visibility belong in every phase. Maintain one primary learning thread and a small prerequisite backlog instead of opening a new course whenever an exercise becomes difficult.

### Step 3: Convert a checklist item into a lesson

Use the item “understand effective permissions” as an example:

1. Define the resource, identities, permitted action, and expected result.
2. Read the operating system's permission model and identify which rules combine.
3. Create two synthetic users and one test resource.
4. Predict each user's access before observing it.
5. Test permitted and forbidden cases and record the identity actually used.
6. Change a single permission and explain the new outcome.
7. Restore the state and write a short explanation without the manual.

The resulting artifact should show understanding, observation, and reasoning. A list of command outputs without the predicted behavior cannot establish whether you interpreted the system correctly.

### Step 4: Use hints without losing the learning

After a genuine attempt, consult increasingly specific help: command documentation, architecture notes, a conceptual hint, then a worked example. Record which hint changed your understanding. Later, repeat the lab from a clean state without the solution and vary one assumption. Completing a guided exercise is useful; label it guided until you can perform the unfamiliar variation independently.

If a lab stalls, distinguish four causes: a missing prerequisite, an environment fault, an incorrect hypothesis, or a tool misunderstanding. Capture the exact error and the smallest reproduction. Reinstalling the whole environment immediately can erase the clue you needed.

### Step 5: Review evidence and choose the next action

At the end of a study block, answer: What can I now explain? What did I demonstrate? What contradicted my prediction? What remains uncertain? What is the smallest next exercise? Update the tracker with the evidence location and your current proficiency level.

Use short reviews after a delay and integrated reviews after several topics. In an integrated review, remove the announced vulnerability category, provide a fixed time budget, and require a report. This tests whether you can choose a method rather than recognize a memorized exercise.

## Completion criteria for using the learning system

- [ ] Your next four sessions have concrete objectives and outputs.
- [ ] Your tracker distinguishes awareness, guided practice, and independent work.
- [ ] One completed lesson contains a prediction, observation, correction, and explanation.
- [ ] Your notes identify source versions and unresolved assumptions.
- [ ] You can show one delayed repeat and explain what you remembered incorrectly.

Keep a distinction between syllabus coverage and mastery. These files preserve the original roadmap and expand its learning steps; products, edge cases, and research will continue changing. Add new discoveries to the relevant topic instead of treating the collection as a permanent inventory of every possible security fact.
