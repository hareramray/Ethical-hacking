# Queued-job authorization: runnable lesson

This lesson follows a fictional export through submission, worker execution, and delivery. It uses real rows in a disposable SQLite store to show how an authorization grant can become stale while work waits, and why creating an artifact does not automatically authorize its download.

Start the [Vue + Django lab](README.md) from the repository root:

```powershell
python labs/browser_security/run_lab.py
```

Open **http://127.0.0.1:8766/**, select **Queued-job authorization**, choose a fixture, and click **Compare export lifecycle**.

## Policy and fixtures

The explicit policy for this application is: **current export permission is required at submission, execution, and download; the relevant resource or artifact must belong to the actor in the actor's current tenant**. Other applications may deliberately define different execution-time policies. Decide and document those semantics before testing; an old grant is not automatically valid under this lesson's chosen policy.

The submitting identity is the server-established fixture `user-ada` in `tenant-blue`. The browser cannot choose a principal, tenant, job, permission, or payload. This is a teaching identity, not a login session. The only exported content is `FICTIONAL-ADA-BLUE-EXPORT`.

| Fixture | Vulnerable behavior | Fixed behavior |
| --- | --- | --- |
| `normal` | Enqueues, creates one artifact, and delivers the marker | Performs the same permitted workflow |
| `revoke-before-worker` | Trusts the saved enqueue grant and creates/delivers the artifact after revocation | Rereads current permission; marks the job denied and creates no artifact |
| `revoke-before-download` | Delivers an already-created artifact after revocation | Preserves the created artifact but denies delivery |
| `peer-download` | Delivers Ada's artifact to Bea by job ID | Denies a different owner, even with valid export permission in the same tenant |
| `cross-tenant-download` | Delivers the Blue artifact to the same user ID in Amber | Denies a different tenant, even with a matching user ID and valid export permission |
| `initially-denied` | Denies before enqueueing | Also denies before enqueueing; neither path creates a job or artifact |

Every mode and comparison receives a new database. The queue is a stored `jobs` table drained synchronously within the comparison request. The worker function loads a queued job, reads its resource, inserts an artifact when permitted, and changes the job state. There is no background broker, external worker, filesystem export, or durable queue left after the response.

## Observe the boundary

Start with `normal` and confirm one completed job, one artifact, and a delivered marker in both panels. The ordered lifecycle records the actual enqueue, worker, and download decisions.

Run `revoke-before-worker`. Both jobs were legitimately submitted and contain `granted_at_enqueue: 1`. The membership row then changes. The vulnerable worker uses the old grant; the fixed worker reads the updated membership and stops before an artifact is inserted. A saved grant is evidence of a past decision, not current authority.

Run `revoke-before-download`. Here the worker succeeds while permission is valid. Both panels still show a completed job and a stored artifact after revocation. The fixed download nevertheless returns no marker. **Artifact existence and download permission are separate observations.** Metadata is shown for teaching; the fixed denied result does not return the artifact payload in its artifact listing.

Use the two foreign-requester fixtures to separate owner and tenant checks from the permission flag. The requesting membership has export permission in both cases. Checking only that flag would still leak the other principal's or tenant's artifact. Finally repeat `normal` to verify that allowed work remains functional.

The comparison API intentionally returns both modes' teaching evidence. Its HTTP response is not an application export API or a production authorization boundary for real user data.

## The repair

The [backend](backend/securitylab/queue_lab.py) performs these decisions against stored state:

1. Submission checks current permission and resource owner/tenant before inserting any job. Both paths enforce this initial check.
2. The fixed worker loads the submitting principal and tenant from the job, then reads current membership and current resource ownership. It inserts no artifact if either check fails.
3. The fixed download separately checks the requesting principal's current permission and the stored artifact owner/tenant before returning its marker.
4. Each stage logs its decision. A rejected submission leaves no job; a rejected execution leaves no artifact; a rejected download leaves the existing artifact undelivered.

The vulnerable worker deliberately trusts `granted_at_enqueue`, and the vulnerable download deliberately loads by job ID alone. Neither behavior is repaired by making job IDs less predictable. A completed or denied job cannot be processed a second time in this fixture store.

[OWASP's Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) recommends deny-by-default behavior, authorization checks on every request, checks at the appropriate application boundary, and tests for those decisions. This lesson applies those principles to a workflow whose business policy requires current permission at execution and delivery.

## API and scope

`POST /api/queue/compare/` accepts JSON containing exactly `{"fixture":"normal"}` or another listed fixture ID. Normal Django CSRF validation applies. Unknown or duplicate fields, unknown/non-string fixture IDs, query parameters, invalid JSON, incorrect content types, and bodies over 2,048 bytes receive HTTP 400. Unsupported methods receive HTTP 405; failed CSRF validation receives HTTP 403.

A valid comparison returns HTTP 200 with `fixture`, `actor`, `downloader`, and `results.vulnerable` / `results.fixed`. Each result contains `outcome`, `jobCount`, `jobState`, `artifactCount`, current submitter/downloader permission, `deliveredMarker`, job rows, artifact metadata, and stored ordered events. The marker is `null` when nothing is delivered. Counts and metadata come from queries after the lifecycle, not hard-coded expected results. A displayed `denied` outcome belongs to the fixture, not to the HTTP comparison request itself.

This model executes changes in a deterministic sequence within one process. It does not demonstrate concurrency-safe permission revocation, policy propagation across services, broker identity, retries across workers, signed download links, storage ACLs, cancellation, partial-output cleanup, or transactional delivery to an external destination. Production designs must define those behaviors and the consistency guarantees for the time between checking permission and using it. Retaining an undelivered artifact here illustrates a separate delivery check; it is not a production retention recommendation.

Related lessons: [object access control](ACCESS_CONTROL.md), [API write authorization](API_WRITES.md), and [business-logic races](BUSINESS_LOGIC.md).

## Verification

The [backend tests](backend/securitylab/test_queue_lab.py) inspect stored transitions, verify both revocation timings, distinguish owner and tenant denials, reject initially unauthorized jobs, remove membership records, mutate resource ownership after enqueue, and confirm downloads read the actual stored artifact. They also cover fresh state, duplicate-processing prevention within the fixture, selector boundaries, and CSRF.

The [browser tests](frontend/tests/queue.spec.js) cover all six fixtures, verify visible job/artifact/delivery evidence, exercise the allowed control after a denial, clear old evidence on selection and server error, and discard delayed responses after leaving the tab.

To run the backend checks alone from the repository root:

```powershell
Push-Location labs/browser_security/backend
..\.venv\Scripts\python.exe manage.py test securitylab.test_queue_lab
Pop-Location
```

For the full suite, stop the lab servers and follow the test command in the [lab README](README.md). Each comparison starts fresh; no reset is required.
