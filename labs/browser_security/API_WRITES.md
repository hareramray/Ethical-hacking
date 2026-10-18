# API write authorization and mass assignment: runnable lesson

This lesson performs actual updates against fictional profiles in disposable SQLite databases. It separates **object permission** (whose profile can be edited) from **property permission** (which fields can be changed), then shows why a rejected patch must not leave a partial update.

Start the [Vue + Django lab](README.md) from the repository root:

```powershell
python labs/browser_security/run_lab.py
```

Open **http://127.0.0.1:8766/**, select **API write authorization**, choose a fixture, and click **Compare writes**. The server establishes the fictional actor as `user-ada` in `tenant-blue`. This identity is part of the teaching harness, not a browser login or an identity supplied by the request.

| Fixture | Vulnerable handler | Fixed handler |
| --- | --- | --- |
| `own`: edit Ada's display name | Commits the intended edit | Commits the intended edit |
| `peer`: edit Bea in the same tenant | Changes Bea's profile by ID | Denies the owner mismatch |
| `cross-tenant`: edit a profile in tenant Amber | Changes the other tenant's profile | Denies the tenant mismatch, even with a matching owner identifier |
| `owner`: assign `ownerId` | Transfers the fictional profile | Rejects the protected field |
| `tenant`: assign `tenantId` | Moves the fictional profile | Rejects the protected field |
| `role`: assign `role` | Stores an administrator label | Rejects the protected field |
| `mixed`: change display name and role together | Changes both properties | Rejects both; the display name remains unchanged |
| `invalid-type`: set a numeric display name | Stores the integer | Rejects the non-string value |
| `too-long`: set a 41-character name | Stores the long value | Rejects the value beyond 40 characters |

The administrator label grants no permissions in the real dashboard. Every comparison creates a separate fresh three-row database for each handler. A result from one mode, fixture, or request cannot affect another. No files or production records are modified.

## Observe stored evidence

Start with `own`. Both panels should report `updated`, one row updated, and only `displayName` changed. The before/after evidence is read from SQLite, rather than generated from expected outcomes.

Next compare `peer` and `cross-tenant`. The first selects a different owner's profile in the same tenant; the second deliberately selects a profile with the same owner identifier in a different tenant. This makes the two permission checks independently observable. The fixed result should report `denied`, zero rows updated, and identical before/after values.

Try `owner`, `tenant`, and `role` to see how permission to edit an object does not automatically grant permission to edit every property. Finally run `mixed`: the fixed handler must preserve **both** the original display name and the original role. Applying the permitted field before noticing the forbidden one would fail this check. Repeat `own` to verify that legitimate edits still succeed.

All result values use Vue text interpolation. The complete fictional profile is displayed for teaching, including protected properties; this is not a recommended production response schema.

## The repair

The [backend handler](backend/securitylab/write_lab.py) deliberately makes the vulnerable branch write by profile ID alone and bind every selected fixture property. SQL values are parameterized in both branches: safe SQL construction does not establish authorization.

The fixed branch opens a transaction, reads the current stored profile, and requires both the persisted owner and tenant to match the server-established actor. It validates the complete patch before issuing an update:

1. Only `displayName` may be present, and the patch must not be empty.
2. The name must be a nonblank string of 1 to 40 characters.
3. Any forbidden property or invalid value rejects the whole patch.
4. An allowed update includes the profile ID, owner, and tenant in its SQL predicate, then commits.

Rejected and denied attempts roll back without issuing an `UPDATE`. A read after the attempt supplies the displayed evidence. The SQLite column for the name intentionally has no type affinity, so the vulnerable numeric fixture visibly persists a number; the fixed handler enforces the application schema itself.

[OWASP API3:2023, Broken Object Property Level Authorization](https://api-security.owasp.org/editions/2023/en/0xa3-broken-object-property-level-authorization/) covers unauthorized modification of object properties, including mass assignment, and recommends allowing changes only to properties the client should edit. Production APIs should also return only the fields needed by the caller.

## API and scope

The UI sends `POST /api/write/compare/` with JSON containing exactly `{"fixture":"mixed"}` or another listed fixture ID. The request cannot supply an actor, patch, target ID, or handler mode. Django CSRF protection remains enabled.

Valid comparisons return HTTP 200 with `fixture`, `actor`, `targetId`, `patch`, and `results.vulnerable` / `results.fixed`. Each result includes `outcome` (`updated`, `denied`, or `rejected`), `before`, `after`, `rowsChanged`, `changedFields`, and `reason`. A lesson result of `denied` is evidence inside a successful comparison response, not an HTTP denial of the comparison API itself.

Malformed JSON, duplicate or extra fields, unknown fixture IDs, query parameters, wrong content types, and bodies larger than 2,048 bytes receive HTTP 400. Missing CSRF validation receives HTTP 403. Unsupported methods receive HTTP 405. The exact fixture selector is the exercise boundary; object authorization, field allowlisting, validation before mutation, and scoped transactions are the application repairs being taught.

This is an isolated write-authorization lesson. It does not implement production login, organization membership changes, administrator workflows, bulk edits, concurrent permission revocation, or distributed transactions. The supplied identities and protected roles are fictional. Extend authorization tests to those real workflows when implementing a production application.

## Verification

The [backend tests](backend/securitylab/test_write_lab.py) verify actual committed SQL updates, unchanged non-target records, owner and tenant denials, protected-property rejection, schema limits, absence of partial updates, fresh fixture state, input boundaries, and CSRF. The [browser tests](frontend/tests/write.spec.js) cover every fixture and check the visible before/after evidence, including clearing stale results on a new selection.

Stop the lab servers before running the full suite:

```powershell
$env:LAB_BROWSER_CHANNEL = 'chrome'
python labs/browser_security/run_lab.py --test
Remove-Item Env:LAB_BROWSER_CHANNEL
```

Record the fixture actor, target, patch, stored values before/after, and the field or object boundary that determined the outcome. Each comparison starts fresh and needs no reset.
