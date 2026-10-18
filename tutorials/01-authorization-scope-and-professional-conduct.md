# 01. Plan an authorized, reviewable assessment

[Index](README.md) | [Complete source curriculum](curriculum/01-authorization-scope-and-professional-conduct.md) | [Original roadmap](../roadmaps/01-authorization-scope-and-professional-conduct.md)

## Prerequisites and lesson outcome

Use a text editor and your own fictional lab inventory. This lesson requires no network activity. You will produce an engagement packet that answers what may be tested, who authorized it, how work stops, how evidence is protected, and how changes are restored. Examples use fictional people, `.test` names, and synthetic records; they are planning exercises rather than legal advice for a real engagement.

Authorization is a property of an agreement and the parties controlling the assets. A working connection proves reachability. It does not prove permission. Equally, permission for one application does not automatically include every service that application uses. Good planning converts broad intentions into operating rules another tester can follow without guessing.

## 1. Choose the assessment type from the question

Start with “Can customer A read customer B's invoices in our local training application?” The asset is invoice content, the actor is an ordinary customer, the action is read, and the intended rule is owner-only access. Success means testing that boundary with synthetic accounts, recording the result, and verifying any repair. It does not automatically include availability testing or employee impersonation.

| Activity | Main question | Suitable evidence |
| --- | --- | --- |
| Vulnerability scanning | Which automated checks report possible weaknesses? | Tool/version, configuration, scoped results; candidates need validation |
| Vulnerability assessment | Which weaknesses are credible and important here? | Validation, affected assets, context, remediation priorities |
| Penetration testing | What specific unauthorized outcomes can be demonstrated within scope? | Minimal reproducible proof and limits of impact |
| Adversary emulation | How does the environment respond to selected known adversary behaviors? | Behavior mapping and observed controls |
| Red teaming | Can an authorized objective be reached despite defenses? | Objective, path, defensive visibility, bounded operations |
| Purple teaming | How can testers and defenders improve a control together? | Joint test, telemetry, tuning, rerun |
| Configuration review | Do settings enforce the intended baseline? | Effective configuration, exceptions, runtime verification |
| Compliance audit | Are specified requirements met with acceptable evidence? | Requirement-to-evidence mapping and exceptions |

Black-box access approximates an outside perspective with little internal information. Gray-box access adds selected accounts or architecture. White-box access includes source and configuration. None is inherently “complete”: source review can identify a missed check, while runtime testing shows what the deployed system actually does. Write two plans for the invoice question: one using customer accounts and one also tracing source routes. State the uncertainty each leaves behind.

## 2. Map ownership and dependency boundaries

Draw the request path:

```text
Lab browser → local invoice application → synthetic database
                         ├→ lab identity fixture
                         └→ mocked payment response
Excluded: actual payment service, personal email, home router
```

Give every component an owner, operational contact, and authorization reference. Domain control, hosting control, account administration, and permission to use a service are different powers. A company-controlled hostname may point to shared infrastructure. A wildcard scope can include outsourced subdomains unless the agreement resolves them. A customer's data access does not imply authority over another tenant.

Use four dependency states: configuration inspection allowed; ordinary documented use allowed; active security testing allowed; observations only. A payment dependency might permit inspecting the application's integration configuration while prohibiting active requests to the payment provider. Replace the live dependency with a mock for your lab exercise.

For an actual program, read the current vulnerability disclosure or bounty policy directly: exact eligible assets, exclusions, allowed techniques, rate limits, report destination, eligibility, duplicates, confidentiality, publication terms, and safe-harbor wording. Keep its date and version. A legal requirement, contract obligation, platform condition, and organizational preference can all affect work but come from different authorities. Have the responsible owner or qualified adviser resolve real jurisdiction and contract ambiguities.

## 3. Write measurable rules of engagement

This fictional agreement is deliberately concrete:

```text
Objective: assess invoice ownership checks on lab invoice application v1.
Owner/authorizer: Mira, fictional lab owner; approval LAB-001.
Included: invoice.test mapped locally; application on loopback TCP 8000;
          synthetic database; accounts customer-a and customer-b.
Excluded: public Internet, external payment/email/identity providers,
          personal host folders, home/office networks, other applications.
Window: example session 18:00–19:00 Asia/Kolkata (UTC+05:30).
Source: lab browser profile and named local command-line client.
Methods: manual reads/updates of synthetic invoices; source/config review.
Limits: one request at a time; maximum one request per second;
        no load test, guessing campaign, persistence, or destructive actions.
Stop signal: unexpected real data, ownership mismatch, or degradation.
Stop authority/contact: Mira through the agreed local exercise channel.
Resume: owner confirms cause and scope in the change record.
Recovery: lab operator restores seeded data and the baseline snapshot.
Evidence: encrypted private lab storage; authorizer/tester access only.
Retention: fictional exercise artifacts removed after the agreed review.
Delivery: private report; publication needs separate recorded permission.
Retest: same synthetic cases in the same window or an agreed new window.
```

These numbers are example constraints, not universally safe rates. A fragile application can fail at very low rates; actual limits follow the owner's environment. Also specify request size, concurrent sessions, account attempts, resource consumption, source addresses, tenant/project IDs, environment names, and time zone where relevant. “Low impact” alone cannot guide an operator.

