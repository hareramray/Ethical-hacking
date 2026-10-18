# 27. Reusable templates and glossary

[All topic roadmaps](README.md) | [Original master roadmap](../../ETHICAL_HACKING_ROADMAP.md#27-reusable-templates-and-glossary)

<!-- TOPIC-TOC:START -->

## Contents

- [Learning note template](#learning-note-template)
- [Scope and rules-of-engagement template](#scope-and-rules-of-engagement-template)
- [Finding template](#finding-template)
- [Example of a precise lab finding](#example-of-a-precise-lab-finding)
- [Coverage and progress templates](#coverage-and-progress-templates)
- [Command and interface vocabulary to practice](#command-and-interface-vocabulary-to-practice)
- [Glossary](#glossary)
- [Personal starting checklist](#personal-starting-checklist)
- [Expanded documentation roadmap](#expanded-documentation-roadmap)
  - [Stage 1: Establish identifiers and artifact organization](#stage-1-establish-identifiers-and-artifact-organization)
  - [Stage 2: Design a test case before collecting output](#stage-2-design-a-test-case-before-collecting-output)
  - [Stage 3: Build a hypothesis log](#stage-3-build-a-hypothesis-log)
  - [Stage 4: Maintain change and cleanup records](#stage-4-maintain-change-and-cleanup-records)
  - [Stage 5: Review templates through actual use](#stage-5-review-templates-through-actual-use)
- [Additional reusable templates](#additional-reusable-templates)
  - [Test-case record](#test-case-record)
  - [Hypothesis record](#hypothesis-record)
  - [Evidence register](#evidence-register)
  - [Change and cleanup register](#change-and-cleanup-register)
  - [Remediation verification record](#remediation-verification-record)
  - [Weekly learning review](#weekly-learning-review)
- [Glossary-building exercise](#glossary-building-exercise)
- [Documentation capstone](#documentation-capstone)

<!-- TOPIC-TOC:END -->



## Learning note template

```markdown
# Topic / exercise title

Date and time zone:
Roadmap section:
Objective and prerequisite:
Authorized lab assets:
Software versions and snapshot:

## Normal behavior
What should happen, and which security boundary should hold?

## Hypothesis and test
What observation would support or disprove the hypothesis?
Actions, inputs, expected result, rate/resource limits, stop condition.

## Evidence and interpretation
Sanitized requests, output, logs, timestamps, and artifact locations.
Observed facts:
Alternative explanations:
Uncertainty and untested conditions:

## Fix and retest
Root cause:
Change made:
Negative test (unauthorized behavior is blocked):
Positive test (legitimate behavior still works):
Remaining variants:

## Cleanup and reflection
Restored/removed artifacts:
Mistakes and lessons:
Next independent exercise:
Current skill level (0–4):
```

## Scope and rules-of-engagement template

```markdown
# Assessment scope

Owner and written authorization reference:
Objective and success criteria:
Dates, time zone, and approved testing windows:
In-scope assets and exact identifiers:
Excluded assets and third-party dependencies:
Test accounts, roles, tenants, and synthetic data:
Permitted methods and source systems:
Rate/resource limits and prohibited actions:
Disruptive/special activities requiring separate agreement:
Stop conditions, emergency contact, and escalation channel:
Backup, restoration, and change owners:
Evidence storage, access, retention, and deletion:
Report recipients and delivery method:
Cleanup and retest responsibilities:
Publication/disclosure terms:
```

## Finding template

```markdown
# FIND-001: Precise title describing the failed control

Status and severity:
Affected assets / versions / endpoints:
Affected identities or roles:
First observed and last verified:
Confidence and prerequisites:

## Summary and root cause
Expected behavior:
Observed behavior:
Underlying cause:

## Minimal reproduction
1. Establish the documented lab/test state.
2. Perform the minimum agreed test action.
3. Compare actual behavior with the control case.

## Evidence
Sanitized artifacts, timestamps, and references.

## Impact and severity reasoning
Demonstrated impact:
Potential impact and assumptions:
CVSS version/vector if required:
Business context and affected scope:

## Remediation
Immediate mitigation:
Durable fix:
Owner and dependencies:
Regression tests and related areas to review:

## Retest
Date and environment:
Change reviewed:
Positive/negative test results:
Remaining issues and final status:
```

## Example of a precise lab finding

**Title:** Ordinary users can read another user's synthetic invoice because the API omits an ownership check.

**Expected:** User A can read invoices assigned to A. User B cannot read A's invoices.

**Observed:** In the owned training application, B's authenticated session received A's synthetic invoice when requesting that record. Both users had the same ordinary role; the test did not use an administrator account.

**Evidence:** Record the two test identities, the invoice's expected owner, a sanitized request/response, and the corresponding server log. Retrieve only the synthetic test record needed to establish the failure.

**Cause and fix:** Authentication was present, but the server did not enforce record ownership for the read operation. Apply an ownership or explicit shared-access rule at the server's data-access boundary.

**Retest:** A still reads A's record; B is denied A's record; B still reads B's record; an unauthenticated request is denied; list/search/export paths obey the same rule. Record what was tested rather than claiming every possible path is fixed.

## Coverage and progress templates

| Test ID | Asset / feature | Role / perspective | Expected boundary | Result | Evidence / limitation |
| --- | --- | --- | --- | --- | --- |
| AUTHZ-01 | Synthetic invoice read | Ordinary user B | Cannot read A's private record | Not started | — |
| AUTHZ-02 | Synthetic invoice read | Record owner A | Can read own record | Not started | — |

| Topic | Target level | Current level | Evidence | Last practiced | Next action |
| --- | ---: | ---: | --- | --- | --- |
| DNS troubleshooting | 3 | 0 | — | — | Explain resolution, then diagnose a local fault. |
| Object authorization | 3 | 0 | — | — | Build a two-user ownership matrix. |
| Kernel research | 1 initially | 0 | — | — | Explain user/kernel boundaries before deeper study. |

## Command and interface vocabulary to practice

Learn what each command accepts, what it changes, how failure is reported, and how to get help. These are study prompts; adapt syntax to your installed OS and version.

- **Linux navigation and text:** `pwd`, `ls`, `cd`, `file`, `stat`, `less`, `head`, `tail`, `find`, `rg`/`grep`, `sort`, `uniq`, `cut`, `awk`, `sed`, and `diff`.
- **Linux administration:** `id`, `groups`, `chmod`, `chown`, `getfacl`, `ps`, `top`, `systemctl`, `journalctl`, `ip`, `ss`, and your distribution's package manager.
- **Windows/PowerShell:** `Get-Help`, `Get-Command`, `Get-ChildItem`, `Get-Content`, `Get-Process`, `Get-Service`, `Get-WinEvent`, `Get-Acl`, `Get-NetIPConfiguration`, `Get-NetTCPConnection`, and `Resolve-DnsName`.
- **Network/application observation:** `curl`, a DNS query client, Wireshark display filters, browser Network/Storage/Console panels, and a proxy's request editor.
- **Development:** `git status`, `git diff`, `git log`, Python virtual environments, debugger controls, your language's test runner, and structured log queries.

Practice reads and observation first; learn the scope and rollback of commands that modify permissions, services, files, accounts, or networking.

## Glossary

| Term | Meaning in this roadmap |
| --- | --- |
| Asset | A system, application, identity, data store, or other resource being protected or assessed. |
| Attack surface | The reachable interfaces and interactions through which a system can be influenced. |
| Trust boundary | A point where identity, privilege, ownership, or confidence in data changes. |
| Threat model | A structured explanation of valuable assets, potential adversaries, failure scenarios, and controls. |
| Authentication / authorization | Establishing an identity / deciding what that identity may do. |
| Session | State associating a sequence of interactions with an authenticated or otherwise identified client. |
| Principal / service account | An identity that can receive permissions / an identity used by a workload or service. |
| Least privilege | Granting only the access needed for the intended task. |
| RBAC / ABAC | Access decisions based on roles / attributes and conditions. |
| ACL | Access-control list specifying permissions for an object. |
| Tenant | A separately managed customer or organizational security context in a shared service. |
| Vulnerability / exploit | A security weakness / a method that takes advantage of a weakness. |
| Proof of concept | A limited demonstration of a behavior or security failure under stated conditions. |
| CWE / CVE | A weakness classification / an identifier for a specific disclosed vulnerability. |
| CVSS / EPSS | A severity scoring system / an estimate of exploitation probability over its defined horizon. |
| False positive / false negative | A reported problem that is not present / a real problem the method misses. |
| IOC / behavior | An observable indicator associated with activity / the action or pattern being performed. |
| TTP | Tactic, technique, or procedure used to describe adversary behavior. |
| ROE | Rules of engagement defining authorized assessment boundaries and operating conditions. |
| OSINT | Analysis of publicly available information for a defined purpose. |
| SAST / DAST / SCA | Static code analysis / testing a running application / analysis of software components and dependencies. |
| SBOM | Software bill of materials describing components in a software artifact. |
| IaC | Infrastructure as code: configuration describing infrastructure in a versionable form. |
| CI/CD | Automated integration and delivery/deployment workflows for software changes. |
| IdP / federation | Identity provider / trust allowing one system to rely on another system's identity assertions. |
| OAuth / OIDC / SAML | An authorization framework / an identity layer over OAuth / an assertion-based federation standard. |
| JWT | A token format carrying claims; security depends on correct validation and context. |
| MFA / passkey | Authentication using distinct factor categories / a public-key credential used through supported authentication protocols. |
| PKI / KMS / HSM | Public-key infrastructure / key management service or system / hardware security module. |
| Hash / MAC / signature | A digest / a keyed integrity check / a public-key-verifiable authenticity and integrity mechanism. |
| SSRF / XSS / CSRF | Server-side request forgery / cross-site scripting / cross-site request forgery. |
| IDOR / BOLA | Insecure direct object reference / broken object-level authorization; naming differs, but object access must be checked. |
| Race condition / TOCTOU | Behavior depending on competing timing / a check and later use occurring under changed conditions. |
| Privilege escalation | Crossing from a lower-authority context to greater authority through an unintended path. |
| Lateral movement | Moving from one system or identity context to another within an environment. |
| Control plane / data plane | Management and configuration interfaces / interfaces carrying workload traffic or data operations. |
| SIEM / EDR | Centralized security-event analysis / endpoint detection and response capabilities. |
| Fuzzing | Exercising a target with varied inputs to discover unexpected behavior. |
| RAG / prompt injection | Retrieval-augmented generation / untrusted content attempting to alter an AI system's behavior. |
| Remediation / retest | Correcting the underlying issue / checking that the correction works under defined conditions. |

## Personal starting checklist

- [ ] Choose a sustainable weekly study time and create a skill tracker.
- [ ] Read the authorization section and establish an isolated practice environment.
- [ ] Complete the first networking, Linux, Windows, and programming exercises.
- [ ] Write one useful lab note every week.
- [ ] Revisit weak prerequisites instead of skipping them.
- [ ] Complete an independent assessment and report before claiming practical proficiency.
- [ ] Choose one specialization based on the work you enjoy and can demonstrate.

## Expanded documentation roadmap

### Stage 1: Establish identifiers and artifact organization

Give each exercise, test case, finding, and evidence item a stable identifier. Use simple names that reveal purpose without exposing secrets. For example, `LAB-API-01`, `TEST-AUTHZ-03`, `FIND-002`, and `EVID-004` can connect notes without embedding a real customer name.

Separate original evidence, redacted copies, analysis, reports, and code. Keep the relationship between an original artifact and its redacted derivative clear. Record collection time, environment, collector, source, and any transformation. A hash can help establish whether a file changed; it does not prove the accuracy of the interpretation attached to it.

For local learning, a simple folder structure is sufficient. Client work must follow the agreed storage and access requirements. Keep report attachments and tool project files in the inventory because they often contain more information than the written findings.

### Stage 2: Design a test case before collecting output

Define the requirement, preconditions, identity, action, expected behavior, actual behavior, evidence, and cleanup. Include a legitimate positive control and an unauthorized negative control where applicable. Record whether a failure is a product defect, an environment problem, or an inconclusive result.

Use reusable parameter sets when a control applies across several roles or objects. Do not collapse distinct requirements into a single “authentication secure” checkbox. Registration, recovery, login, session renewal, elevation, revocation, and deletion have different state and evidence requirements.

### Stage 3: Build a hypothesis log

A hypothesis log preserves reasoning that disappears from a final report. Record the suspected failure, what would confirm or disprove it, the smallest test, its result, and the next decision. Include rejected hypotheses so you do not repeat the same unsuccessful work without a reason.

This is particularly useful for races, caches, identity propagation, and distributed systems. Several components may contribute to an observation. Changing one variable at a time and recording the state makes the eventual explanation more defensible.

### Stage 4: Maintain change and cleanup records

Record every temporary account, permission, certificate, listener, file, integration, resource, and synthetic dataset you create. Include its owner, location, purpose, creation time, removal method, and verification result. Cleanup must account for remote and external state that a local VM snapshot cannot restore.

For a correction, record the original condition, proposed change, expected behavior, operational tradeoff, rollback method, and retest. This supports both implementation review and later assessment of whether the fix was complete.

### Stage 5: Review templates through actual use

Use a template on a small exercise, then ask someone to reproduce the result. Add fields only when they resolve a real omission. Remove unused fields if they encourage empty boilerplate, but retain the information necessary for scope, identity, evidence, reasoning, and verification.

Track statuses consistently. “Not tested,” “inconclusive,” “not applicable,” and “passed the stated test” have different meanings. A blank cell is ambiguous. In a final report, explain constraints rather than letting an incomplete test look like a successful check.

## Additional reusable templates

### Test-case record

```markdown
# TEST-001: Specific security requirement

Related roadmap topic:
Requirement and reference version:
Asset, environment, and build:
Identity, role, tenant, and object ownership:
Preconditions and initial state:
Authorized action and resource/rate limits:
Expected secure behavior:
Actual behavior and side effects:
Positive-control result:
Negative-control result:
Evidence identifiers:
Result: passed / finding / inconclusive / not applicable / not tested
Limitations and next action:
Reset or cleanup verified:
```

### Hypothesis record

```markdown
# HYP-001

Observed symptom:
Suspected root cause:
Alternative explanation:
Evidence that would distinguish them:
Smallest permitted test:
Prediction:
Observation:
Interpretation and confidence:
Decision: supported / rejected / unresolved
Next test or reporting action:
```

### Evidence register

| Evidence ID | Source and time zone | Identity/context | Purpose | Original location | Redacted copy | Access/retention rule |
| --- | --- | --- | --- | --- | --- | --- |
| EVID-001 | Lab app log, recorded timestamp | Synthetic user A | Establish authorized access | Private artifact path | Report attachment path | According to lab/engagement plan |

### Change and cleanup register

| Change ID | Asset and owner | Temporary change | Intended duration | Rollback/removal | Verification | Final status |
| --- | --- | --- | --- | --- | --- | --- |
| CHG-001 | Owned lab application | Synthetic test account | Current exercise | Remove account and review related sessions | Account/session checks | Planned |

### Remediation verification record

```markdown
# RETEST-001

Related finding:
Fix description and change reference:
Corrected build/configuration:
Environment and test identities:
Original failing case:
Observed post-fix result:
Legitimate-use control:
Adjacent variants tested:
Logs or code evidence:
Remaining uncertainty or exposure:
Status and owner:
Cleanup evidence:
```

### Weekly learning review

```markdown
# Week review

Planned objectives:
Completed exercises and evidence:
Help used and remaining independence gaps:
One corrected misunderstanding:
One delayed repeat result:
Actual focused time:
Tracker levels changed and why:
Deferred topics:
Next week's smallest useful outcomes:
```

## Glossary-building exercise

For every unfamiliar term, record its expanded name, purpose, a concrete example, what it is often confused with, and where it appears in a protocol or architecture. Include a diagram or small experiment when that makes the distinction clearer.

Useful contrasts include authentication versus authorization, hashing versus encryption, identity policy versus resource policy, origin versus site, severity versus likelihood, code signing versus safe behavior, and a vulnerability identifier versus a confirmed affected deployment. Expand abbreviations at first use in a report so a reader does not need to infer their meaning.

## Documentation capstone

Run a small assessment using the scope template, three test cases, two hypotheses, an evidence register, one finding, one repair, and a cleanup record. Hand only the documentation to a reviewer. Ask them to identify what happened, which claim is supported, how to reproduce it, which fix was verified, and what remains unknown.

**Pass:** The artifacts agree about assets, identities, times, statuses, and scope; sensitive fields are handled consistently; the reviewer can follow the chain from requirement to test to finding to remediation evidence without hidden assumptions.
