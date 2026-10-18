# 20. Detection engineering, incident response, and forensics

[All topic roadmaps](README.md) | [Original master roadmap](../../ETHICAL_HACKING_ROADMAP.md#20-detection-engineering-incident-response-and-forensics)

<!-- TOPIC-TOC:START -->

## Contents

- [Knowledge and skill checklist](#knowledge-and-skill-checklist)
- [Safe projects and evidence](#safe-projects-and-evidence)
- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1: Establish an observable lab](#stage-1-establish-an-observable-lab)
  - [Stage 2: Build detection hypotheses before queries](#stage-2-build-detection-hypotheses-before-queries)
  - [Stage 3: Measure quality and maintain ownership](#stage-3-measure-quality-and-maintain-ownership)
  - [Stage 4: Practice a defensible investigation](#stage-4-practice-a-defensible-investigation)
  - [Stage 5: Learn acquisition, containment, and recovery decisions](#stage-5-learn-acquisition-containment-and-recovery-decisions)
- [Worked lab: a synthetic document-access incident](#worked-lab-a-synthetic-document-access-incident)
- [Debugging blind spots and completion gates](#debugging-blind-spots-and-completion-gates)

<!-- TOPIC-TOC:END -->



**Prerequisites:** Networking, Windows/Linux administration, scripting, authentication, basic cloud concepts, and evidence documentation. Offensive assessment becomes more useful when you can show what defenders could observe and how to improve response.

## Knowledge and skill checklist

- [ ] Understand logs, metrics, traces, alerts, incidents, indicators, behaviors, baselines, and threat hypotheses. Distinguish an unusual event from confirmed malicious activity.
- [ ] Collect and interpret Windows security and service logs, PowerShell telemetry, Sysmon, Linux authentication/audit/service logs, application logs, and endpoint detection events.
- [ ] Learn process identity, parent/child relationships, command lines, user/logon context, file hashes, network connections, DNS, and identity-provider events. Identify missing fields before writing detections.
- [ ] Understand network telemetry: packet capture, flow records, DNS, proxy, firewall, VPN, IDS/IPS, TLS metadata, and the limitations imposed by encryption and sensor placement.
- [ ] Learn cloud control-plane audit logs, identity sign-ins, role changes, object-storage access, network flow logs, container/Kubernetes audit events, and SaaS audit trails.
- [ ] Verify time synchronization, UTC conversion, event delay, clock skew, parsing, normalization, deduplication, retention, integrity, access controls, and dropped-event monitoring.
- [ ] Learn one SIEM query language well, then understand how its field mappings and query behavior differ from other platforms.
- [ ] Write Sigma rules with explicit log sources, fields, conditions, exclusions, severity, assumptions, references, and expected false positives. Validate the translated rule in the target backend.
- [ ] Write YARA rules for controlled file collections; learn meaningful strings or byte patterns, conditions, metadata, performance, and false-positive testing. A pattern match requires interpretation.
- [ ] Study rule lifecycle: threat hypothesis, necessary telemetry, logic, positive/negative test data, review, staging, tuning, deployment, ownership, and retirement.
- [ ] Measure precision, recall where labeled data permits, false-positive burden, detection latency, investigation effort, and known blind spots. An ATT&CK mapping does not prove comprehensive coverage.
- [ ] Practice threat hunting as a bounded hypothesis-driven investigation with a documented dataset, queries, findings, and follow-up actions.
- [ ] Learn incident preparation, triage, severity, scope determination, stakeholder roles, containment choices, eradication, recovery validation, communication, and lessons learned.
- [ ] Understand when containment can destroy volatile evidence or disrupt business; rehearse decision points with system owners before emergencies.
- [ ] Learn evidence acquisition, write protection where appropriate, chain of custody, cryptographic hashing, original versus working copies, timestamps, and reproducible analysis.
- [ ] Understand disk, memory, browser, email, endpoint, network, identity, and cloud evidence; distinguish live acquisition from offline analysis and document collection limitations.
- [ ] Build event timelines and correlate independent sources. Know that deleted records, encrypted storage, missing logs, and retention limits constrain conclusions.
- [ ] Learn threat-intelligence reliability, indicator expiry, enrichment, sharing permissions, and confidence ratings; avoid identifying an actor solely from a reused tool or IP address.

## Safe projects and evidence

1. Centralize logs from one Windows VM, one Linux VM, and a local application. Generate benign sign-ins, administration changes, and file events; confirm their arrival and timestamps.
2. Create five detection hypotheses, each with matching and nonmatching test fixtures, an investigation note, and a documented telemetry dependency.
3. Use a synthetic incident dataset to build a timeline and determine affected accounts, hosts, and data; clearly mark uncertainty.
4. Run a collaborative purple-team exercise with harmless predefined actions: agree the action, expected evidence, detection, response, and success criteria before execution.
5. Conduct a recovery tabletop covering credential rotation, restoration from a clean backup, renewed monitoring, and a retest of the original weakness.

**Exit criteria:** Demonstrate that a detection fires for intended test data and stays quiet on realistic benign data; explain at least one blind spot; deliver an incident timeline and a defensible evidence log. Consult [Microsoft Sysmon documentation](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon), [Sigma rule documentation](https://sigmahq.io/docs/basics/rules.html), and [YARA rule documentation](https://yara.readthedocs.io/en/stable/writingrules.html). Align incident-response planning with [NIST SP 800-61 Rev. 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final).

## Detailed learning sequence

### Stage 1: Establish an observable lab

Choose a small scope: one Windows host, one Linux host, a local web service, and a central log store. List every source, collection method, destination, timestamp format, and retention policy. Generate known benign events before writing rules. Confirm that an event can travel from the source to a searchable record, and document collection delays.

- [ ] Distinguish event time, collection time, indexing time, and analyst observation time.
- [ ] Record host identifiers, user identifiers, process identifiers, and how identifiers are reused.
- [ ] Compare raw source records with normalized fields and explain any transformations.
- [ ] Detect missing agents, disabled sources, parsing errors, clock drift, and ingestion drops.
- [ ] Restrict access to logs that contain command lines, identifiers, or other sensitive data.
- [ ] Establish a retention period suited to the training dataset and a documented deletion procedure.

### Stage 2: Build detection hypotheses before queries

Write a hypothesis in plain language: an administrative action performed by an unexpected account on a protected training asset should be reviewed. Specify required fields, legitimate exceptions, expected evidence, and a responder action. Then translate it into a query or rule.

Study equality, substring and regular-expression matching, case normalization, null handling, field existence, arrays, joins, grouping, time windows, and sequence logic. Compare a single event rule with a behavioral correlation. Understand that an absent field is different from a field whose value does not match. Include events just inside and outside time boundaries.

For Sigma, document the target log source and verify the converted rule against the actual backend schema. For YARA, test both intended samples and benign files from the same format family. A generic string may describe common software rather than malicious behavior. Review performance on the dataset size you intend to scan.

### Stage 3: Measure quality and maintain ownership

Build a labeled fixture set with positive examples, ordinary negatives, and confusing near-matches. Record expected results before running the rule. Calculate true and false positives for this fixture set, while stating that a small training set does not establish production precision. Recall requires a defined set of relevant cases; unobserved incidents cannot be counted honestly.

Measure detection latency separately from triage latency. Record analyst effort, alert grouping, duplicate suppression, and the effect of exceptions. Give each rule an owner, description, dependency list, version, test evidence, and review trigger. A detection can fail because the source is missing, parsing is broken, logic is wrong, an alert is suppressed, or the response workflow is unclear.

### Stage 4: Practice a defensible investigation

Start with a bounded question, such as whether a synthetic account accessed a training document after its permissions changed. Preserve source records and build a working timeline. Correlate identity, endpoint, application, and network evidence. Confirm identity mappings before merging events that share a display name or an IP address.

Use three confidence labels in notes: observed, supported inference, and unresolved. Document alternative explanations and queries that could distinguish them. Record scope expansion explicitly. Avoid assuming that the first suspicious event is the initial event or that every system lacking logs was unaffected.

### Stage 5: Learn acquisition, containment, and recovery decisions

Study volatile evidence, disk images, application exports, cloud audit records, snapshots, and provider retention limits. Write acquisition notes describing who collected what, from which system, at which time, with which tool and settings. Hash preserved files and maintain originals separately from working copies. A matching hash supports integrity of the copied bytes; it does not establish the truth of the source event.

For containment, compare account suspension, token revocation, network isolation, service shutdown, and temporary policy restrictions. Explain operational consequences and evidence loss risks. Recovery should verify clean configuration, repaired root cause, restored data, appropriate credential rotation, functional service, and renewed monitoring. Rehearse authority and communication decisions before an incident.

## Worked lab: a synthetic document-access incident

**Setup:** Create an application with two fictional accounts and three synthetic documents. Enable application audit events, identity events, and host telemetry. Prepare a separate ground-truth timeline hidden from the learner during analysis. Save a clean snapshot.

**Actions:** Generate a normal login, an approved role change, a denied document read, a permitted document read, and a session revocation. Include one deliberately delayed log delivery and one benign event with a similar username. Write a rule for the agreed suspicious combination, then analyze the dataset as an incident.

**Expected behavior:** The rule matches the intended sequence, ignores the similar benign event, and preserves necessary evidence for a reviewer. The analyst distinguishes event order from ingestion order and identifies limitations caused by absent data.

**Evidence:** Deliver raw-log references, normalized queries, a UTC timeline with source timezones recorded, an account-to-identifier map, tested detection logic, and a short decision log. Include the negative fixture results and the known ground-truth comparison after analysis.

**Correction:** If the rule fails, trace source generation, collection, parsing, field selection, logic, and suppression in sequence. If the investigation overstates scope, revise the claim to match observable evidence. Add a fixture for the mistaken assumption, then repeat the exercise from a clean dataset.

## Debugging blind spots and completion gates

Process IDs are reused; IP addresses can represent NAT or proxies; cloud role changes may propagate asynchronously; timestamps can describe different lifecycle stages. A missing alert may mean missing telemetry. An alert marked closed may never have been investigated. A recovered service may still contain the original vulnerable configuration. Keep these questions separate.

- [ ] Demonstrate collection-health monitoring alongside behavioral detection.
- [ ] Deliver five rules with positive, negative, and near-match fixtures.
- [ ] Explain a rule's required fields and an environmental condition that makes it blind.
- [ ] Reproduce an investigation from preserved inputs and saved queries.
- [ ] Run a recovery tabletop with explicit authority, rollback, and validation decisions.
- [ ] Produce a report that distinguishes confirmed facts from confidence-limited conclusions.

**Primary reading:** Use the Sysmon, Sigma, YARA, and NIST incident-response links above as implementation and process references. For evidence handling and analysis foundations, consult [NIST SP 800-86](https://csrc.nist.gov/pubs/sp/800/86/final); recognize its age and supplement platform-specific acquisition procedures with the tool and service documentation for your actual environment.