Create explicit gates for disruptive tests, credential testing, social engineering, physical entry, persistence simulation, and movement beyond an initial host when those activities fall outside the agreed scope. A new technical hypothesis does not amend the agreement. Record who may approve changes and how the updated scope reaches every participant.

## 4. Rehearse stop and escalation decisions

Stopping is an operational procedure: cease new actions, allow safe cancellation of current work, preserve the minimum relevant state, notify the named contact, and wait for the agreed resumption condition. Do not “verify” an unexpected sensitive record by downloading more records.

| Observation | Immediate response | Resume evidence |
| --- | --- | --- |
| Certificate mentions an unfamiliar host | Record its origin; classify ownership without testing it | Written inclusion or exclusion |
| Local request unexpectedly reaches a vendor | Stop that path and inspect integration configuration | Approved mock or explicitly authorized dependency |
| Real personal data appears | Stop collection and restrict the minimal artifact | Owner's handling decision and corrected dataset |
| Application becomes slow | Stop test traffic, record timeline and rate | Operational recovery and owner approval to resume |
| A live incident is suspected | Follow incident contact path; preserve relevant evidence | Incident owner's direction |
| A critical boundary failure is proven | Notify early using minimum proof | Agreed next steps, without exaggerating impact |
| Fix changes the target environment | Check retest authorization and new dependencies | Change reference and scoped regression plan |
| Provider flags traffic | Refer the owner to the applicable current provider conditions | Resolved provider/owner response |

Cloud conditions are additional constraints, even when the application owner agrees to testing. Read the applicable provider policy for the exact service and account before a real assessment. This tutorial performs no cloud deployment and does not infer any standing provider permission.

## 5. Protect evidence throughout its lifecycle

Classify information before collecting it. General study notes and synthetic data differ from internal configurations, access tokens, personal records, and restricted business documents. Choose collection, storage, transmission, access, retention, deletion, and reporting rules for each class. Encrypt sensitive evidence where required and ensure recovery keys do not live only beside the encrypted copy.

Common hidden copies include terminal history, clipboard managers, screenshots, browser sync, proxy projects, debug traces, packet captures, crash dumps, cloud exports, repository commits, and report attachments. Sanitizing the report body leaves those copies unchanged. Inventory them so cleanup has a defined scope.

Practice with this synthetic observation:

```text
Original: user=alex@example.test token=DEMO-ONLY-ABC invoice=inv-204
Report: actor=CUSTOMER-A token=[REDACTED] invoice=OBJECT-02
Private correlation map: CUSTOMER-A → synthetic account alex;
                         OBJECT-02 → inv-204
```

Keep actor/record relationships because they explain the authorization failure. Remove the token because its exact bytes are unnecessary to demonstrate the decision. Preserve raw and redacted versions as distinct artifacts with identifiers and hashes where appropriate. A hash helps identify an artifact; it does not remove sensitive content or establish the truth of an interpretation.

Your artifact register should include ID, description, sensitivity, source/time, storage location, permitted readers, redacted counterpart, retention deadline, and deletion result. For the fictional exercise, use only synthetic identifiers. Do not fill examples with real credentials to make them look realistic.

## 6. Communicate what is established

Write an initial notification containing affected asset, observed boundary failure, immediate impact, confidence, minimal evidence reference, and a proposed containment step. For example:

> In the local invoice fixture, customer A received the contents of customer B's synthetic invoice through the single-record API. The ownership rule was not enforced for that route. We stopped after this one record; bulk access and other routes are untested. Evidence LAB-E03 contains the sanitized request and response. Restrict the route pending a server-side ownership fix, then retest both customers.

A follow-up adds exact prerequisites, source versions, reproducible steps, expected/observed behavior, remediation, and retest cases. Do not claim access to all production tenants when you tested one lab record. For a newly discovered product vulnerability, coordinate confidentially with the vendor through its current channel, provide affected versions and a minimal reproduction, and document disclosure decisions. Publication permission for a client report is separate from permission to conduct testing.

## 7. Keep cleanup and retesting accountable

Record temporary users, files, service settings, scheduled tasks, access rules, certificates, and proxy configuration at creation time. For each change, save its owner, purpose, prior state, removal method, and verification. Cleanup fails when the tester remembers the visible exploit but forgets the helper account or browser trust change.

Retest the originally failing case, an allowed case, another user's denied case, and relevant alternate routes. Check state before and after. Confirm synthetic data and configuration return to the intended baseline, not merely that the application starts. Deliver unresolved limitations with the report.

## Exercises and answer guidance

Classify these actions against LAB-001: request customer A's synthetic invoice; test the real payment provider; increase concurrency to 100; inspect authorized local source; publish the final screenshots. The first and fourth are within the example methods. The provider test and concurrency increase are outside scope. Publication requires its own recorded permission. A technically feasible action can still be outside the agreement.

Ask a reviewer to invent three ambiguities: a second hostname, an unexpected external redirect, and a fix moved to another environment. Your packet passes when the reviewer can identify the authorizer, permitted actions, stop mechanism, artifact destination, cleanup owner, and resumption conditions without unrecorded assumptions. Fix ambiguous wording and repeat the scenario review before any real test.
