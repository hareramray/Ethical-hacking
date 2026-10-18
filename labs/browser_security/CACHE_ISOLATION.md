# Personalized cache isolation

This runnable lesson compares a path-only application cache with a handler that authorizes the current request and keeps private responses out of shared storage. It uses an actual in-memory cache and fictional identities; no browser, CDN or reverse-proxy cache is configured by this exercise.

Start the [Vue + Django lab](README.md) and select **Personalized cache isolation**. Choose a sequence, then select **Compare cache decisions**. Each mode gets its own empty cache, which is discarded after the comparison. The two fictional requests within a sequence share that mode's cache.

## Fixtures and expected evidence

| Fixture | Vulnerable path | Fixed path |
| --- | --- | --- |
| Private control | Ada receives `PRIVATE_ADA_BLUE` twice; the second response is a cache HIT. | Ada receives her marker twice, with two origin reads and no private entries. |
| Cross-user | Bea requests her own summary at the same URL and receives Ada's cached marker. | Bea receives `PRIVATE_BEA_BLUE`. |
| Cross-tenant | Cy from tenant-amber receives Ada's tenant-blue marker. | Cy receives `PRIVATE_CY_AMBER`. |
| Revoked permission | After Ada's permission is removed, a cache HIT still returns her private marker. | The second request is denied before a cache or origin read. |
| Logout | A later anonymous request receives Ada's cached marker. | The anonymous request is denied with no returned content. |
| Public control | An anonymous visitor reuses the public catalog response warmed by Ada. | The public catalog still gets a real cache HIT: two lookups, one write and one origin read. |

All identities, permissions, routes and markers come from server-owned fixtures. The logout fixture switches to an anonymous synthetic identity; it does not alter the dashboard's Django session cookie. The revoked fixture changes a per-run permission set between requests.

## Read the evidence

Each response shows the current identity, tenant, permission, actual authorization check, cache decision, key, origin-read flag and returned marker. The status `403` belongs to a fictional request inside the comparison; the successful comparison API itself returns HTTP `200`.

- `MISS`: an actual cache lookup found no entry. An allowed origin response can then be stored.
- `HIT`: the handler returned an entry already in its in-memory cache without reading the origin.
- `BYPASS`: the fixed handler authorized a private request and deliberately skipped shared storage.
- `NOT_CHECKED`: authorization denied the fixed request before a cache lookup.

The stored-entry panel is read from the actual cache contents. Expand **Inspect the operation order** to see authorization, lookup, origin-read, store and permission-change events. A fresh run clears state; selecting a new fixture clears the old display.

The ordinary private control does not expose another user's marker, but its vulnerable cache still has the faulty sharing policy. An uneventful control is not evidence that the handler is safe for other identities.

## The repair

The fixed handler checks current permission before any cached content can be returned. It classifies the private summary route as ineligible for shared storage. Public catalog responses use a separate versioned key and remain shareable because the content does not vary by identity.

This lesson chooses to bypass shared caching for private content. An application that deliberately caches private data needs trusted user/tenant/resource dimensions, current authorization and an invalidation design. Merely adding a user ID to a key does not solve revoked permissions. Cookies and a successful login also do not make shared entries private.

For deployed HTTP caches, `Cache-Control: no-store` prevents new storage by compliant caches; it does not purge old entries. `private` prohibits shared-cache storage but may allow private-cache storage. `no-cache` permits storage with revalidation. Changing a policy requires handling already stored sensitive entries and checking every intermediary's configuration. These distinctions and the application-cache authorization boundary are covered by [OWASP Web Cache Security](https://cheatsheetseries.owasp.org/cheatsheets/Web_Cache_Security_Cheat_Sheet.html).

The lab's normal HTTP responses retain their existing `Cache-Control: no-store` header. A displayed application-cache HIT is entirely inside Python and does not imply that the browser cached the comparison response. The fixed application handler bypasses an old private entry if one exists; it does not implement a production purge service.

## Verify

From the repository root, run the focused backend tests:

```powershell
Push-Location labs/browser_security/backend
../.venv/Scripts/python.exe manage.py test securitylab.test_cache_lab --noinput
Pop-Location
```

Build the Vue interface and stop any running lab on ports 8766 and 8767 before running the browser checks. Playwright starts and stops its own servers; see the [lab README](README.md#check-the-implementation) for browser installation or the Chrome channel option:

```powershell
python labs/browser_security/run_lab.py --build
Push-Location labs/browser_security/frontend
npx playwright test tests/cache.spec.js
Pop-Location
```

Tests check returned markers and real stored contents, both identity boundaries, permission removal and anonymous access, private and public positive controls, authorization before reads even with a pre-existing private entry, disposable stores, fixture validation, CSRF, error recovery and leaving the tab while a request is pending.

## Boundaries

This is an application/shared-cache model with two deterministic requests per run. It does not implement HTTP cache semantics, TTLs, conditional requests, CDN purge APIs, multi-process invalidation, concurrent cache fills, browser history or back/forward cache behavior. It does not demonstrate cache poisoning, cache deception, URL-normalization disagreements, unkeyed header effects or a real logout implementation. Test those through the actual cache layers of an owned system with separate fixtures.

See [access control](ACCESS_CONTROL.md) for object boundaries and [authentication and sessions](AUTH_SESSIONS.md) for the separate session lesson. The implementation is in [cache_lab.py](backend/securitylab/cache_lab.py), with the controls in [CacheLab.vue](frontend/src/CacheLab.vue).
