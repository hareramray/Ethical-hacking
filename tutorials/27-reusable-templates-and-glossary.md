# 27. Tutorial: reusable templates, vocabulary, and evidence organization

[Index](README.md) | [Complete source curriculum](curriculum/27-reusable-templates-and-glossary.md) | [Original roadmap](../roadmaps/27-reusable-templates-and-glossary.md)

The [template folder](templates/README.md) contains editable copies of every source template, the registers, coverage/progress tables, and complete glossary. This lesson shows how to fill them using one consistent synthetic example. Copy blanks into your own practice folder; keep the reusable originals unchanged.

## Lesson 1: establish identifiers before collecting evidence

Use `LAB-API-01` for the exercise, `TEST-001` for a requirement, `HYP-001` for an explanation, `EVID-001` for an artifact, `FIND-001` for a confirmed weakness, and `RETEST-001` for verification. Identifiers connect reasoning without embedding a real customer or secret in filenames.

Separate original evidence, redacted derivatives, analysis, reports, and code:

```text
practice/LAB-API-01/
  scope.md
  tests/
  originals/
  redacted/
  analysis/
  report/
  changes.md
```

The tutorial folder ignores `practice/` in Git, but that is convenience rather than access control. Store real engagement material only where its owner permits. Record who collected each artifact, source/environment, time/timezone, tool/settings, transformation, and access/retention rule. A hash detects byte changes relative to a known value; it does not prove the interpretation or truth of an event.

## Lesson 2: write scope and a learning note

Fill [scope-and-roe.md](templates/scope-and-roe.md) with your owned local fixture, exact loopback endpoint if used, test identities, synthetic data, permitted actions, rate/resource bounds, stop condition, restoration method, evidence handling, recipients, retest, and publication terms. Exclude unrelated hosts and services explicitly. A written list of targets without an authorizing owner is incomplete for a real engagement.

Fill [learning-note.md](templates/learning-note.md): objective “distinguish authentication from record ownership”; prerequisite Python/function basics; environment “public synthetic fixture, interpreter version recorded”; normal behavior “only the owner reads a note”; evidence “local calls and returned statuses”; repair “apply owner check before returning data”; reflection “HTTP status alone needs identity and body context.” Use [the portable examples](examples/README.md) to reproduce it.

Keep negative and positive tests distinct. A negative case means the unauthorized behavior should fail, not that the experiment was unsuccessful. A positive control means a legitimate action should continue to work. If both fail because the server is stopped, you have not demonstrated authorization enforcement.

## Lesson 3: design tests and hypotheses before drawing conclusions

Complete [test-case.md](templates/test-case.md) with:

| Field | Filled training example |
| --- | --- |
| Requirement | Bob cannot read Alice's private note. |
| Build/state | Supplied local authorization model; synthetic `n1` belongs to Alice, no sharing. |
| Identity | Bob, ordinary fixture user; no administrator rights. |
| Action | Call `read_note('bob', 'n1', enforce_owner=False)` only in the in-memory comparison. |
| Expected | Denial without note data. |
| Actual | Status 200 and synthetic Alice data in the intentionally defective branch. |
| Controls | Alice succeeds; unknown identity fails; enabling check denies Bob. |
| Limitation | This branch is not exposed by the supplied HTTP server. |

Use [hypothesis.md](templates/hypothesis.md) for “ownership check missing” and an alternative “record was intentionally shared.” Evidence that distinguishes them is the fixture's policy/owner state plus the controlling code branch. Reject the sharing explanation in this fixture, but do not assume it is false in an unfamiliar real application.

Authentication registration, login, recovery, refresh, elevation, revocation, and deletion are separate stateful requirements. Do not compress them into “auth secure.” A hypothesis log is particularly useful for caches, asynchronous workers, races, and identity propagation: record the smallest test that changes one variable and preserves the rest.

## Lesson 4: connect a finding, evidence, change, and retest

Fill [finding.md](templates/finding.md) with a precise title, scope/build, role, prerequisites, expected/observed behavior, root cause, minimal reproduction, sanitized artifacts, impact, assumptions, correction, and retest. The source's synthetic invoice example and this synthetic note example have the same missing object-authorization pattern, but their evidence belongs to different fixtures. Do not merge them into a claimed observation.

The [evidence register](templates/evidence-register.md) connects EVID-001 to the original call/result and EVID-002 to its corrected counterpart. The [change register](templates/change-and-cleanup-register.md) records a temporary listener, profile, test account, certificate, permission, file, integration, or cloud resource, including owner, lifetime, reversal, verification, and final state. A VM snapshot does not undo external cloud resources or revoked/issued credentials.

Use [retest.md](templates/retest.md) to identify the corrected build/configuration, original failing case, legitimate control, adjacent variants, logs/code evidence, remaining exposure, and final status. For the API fixture, validate owner/non-owner/unknown/missing-object cases. Do not claim list/search/export coverage when those routes are not implemented.

