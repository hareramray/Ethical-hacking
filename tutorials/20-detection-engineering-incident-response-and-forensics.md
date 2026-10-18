# 20. Tutorial: detection engineering, incident response, and forensics

[Index](README.md) | [Complete source curriculum](curriculum/20-detection-engineering-incident-response-and-forensics.md) | [Original roadmap](../roadmaps/20-detection-engineering-incident-response-and-forensics.md)

Prerequisites: networking, Windows/Linux administration, scripting, identity, and basic cloud concepts. Begin with the supplied synthetic records; later reproduce the collection pipeline in your own monitored VMs. A log describes an observation made by a system, while an incident is a conclusion requiring investigation and response.

## Lesson 1: establish what you can observe

A log records an event, a metric aggregates measurements, and a trace connects work across components. An alert is a rule's output; it is not automatically malicious activity. Indicators identify particular observable values, while behaviors describe actions. A baseline describes expected patterns under stated conditions; unusual does not automatically mean harmful.

| Source | Useful fields and important blind spot |
| --- | --- |
| Windows security/service logs, PowerShell, Sysmon, EDR | Stable host/account context, process/parent, command line, logon/session, file/network activity. Availability depends on collection and policy; absence is not a clean result. |
| Linux authentication, audit, and service logs | Identity, service action, process, path, outcome. Permissions, rotation, and disabled audit rules can remove evidence. |
| Application/IdP | Session, actor ID, object, tenant, operation, authorization outcome. Display names alone are weak join keys. |
| Packets, flows, DNS, proxy, firewall, VPN, IDS/IPS | Different views of endpoints and transactions. Encryption and sensor placement constrain payload visibility. |
| Cloud control-plane and storage logs | Role/policy changes and data access are different event families; verify both are enabled as required. |
| Containers, Kubernetes, SaaS | Workload/API identity, resource, operation, tenant. A short-lived container identifier needs time/context to interpret. |

Create a source register with event schema, collector, destination, owner, retention, access controls, and a known test event. Generate a benign login, confirm it exists at source, then compare the raw event with its normalized searchable version. Missing fields, parse failures, drops, deduplication, or disabled agents can break a detection before its logic runs.

Keep event time, collection/ingestion time, indexing time, and analyst time distinct. Record original timezone and UTC conversion. Clock skew and delayed delivery can reverse apparent order. Protect logs and hashes, monitor collection health, and limit who can read sensitive command lines or identifiers.

## Lesson 2: write the hypothesis before the query

Use this hypothesis: “A denied document read followed by an allowed read of the same document by the same account and session within two minutes deserves review.” Required fields are stable actor ID, session ID, document ID, outcome, and event time. A legitimate permission change is an alternative explanation.

Run:

```powershell
python tutorials/examples/analyze_events.py
```

Read [events.jsonl](examples/events.jsonl). E2 is a role change delivered later than several subsequent events. E3 and E5 concern account `u2`, session `s2`, document `n1`; they form the review pair. E4 has a similar display name but belongs to `u20`. Joining on a substring such as `bob` would incorrectly merge identities.

Inspect [analyze_events.py](examples/analyze_events.py). It sorts by event time, ignores other event families, groups by three stable identifiers, and checks a 120-second boundary. Missing key fields cause an event to be skipped. In production that skip should feed a data-quality monitor; silently dropping malformed input can hide activity. This finite offline example does not implement streaming late-arrival windows or deduplication.

For a native query language, learn equality, substrings, regular expressions, case handling, nulls, field existence, arrays, grouping, joins, and bounded sequences. A count of matching events and a sequence of related events answer different questions. Test exactly at the time boundary and one second beyond it.

## Lesson 3: understand Sigma and YARA by purpose

Sigma describes log-event matching in a portable format; a backend/pipeline maps it to actual fields and queries. For a fictional application log, this illustrative rule identifies explicit denied reads:

```yaml
title: Training Application Denied Document Read
status: experimental
description: Review fixture events; this is not a malicious-activity verdict.
logsource:
  product: tutorial_app
  service: audit
detection:
  selection:
    kind: document_read
    outcome: denied
  condition: selection
falsepositives:
  - Ordinary users opening a note they no longer own
level: low
```

