# 13. Secure code review and software delivery

[All topic roadmaps](README.md) | [Original master roadmap](../../ETHICAL_HACKING_ROADMAP.md#13-secure-code-review-and-software-delivery)

<!-- TOPIC-TOC:START -->

## Contents

- [13.1 Read code as a system](#131-read-code-as-a-system)
- [13.2 Verification tools and secure changes](#132-verification-tools-and-secure-changes)
- [13.3 Dependencies, builds, and delivery infrastructure](#133-dependencies-builds-and-delivery-infrastructure)
- [13.4 Delivery capstone and exit criteria](#134-delivery-capstone-and-exit-criteria)
- [Expanded review and delivery learning path](#expanded-review-and-delivery-learning-path)
  - [Module 1: orient yourself before searching for defects](#module-1-orient-yourself-before-searching-for-defects)
  - [Module 2: review data flow and control flow together](#module-2-review-data-flow-and-control-flow-together)
  - [Module 3: learn stack-specific hazards without memorizing payloads](#module-3-learn-stack-specific-hazards-without-memorizing-payloads)
  - [Module 4: use analysis tools as evidence collectors](#module-4-use-analysis-tools-as-evidence-collectors)
- [Software delivery as a chain of trust](#software-delivery-as-a-chain-of-trust)
- [Three scenario labs](#three-scenario-labs)
  - [Lab A: authorization present in HTTP but absent in the worker](#lab-a-authorization-present-in-http-but-absent-in-the-worker)
  - [Lab B: an analysis warning with uncertain reachability](#lab-b-an-analysis-warning-with-uncertain-reachability)
  - [Lab C: artifact promotion and permissions](#lab-c-artifact-promotion-and-permissions)
- [Troubleshooting, review quality, and pass criteria](#troubleshooting-review-quality-and-pass-criteria)

<!-- TOPIC-TOC:END -->



**Priority:** Core: read a small application's data flows, identify unsafe operations, understand dependencies/secrets, and verify fixes. Track depth: complex codebases, advanced fuzzing, full pipeline assessment, build provenance, and release-integrity engineering.

**Prerequisites:** proficiency in one language/framework, debugging, tests, Git, dependency management, basic build tooling, and Sections 11–12. Learn one stack deeply, then transfer the principles to a second stack with different parsing and type behavior.

## 13.1 Read code as a system

- [ ] Start with architecture, assets, trust boundaries, entry points, authentication middleware, authorization policies, data models, external integrations, and deployment configuration.
- [ ] Trace sources → transformations → validation → sensitive sinks. Sources include HTTP, files, messages, database records, environment settings, and partner data; stored data can remain untrusted.
- [ ] Recognize sinks: queries, process execution, template rendering, deserialization, filesystem access, network fetches, redirects, logging, cryptography, authorization decisions, and serialization to clients.
- [ ] Distinguish validation, escaping, encoding, canonicalization, sanitization, parameterization, and authorization. Check their order, context, completeness, and whether alternate paths bypass them.
- [ ] Follow control flow through middleware, decorators, callbacks, exceptions, feature flags, workers, retries, and administrative jobs. Review denial behavior and partial side effects.
- [ ] Inspect business invariants and transactional boundaries, permission changes, identifier reuse, stale caches, and object ownership. Many important defects are absent from pattern-based scanner rules.
- [ ] Review crypto usage: approved libraries, secure randomness, password hashing, authenticated encryption, nonce handling, key separation/rotation, certificate verification, and error handling. Avoid custom cryptographic designs.
- [ ] Review language hazards: dynamic evaluation, coercion, unsafe reflection, unsafe native interfaces, integer boundaries, memory ownership, concurrency, filesystem races, and framework-specific insecure defaults.

**Lab:** Review a small codebase without scanning first. Draw three complete data flows, write explicit security hypotheses, inspect tests and configuration, and then compare your findings with static analysis. For every warning, document reachability, attacker control, mitigating checks, and actual impact.

## 13.2 Verification tools and secure changes

- [ ] Understand SAST, software composition analysis, secret scanning, DAST, interactive analysis, fuzzing, and manual review: inputs required, classes detected, false positives, blind spots, and operational cost.
- [ ] Learn dependency reachability and advisory interpretation; distinguish an installed vulnerable package from a reachable vulnerable behavior while still tracking required updates.
- [ ] Practice unit, integration, property-based, contract, and end-to-end security tests. Use positive cases so a repair cannot pass simply by disabling the feature.
- [ ] Use bounded fuzzing against a local parser or handler with time/memory limits, reproducible seeds, crash minimization, and triage. Fix the underlying invariant rather than one discovered input.
- [ ] Add review checks to pull requests, define justified severity thresholds, document exceptions with owners/expiry, and keep suppression narrowly scoped.
- [ ] Check patch completeness across alternate routes, encodings, types, API versions, workers, tenant contexts, and duplicated implementations.

The [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) provides focused guidance for implementation topics such as authorization, secure code review, secret management, and CI/CD security. Use the relevant language/framework documentation to confirm the exact behavior of your chosen APIs.

## 13.3 Dependencies, builds, and delivery infrastructure

- [ ] Dependency graph: direct/transitive, production/development/build dependencies, lockfiles, integrity hashes, private registries, namespace confusion, abandoned packages, lifecycle scripts, and update ownership.
- [ ] SBOM: generate a machine-readable inventory, record versions/components/relationships, connect it to the built artifact, and use it to answer whether an advisory affects a released build. Learn SPDX/CycloneDX concepts and VEX limitations.
- [ ] Source controls: protected branches, review requirements, identity protection, least-privilege tokens, repository access reviews, release-tag integrity, and auditability.
- [ ] CI/CD trust: untrusted pull requests, workflow permissions, reusable actions, pinned dependencies, third-party integrations, runner isolation, workspace cleanup, cache/artifact trust, environment approvals, and fork behavior.
- [ ] Secrets: creation, storage, injection, scope, rotation, revocation, redaction, and incident response. Prefer short-lived workload credentials where supported; removing a committed secret does not revoke it.
- [ ] Build integrity: isolated build environments, immutable inputs, reproducibility concepts, provenance, artifact digests, signing, verification policy, trusted builders, and protection of signing identities. A valid signature must still be connected to an authorized producer and expected build.
- [ ] Use the [SLSA specification](https://slsa.dev/spec/) to study supply-chain integrity and provenance requirements; identify which evidence a consumer actually verifies before trusting an artifact.
- [ ] Infrastructure as code: versioned configuration, plan review, module/provider trust, remote-state confidentiality, policy checks, least-privilege deployment credentials, environment separation, and drift detection.
- [ ] Packaging and release: minimal runtime images, non-root execution where appropriate, patch cadence, artifact promotion, migration safety, staged rollout, rollback, and retention of release evidence.
- [ ] Post-release loop: telemetry, vulnerability intake, dependency advisories, patch verification, emergency access, key compromise response, and feedback into design requirements.

## 13.4 Delivery capstone and exit criteria

Create a small repository containing the lab application, tests, dependency lockfile, deployment configuration, and CI workflow. Seed a harmless mock secret and an intentionally insecure local code path; use dedicated test fixtures so no genuine credential or vulnerable service is published.

**Root cause → verification → repair → regression:** trace the insecure source-to-sink flow; demonstrate its harmless local effect; replace the unsafe behavior; and prove both rejection and legitimate use. For the mock secret, verify detection, remove it, and document the revocation process using a disposable test credential.

**Exit evidence:** two manual code reviews; four confirmed and fixed defects; ten meaningful security assertions; a triaged scanner report; an SBOM tied to a build digest; verified build provenance/signature where your tooling supports them; a least-privilege CI workflow; and a tested rollback procedure. Be able to explain which security properties each artifact demonstrates and what remains unproven.

## Expanded review and delivery learning path

Start with a single small application and one build pipeline. Core competence is understanding its trust boundaries, reviewing reachable code, and verifying durable fixes. Advanced compiler analysis, large-scale fuzzing, organization-wide build provenance, and complex release infrastructure are later specializations. Preserve the difference between what you personally reviewed and what a tool merely reported.

### Module 1: orient yourself before searching for defects

- [ ] Identify supported entry points: HTTP routes, CLI commands, uploaded files, message consumers, scheduled tasks, administrative jobs, and library interfaces used by other applications.
- [ ] Find configuration loading, dependency injection, authentication middleware, authorization policies, error handlers, serializers, storage clients, and transaction boundaries.
- [ ] Build a call path for one ordinary user action and one privileged action. Include asynchronous work, retries, and feature flags that alter execution.
- [ ] Read the relevant data model: ownership, tenant identifiers, unique constraints, lifecycle states, and fields that must be server-controlled.
- [ ] Identify execution identities for the web process, worker, deployment job, and database connection. Code safety depends partly on the privileges available at its sinks.
- [ ] Record build/run commands, test fixtures, dependency versions, and configuration assumptions so the reviewed code can be matched to a runnable artifact.

**Deliverable:** a compact review map and three security invariants, such as 'a tenant cannot select another tenant's storage key' or 'a worker cannot write outside its assigned output directory.'

### Module 2: review data flow and control flow together

For each selected path, track the data source, transformations, validation, authorization, sensitive operation, serialization, and logging. Then ask how exceptions, retries, cancellation, partial failure, or concurrency change that sequence.

- [ ] Check whether a value remains untrusted after being stored in a database, cache, or queue. Persistence is not validation.
- [ ] Distinguish validating a value from proving the caller is allowed to use it. A valid object identifier may still refer to another tenant's object.
- [ ] Verify normalization order: decoding and canonicalization must not change the meaning after the security check that relies on that meaning.
- [ ] Inspect helper functions instead of trusting names such as `safe`, `sanitize`, or `authorize`. Read their actual guarantees, failure behavior, and caller expectations.
- [ ] Follow indirect uses through wrappers, callbacks, template helpers, reflection, and framework hooks. Identify which behavior is provided by the framework and which is application-specific.
- [ ] Review denial and exception paths for partial writes, background messages, unsafe fallback behavior, and missing transaction rollback.
- [ ] Inspect concurrency around balances, inventory, single-use tokens, role changes, file creation, and ownership transfers. Write the invariant that must hold under overlapping operations.

**Deliverable:** four source-to-sink traces with code references, a reachability explanation, a proposed failure condition, and a minimal local verification plan.

### Module 3: learn stack-specific hazards without memorizing payloads

| Area | Questions for the reviewer | Useful local verification |
| --- | --- | --- |
| Queries and interpreters | Are values kept separate from executable structure? | Synthetic inputs preserve the intended operation |
| Files and processes | Who controls path components, arguments, environment, and working directory? | Harmless sentinel files and a stub executable reveal actual boundaries |
| Serialization | Can input select types or output expose internal fields? | Schema and response-contract assertions |
| Language types | How do missing/null values, coercion, overflows, and implicit conversions behave? | Boundary-value tests against the real runtime |
| Memory and native interfaces | Who owns buffers and what lengths/lifetimes are trusted? | Bounded sanitizer-assisted tests in a disposable build |
| Concurrency | What protects the invariant across interleavings and retries? | Small deterministic competing-operation fixtures |
| Cryptography | Are vetted APIs configured for the intended purpose with correct key/nonce handling? | Library-level assertions and rotation/failure-path tests |
| Error handling | Can failure disclose data, bypass checks, or leave partial effects? | Simulated dependency errors and state inspection |

Study your chosen framework's documented defaults and extension points. A safe framework API can be undermined by an escape hatch, custom serializer, raw query, disabled check, or privileged deployment identity.

### Module 4: use analysis tools as evidence collectors

- [ ] Run static analysis after your manual baseline. Compare the warnings with actual reachable flows and record why each is confirmed, dismissed, or unresolved.
- [ ] For dependency alerts, identify the dependency path, runtime/build usage, affected functionality, advisory prerequisites, deployed artifact, and update ownership.
- [ ] For secret scanning, use clearly fictional markers or dedicated disposable test credentials. Learn how findings are reported and how deletion differs from revocation.
- [ ] Add property-based tests when an invariant covers many input forms. Use generated values that explore structure and boundaries without unbounded resource use.
- [ ] For a local fuzz target, define the accepted input format, seed corpus, time/memory budget, crash collection, minimization, and reset procedure. A minimized failure should become an explanatory regression test.
- [ ] Keep tool suppression narrow, justified, reviewable, and temporary where appropriate. Capture the reason and owner rather than silencing a whole category.

**Deliverable:** a short tool-comparison note showing one useful detection, one false positive, and one manually identified issue the selected tool missed.

## Software delivery as a chain of trust

Trace source commit → dependency resolution → build execution → artifact storage → release approval → deployment → runtime configuration. For each transition, identify who can write the input, who executes it, which credentials are available, and how the next stage verifies it.

- [ ] Separate untrusted contribution checks from privileged release work. Review event triggers, branch/ref assumptions, reusable workflows, parameter handling, and which contexts receive secrets.
- [ ] Inspect runner isolation, persistent workspaces, caches, downloaded artifacts, tool installation, and cleanup. Treat a reused build input as untrusted until its origin and integrity requirements are satisfied.
- [ ] Review token permissions per job. A test job should not inherit publication or deployment rights simply because a later release job needs them.
- [ ] Pin dependencies in a way appropriate to the ecosystem and document the update process. A lockfile supports reproducibility but does not establish that the selected components are trustworthy.
- [ ] Tie the SBOM and provenance to the exact built artifact digest. Check the producer identity, expected source, build workflow, and verification policy, not just the presence of a signature file.
- [ ] Separate build-time and runtime secrets. Check environment variables, logs, caches, images, archives, and debugging artifacts for unintended retention.
- [ ] Review infrastructure state and deployment plans as sensitive inputs. Distinguish a proposed change from the actual applied configuration and track drift.
- [ ] Practice rollback, credential compromise response, and emergency dependency replacement. Record which evidence is needed to identify affected releases quickly.

Use the SLSA reference above to deepen provenance study, while keeping the exercise tied to the claims your own build system can actually demonstrate.

## Three scenario labs

### Lab A: authorization present in HTTP but absent in the worker

**Setup:** an owned application enqueues a report for a fictional tenant. **Action:** trace the request through policy checks and message processing, then change the user's role before execution. **Expected result:** the worker follows the documented authorization policy and produces only permitted data. **Evidence:** call graph, message schema, policy decision, job state, and test result. **Control:** an authorized job completes. **Fix:** preserve trusted context and enforce the selected policy at execution/delivery boundaries; add a regression test for the lifecycle change.

### Lab B: an analysis warning with uncertain reachability

**Setup:** a local repository containing one reachable unsafe operation and one unused training helper. **Action:** manually trace both, run analysis, and compare results. **Expected result:** distinguish a demonstrated application issue from an uncalled helper while still considering whether the helper should be removed or hardened. **Evidence:** entry-point map, call paths, tests, and scanner output. **Control:** a normal feature test remains successful. **Fix:** repair the reachable invariant and document the disposition of unused code without overstating impact.

### Lab C: artifact promotion and permissions

**Setup:** a local or permitted test pipeline that creates a harmless package, an SBOM, and a digest manifest. **Action:** inspect job privileges, alter a copy of the artifact, and verify the promotion check rejects the mismatch. **Expected result:** only the intended build artifact is promoted and ordinary test jobs lack release authority. **Evidence:** workflow, permissions, digest comparison, verification result, and release record. **Control:** the original authorized artifact promotes successfully. **Fix:** enforce artifact identity and scoped credentials, then test rollback to a known approved artifact.

## Troubleshooting, review quality, and pass criteria

If a fix breaks valid requests, revisit the invariant and API contract instead of broadly disabling validation. If a static warning disappears, confirm the unsafe behavior was actually removed rather than merely hidden from the analyzer. If a dependency remains in an SBOM after an update, inspect transitive paths and the built image rather than relying on the source lockfile alone. If provenance verification succeeds for the wrong producer, correct the trust policy.

Finish with two reviews performed from a clean checkout, four repaired defects with meaningful positive/negative tests, an annotated scanner report, a build-linked component inventory, and a release/rollback exercise. Another learner should be able to connect each claim to code, configuration, test evidence, and a particular artifact. Keep advanced fuzzing or provenance work as an explicitly chosen extension rather than allowing it to block completion of the core review track.