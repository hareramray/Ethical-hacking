# 13. Tutorial: secure code review and software delivery

[Index](README.md) · [Complete source curriculum](curriculum/13-secure-code-review-and-software-delivery.md) · [Original roadmap](../roadmaps/13-secure-code-review-and-software-delivery.md)

## Review the code that actually runs

Secure review connects an implementation claim to a particular build and deployment. “We validate filenames” is incomplete until you know the helper's guarantee, the callers, the normalization order, the worker's identity, and the directory permissions. Prerequisites are one language/framework, Git, tests, debugging, dependencies, and tutorials 11–12. Use an owned small repository with synthetic data and disposable credentials.

Start manually before running scanners. Map a normal user action, a privileged action, and a background action. Include HTTP, CLI, uploads, file imports, scheduled tasks, message consumers, administrative jobs, and exported library interfaces. Locate configuration loading, dependency injection, authentication, authorization, transaction boundaries, serializers, errors, storage clients, and external integrations.

## Lesson 1: create a review map and invariants

For each path, write source → transformations → validation → authorization → sink → response/log. Sources include requests, files, messages, stored records, environment settings, and partner data. Sinks include queries, process execution, templates, deserialization, files, network fetches, redirects, logs, cryptography, policy decisions, and client serialization. Stored data is not automatically trusted: a user-supplied comment remains user-supplied after a database round trip.

Add control flow: middleware, decorators, wrappers, callbacks, exceptions, feature flags, retries, cancellation, worker scheduling, and administrative overrides. A correct handler can call an unsafe helper; a secure normal path can have a fail-open exception path. Record execution identities for web process, worker, deployment job, and database connection because sink privileges determine consequence.

Use concrete invariants: “Only the current tenant's records appear in an export”; “the worker writes only inside its assigned output directory”; “a coupon is redeemed at most once”; “caller-controlled fields cannot change ownership.” Include data-model constraints, lifecycle states, identifier reuse, stale caches, permission changes, and transactions. Record commit, dependency versions, configuration assumptions, build/run commands, and fixture reset so the review matches a runnable artifact.

## Lesson 2: distinguish security operations

| Operation | Question it answers | Common mistake |
| --- | --- | --- |
| Validation | Does this value satisfy the input/domain contract? | Treating a valid identifier as proof of ownership |
| Canonicalization | What normalized object or meaning does this representation denote? | Decoding again after the relevant check |
| Encoding/escaping | How is data represented safely in a specific output grammar? | Reusing HTML escaping for SQL or a shell |
| Sanitization | Which parts of intentionally structured content are permitted? | Assuming a helper named `safe` provides every required guarantee |
| Parameterization | Can values be supplied separately from interpreter structure? | Concatenating dynamic identifiers despite parameterized values |
| Authorization | May this subject perform this action on this resource/context? | Checking only the HTTP route while workers bypass it |

Read implementations and failure semantics rather than names. Check alternate encodings, types, API versions, tenant contexts, duplicated code, custom serializers, raw-query escape hatches, and framework hooks. Follow denial to its end: a rejected response must not leave a partial write or queued message. Concurrency around balances, inventory, tokens, ownership, and file creation needs an atomic invariant, not merely a sequence of individually valid statements.

## Lesson 3: a local worker authorization exercise

Save this as `worker_review.py`; run with Python 3 on Windows or Linux. It does not create files or contact services.

```python
users = {"alice": {"tenant": "alpha", "active": True}}
reports = {"r1": {"tenant": "alpha", "label": "TRAINING_REPORT"}}
jobs = []

def permitted(user, report):
    return user["active"] and user["tenant"] == report["tenant"]

def enqueue(subject, report_id):
    if not permitted(users[subject], reports[report_id]):
        raise PermissionError("denied")
    jobs.append({"subject": subject, "report": report_id})

def run_job(job):
    user = users[job["subject"]]
    report = reports[job["report"]]
    if not permitted(user, report):
        return {"state": "denied", "output": None}
    return {"state": "complete", "output": report["label"]}

enqueue("alice", "r1")
users["alice"]["active"] = False
assert run_job(jobs[0]) == {"state": "denied", "output": None}
users["alice"]["active"] = True
assert run_job(jobs[0])["state"] == "complete"
print("revoked job denied; authorized job completed")
```

