# DOM clobbering: named HTML versus explicit references

This lesson demonstrates real browser property lookup with harmless HTML. A named form changes a preview badge, and a named input changes a method label. There is no injected script, external URL, form submission, or navigation.

Start the lab with the [setup instructions](README.md), open `http://127.0.0.1:8766/`, and select **DOM clobbering**. Choose a fixture and click **Compare named and explicit access**. The two frames contain the same fixture; their application code chooses different ways to read configuration and form data.

## What to observe

| Fixture | Actual browser lookup | Vulnerable display | Fixed display |
| --- | --- | --- | --- |
| Ordinary note | `window.labConfig` is undefined; `form.method` is a string | `Standard view \| method: post` | Same |
| Named configuration form | `window.labConfig` is an `HTMLFormElement`; `.preview` is an `HTMLInputElement` | `Preview mode \| method: post` | `Standard view \| method: post` |
| Named method input | `form.method` is an `HTMLInputElement`, while the method attribute remains `post` | `Standard view \| method: [object HTMLInputElement]` | `Standard view \| method: post` |

Every fixture retains the legitimate note, `Hello from a scoped field`. The type fields and final labels are measured inside the browser frames. The server does not substitute expected results for browser observations.

The fixed frame still reports the named collision. Its fix is to stop treating named DOM properties as trusted configuration. A named element existing on `window` is not, by itself, evidence of XSS: vulnerable application code must consume that value in a consequential way. This exercise demonstrates a display change, not script execution.

## Why the lookups differ

The named configuration fixture is ordinary non-script HTML:

```html
<form id="labConfig">
  <input name="preview" value="true" aria-label="Fixture preview value">
</form>
```

The vulnerable code relies on a window property fallback:

```javascript
const selectedConfig = window.labConfig || trustedConfig;
const previewEnabled = Boolean(selectedConfig.preview);
```

The form is truthy, so the fallback is skipped. Its named input is also truthy, regardless of what string its value contains. Existing code therefore selects the wrong display state without any injected JavaScript.

The second collision places this control inside the existing application form:

```html
<input name="method" value="HARMLESS_METHOD_MARKER"
       aria-label="Fixture method value">
```

`String(form.method)` now converts the input element rather than reading the form's method string. The method attribute itself remains `post`.

The fixed version keeps configuration in lexical scope and uses an explicit, validated DOM contract:

```javascript
const trustedConfig = Object.freeze({ preview: false });
const previewEnabled = trustedConfig.preview === true;
const form = document.querySelector('form[data-owned-form="note"]');
const note = form.querySelector('input[data-owned-note]');
if (!(form instanceof HTMLFormElement) ||
    !(note instanceof HTMLInputElement) || note.type !== 'text') {
  throw new Error('Unexpected owned form shape');
}
const attribute = form.getAttribute('method');
const method = attribute === 'post' ? attribute : 'invalid';
```

Both versions assign the display with `textContent`. Freezing a local object is an additional guard; freezing alone would not fix a later `window.labConfig` fallback. This explicit-reference repair is specific to the finite fixtures. Arbitrary markup could forge `data-owned-*` attributes or add a control named `getAttribute` that shadows that method too. General rich-HTML handling needs sanitization, an application-controlled DOM boundary, and trusted references that do not depend on names in the injected content. Apply a policy for IDs and names as well; see [Sanitization](SANITIZATION.md).

## Isolation and repeatability

- The API accepts only `normal`, `named-config`, or `form-property`. It rejects custom HTML, duplicate JSON keys, additional fields, and ambiguous frame queries.
- Each prepare call creates a random run bound to the browser's Django session. A new run replaces only this lesson's prior run. Another session and old run URLs cannot load its frames.
- Each preview has response-level CSP `sandbox allow-scripts`, without `allow-same-origin`. The same isolation applies when a frame URL is opened directly. Network connections, child frames, form actions, objects, and base URLs are denied. A fresh nonce permits only the lesson's own script and style.
- The dashboard accepts bounded observation messages only from the current frame window, opaque origin `null`, current run, and matching mode. It displays all evidence as text. Changing fixtures or tabs clears the frames and observations.
- A missing observation produces a timeout message instead of an inferred success.

These three fixtures are not an exhaustive list of named-access behavior across all browsers, element types, collections, or nesting patterns. CSP can restrict resource loading and script execution, but the collision here occurs in already permitted application code. The lesson does not claim that CSP removes named-property collisions.

## Relevant files and checks

- [Django fixture and frame handlers](backend/securitylab/clobber_lab.py)
- [Vue comparison UI](frontend/src/ClobberLab.vue)
- [Backend boundary tests](backend/securitylab/test_clobber_lab.py)
- [Browser tests](frontend/tests/clobber.spec.js)

From `labs/browser_security`, run:

```powershell
.\.venv\Scripts\python.exe backend\manage.py test securitylab.test_clobber_lab
```

With the normal lab launcher stopped, run the focused browser checks from `frontend`:

```powershell
$env:LAB_BROWSER_CHANNEL = 'chrome'
npm run test:e2e -- tests/clobber.spec.js
```

The browser checks verify the actual named object types and output in both frames, a legitimate control, parent/session isolation, direct-navigation sandboxing, expired runs, stale or malformed telemetry rejection, and cleanup when leaving during a request.

## References

- [OWASP DOM Clobbering Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/DOM_Clobbering_Prevention_Cheat_Sheet.html) covers named collisions, scoped configuration, type checks, and sanitization of names.
- [MDN: HTMLFormElement](https://developer.mozilla.org/en-US/docs/Web/API/HTMLFormElement) documents that named controls can overshadow form properties.
- [MDN: the HTML id attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/id) explains named window access and recommends explicit element lookup.