The two fields in the mapping are conjunctive. This is a single-event rule, not the denied-then-allowed correlation above. A custom `tutorial_app` source requires your own backend field mapping and validation. Follow the [Sigma rule documentation](https://sigmahq.io/docs/basics/rules.html) for format semantics and backend requirements.

YARA matches content rather than event sequences. An original harmless fixture rule can be:

```text
rule Tutorial_Marker {
    meta:
        description = "Synthetic marker, not malware identification"
    strings:
        $marker = "TRAINING_MARKER_27" ascii
    condition:
        filesize < 4096 and $marker
}
```

Create a small text file with that marker, a similar marker ending in `28`, and an ordinary text file. Expect only the exact marker case to match. Add a document that quotes the marker and observe the false-positive risk: context matters. Evaluate file formats, pattern specificity, metadata, conditions, and performance using the [YARA rule documentation](https://yara.readthedocs.io/en/stable/writingrules.html). These snippets are teaching artifacts; Sigma/YARA engines are not bundled or executed by the Python checks.

## Lesson 4: measure the experiment honestly

Label cases before running a rule. Suppose a fixture set has 8 correctly detected relevant cases, 2 missed relevant cases, and 2 benign alerts. Precision is `8/(8+2)=80%`; recall is `8/(8+2)=80%`. The equal numbers are coincidence. Small curated data does not estimate production rates reliably, and recall cannot be measured against unknown incidents.

Measure source-to-alert latency separately from alert-to-triage time and decision quality. Count duplicates and analyst effort. Document each rule's hypothesis, telemetry, assumptions, tests, exclusions, severity, owner, staging result, deployment version, review trigger, and retirement condition. An ATT&CK mapping helps describe behavior; it does not establish comprehensive visibility. Use the [MITRE ATT&CK knowledge base](https://attack.mitre.org/) for behavior descriptions, then verify your own evidence.

Build five harmless hypotheses: denied-then-allowed access, an unapproved synthetic role change, access using a revoked fixture session, missing expected collection heartbeat, and a training service configuration change. For each, create a matching case, an ordinary negative, and a near-match. Distinguish administrative activity requiring review from verified compromise.

## Lesson 5: investigate the supplied document-access scenario

1. Preserve the original event file and work on a copy. Record collector/source, acquisition time, tool version, and hash.
2. Define the question: did `u2` read `n1` after a role change, and was that permitted by the training policy?
3. Build the event-time timeline. Record E2's late ingestion separately. Do not infer a delayed action from a delayed record.
4. Correlate stable actor/session/document IDs, then identify the policy and ownership evidence missing from the dataset.
5. Write “observed”: E3 denied and E5 allowed. Write “supported inference”: the authorization state may have changed. Write “unresolved”: whether the read violated policy. The logs alone cannot settle that last claim.
6. Add a fictional policy register in your working copy and explain whether it supports or refutes the hypothesis. Preserve the distinction between supplied evidence and your added assumption.

A hunt is a bounded question over a defined dataset, not an unlimited search for suspicious-looking values. Include saved queries, time range, exclusions, negative results, and follow-up work. IP addresses may represent NAT/proxies, process IDs can be reused, and account names can change; correlation must reflect those limits.

## Lesson 6: rehearse response and evidence decisions

Preparation establishes owners, contacts, evidence access, and recovery methods. Triage assesses confidence, severity, and scope. Containment might suspend an account, revoke sessions, restrict a route, or isolate a host; compare operational impact and potential volatile-evidence loss before choosing. Eradication removes the cause and unwanted changes. Recovery restores useful service, correct permissions, clean data, appropriate credential state, and monitoring. Communication and lessons learned continue throughout. [NIST SP 800-61 Rev. 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final) connects incident response with broader risk management.

Forensics requires documented acquisition and reproducible analysis. Disk, memory, browser, email, endpoint, network, identity, and cloud sources have different volatility and collection limits. Live acquisition changes the environment; offline copies may omit volatile context. Where appropriate, use write protection and preserve originals separately. Chain of custody records handling; a matching cryptographic hash shows byte consistency, not whether an event was truthful or who caused it. Encryption, deletion, retention, and missing sensors constrain conclusions.

Threat intelligence adds context with source confidence, sharing conditions, and expiry. A reused IP or common tool does not uniquely identify an actor. Prefer a defensible limited conclusion to an unsupported attribution.

**Capstone:** deliver five tested hypotheses, a collection-health check, a UTC timeline, evidence register, confidence-labeled findings, and a recovery tabletop. A service that works after restoration may still contain the original misconfiguration; verify the corrected security boundary and legitimate operation separately.