The selected policy requires current authority at execution. Some business systems intentionally use a different snapshot-of-approval model; document that decision rather than assuming one universal answer. Trace the job's subject and report identifiers back to trusted enqueue context, then inspect delivery authorization separately. As a paper comparison, remove the `permitted` check from `run_job`: earlier handler authorization no longer guarantees the chosen lifecycle rule.

Capture four source-to-sink traces with code references, reachability, caller control, intervening checks, failure condition, and minimal verification. For the worker, evidence includes message schema, policy decision, job state, and the active-user control. Repair the shared invariant and all call paths instead of adding one isolated HTTP check.

## Lesson 4: stack-specific hazards

| Area | What to inspect | Bounded local verification |
| --- | --- | --- |
| Queries/interpreters | Trusted structure, typed APIs, dynamic identifiers, template helpers | Quoted synthetic strings preserve data meaning |
| Files/processes | Path components, parent ownership, links, arguments, environment, working directory, executable selection | Harmless sentinels and a stub that records arguments |
| Serialization/reflection | Input-selected types, dynamic evaluation, unsafe convenience APIs, excess output fields | Contract assertions against allowed data structures |
| Types | Missing/null, coercion, numeric boundaries, overflow, implicit conversions | Runtime-specific boundary values, including false and zero |
| Memory/native interfaces | Buffer bounds, ownership, lifetime, trusted lengths, unsafe FFI | Disposable sanitizer-assisted build with small fixtures |
| Concurrency/filesystem races | Check-then-act, locks, unique constraints, retries, temporary-file creation | Deterministic competing operations with strict timeouts |
| Cryptography | Vetted APIs, secure randomness, password hashing, authenticated encryption, nonce use, key separation/rotation, certificate verification | Library failure/rotation tests; no custom cryptographic scheme |
| Errors | Partial writes, missing rollback, unsafe fallbacks, log disclosure | Simulated dependency outage and inspection of resulting state |

Consult the actual language/framework documentation for semantics. A framework's safe default can be bypassed by an extension or deployment setting. A local helper that is currently unreachable should be labeled accurately: harden or remove it when sensible, but do not claim a demonstrated remote path without evidence.

## Lesson 5: choose verification tools by their evidence

SAST analyzes code patterns/data flow; software composition analysis identifies dependency/advisory relationships; secret scanning identifies credential-like content; DAST observes running behavior; interactive analysis combines runtime instrumentation and activity; fuzzing explores input space; manual review explains business invariants and control flow. Each has blind spots and input requirements.

Run static analysis after your manual baseline. For every warning, record entry point, reachability, attacker control, mitigation, impact, and disposition. Compare one useful detection, one false positive, and one manual finding the tool missed. A warning disappearing after a rename is not evidence that the insecure behavior disappeared.

Use unit tests for policy functions, integration tests for persistence/worker behavior, contracts for input/output agreement, property-based tests for broad invariants, and end-to-end tests for critical real flows. Every rejection needs a successful intended operation. Add narrow justified suppressions with owner and expiry when needed; choose pull-request thresholds based on risk rather than silencing a whole category.

A bounded fuzz target needs a format, deterministic seeds, time/memory limits, crash capture, minimization, and reset. Start with a local parser and a small corpus of valid/boundary inputs. Minimize a failure to its essential structure, identify whether it is an actual security consequence or ordinary input error, then turn the invariant into a regression. Advanced large-scale fuzzing is an extension, not a substitute for this reasoning.

## Lesson 6: dependencies and release artifacts

Map direct/transitive and production/development/build dependencies. Inspect lockfiles, integrity hashes, private registries, namespace resolution, abandoned packages, lifecycle scripts, and update ownership. An installed affected package requires triage of vulnerable functionality and runtime/build use, while still tracking supported updates. A lockfile improves reproducibility but does not establish trust in the selected package.

An SBOM records components, versions, and relationships in a machine-readable format such as SPDX or CycloneDX. Bind it to the built artifact digest so it answers questions about a released image rather than only today's source tree. VEX communicates an applicability assessment under stated conditions; it is not permanent proof or a replacement for local evidence.

