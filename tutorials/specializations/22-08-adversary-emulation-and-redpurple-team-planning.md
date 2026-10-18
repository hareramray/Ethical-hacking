# Tutorial: Adversary emulation and red/purple-team planning

[Index](../README.md) | [Full source curriculum](../curriculum/specializations/22-08-adversary-emulation-and-redpurple-team-planning.md) | [Original roadmap](../../roadmaps/specializations/22-08-adversary-emulation-and-redpurple-team-planning.md)

## Define a question that evidence can answer

Use a monitored, owned lab and a synthetic objective: can a team recognize and correctly assess a test-account role change followed by creation of a benign marker and a read of an invented project document? The exercise uses transparent collaboration, named accounts, local artifacts, and reversible changes. It requires no stealth, credential collection, harmful payload, real data removal, or external command channel.

A vulnerability assessment identifies weaknesses. A penetration test examines whether scoped weaknesses can be demonstrated and connected to impact. Adversary emulation models selected behaviors and assumptions relevant to a threat scenario. Control validation tests a defined control property. Purple-team collaboration brings operators and defenders together to improve evidence, detection, and response. These activities overlap, but their success criteria differ.

Start from the organization's fictional workflow. An administrator may approve a role change for a project editor. Editors may read synthetic project notes. Ordinary note creation is common. Your defensive question concerns whether an unexpected combination is visible and correctly interpreted—not whether every event with an exercise marker triggers an alert.

