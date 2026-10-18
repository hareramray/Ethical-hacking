# Access control: owners, roles and tenants

Start the lab from the repository root, open <http://127.0.0.1:8766/>, and choose **Access control**:

```powershell
python labs/browser_security/run_lab.py
```

Run `python labs/browser_security/run_lab.py --setup` first if the lab has not been installed. See the [lab guide](README.md) for prerequisites and browser setup.

This lesson makes real HTTP requests to Django and returns only synthetic record markers. The vulnerable handler checks for a practice identity but omits authorization. The fixed handler checks permissions before returning record content. Changing an identifier to reach another person's record is an insecure direct object reference when the server does not enforce the required access check. See [OWASP's IDOR guidance](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html).

## Practice identities

| Persona | Tenant | Role | Fixed read permission | Fixed review permission |
| --- | --- | --- | --- | --- |
| Alice | team-a | member | alice-a only | None |
| Bob | team-a | member | bob-a only | None |
| Carol | team-b | member | carol-b only | None |
| Admin A | team-a | admin | alice-a and bob-a | alice-a and bob-a |
| Anonymous | None | None | None | None |

**Persona switching is a teaching control, not authentication.** There is no password or real account login. A CSRF-protected POST stores the chosen persona in the current lab session. Roles and tenants come from a fixed server-side map; the record endpoint rejects caller-supplied `role`, `tenant` and `actorId` fields. New sessions start as Anonymous.

All record IDs, owners and tenant names are intentionally visible as fixture metadata. The protected content is each record's harmless marker. `review` is a privileged **read**, not an approval or write operation. Neither handler changes records.

## Run these comparisons

For each row, select the persona, record and action, then choose **Compare handlers**. The result cards show actual HTTP statuses and server decisions.

| Persona / record / action | Vulnerable | Fixed | What it tests |
| --- | --- | --- | --- |
| Alice / alice-a / read | 200 + marker | 200 + marker | Positive control: owner's legitimate access |
| Alice / bob-a / read | 200 + marker | 403, no record content | Horizontal access within one tenant |
| Alice / carol-b / read | 200 + marker | 403, no record content | Cross-tenant isolation |
| Alice / alice-a / review | 200 + marker | 403, no record content | Ownership does not grant administrator actions |
| Admin A / bob-a / review | 200 + marker | 200 + marker | Legitimate administrator permission |
| Admin A / carol-b / review | 200 + marker | 403, no record content | Administrator scope stays within its tenant |
| Anonymous / alice-a / read | 401, no record content | 401, no record content | Identity requirement in both handlers |

An allowed result contains a marker such as `BOB_PRIVATE_LAB_RECORD`. A denied or unauthenticated result has `record: null`; it must not merely hide the marker in the interface. Use the browser Network panel to inspect the JSON response.

## Trace the server decision

The implementation is in [access_lab.py](backend/securitylab/access_lab.py). In fixed mode, the decision reduces to:

```python
same_tenant = actor["tenant"] == record["tenant"]
tenant_admin = same_tenant and actor["role"] == "admin"
owner = same_tenant and actor["id"] == record["ownerId"]

allowed = tenant_admin if action == "review" else owner or tenant_admin
```

Before this check, the handler validates the input and requires a known server-side persona. The vulnerable handler instead returns the requested fixture after checking only that a persona exists.

The permission rule must be enforced for every relevant request on the server, including direct API calls. Hiding controls or choosing less predictable identifiers does not replace authorization. [OWASP's authorization guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) explains these principles.

## Inspect the API

- `GET /api/access/state/` returns the active practice persona and public fixture metadata.
- `POST /api/access/identity/` accepts JSON `{"actorId":"alice"}` and requires the dashboard's CSRF token.
- `GET /api/access/record/?mode=fixed&record=bob-a&action=read` runs the decision for the persona stored in the session.

Only `mode`, `record` and `action` are accepted on the record endpoint. Unknown or duplicate parameters return 400. An authenticated request for a nonexistent record returns 404. A missing or unknown session persona returns 401. Responses use `Cache-Control: no-store`.

Try opening a separate private browsing session: its persona starts as Anonymous and can be changed independently. Tabs in the same browsing session share the practice persona. Avoid changing it in another tab while a comparison is running; each result card reports the server identity used for that request.

## Verify the lesson

Stop the running lab before the full `--test` command so its browser tests can use ports 8766 and 8767. See the [lab guide](README.md#check-the-implementation) for browser installation or the Chrome channel setting.

```powershell
labs/browser_security/.venv/Scripts/python.exe labs/browser_security/backend/manage.py test securitylab.test_access_lab
python labs/browser_security/run_lab.py --test
```

Backend checks cover ownership, peer access, tenant isolation, administrator actions, anonymous access, CSRF, identity validation, per-session state, unsupported parameters, missing records and read-only behavior. Browser checks exercise the displayed positive and negative results and confirm that denied responses clear earlier content.

This lesson does not implement production authentication, password resets, object creation, database row filtering, API keys, permission inheritance or write-operation authorization. In a real application, derive the actor from trusted authentication, apply the application's policy to every operation, and separately test its full permission matrix.