Trace source commit → dependency resolution → builder → artifact store → release approval → deployment → runtime. At each transition ask who can write input, what executes, which credentials are present, and what the next stage verifies. Protect branches, reviews, identities, repository tokens, tags, and audits. A signed artifact still needs a trusted producer, expected source/workflow, and an enforced verification policy. Provenance records build origin and process claims; use the [SLSA specification](https://slsa.dev/spec/) to study what your consumer actually verifies.

For a portable integrity demonstration, save the following as `artifact_lab.py` in an empty lab folder:

```python
from hashlib import sha256

artifact = b"TRAINING_RELEASE\n"
approved = sha256(artifact).hexdigest()
def accepted(candidate):
    return sha256(candidate).hexdigest() == approved

assert accepted(artifact)
assert not accepted(artifact + b"UNAPPROVED_CHANGE\n")
print("original accepted; modified copy rejected")
```

This demonstrates digest comparison, not producer authentication. If an attacker can replace both artifact and approved digest, this check alone is insufficient. Keep the approval record in a separately protected release process, then add supported signature/provenance verification with an explicit trusted identity. Preserve this limitation in your evidence.

## Lesson 7: protect CI/CD and infrastructure

Separate untrusted contribution tests from privileged release jobs. Inspect event triggers, fork behavior, branch/ref assumptions, reusable actions/workflows, parameter handling, dependency pins, third-party integrations, and environments receiving secrets. Give each job only the token permissions it needs. A test job should not inherit artifact publication or deployment authority.

Review runner isolation, reused workspaces, caches, downloaded artifacts, tool installation, and cleanup. Treat cached inputs according to their provenance and integrity. Secret lifecycle includes creation, storage, injection, scope, rotation, revocation, redaction, and incident response. Prefer supported short-lived workload credentials. Removing a secret from Git or a build log does not revoke it; use a fictional marker for detection exercises and document revocation using a disposable credential.

Keep build-time and runtime secrets distinct. Inspect logs, archives, images/layers, caches, debug artifacts, and environment exports for retention. Infrastructure-as-code plans, state files, modules/providers, deployment identities, and remote state have their own trust and confidentiality needs. Review plans before application, separate environments, and compare intended configuration with drift.

Package minimal runtime images, choose appropriate non-root identities, maintain patch/rebuild cadence, and promote the same reviewed artifact. Plan migrations, staged rollout, rollback, and retention of release evidence. Post-release work includes telemetry, vulnerability intake, dependency advisories, patch verification, emergency access, key compromise response, and feeding lessons into design requirements.

## Three scenarios, troubleshooting, and completion

**HTTP policy missing in worker:** use the earlier lab, trace lifecycle change, repair execution/delivery policy, and prove authorized jobs still complete. **Uncertain static warning:** place one unsafe training helper in an unreachable module and one reachable equivalent behind a local entry point; compare call graphs, tests, and scanner output without overstating the unused helper's impact. **Artifact promotion:** compare original and modified bytes, inspect per-job permissions, enforce artifact identity at promotion, and practice rollback to a known approved build.

If a repair breaks valid requests, revisit the intended invariant and contract. If an updated dependency persists in the SBOM, inspect transitive paths and the actual built image. If signature verification accepts the wrong producer, repair the trust policy. If an unchanged source commit produces different output, investigate build inputs, toolchain, environment, and nondeterministic metadata rather than assuming compromise.

Submit two manual reviews from clean checkouts, four confirmed/repaired defects, ten meaningful security assertions, a triaged scanner report, build-linked SBOM, supported signature/provenance evidence with limitations, a scoped CI workflow, and a tested rollback. Keep code, configuration, tests, and artifact identity connected. The [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) supplies focused implementation guidance for individual controls.

**Answer-guided checks:** Is persisted data trusted? No; its origin and validation still matter. Does a hash authenticate a producer? No, unless the expected value is trusted through another mechanism. Does removing a committed key revoke it? No; invalidate the credential at its authority. Why review exceptions and workers? They can bypass the checks visible in the normal HTTP path.