Use credible threat information with provenance and confidence to justify behavior selection. MITRE ATT&CK organizes observed adversary behaviors and their supporting references; it is not a ready-made exercise objective or a guarantee that a technique applies to every environment. Choose a small relevant set only after reading the underlying descriptions. [MITRE ATT&CK](https://attack.mitre.org/)

## 1. Translate the objective into three observable actions

Define an owned application `Project-Lab`, fictional user `test-mira`, endpoint `LAB-01`, and document `SYNTHETIC-PROJECT-7`. Starting access is an already authorized lab administrator identity. This is an assumption, not a claim that the exercise established initial compromise.

| Action | Harmless operation | Expected source | Defensive question |
|---|---|---|---|
| A1 | Approved test-account role change | Application audit log | Can responders identify actor, target, and old/new role? |
| A2 | Create an identifiable plain-text marker | Endpoint or file audit | Is the file event collected and linked to LAB-01? |
| A3 | Read the invented project document | Application access log | Can responders establish which identity accessed which object? |

The marker contains only `TRAINING PROJECT-LAB RUN-01`. It should remain harmless when scanned, indexed, synchronized, or backed up. The document contains invented project text and no sensitive information. No action requires an Internet endpoint.

Behavior categories such as command-and-control, persistence, collection, and exfiltration help organize telemetry questions. For beginner practice, represent them with documented fixtures or tabletop questions where relevant. For example, a mock record of a scheduled setting can support discussion of persistence evidence, while an in-memory transfer of synthetic text can illustrate data-flow logging. Do not report a mock event as proof that a production endpoint sensor observes a real behavior.

## 2. Write rules that an operator can execute

Create an exercise plan with sponsor, owner, controller, operator, defender, system owner, and emergency contact. Name exact assets, identities, time window, allowed operations, prohibited effects, data rules, communication routes, visibility model, and termination authority. Agree how a real incident takes priority if one occurs during the exercise.

For this lab, the controller is `Ravi`, the operator is `Mira`, and the defender is `Chen`. The visibility model is transparent: Chen knows the sequence and expected evidence. The synthetic objective is a documented assessment of the event chain, followed by a mock escalation decision. Real containment is replaced by a written recommendation unless a reversible lab control action is explicitly part of the plan.

Write each action card with prerequisites, expected state, telemetry, detection hypothesis, measurement, resource limit, rollback, and cleanup check. For A1, record the original role, the permitted temporary role, the application audit event type, and the exact restoration procedure. For A2, record the dedicated exercise directory and marker filename. For A3, record the document ID and account used.

Make stop conditions observable: unexpected instability, changes outside lab assets, exposure of nonsynthetic data, loss of contact with Ravi, or withdrawal of the approved window. The controller must be able to identify all artifacts and stop the sequence. A vague instruction to “be careful” is not an executable boundary.

Classify evidence honestly. A live benign operation tests real generation and collection in the lab. A replayed fixture tests selected downstream handling. A synthetic event tests a schema or rule. A tabletop inject tests reasoning and coordination. They can complement one another, but their claims are not interchangeable.

## 3. Verify instrumentation before measuring detection

Save the baseline: account roles, synthetic-document state, exercise-directory contents, log configuration, rule revision, and relevant service versions. Check timestamp format and synchronization. Use an explicit time reference and record known clock uncertainty. If the sensor clock is two minutes behind the application, apparent response latency may be meaningless until corrected.

Rehearse each benign action separately and reset afterward. Find its raw source event, confirm arrival in the central store, inspect parsed fields, and verify that searches return it. Do not begin a detection exercise while collection is known to be absent.

For each event preserve `run_id`, action ID, ground-truth time, source event time, ingestion time, actor, asset, object, operation, result, and a pointer to original evidence. Avoid copying unnecessary unrelated logs. Redaction should preserve the fields required for correlation while removing data outside the exercise.

Now create a small in-memory fixture to learn the difference between event visibility and detection:

```python
events = [
    {"time": 0, "kind": "role_change", "actor": "lab-admin",
     "subject": "test-mira", "asset": "LAB-01"},
    {"time": 15, "kind": "file_create", "actor": "test-mira",
     "subject": "marker.txt", "asset": "LAB-01"},
    {"time": 35, "kind": "document_read", "actor": "test-mira",
     "subject": "SYNTHETIC-PROJECT-7", "asset": "LAB-01"},
]

def candidate_sequences(records):
    changes = [e for e in records if e["kind"] == "role_change"]
    reads = [e for e in records if e["kind"] == "document_read"]
    return [(change, read) for change in changes for read in reads
            if change["subject"] == read["actor"]
            and change["asset"] == read["asset"]
            and 0 <= read["time"] - change["time"] <= 60]

print(len(candidate_sequences(events)))
```

Expected output is `1`. The rule identifies a candidate pattern; it does not establish malicious intent. The marker's literal text is not part of the logic, so a magic exercise string cannot be the sole reason for success. Approval context and normal workflow still matter during triage.

## 4. Run a transparent iteration

Before each action, Chen states the expected source and fields. Mira performs the written benign action. Ravi records ground truth and confirms scope. Chen locates the evidence, determines whether the rule matched, and explains the context. Separate five outcomes: event visible, alert generated, alert routed, analyst interpretation correct, and response decision appropriate.

For the fixture, remove A1 and rerun: the expected candidate count is zero. Change the document-read actor to another fictional account: it should remain zero. Move the read to time 120: the selected 60-second correlation window no longer matches. These negative cases test rule boundaries. An approved role change followed by normal document work may still match technically; triage or contextual rule logic must distinguish its legitimate reason.

When a result fails, walk the pipeline in order: event generated, collected, parsed, searchable, matched, suppressed, routed, understood, acted upon. Suppose the role event stores `target_user` while the parser expects `subject`. Raw evidence exists but identity correlation fails. The correction is a field mapping with a regression fixture, not an unsupported claim that the endpoint lacks all visibility.

Tune one relevant layer, repeat the same case, then run a benign comparison. Record whether the change increases ordinary alert volume. If advance notice makes discovery easy, state that limitation. Reduced defender foreknowledge is a separate exercise design decision requiring coordination; it is not automatically better or the next mandatory step.

## 5. Measure response with honest timestamps

Use an illustrative timeline to practice calculations:

| Milestone | Seconds after A1 |
|---|---:|
| Source evidence available | 2 |
| A3 completes | 35 |
| Pattern alert generated | 40 |
| Triage begins | 55 |
| Correct interpretation recorded | 85 |
| Mock escalation decision | 100 |
| Tabletop containment decision | 130 |

If the hypothesis requires A3, pattern-detection latency is 5 seconds after the qualifying sequence completes, not 40 seconds after A1. Both reference points can be useful if labeled. Missing timestamps should be reported as missing. Do not invent an exact containment time for a response discussed only in a tabletop.

Measure quality alongside speed. Did Chen identify the correct account, asset, role change, document, approval context, and appropriate owner? Fast isolation of the wrong asset is a failed response. Record investigation completeness and available evidence, not just a mean detection number.

## 6. Turn the debrief into verified improvements

Write findings around causes. A missing event belongs to telemetry ownership; an incorrect parser field belongs to ingestion; an unclear escalation route belongs to the playbook and decision authority. Assign each improvement an owner and acceptance criterion. For the field mapping, require the original fixture to match, an unrelated-account fixture not to match, and the raw event reference to remain available.

Debrief collaboratively. Ask which information was missing when a decision was needed, whether approval context was accessible, and whether the training rule created unreasonable ordinary workload. Preserve alternative explanations and simulation limitations. Technique labels should summarize relevant behavior, not substitute for evidence.

Restore the original role, remove only the known benign marker in its recorded exercise directory, retire temporary test credentials, restore temporary logging or rule settings, and handle synthetic records according to the plan. Compare against the saved baseline. Visible files are only one artifact category; roles, scheduled configuration, permissions, and account state also require checking.

## Questions with answer guidance

1. **Does a searchable event prove detection?** No. Collection, alerting, routing, interpretation, and response are separate outcomes.
2. **Why retain negative cases?** They reveal overbroad rules and identity-correlation mistakes that a single positive exercise conceals.
3. **Can synthetic events prove endpoint collection works?** Only if the event was actually generated and collected through that path; direct fixture injection tests a narrower layer.
4. **What makes cleanup complete?** A baseline comparison covering accounts, roles, files, records, credentials, and temporary configuration, with discrepancies explained.

Deliver the reviewed plan, action cards, identity and asset scope, ground-truth timeline, telemetry references, measurements, investigation notes, improvement owners, retest results, and cleanup comparison. State that transparent notice and harmless substitutions limit realism. The accomplishment is a defensible improvement in control performance, not a claim that three events cover an entire adversary campaign.
