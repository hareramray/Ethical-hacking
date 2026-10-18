# 23. Tutorial: reporting, remediation, and retesting

[Index](README.md) | [Complete source curriculum](curriculum/23-reporting-remediation-and-retesting.md) | [Original roadmap](../roadmaps/23-reporting-remediation-and-retesting.md)

Start this chapter with your first practical lesson. Your report should let an owner understand a risk, an engineer correct its cause, and a second tester verify the outcome. Use [the templates](templates/README.md) and the [portable authorization example](examples/README.md) to practice without collecting real records.

## Lesson 1: convert an observation into a bounded claim

“The response was 200” is an observation, not a finding. A defensible statement is: “In the synthetic local function with ownership enforcement disabled, ordinary user Bob received Alice's private note despite the specified owner-only rule.” This identifies actor, resource, intended control, conditions, and observed result.

Before confirming it, check account identity, role, record owner, sharing rules, and current application state. A stale cache, administrator session, incorrect fixture, or deliberate share could explain the same screen. Test each plausible explanation with a small change. A confirmed false positive is a useful result because it improves the method.

| Observation | Interpretation | Evidence | Remaining uncertainty |
| --- | --- | --- | --- |
| Bob receives `n1` with owner `alice` in the disabled-check model | Owner rule not enforced in this branch | Test call, result, source/configuration | Only this function/path was assessed. |
| Bob receives 403 with check enabled | Cross-owner read rejected | Repeat call and result | Does not test exports, workers, or mobile cache. |
| Alice still receives 200 | Legitimate owner behavior remains | Positive control | Other roles were not implemented. |

Keep observed impact separate from a supported wider implication and untested speculation. “All customer data was exposed” requires evidence of that scope; one synthetic record proves a narrower boundary failure. Where useful, add the applicable CWE category or verification requirement with its reference version. A classification label never replaces the root-cause explanation.

## Lesson 2: make reproduction independent of memory

Run `python tutorials/examples/access_lab.py`. Save the output in a private exercise folder, recording interpreter version and date/timezone. Document the exact starting state: two public fixture identities, two invented notes, no sharing, and a local function comparison. The HTTP server always enforces ownership, so do not describe the deliberately disabled function branch as a remotely exposed server flaw.

Write reproduction as a short sequence:

1. Obtain the documented source revision and inspect `NOTES` to establish `n1` ownership.
2. Invoke `read_note('bob', 'n1', enforce_owner=False)` in the local test model.
3. Record status 200 and the synthetic note body; compare Bob's intended permission.
4. Repeat with ownership enforcement enabled and record 403 without the note.
5. Repeat Alice's owner read and an unauthenticated case to exclude a broken service or account as the explanation.

Record target/build, identity/role/tenant, preconditions, inputs, sequence, expected/actual results, side effects, and limitations. For races or asynchronous work, record timing and worker completion. A request that returns an error may still cause a forbidden side effect; verify persisted state too.

Redact token values, personal records, and unrelated context. Preserve field relationships needed to assess the claim. Maintain original evidence separately where retention is justified, plus a labeled redacted derivative; do not overwrite the only original. Machine-readable output often provides stronger reproducibility than a cropped screenshot, though screenshots can clarify UI state.

## Lesson 3: explain severity without inventing business impact

Describe the technical effect, reachability, privileges, user interaction, affected data/operations, scope, preconditions, and existing controls. Then ask the owner about real business consequences. The same missing owner check in a toy calendar and a billing platform shares a failure mechanism but may have different priorities and data sensitivity.

If an engagement uses CVSS, include its version, vector, and metric rationale, and identify which threat/environment context was considered. A base score, an exploitation forecast, and a business priority answer different questions. Do not copy a scanner rating as if it settled all three. Use the [FIRST CVSS v4.0 specification](https://www.first.org/cvss/v4.0/specification-document) for that version's metric definitions; do not mix vectors across versions.

For this local learning fixture, state “training severity only; no production asset assessed.” You can discuss hypothetical consequences explicitly without assigning fabricated losses, legal conclusions, or a universal remediation deadline.

## Lesson 4: write a fix an engineer can implement

Specify where enforcement belongs and the property it must enforce. For object access: the server/data-access boundary must authorize the authenticated principal for the requested object and operation before returning data or scheduling side effects. Hiding a button or changing IDs does not enforce that requirement.

Separate three layers:

| Layer | Example | What remains |
| --- | --- | --- |
| Immediate mitigation | Temporarily restrict an affected route while evaluating exposure | Other paths may still exist. |
| Durable fix | Centralize owner/shared-access checks for reads and writes | Correctly integrate every relevant caller. |
| Systemic improvement | Add role/tenant/operation regression cases and review analogous endpoints | Maintain tests as architecture changes. |

For an excessive service permission, name the account, object/parent path, unnecessary right, required legitimate right, and rollback. For a leaked synthetic secret, removing the visible file is only one action: revoke/rotate the credential, update consumers, and verify obsolete access fails. Include owner, dependencies, compatibility risks, and validation. If source access is unavailable, specify required behavior without inventing internal line numbers.

## Lesson 5: retest the root cause and adjacent paths

Prepare the matrix while the original failure is fresh:

| Case | Secure result | Why it matters |
| --- | --- | --- |
| Alice reads Alice's record | Allowed | Legitimate operation survives. |
| Bob reads Alice's record | Denied without body | Original unauthorized case is blocked. |
| Bob reads Bob's record | Allowed | Fix did not deny the entire role. |
| Unknown identity | Denied | Authentication remains enforced. |
| Missing record | Controlled not-found behavior | Error handling remains coherent. |
| List/search/export/worker paths | Same intended access policy | Adjacent bypass surfaces, if implemented. |

Confirm corrected build/configuration, environment, current identities, and data state. A denial caused by expired credentials, removed data, or a stopped service is not proof of the fix. Use logs/source and side-effect checks to strengthen the interpretation. Record unimplemented/unavailable variants as not tested.

Use distinct statuses: open; partially remediated; remediated and verified; risk accepted by the responsible owner; not retested. “Developer says fixed” is a change notification, not verification. Preserve dates, change reference, test evidence, residual exposure, and cleanup.

## Lesson 6: assemble reports for two audiences

Use an executive summary stating objective, environment, most material supported risks, strengths, corrective actions, and limitations in plain language. Follow it with scope/constraints, methodology and coverage, findings overview, detailed findings, remediation plan, retest results, and technical appendices. Ensure the summary does not strengthen claims beyond the supporting findings.

An engineer needs the controlling condition, minimal reproduction, cause, fix, and regression cases. An owner needs the affected operation, business context, priority rationale, decision/owner, and unresolved risk. Practice a two-minute explanation and a technical walkthrough of the same evidence. When someone disputes a finding, revisit preconditions together and correct mistakes openly.

Urgent findings go through the agreed escalation channel, with a written record. Routine status updates should identify completed coverage, material findings, blockers, next work, and timing. A handover needs stable artifact references rather than a terminal-history dump.

**Capstone:** write three distinct lab findings, one inconclusive test, one dismissed false positive, a coverage matrix, and cleanup register. Retest two findings and leave the third's status explicit. Ask a reviewer to reproduce one result from a clean state. Review scope, evidence, reproducibility, severity, root-cause fix, positive/negative checks, redaction, and clarity. If the reviewer must guess which identity you used, the report is not finished.