Distinguish `not tested`, `inconclusive`, `not applicable`, `passed the stated test`, and `finding`. Finding remediation statuses separately distinguish open, partial, verified, accepted by owner, and not retested. An empty table cell does not tell a reviewer which applies.

## Lesson 5: learn command vocabulary by question and side effect

| Question | Linux tools | Windows/PowerShell counterparts |
| --- | --- | --- |
| Where am I and what is here? | `pwd`, `ls`, `cd`, `find` | `Get-Location`, `Get-ChildItem`, `Set-Location` |
| What are the bytes/type/metadata? | `file`, `stat`, `less`, `head`, `tail` | `Get-Item`, `Get-Content`, appropriate format/byte tools |
| How can I filter/compare text? | `rg`/`grep`, `sort`, `uniq`, `cut`, `awk`, `sed`, `diff` | `Select-String`, `Sort-Object`, `Select-Object`, `Compare-Object` |
| Who has access? | `id`, `groups`, `getfacl` | `whoami`, `Get-Acl` |
| Which processes/services/logs? | `ps`, `top`, `systemctl`, `journalctl` | `Get-Process`, `Get-Service`, `Get-WinEvent` |
| Which network configuration? | `ip`, `ss`, DNS client | `Get-NetIPConfiguration`, `Get-NetTCPConnection`, `Resolve-DnsName` |
| How do I learn the interface? | `man`, documented `--help` | `Get-Help`, `Get-Command` |

These are analogous tasks, not drop-in syntax translations. PowerShell pipelines pass objects; many Unix tools process text. `chmod`, `chown`, package managers, and service/network modification commands change state: learn target, privilege, effect, and rollback before running them. Practice on a disposable file first. Browser Network/Storage/Console panels, a proxy request editor, `curl`, and Wireshark display filters answer different application questions.

For development, use `git status`, `git diff`, and `git log` to explain changes; isolate Python dependencies with a virtual environment; learn debugger step/continue/breakpoint controls and your test runner. Structured log queries need schema and null/time handling, not only syntax recall.

## Lesson 6: turn the glossary into usable distinctions

The [complete glossary](templates/glossary.md) retains every original term. For each unfamiliar term, add expanded name, purpose, concrete example, common confusion, and location in a system. Start with these contrasts:

| Terms | Applied distinction |
| --- | --- |
| Asset / attack surface / trust boundary | A note store is the asset; its API is an influence path; user-to-server and tenant-to-tenant transitions are boundaries. |
| Principal / service account / least privilege | An identity receives rights; a workload uses a service identity; grant only its intended operations. |
| RBAC / ABAC / ACL / tenant | Roles, attributes, object permission entries, and organizational isolation describe related but different policy structures. |
| Vulnerability / exploit / proof of concept | A weakness, a way to exercise it, and a bounded demonstration are not interchangeable claims. |
| CWE / CVE / CVSS / EPSS | Weakness class, disclosed-vulnerability identifier, severity model, and exploitation forecast answer different questions. |
| Hash / MAC / signature / encryption | Digest, keyed integrity, public-key-verifiable authenticity, and confidentiality have distinct key/trust properties. |
| OAuth / OIDC / SAML / JWT | Delegated authorization, an identity layer, assertion federation, and a token format are not four synonyms for login. |
| SSRF / XSS / CSRF / IDOR-BOLA | Server destination abuse, browser code execution, forged authenticated requests, and missing object authorization involve different boundaries. |
| Race / TOCTOU | Timing-dependent behavior includes cases where state changes between checking and using it. |
| Control plane / data plane | Management/configuration operations differ from workload traffic/data operations. |
| SAST / DAST / SCA / SBOM | Code analysis, running-app tests, component analysis, and component inventory provide different evidence. |
| IOC / behavior / TTP / SIEM / EDR | Indicators, actions, behavior descriptions, central event analysis, and endpoint response describe distinct investigation elements. |
| RAG / prompt injection | Retrieval supplies context; untrusted content may attempt to redirect behavior. Authorization must still hold outside generated text. |

Use the glossary for remaining terms including threat model, session, false positive/negative, ROE, OSINT, IaC, CI/CD, IdP/federation, MFA/passkeys, PKI/KMS/HSM, privilege escalation, lateral movement, fuzzing, remediation, and retest. Explain each with a fixture rather than merely expanding letters.

## Lesson 7: review the documentation as a complete chain

Fill [weekly-review.md](templates/weekly-review.md) with planned/completed outcomes, evidence, help, corrected misunderstanding, delayed repeat, focused time, level changes, deferred topics, and the next small task. Use [coverage-and-progress.md](templates/coverage-and-progress.md) for test coverage separately from proficiency.

Complete one scope record, three tests, two hypotheses, evidence register, one finding, correction, retest, and cleanup. Give only the packet to a reviewer. They should identify the requirement, actual identity/state, supported claim, reproduction, verified correction, and remaining uncertainty. Remove fields that only produce boilerplate, but retain the information needed for those decisions. A consistent, reviewable evidence chain is the purpose of the templates.
