# Trusted Types: sanitizer policies and real HTML sinks

Open **Trusted Types policies** in the [local lab](http://127.0.0.1:8766/). This lesson compares two browser-created `TrustedHTML` values at a real `innerHTML` assignment. It extends the original CSP lesson, whose Trusted Types mode blocks raw strings and forbids every policy.

Both frames enforce `require-trusted-types-for 'script'`. The vulnerable frame permits `lab-pass`, whose callback returns input unchanged. The fixed frame permits `lab-sanitize` plus DOMPurify's internal `dompurify` policy, with no default policy and no duplicate policy names. A permitted policy name identifies a conversion point; it does not establish that the conversion sanitizes HTML. [Trusted Types API](https://developer.mozilla.org/en-US/docs/Web/API/Trusted_Types_API), [CSP policy names](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/trusted-types)

## Five fixed fixtures

| Fixture | Pass-through frame | Sanitizer-backed frame |
| --- | --- | --- |
| Useful formatting | Accepted `TrustedHTML`; actual `strong`, `em`, and `code` elements remain. | The same legitimate formatting survives the sanitizer. |
| Inert text | Encoded markup renders as literal text; no `strong` element appears. | The same literal text remains. |
| Harmless event | Accepted `TrustedHTML` includes an invalid data image; its exact error handler sets `HARMLESS_TT_MARKER`. | The image and handler are removed; the legitimate `strong` element remains and no marker runs. |
| Raw string | Direct `innerHTML = string` raises `TypeError`; no policy conversion occurs. | The same sink rejection occurs. |
| Forbidden policy | `createPolicy('lab-forbidden')` raises `TypeError`; the sink is never attempted. | The same policy-name rejection occurs. |

The marker writes only to an output element inside the frame. It reads no cookies, storage, or private data. The invalid `data:,` image makes no external network request. Payloads, policy callbacks, and destinations are fixed by the lesson; preparation accepts a fixture ID only.

## The fixed conversion

The frame uses the pinned local **DOMPurify 3.4.16** dependency:

```javascript
const policy = trustedTypes.createPolicy('lab-sanitize', {
  createHTML: value => DOMPurify.sanitize(value, {
    ALLOWED_TAGS: ['p', 'strong', 'em', 'code'],
    ALLOWED_ATTR: [],
    ALLOW_DATA_ATTR: false,
    ALLOW_ARIA_ATTR: false,
    RETURN_TRUSTED_TYPE: false,
  }),
});
const html = policy.createHTML(fixedFixture);
output.innerHTML = html;
```

`RETURN_TRUSTED_TYPE: false` lets the sanitizer return a string to the callback; `createHTML` wraps the sanitized result as `TrustedHTML`. DOMPurify's internal policy supports its inert parsing under enforcement. The lesson retains a deliberately small formatting vocabulary and permits no attributes. This configuration is specific to these output requirements, rather than a universal policy for every HTML feature. [DOMPurify documentation](https://github.com/cure53/DOMPurify#what-about-dompurify-and-trusted-types)

The comparison deliberately permits one exact event handler through `script-src-attr 'unsafe-hashes' 'sha256-…'` in both frames. Other inline handlers are not permitted. Without that controlled permission, a separate script policy could hide the unsafe pass-through policy by blocking its marker. Nonced observer and sanitizer scripts are independently allowed. [CSP script-src-attr](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/script-src-attr)

## Reading the evidence

Each run displays independent observations:

- **Raw-string guard:** a real assignment into a detached element must throw `TypeError`, proving that enforcement is active. Every supported run therefore emits a `require-trusted-types-for` event, including successful sanitized runs. That guard event is not evidence of sanitizer failure.
- **Policy creation:** distinguishes accepted policy construction from a rejected policy name.
- **Sink assignment and value type:** reports whether `innerHTML` accepted the value and whether `trustedTypes.isHTML` identified `TrustedHTML`.
- **DOM and marker:** shows the text, retained `strong` element, and the actual output marker. The browser tests inspect the frame DOM as well as controller telemetry.
- **Local CSP events:** records bounded directive names. This lesson does not send HTTP violation reports; use [CSP workers and reporting](CSP_WORKERS_REPORTING.md) for that boundary.

If the API is absent, or the raw-string guard is accepted despite the CSP header, the frame reports **unsupported** and stops without inserting the fixture. An initialization error or missing frame response is **inconclusive**, not proof of protection. The automated suite checks the real configured Chromium browser and separately simulates a missing API; it does not establish Firefox or WebKit compatibility.

## Local assets and isolation

`npm run build` first builds Vue, then copies the exact installed DOMPurify UMD file and its license into `frontend/dist`. Django reads `trusted-sanitizer.js` from that build and embeds it with a fresh nonce in the fixed frame. There is no CDN dependency and running a completed build does not require `node_modules`. A missing, unexpected, or oversized artifact produces an actionable HTTP 503 instead of silently replacing the sanitizer.

After updating the dependency, update the backend's expected version and rebuild so the served artifact matches the installed release. The package lock pins the dependency and its integrity. The build retains the upstream license; the server checks the expected version banner and rejects a script-closing sequence before embedding the fixed artifact. Those are build-consistency checks, not protection from an attacker who controls the project files.

Frames use CSP and iframe `sandbox="allow-scripts"` without `allow-same-origin`, giving them opaque origins. CSP blocks network connections, child frames, workers, objects, forms, and base-URL changes; image loads are limited to data URLs. Frame documents require the creating Django session, a fresh run ID, and the main configured origin. Preparing another run revokes the old URL, and runs expire after five minutes.

The controller accepts observations only from the current frame window, the opaque `null` origin, the active run/mode, and the exact bounded message schema. An origin string of `null` alone is not an identity check. Changing fixtures or leaving the lesson removes frames, aborts pending requests, and clears timers. No user-supplied HTML enters the Vue controller through `v-html`.

## Run and verify

Use the [lab setup instructions](README.md). Install and build from `labs/browser_security/frontend`:

```powershell
npm ci
npm run build
```

With the normal launcher stopped so ports 8766 and 8767 are free, the existing Playwright configuration starts its own test servers:

```powershell
$env:LAB_BROWSER_CHANNEL = 'chrome'
npm run test:e2e -- tests/trusted.spec.js
```

From `labs/browser_security/backend`, run the backend checks after building the sanitizer artifact:

```powershell
..\.venv\Scripts\python.exe manage.py test securitylab.test_trusted_lab
```

Backend checks cover session ownership and expiry, fixture-only inputs, CSRF, exact origins, fresh nonces, policy allowlists, the exact handler hash, and missing assets. Browser checks cover all five fixtures, real retained/removed elements, the executed marker, unsupported API handling, source-bound telemetry, and teardown during delayed preparation.

This lesson covers `TrustedHTML` and `innerHTML`. It does not implement `TrustedScript`, `TrustedScriptURL`, default-policy migration, arbitrary third-party widgets, or a comprehensive HTML parser mutation corpus. CSP and sanitizer behavior remain separate layers; the exercise demonstrates why both the conversion implementation and the resulting DOM matter.
