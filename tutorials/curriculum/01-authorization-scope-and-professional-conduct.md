# 01. Authorization, scope, and professional conduct

[All topic roadmaps](README.md) | [Original master roadmap](../../ETHICAL_HACKING_ROADMAP.md#01-authorization-scope-and-professional-conduct)

<!-- TOPIC-TOC:START -->

## Contents

- [Understand the boundaries](#understand-the-boundaries)
- [Produce rules of engagement](#produce-rules-of-engagement)
- [Lab and completion check](#lab-and-completion-check)
- [Expanded learning sequence: plan an assessment that can actually run](#expanded-learning-sequence-plan-an-assessment-that-can-actually-run)
  - [Module 1: Translate a request into an objective](#module-1-translate-a-request-into-an-objective)
  - [Module 2: Establish who controls every boundary](#module-2-establish-who-controls-every-boundary)
  - [Module 3: Make operating conditions measurable](#module-3-make-operating-conditions-measurable)
  - [Module 4: Protect assessment data throughout its lifecycle](#module-4-protect-assessment-data-throughout-its-lifecycle)
  - [Module 5: Communicate findings and disclosure responsibly](#module-5-communicate-findings-and-disclosure-responsibly)
- [Scenario decision table](#scenario-decision-table)
- [Capstone: a complete engagement packet](#capstone-a-complete-engagement-packet)

<!-- TOPIC-TOC:END -->



**Priority:** Core, before any active testing.

## Understand the boundaries

- [ ] Distinguish vulnerability scanning, vulnerability assessment, penetration testing, adversary emulation, red teaming, purple teaming, configuration review, and compliance auditing. Each has a different objective and evidence standard.
- [ ] Understand ownership, written authorization, acceptable-use conditions, data sensitivity, confidentiality, and coordinated disclosure. An accessible system or a public IP address is not permission to test.
- [ ] Identify the person who can authorize the assessment and all relevant asset owners. A customer's permission does not automatically cover its hosting provider, payment processor, identity provider, employees' personal devices, or another tenant.
- [ ] Learn to read a bug bounty or vulnerability disclosure policy: exact asset list, exclusions, allowed techniques, rate limits, disclosure rules, report channel, and any safe-harbor wording. Policies are specific to the program.
- [ ] Learn the difference between a legal requirement, a contract requirement, a platform policy, and an organizational preference. For an actual engagement, have the responsible owner or qualified adviser resolve jurisdiction and contract questions.

## Produce rules of engagement

- [ ] Record target domains, IP ranges, applications, accounts, tenant/project IDs, environments, and explicitly excluded dependencies.
- [ ] Set objectives, success conditions, dates, testing windows with time zones, source systems, allowed methods, maximum rates, and resource limits.
- [ ] Define approval gates for disruptive tests, credential testing, social engineering, physical access, persistence simulations, and any movement beyond the initial host. Separate authorization is necessary when these are outside the agreed assessment.
- [ ] Specify test identities, synthetic data, backup/recovery readiness, change ownership, escalation contacts, and an immediate stop mechanism.
- [ ] Agree how to handle an accidental discovery outside scope, real sensitive data, a live incident, service degradation, or a potentially critical finding.
- [ ] Define evidence encryption, access, retention, deletion, report delivery, and permission for any later public write-up.
- [ ] Establish cleanup and retesting responsibilities. Log every temporary account, configuration change, file, scheduled task, and access rule created during testing.

Cloud providers publish additional testing conditions. Review the current [AWS penetration testing policy](https://aws.amazon.com/security/penetration-testing/) or [Microsoft Azure testing guidance](https://learn.microsoft.com/en-us/azure/security/fundamentals/pen-testing) when those platforms are involved. Recheck the rules before each engagement; do not treat a cached summary as authorization.

## Lab and completion check

Write a one-page assessment agreement for a fictional company using your own lab assets. Include an in-scope host, an excluded host, a maintenance window, a stop contact, a data-handling rule, and a restoration plan. Given five example actions, explain which are allowed, disallowed, or require clarification.

**Ready to move on:** You can determine whether an action is in scope before running it, stop safely, and explain how evidence will be protected.

## Expanded learning sequence: plan an assessment that can actually run

### Module 1: Translate a request into an objective

Start with a fictional request: “Check whether ordinary customers can access another customer's invoices.” Identify the protected asset, the relevant users, the environments, and the expected boundary. Then distinguish this objective from a complete application assessment, a load test, or a red-team exercise. A broad phrase such as test everything must be converted into specific coverage and operating conditions before execution.

Prepare a discovery questionnaire covering business purpose, critical workflows, data classes, application owners, dependencies, maintenance constraints, recent changes, and known operational sensitivities. Learn how black-box, gray-box, and white-box access changes what the assessment can establish. A source-assisted review may explain root causes that a short external test cannot resolve.

**Exercise:** Produce two test plans for the same local application: one with only ordinary-user access and another with source code and administrator-provided configuration. Identify findings each perspective might miss and the additional evidence each can obtain.

### Module 2: Establish who controls every boundary

Draw an ownership map covering the application, domain, hosting account, tenant, identity provider, email provider, payment integration, and employee devices. Record the party authorizing each included asset. Learn to distinguish legal ownership, operational responsibility, hosting-provider authority, and a customer's right to use a service.

A wildcard domain can still contain outsourced services. A company-controlled hostname can resolve to shared infrastructure. An application may initiate requests to a third party even when your test URL is in scope. For each dependency, state whether you may inspect configuration, use ordinary documented functionality, conduct active security tests, or only record observations for the owner.

**Exercise:** Give your fictional application five dependencies, including one excluded SaaS system. Trace an example request through them and mark exactly where the permitted assessment ends.

### Module 3: Make operating conditions measurable

Replace vague conditions with observable limits. “Low impact” should become agreed limits for request rate, concurrency, file size, account attempts, cloud resources, and timing where relevant. “Stop if something breaks” needs a named signal, a communication channel, a person authorized to pause work, and a restoration owner.

Define source addresses and accounts, test windows with time zones, permitted environments, the handling of emergency changes, and how scope changes are recorded. Establish whether defenders know the test is occurring and who can distinguish a simulation from a real incident. Do not infer that a technical objective permits a physical or human assessment.

**Exercise:** Write three operating constraints for your local application, then simulate a rate-limit warning, unexpected sensitive record, and target ownership mismatch. Describe your immediate action, evidence retained, notification path, and condition for resuming.

### Module 4: Protect assessment data throughout its lifecycle

Classify artifacts before collecting them: general notes, synthetic evidence, internal configuration, authentication material, personal data, and highly restricted business records. Select storage, access, transmission, retention, and deletion methods according to the engagement's actual requirements. Keep raw and redacted versions distinguishable and avoid storing evidence in tool logs or external services by accident.

Learn how screenshots, proxy projects, packet captures, terminal histories, debug traces, cloud exports, and repository history can preserve secrets. A report can be sanitized while its attachment remains sensitive. Use synthetic examples to practice redaction without removing the facts necessary for reproduction.

**Exercise:** Create a synthetic finding containing a token-like string, fictional customer email, and invoice ID. Produce a useful sanitized report and an artifact inventory. Explain which fields you retained, which you replaced, and how an authorized reviewer can correlate the records.

### Module 5: Communicate findings and disclosure responsibly

Agree how urgent findings are escalated, how ordinary findings are reviewed, and who receives reports. A critical finding may require early notification before the final report. Record what you established and avoid expanding testing solely to make the finding look more severe.

For a public vulnerability-disclosure program, read the current policy directly. Learn eligibility, scope, report format, excluded activity, handling of duplicates, and publication rules. For a previously unknown product vulnerability, study confidential vendor contact, a reproducible report, affected versions, coordination, and unresolved disagreement. Disclosure arrangements and applicable obligations vary; have the responsible owner resolve real contractual or jurisdiction-specific questions.

**Exercise:** Write a concise notification for a fictional cross-tenant issue, then a follow-up containing reproduction and mitigation information. Mark unverified impact claims and remove them or label their assumptions.

## Scenario decision table

| Situation in a planned assessment | What to determine before further action | Useful record |
| --- | --- | --- |
| A new hostname appears in a certificate | Ownership, environment, and whether scope includes it. | Discovery source, timestamp, scope decision. |
| An endpoint calls an excluded vendor | Which actions reach that vendor and which tests remain within scope. | Dependency boundary and permitted alternatives. |
| A request returns unexpected personal data | Minimum evidence needed and the agreed stop/escalation procedure. | Redacted observation and handling decision. |
| A service becomes slow | Whether testing contributed and which stop threshold applies. | Timeline, test rate, operational notification. |
| A fix changes the environment | Whether retesting remains authorized and which regression paths matter. | Change reference, retest scope, result. |
| A provider flags traffic | Current provider policy and the authorized owner's response process. | Authorization reference and scoped activity log. |

## Capstone: a complete engagement packet

Create a fictional assessment packet containing an objective, asset/ownership map, rules of engagement, synthetic accounts, data-handling plan, escalation contacts, change log, test cases, cleanup checklist, and reporting schedule. Give it to a reviewer who invents three scope ambiguities. Resolve each without silently expanding authority.

**Pass:** A second tester can determine what is permitted, what requires a scope change, how to stop, where evidence belongs, and who owns restoration. Your packet should be usable without relying on unrecorded verbal assumptions.

Use [NIST SP 800-115](https://csrc.nist.gov/pubs/sp/800/115/final) as a historical reference for assessment planning and process. Pair it with current platform policies and the actual engagement agreement; its publication date and scope make it unsuitable as a universal current platform rulebook.
