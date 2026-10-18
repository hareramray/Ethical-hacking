# Client-side prototype pollution

Run the [Vue + Django lab](README.md) and open **Prototype pollution**. Select a fixture and choose **Compare both merge paths**. Both previews execute real JavaScript in separate, disposable iframe realms.

The harmless target is a fictional theme preference named `labTheme`. This lesson changes no account, file, browser setting, or dashboard prototype. Django selects a fixed JSON fixture; the browser performs the merge and reports what it actually observed.

## Try the six fixtures

| Fixture | Unsafe merge | Validated copy |
| --- | --- | --- |
| Allowed preferences | Own `ocean` theme and `large` font; prototype unchanged | Same preferences accepted |
| `__proto__` | Adds `labTheme` to the frame's `Object.prototype`; an empty preference object inherits `polluted-marker` | Rejected before assignment |
| `constructor.prototype` | Reaches the same prototype through an inherited constructor | Rejected before assignment |
| Allowed fields followed by a dangerous key | Own `sunset` preference hides the polluted inherited theme, although the prototype still changed | Entire input rejected; no partial `sunset` preference remains |
| Nested dangerous key | Reaches the prototype through `preferences.__proto__` | Recursive preflight rejects the nested key |
| Wrong preference type | Stores numeric font size `42` without validation | Type check rejects the entire input |

For each result, inspect **Prototype before**, **Prototype after**, **Theme source**, and **Own preferences**. Expand **Observed frame state** inside a preview to see the data reported by that browser realm. Run the allowed fixture after a pollution fixture: each new frame starts with an unchanged prototype.

## Where the defect occurs

`JSON.parse` gives `__proto__` an ordinary own data property. Pollution occurs later when a merge reads an inherited target and recursively writes through it. A missing own preference can then resolve to a value on its prototype. [MDN describes the distinction between the pollution source and the later property lookup](https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/Prototype_pollution).

The intentionally unsafe merge follows object or function targets. For these fixed fixtures, that permits both `__proto__` and `constructor.prototype` to reach `Object.prototype`. The demonstration uses no evaluation, dynamic script construction, HTML sink, network request, or command execution.

## What the fixed path does

It completes all checks before the first preference assignment:

1. Bound traversal depth and key count; reject arrays.
2. Reject `__proto__`, `constructor`, and `prototype` at every nested level.
3. Require the expected preference shape and allowed string values.
4. Copy only the two explicitly supported own fields into an object created with `Object.create(null)`.

The schema is deliberately small. A key denylist alone is insufficient for arbitrary application data or third-party merge libraries. Null-prototype containers and `Map` are useful for avoiding inherited property lookups; preventing only the `__proto__` route leaves other paths to consider. [OWASP's prevention guidance discusses these measures](https://cheatsheetseries.owasp.org/cheatsheets/Prototype_Pollution_Prevention_Cheat_Sheet.html).

## Isolation and evidence

The API accepts one fixture identifier, not a custom JSON payload. A CSRF-protected preparation request stores only the current run and fixture in the Django session. Frames require that session and exact selection; preparing a new run invalidates old frame URLs.

Both modes receive a response-level CSP with `sandbox allow-scripts`, no `allow-same-origin`, a fresh script/style nonce, and blocked connections, forms, objects, and child frames. Response sandboxing also applies if a preview URL is opened directly. Each frame therefore has its own opaque origin and JavaScript realm.

The parent checks the message's opaque origin, exact current iframe window, run, mode, and bounded evidence schema. It renders text through Vue interpolation. A message claiming an expected origin is not sufficient by itself: the frame source and active run must also match.

## Scope and verification

This is **client-side JavaScript** prototype pollution. It is not a Python/Django pollution example, a server-side JavaScript runtime, a demonstration of arbitrary code execution, or a complete audit of a merge library. Actual impact elsewhere depends on the code that consumes inherited values.

Backend tests cover finite input selection, session isolation and replacement, CSRF, exact queries, peer-role denial, and sandbox/nonce headers. Browser tests check actual prototype mutation, inherited versus own lookup, no partial fixed writes, type validation, fresh realms, dashboard isolation, direct-navigation sandboxing, and rejected telemetry.

Inspect the [Django fixtures and browser script](backend/securitylab/prototype_lab.py), [Vue comparison](frontend/src/PrototypeLab.vue), [backend tests](backend/securitylab/test_prototype_lab.py), and [browser tests](frontend/tests/prototype.spec.js).

From `labs/browser_security`, run `.venv/Scripts/python.exe backend/manage.py test securitylab.test_prototype_lab`. For the browser checks, stop the interactive lab, set `LAB_BROWSER_CHANNEL=chrome`, and run `npm run test:e2e -- tests/prototype.spec.js` from `frontend`. The test runner starts its own servers.

Related lessons: [DOM clobbering](DOM_CLOBBERING.md), [sanitization](SANITIZATION.md), and [postMessage security](POSTMESSAGE.md).
