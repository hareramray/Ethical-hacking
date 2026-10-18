# Harmless CSP and XSS test scripts

Use these examples in a local lab or an application you are authorized to test. The supplied probes print a fixed marker, add test content, or contact the lab's own loopback server. They do not read cookies, credentials, or unrelated browser storage. The optional storage exercise uses one dedicated lab key.

This covers the principal XSS families and browser contexts, plus common CSP controls. A finite collection cannot cover every parser, framework, sanitizer, or browser bug. A non-executing payload alone does not establish that an application is safe.

Jump to [individual inputs](#context-specific-harmless-inputs), [JSONP tests](#jsonp-tests), [file-upload tests](#file-upload-tests), [runnable lab](#local-practice-lab), [expected results](#expected-csp-results-for-this-exact-lab), [CSP diagnostics](#csp-diagnostics-for-your-own-application), or [additional coverage](#additional-csp-coverage-checklist).

## Quick start

For the Vue + Django application with an evidence panel, stored fixtures, and a real upload API, see [Browser Security Lab](labs/browser_security/README.md):

```powershell
python labs/browser_security/run_lab.py --setup
python labs/browser_security/run_lab.py
```

Open `http://127.0.0.1:8766/`. That application's sandbox remains enabled even in its `off` script-policy mode. The standalone standard-library server below remains a separate reference fixture on port 8765.

The Vue + Django application also includes a **Path traversal** tab. Its [file-read walkthrough](labs/browser_security/PATH_TRAVERSAL.md) compares a vulnerable handler with a repaired handler using disposable public files and a harmless private sentinel. This is a server-side file-access exercise, separate from the CSP/XSS probes below.

Three more runnable lessons cover [SQL injection and parameterized queries](labs/browser_security/SQL_INJECTION.md), [owner, tenant, and role access checks](labs/browser_security/ACCESS_CONTROL.md), and [CSRF versus CORS](labs/browser_security/CSRF_CORS.md). They compare vulnerable and fixed handlers using synthetic records and counters. The same launcher starts both the main origin on port 8766 and the companion origin on port 8767.

Continue with [authentication and session lifecycle](labs/browser_security/AUTH_SESSIONS.md), [SSRF between local mock services](labs/browser_security/SSRF.md), and [single-use business rules and race conditions](labs/browser_security/BUSINESS_LOGIC.md). These server-side exercises use disposable accounts, token stores, HTTP fixtures, and coupon data.

The [template injection](labs/browser_security/TEMPLATE_INJECTION.md), [command/argument injection](labs/browser_security/COMMAND_INJECTION.md), and [XML external-entity](labs/browser_security/XML_ENTITIES.md) lessons extend this into server-side interpreters. Select predefined harmless fixtures and compare actual vulnerable/fixed results; the interfaces do not accept arbitrary templates, commands, or XML documents.

1. For individual inputs, use the context-specific examples below. Change the marker ID for each test.
2. For a working practice environment, save the Python block under **Local practice lab** as `csp_xss_lab.py`, then run `python csp_xss_lab.py`.
3. Open `http://127.0.0.1:8765/` and the browser's developer-tools Console and Network panels. The initial page uses a nonce CSP and escapes reflected text.
4. Follow the lab walkthrough. Stop the server with `Ctrl+C`; use **Delete stored lab marker** to remove its storage fixture.

Do not run the intentionally vulnerable lab on a public interface. It binds only to `127.0.0.1`, serves fixed routes rather than files, and needs only Python 3.9+.

## How to interpret evidence

| Observation | Meaning |
| --- | --- |
| Marker executes after submitting an application input | Execution is demonstrated for that source, sink, context, and browser. Record the actual input path. |
| Marker executes because you typed JavaScript into DevTools | Only proves the console can execute JavaScript; it is not evidence of XSS or a CSP bypass. |
| HTML renders, but no JavaScript marker appears | HTML injection may exist; execution might be blocked, inert, untriggered, or in another frame. |
| CSP violation with `disposition: "enforce"` | An enforced policy rejected that operation. Check the input is still encoded or sanitized correctly. |
| CSP violation with `disposition: "report"` | A report-only policy observed the operation; that policy did not block it. |
| Plain text appears through `textContent` | Expected safe behavior for that plain-text sink. |
| No marker and no useful diagnostic | Inconclusive until the positive control, trigger, context, and source-to-sink flow are checked. |

Always compare a positive control with a safe negative control. Keep the browser version, exact response headers, input, final DOM, and console evidence. Scripts inserted through `innerHTML` are normally inert, while event-handler markup can still execute; testing only `<script>` misses that distinction. [MDN: innerHTML](https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML).

## XSS families: where to deliver the marker

| Family | Harmless procedure |
| --- | --- |
| Reflected | Submit one marker in a search/form/query input; inspect that specific response and rendered page. |
| Stored | Save one marker in a disposable test record, revisit every authorized rendering view, and delete the record afterward. Test later readers as well as the submitter. |
| DOM-based | Trace query/fragment/message/storage data to an HTML, URL, or JavaScript sink. The lab includes fragment and storage paths. |
| Stored DOM-based | Reopen a value saved in a lab-only storage key and compare `innerHTML` with `textContent`. |
| Blind stored | Use a designated test reviewer/viewer and a local console or visible marker. If the consuming view cannot be observed, record **not verified**; these examples do not use callback services. |
| Second-order / multi-view | Test the later preview, export, moderation view, notification renderer, or client-side re-render where the same test record is consumed. |
| Self-XSS | Distinguish code a user deliberately runs themselves from attacker-controlled data reaching another user's execution context. |

Reflected/stored describe delivery and persistence; DOM-based describes unsafe client-side processing. They overlap rather than forming mutually exclusive categories. [OWASP: DOM-based XSS prevention](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html).

## Context-specific harmless inputs

Use one input at a time. The surrounding template determines which input is meaningful. CSP, sanitization, and sandboxing can prevent execution even when the markup reaches a parser. These examples are deliberately small and readable.

### 1. Plain HTML injection control: no script

```html
<strong data-xss-test="HTML_01">XSS_TEST_HTML_01</strong>
```

Bold rendered text shows that markup was interpreted, not that JavaScript executed.

### 2. HTML body: parser-inserted script

```html
<script>console.log('XSS_TEST_HTML_SCRIPT_02')</script>
```

Use in server-rendered HTML. This is not a reliable `innerHTML` execution probe.

### 3. HTML body: event handlers

```html
<svg onload="console.log('XSS_TEST_SVG_03')"></svg>
```

```html
<img src="data:image/png;base64,AA==" alt="lab image" onerror="console.log('XSS_TEST_IMAGE_04')">
```

The image is deliberately invalid and uses no remote URL. An image CSP violation is separate from whether the `onerror` handler is allowed to execute. SVG load events can depend on insertion timing and browser behavior; prefer this image error probe for dynamic `innerHTML` tests.

```html
<button type="button" onclick="console.log('XSS_TEST_CLICK_05')">Run harmless marker</button>
```

Click the button. A missing click is not a passing security test.

### 4. Break out of a double-quoted attribute

Given `<input value="USER_INPUT">`, submit:

```text
"><svg onload="console.log('XSS_TEST_ATTR_DOUBLE_06')"></svg><span data-rest="
```

### 5. Break out of a single-quoted attribute

Given `<input value='USER_INPUT'>`, submit:

```text
'><svg onload="console.log('XSS_TEST_ATTR_SINGLE_07')"></svg><span data-rest='
```

### 6. Break out of an unquoted attribute

Given `<input value=USER_INPUT>`, submit:

```text
x><svg onload="console.log('XSS_TEST_ATTR_UNQUOTED_08')"></svg><span data-rest=x
```

These three examples test HTML parsing of interpolated strings. Assigning a fixed ordinary attribute with a DOM API does not reparse the value as new attributes.

### 7. Existing event-handler JavaScript string

Given `<button onclick="showName('USER_INPUT')">Show</button>`, with a defined `showName`, submit and click:

```text
');console.log('XSS_TEST_HANDLER_STRING_09');//
```

The HTML-attribute and JavaScript-string parsers both matter. Prefer trusted code with `addEventListener` and data passed as data.

### 8. JavaScript strings and template literals

Given `<script>const label = 'USER_INPUT';</script>`:

```text
';console.log('XSS_TEST_JS_SINGLE_10');//
```

Given `<script>const label = "USER_INPUT";</script>`:

```text
";console.log('XSS_TEST_JS_DOUBLE_11');//
```

Given a JavaScript template literal containing `USER_INPUT` between backticks:

```text
${console.log('XSS_TEST_JS_TEMPLATE_12')}
```

These depend on the exact surrounding syntax and on the containing script being allowed to execute. Do not insert untrusted text directly into executable JavaScript.

### 9. HTML end-tag termination

Inside a server-rendered `<textarea>`:

```html
</textarea><svg onload="console.log('XSS_TEST_TEXTAREA_13')"></svg>
```

Inside a `<title>`:

```html
</title><svg onload="console.log('XSS_TEST_TITLE_14')"></svg>
```

Inside an HTML `<script>` element, including an improperly embedded JSON data block:

```html
</script><svg onload="console.log('XSS_TEST_SCRIPT_END_15')"></svg>
```

The HTML parser recognizes the end tag before JavaScript or JSON parsing. A correct JSON serializer alone is not necessarily sufficient for embedding JSON inside HTML; use an HTML-safe serialization strategy.

### 10. URL-valued attributes

If the input becomes an anchor's `href`, submit this value, then click the resulting link:

```text
javascript:void(console.log('XSS_TEST_URL_16'))
```

Full isolated fixture:

```html
<a href="javascript:void(console.log('XSS_TEST_URL_16'))">Run URL marker</a>
```

Encoding quotes is not a URL-scheme allowlist. This is an anchor-navigation test, not a generic image-source test.

### 11. `srcdoc` and frame boundaries

```html
<iframe title="Harmless srcdoc probe" srcdoc="&lt;script&gt;console.log('XSS_TEST_SRCDOC_17')&lt;/script&gt;"></iframe>
```

Compare with the same frame carrying `sandbox=""`; its script should not run. Parent CSP inheritance and frame restrictions can affect both cases. Check the correct frame's console. A sandboxed frame's behavior does not prove the parent page is safe. [MDN: iframe](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe).

### 12. DOM sinks and their safe counterpart

Save this as part of your own lab's allowed JavaScript, with three designated container elements present:

```javascript
const probe = '<img src="data:image/png;base64,AA==" alt="lab" onerror="console.log(\'XSS_TEST_DOM_18\')">';
document.getElementById('unsafe-inner').innerHTML = probe;
document.getElementById('unsafe-insert').insertAdjacentHTML('beforeend', probe);
document.getElementById('safe-text').textContent = probe;
```

The first two deliberately parse HTML. The third displays literal text. Trusted Types enforcement can throw at the first assignment, so run each sink separately when measuring that control. Also review `outerHTML`, `document.write`, `Range.createContextualFragment`, and framework HTML escape hatches in their actual application paths; parsing a detached fragment is not itself execution.

### 13. Query, fragment, message, and storage sources

Use the preceding DOM marker as data in one source at a time. Let the application's normal code consume it. The lab below supplies fragment and dedicated storage fixtures.

For a message-driven widget in your own lab, send a fixed marker from its intended sender:

```javascript
window.postMessage(
  {kind: 'xss-lab-marker', text: '<img src="data:image/png;base64,AA==" alt="lab" onerror="console.log(\'XSS_TEST_MESSAGE_19\')">'},
  location.origin
);
```

This sends to the current window; it proves nothing unless a matching receiver exists. A safe lab receiver checks the sender and message shape and renders text:

```javascript
window.addEventListener('message', (event) => {
  if (event.origin !== location.origin || event.source !== window) return;
  const data = event.data;
  if (!data || data.kind !== 'xss-lab-marker' || typeof data.text !== 'string') return;
  document.getElementById('safe-text').textContent = data.text.slice(0, 2000);
});
```

For real cross-frame widgets, use the intended frame's `contentWindow` and exact expected origin instead of this self-message fixture. Do not change a production receiver to accept arbitrary senders just to run a test. [MDN: postMessage](https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage).

### 14. Framework templates, rich text, Markdown, and mutation XSS

- Put the HTML, SVG, and URL probes through the real preview, sanitizer, persistence, and re-render pipeline. Compare the sanitized string with the final DOM after all transformations.
- For a template engine, try the inert arithmetic marker `{{7*7}}` only if that is its actual interpolation syntax. Output `49` shows expression evaluation, not JavaScript execution or a sandbox escape.
- Test a rich-text editor's preview and saved display separately. A sanitizer result changed by later DOM processing needs its own regression test.
- Mutation XSS depends on parser/namespace transformations and sanitizer versions. There is no universal harmless string that certifies all of them; use the sanitizer's maintained regression suite in addition to these smoke tests.

Use context-appropriate output encoding, safe DOM sinks, and a maintained HTML sanitizer for deliberately allowed rich HTML. Do not attempt to build an HTML sanitizer with regular expressions. [OWASP: XSS prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html).

### 15. Related check: DOM clobbering

In a disposable page, insert:

```html
<form id="xss_lab_named_probe_20"></form>
```

From the page's own allowed diagnostic script, inspect only that name:

```javascript
console.log('XSS_TEST_CLOBBER_20', window.xss_lab_named_probe_20 instanceof HTMLFormElement);
```

A named element becoming accessible on `window` is a collision surface, not by itself XSS. Review whether application code trusts named globals as configuration, URLs, or functions. Avoid real application variable names in this fixture. [OWASP: DOM clobbering prevention](https://cheatsheetseries.owasp.org/cheatsheets/DOM_Clobbering_Prevention_Cheat_Sheet.html).

## JSONP tests

JSONP returns JavaScript that calls a function, rather than a JSON document. For example, `labJsonp({"marker":"JSONP_TEST_22"});` is executable script. A classic script element can load a JSONP endpoint across origins subject to CSP and other browser resource controls; a missing CORS permission is not a dependable JSONP defense. Use only an owned endpoint returning synthetic data. [jQuery API: JSONP handling](https://api.jquery.com/jQuery.ajax/).

### 1. Observe intended callback execution

The local lab below now includes `/jsonp.js?callback=labJsonp`, an exact callback allowlist, a harmless synthetic response, and a **Load JSONP callback** button. Its allowed bootstrap defines the callback and displays data using `textContent` through `hit`.

After starting the lab, open these pages and click the button:

| Lab policy | Expected dynamic JSONP result |
| --- | --- |
| `/?mode=off` | `JSONP_TEST_22` and literal `<strong>JSONP_TEXT_ONLY</strong>` appear. |
| `/?mode=self` | Same result: the script endpoint is same-origin. |
| `/?mode=nonce` or `/?mode=hash` | Blocked: the new script lacks an accepted nonce/hash. |
| `/?mode=dynamic` | Executes through the trusted bootstrap's allowed dynamic script creation. |
| `/?mode=report` | Executes and produces a report-only violation. |
| `/?mode=tt` | Assigning the script URL string throws in a browser enforcing Trusted Types; the nonce policy also restricts untrusted scripts. |

Seeing this callback run is expected JSONP behavior. It is not by itself proof of XSS, callback injection, or sensitive-data exposure.

### 2. Compare parser-inserted JSONP with dynamic loading

In the lab's **Reflected input**, submit the following as **raw HTML**:

```html
<script src="/jsonp.js?callback=labJsonp"></script>
```

This script is parser-inserted and has no nonce. It should execute in `off`, `self`, and `report`; it should be blocked in `nonce`, `hash`, `dynamic`, and `tt`. The callback already exists when reflected HTML is parsed. `script-src 'self'` permits same-origin script endpoints, including JSONP; adding a nonce alongside `'self'` does not remove that source permission. These results demonstrate policy matching, not a universal CSP bypass. [MDN: script-src](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/script-src).

### 3. Validate callback names and query handling

Run this Python check against the local lab. It makes five loopback GET requests, reads only the fixture responses, and does not execute them:

```python
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

base = 'http://127.0.0.1:8765/jsonp.js'
cases = [
    ('known callback', [('callback', 'labJsonp')], 200),
    ('missing callback', [], 400),
    ('empty callback', [('callback', '')], 400),
    ('duplicate callback', [('callback', 'labJsonp'), ('callback', 'other')], 400),
    ('code instead of a name', [('callback', "console.log('JSONP_CALLBACK_TEST_23');//")], 400),
]
for label, query, expected in cases:
    try:
        with urlopen(base + '?' + urlencode(query), timeout=5) as response:
            status = response.status
            body = response.read(4096).decode('utf-8')
            mime = response.headers.get_content_type()
    except HTTPError as error:
        status = error.code
        body = error.read(4096).decode('utf-8')
        mime = error.headers.get_content_type()
        error.close()
    assert status == expected, (label, status, expected)
    if status == 200:
        assert mime == 'text/javascript' and body.startswith('labJsonp(')
    else:
        assert mime == 'text/plain' and 'JSONP_CALLBACK_TEST_23' not in body
    print(label, status, 'PASS')
```

For another owned JSONP implementation, adapt its actual callback parameter. The final input is a fixed console marker used to check whether a callback field is improperly treated as a JavaScript expression. A robust implementation rejects it. Inspect the response first; code reflected as plain text is not proof that a browser executes it. The lab intentionally provides a rejecting implementation.

Also check the response's data serialization: quotes, backslashes, line breaks, and HTML-like strings should remain data. Use a serializer rather than concatenating raw strings into JavaScript. JSONP callback validation does not fix an unsafe receiver that assigns response fields to `innerHTML`. Nor does it make private data safe to expose as a script. Prefer an ordinary JSON API with appropriate authorization and a deliberate CORS policy when JSONP is unnecessary.

## File-upload tests

Test both the upload decision and every way the stored file is served or displayed. Acceptance alone is not XSS; rejection alone does not establish that previews, metadata, and earlier uploads are safe. Use a disposable test record and record its generated ID for cleanup. This section targets browser-side content handling; the provided artifacts contain no server-side code, external references, or large files.

### 1. Generate a small harmless fixture set

Save this block as `make_upload_markers.py` and run `python make_upload_markers.py`. It creates a new `xss-upload-fixtures-*` folder under the current directory without overwriting existing files. The PNG is a real one-pixel image; the mislabeled files are deliberate validation controls.

```python
import json
import struct
import tempfile
import zlib
from pathlib import Path

folder = Path(tempfile.mkdtemp(prefix='xss-upload-fixtures-', dir='.')).resolve()
html_marker = '''<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Upload marker</title>
<body><p id="marker">UPLOAD_HTML_STATIC</p>
<script>
console.log('UPLOAD_HTML_TEST_24');
document.getElementById('marker').textContent = 'UPLOAD_HTML_TEST_24';
</script></body></html>
'''
svg_marker = '''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="50">
<rect width="320" height="50" fill="white"/>
<text id="marker" x="8" y="30" fill="black">UPLOAD_SVG_STATIC</text>
<script>
console.log('UPLOAD_SVG_TEST_25');
document.getElementById('marker').textContent = 'UPLOAD_SVG_TEST_25';
</script></svg>
'''
def png_chunk(kind, data):
    return (struct.pack('>I', len(data)) + kind + data
            + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff))

png = (b'\x89PNG\r\n\x1a\n'
       + png_chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0))
       + png_chunk(b'IDAT', zlib.compress(b'\x00\x00\x00\x00\xff'))
       + png_chunk(b'IEND', b''))
fixtures = {
    'marker.txt': b'UPLOAD_TEXT_TEST_27\n',
    'marker.html': html_marker.encode('utf-8'),
    'marker.svg': svg_marker.encode('utf-8'),
    'marker.js': b"console.log('UPLOAD_JS_TEST_26');\n",
    'marker.json': json.dumps({'marker': 'UPLOAD_JSON_DATA_ONLY'}).encode('utf-8'),
    'pixel.png': png,
    'pixel-upper.PNG': png,
    'marker.html.txt': html_marker.encode('utf-8'),
    'marker.txt.html': html_marker.encode('utf-8'),
    'html-as-image.png': html_marker.encode('utf-8'),
}
for name, data in fixtures.items():
    (folder / name).write_bytes(data)
    print(name, len(data), 'bytes')
print('Created:', folder)
```

### 2. Vary one upload property at a time

Start with the valid PNG and plain-text controls, if those types are supported by the application. Record the response, stored name, detected type, and retrieval headers for each accepted file.

| Technique | Fixture or change | What to check |
| --- | --- | --- |
| Active HTML | `marker.html` | Is it rejected, downloaded, isolated, or rendered as an application-origin document? |
| Active SVG | `marker.svg` | Compare image preview with direct navigation and document embedding. |
| Uploaded script | `marker.js` | In a disposable page, test it as a script source only if the application exposes it at a script-loadable URL. |
| Extension case | `pixel.png` vs `pixel-upper.PNG` (identical bytes) | Consistent canonicalization and file-type policy. Distinct stems keep both fixtures on Windows. Case variation alone is not a vulnerability. |
| Multiple extensions | `marker.html.txt` vs `marker.txt.html` | Which extension and decoded content determine storage and serving behavior? |
| Content/extension disagreement | `html-as-image.png` | An image-only endpoint should reject or safely process it; changing the name does not create a valid PNG. |
| Claimed MIME disagreement | Upload the same HTML bytes with part type `image/png` | The client-supplied part type must not be the sole validation control. |
| Metadata rendering | A plain-text description or filename containing `<strong>UPLOAD_NAME_28</strong>` | It should display as literal text in lists, errors, previews, and review screens. Intentionally supported rich text needs its own sanitization tests. |
| Reprocessing | Preview, thumbnail, download, and saved record | Inspect each output; transformations can change which bytes and content types reach a browser. |

A file part's claimed MIME type, its filename, and its actual format are separate inputs. Validate the allowed format and contents server-side and choose storage names independently of user-controlled paths. [OWASP: file upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).

For an owned upload app listening on `127.0.0.1:8000` with a `file` form field, this PowerShell command sends one HTML marker while claiming a PNG filename and part type. Run it from the generated fixture folder, and adapt the route/field to that app:

```powershell
curl.exe --fail-with-body --max-time 15 --form 'file=@marker.html;filename=marker.png;type=image/png' 'http://127.0.0.1:8000/upload'
```

The CSP practice server on port 8765 has **no upload endpoint**. Use your application's normal login and CSRF workflow when required; an authentication rejection is not a file-validation result. The command tests a mismatch, not a valid image upload. Unexpected types should be assessed against the application's documented requirements. [OWASP WSTG: unexpected file types](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/10-Business_Logic_Testing/08-Test_Upload_of_Unexpected_File_Types/).

To build a filename-rendering test without trying to create an invalid Windows filename, construct a browser `File` for your own app's upload client:

```javascript
const filenameProbe = new File(
  ['UPLOAD_NAME_BODY_28'],
  '<strong>UPLOAD_NAME_28</strong>.txt',
  {type: 'text/plain'}
);
const uploadForm = new FormData();
uploadForm.append('file', filenameProbe);
console.log('UPLOAD_NAME_FIXTURE_READY', filenameProbe.name);
// Pass uploadForm through your own application's upload client and CSRF handling.
// This snippet constructs the request body; it does not submit anything.
```

This inert filename checks HTML interpretation only. Record the actual transmitted and stored name if the client or server normalizes it. If markup renders, follow the existing context-specific probes in a disposable view to determine whether execution is also possible. Treat filenames and descriptions as untrusted output, even when the file bytes are a valid image. [OWASP: input validation and output handling](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html).

### 3. Compare retrieval contexts

| Retrieval context | Expected distinction |
| --- | --- |
| HTML or SVG opened as a document | Its scripts may run if its own response policy permits them. Record the actual serving origin. |
| SVG through `<img src="...">` | Script should be disabled in SVG image mode; the static label should remain. This does not test direct navigation. |
| SVG/HTML in `<iframe>` or `<object>` | Document context can execute scripts unless applicable CSP/sandbox rules prevent it. |
| File in `<iframe sandbox="">` | Scripts should be blocked. Separately test opening the file URL directly, outside that embedding sandbox. |
| JavaScript loaded using `<script src="...">` | Executes in the including page if CSP, MIME, and other resource checks permit it. Directly opening `.js` is a different test. |
| Download attachment | Normally prompts a download instead of inline display. Downloading is not evidence that the bytes are safe to open later. |

SVG image-mode restrictions do not apply identically when SVG is used as a document. [MDN: SVG as an image](https://developer.mozilla.org/en-US/docs/Web/SVG/Guides/SVG_as_an_image). An iframe's sandbox is an embedding restriction; inspect the file's own response protections as well. [MDN: iframe sandbox](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe).

In an owned test page, use this fixture with the **actual returned upload paths**, one context at a time:

```html
<img src="/uploads/marker.svg" alt="SVG image-mode control">
<iframe title="Sandboxed uploaded HTML" sandbox="" src="/uploads/marker.html"></iframe>
<script src="/uploads/marker.js"></script>
```

If the host generates object IDs, use those URLs instead; the sample paths are not lab routes. Avoid adding a nonce to the script element when testing whether an unauthorized upload can become an allowed script source. A blocked frame or image load is not automatically a script-execution result.

### 4. Inspect the final response and CSP boundary

Inspect the actual GET response after redirects, including CDN/object-store URLs. Do not rely only on an upload response or a potentially different HEAD response. Record:

- `Content-Type`: does it accurately describe the served bytes?
- `Content-Disposition`: is the intended behavior inline display or attachment?
- `X-Content-Type-Options: nosniff`: is unintended MIME interpretation constrained?
- `Content-Security-Policy`: does the uploaded document have its own effective policy?
- Final origin and access controls: can only the intended test users retrieve the record?

For a download-only route, a possible response design is:

```http
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="download.bin"
X-Content-Type-Options: nosniff
Content-Security-Policy: sandbox; default-src 'none'; base-uri 'none'; form-action 'none'
```

These headers are a serving pattern, not a substitute for validation. `nosniff` is not a sanitizer: correctly labeled active HTML/SVG still needs appropriate isolation or restrictions. [MDN: nosniff](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Content-Type-Options). `attachment` controls disposition, not the safety of opening the downloaded file. [MDN: Content-Disposition](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Disposition).

A normal HTTP upload document does not automatically inherit the application page's CSP. A separate upload origin with no application credentials can reduce same-origin exposure; allowing that origin as a script source can still let its JavaScript run in the including application. Keep those two execution contexts separate when reporting results.

Delete only the test records you created through the application's normal deletion flow, including their preview/thumbnail objects if applicable. Keep these results separate from broader upload testing such as parser vulnerabilities, archive extraction, file-size limits, and authorization; the marker files do not establish those controls.

## Local practice lab

Save the entire block as `csp_xss_lab.py`. It contains the server, HTML, JavaScript probes, safe controls, and violation logger. No package installation is required.

The lab exposes intentionally unsafe HTML parsing only when you select it. Use the supplied marker strings, not arbitrary scripts. The server accepts only the literal loopback Host, does not serve workspace files, and has no external reporting endpoint.

```python
import base64
import hashlib
import html
import json
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

HOST, PORT = "127.0.0.1", 8765
HASH_BODY = "hit('CSP_HASH_EXACT');"
BOOT = r"""
window.hit = (id) => {
  console.log(id);
  const line = document.createElement('div');
  line.textContent = id;
  document.getElementById('results').appendChild(line);
};
window.labJsonp = (data) => {
  if (!data || data.marker !== 'JSONP_TEST_22' || typeof data.text !== 'string') return;
  hit(data.marker);
  hit(data.text);
};
document.addEventListener('securitypolicyviolation', (e) => {
  hit('CSP_VIOLATION ' + JSON.stringify({
    directive: e.effectiveDirective,
    disposition: e.disposition,
    blocked: e.blockedURI,
    line: e.lineNumber
  }));
});
function attempt(id, operation) {
  try { operation(); }
  catch (error) { hit(id + ' EXCEPTION ' + error.name); }
}
document.addEventListener('DOMContentLoaded', () => {
  hit('CSP_BOOT_OK');
  const marker = '<img src="data:image/png;base64,AA==" alt="lab" onerror="hit(\'XSS_DOM_MARKER\')">';
  const input = document.getElementById('payload');
  const sink = document.getElementById('sink');
  const key = 'csp-xss-harmless-lab:v1:marker';
  input.value = marker;
  const actions = {
    text: () => { sink.textContent = input.value; hit('SAFE_TEXT_RENDERED'); },
    html: () => { sink.innerHTML = input.value; },
    fragment: () => {
      const value = decodeURIComponent(location.hash.slice(1));
      sink.innerHTML = value.slice(0, 2000);
    },
    save: () => { localStorage.setItem(key, input.value); hit('LAB_MARKER_SAVED'); },
    load: () => { sink.innerHTML = localStorage.getItem(key) || ''; },
    clear: () => { localStorage.removeItem(key); hit('LAB_MARKER_DELETED'); },
    inline: () => {
      const script = document.createElement('script');
      script.text = "hit('CSP_DYNAMIC_INLINE');";
      document.body.appendChild(script);
    },
    external: () => {
      const script = document.createElement('script');
      script.src = '/probe.js';
      script.onerror = () => hit('CSP_EXTERNAL_LOAD_ERROR');
      document.body.appendChild(script);
    },
    jsonp: () => {
      const script = document.createElement('script');
      script.src = '/jsonp.js?callback=labJsonp';
      script.onerror = () => hit('JSONP_LOAD_ERROR');
      script.onload = () => script.remove();
      document.body.appendChild(script);
    },
    eval: () => { eval("hit('CSP_EVAL');"); },
    function: () => { new Function("hit('CSP_FUNCTION');")(); },
    timer: () => { setTimeout("hit('CSP_STRING_TIMER');", 0); },
    callback: () => { setTimeout(() => hit('CSP_CALLBACK_TIMER'), 0); },
    connect: () => {
      fetch('/ping', {credentials: 'omit'})
        .then((r) => { if (r.ok) hit('CSP_CONNECT_OK'); })
        .catch(() => hit('CSP_CONNECT_FAILED'));
    }
  };
  for (const button of document.querySelectorAll('button[data-action]')) {
    button.addEventListener('click', () => {
      const id = button.dataset.action;
      hit('TRY ' + id);
      attempt(id, actions[id]);
    });
  }
});
"""

def digest(source):
    return base64.b64encode(hashlib.sha256(source.encode("utf-8")).digest()).decode("ascii")

def policy(mode, nonce):
    common = (
        "default-src 'none'; base-uri 'none'; object-src 'none'; "
        "frame-ancestors 'none'; form-action 'self'; img-src data:; "
        "connect-src 'none'; script-src-attr 'none'; "
    )
    scripts = {
        "self": "'self'",
        "nonce": f"'nonce-{nonce}'",
        "hash": f"'sha256-{digest(BOOT)}' 'sha256-{digest(HASH_BODY)}'",
        "dynamic": f"'nonce-{nonce}' 'strict-dynamic'",
        "report": f"'nonce-{nonce}'",
        "tt": f"'nonce-{nonce}'",
    }
    value = common + "script-src " + scripts[mode] + ";"
    if mode == "tt":
        value += " require-trusted-types-for 'script'; trusted-types 'none';"
    return value

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Do not log query inputs.

    def send(self, body, content_type="text/html; charset=utf-8", status=200, headers=()):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.headers.get("Host") != f"{HOST}:{PORT}":
            self.send("Use the printed loopback URL.", status=400)
            return
        if len(self.path) > 12000:
            self.send("Input too long.", status=414)
            return
        parts = urlsplit(self.path)
        if parts.path == "/jsonp.js":
            params = parse_qs(parts.query, keep_blank_values=True)
            if params != {"callback": ["labJsonp"]}:
                self.send("Invalid callback", "text/plain; charset=utf-8", 400)
                return
            data = {"marker": "JSONP_TEST_22", "text": "<strong>JSONP_TEXT_ONLY</strong>"}
            self.send("labJsonp(" + json.dumps(data) + ");", "text/javascript; charset=utf-8")
            return
        if parts.path in ("/boot.js", "/probe.js", "/parser.js"):
            source = {
                "/boot.js": BOOT,
                "/probe.js": "hit('CSP_DYNAMIC_EXTERNAL');",
                "/parser.js": "hit('CSP_PARSER_EXTERNAL');",
            }[parts.path]
            self.send(source, "text/javascript; charset=utf-8")
            return
        if parts.path == "/ping":
            self.send("LOCAL_LAB_PING", "text/plain; charset=utf-8")
            return
        if parts.path != "/":
            self.send("Not found", "text/plain; charset=utf-8", 404)
            return
        args = parse_qs(parts.query)
        mode = args.get("mode", ["nonce"])[0]
        modes = ("off", "self", "nonce", "hash", "dynamic", "report", "tt")
        if mode not in modes:
            self.send("Unknown mode", status=400)
            return
        nonce = secrets.token_urlsafe(24)
        headers = []
        if mode != "off":
            name = "Content-Security-Policy-Report-Only" if mode == "report" else "Content-Security-Policy"
            headers.append((name, policy(mode, nonce)))
        query = args.get("q", [""])[0][:2000]
        raw = args.get("render", ["text"])[0] == "raw"
        reflected = query if raw else html.escape(query, quote=True)
        links = " | ".join(f'<a href="/?mode={m}">{m}</a>' for m in modes)
        options = "".join(f'<option{" selected" if m == mode else ""}>{m}</option>' for m in modes)
        if mode in ("off", "self", "report"):
            boot = f'<script nonce="{nonce}" src="/boot.js"></script>'
        else:
            boot = f'<script nonce="{nonce}">{BOOT}</script>'
        names = {
            "text": "Render safe text", "html": "Render unsafe HTML",
            "fragment": "Render URL fragment as HTML", "save": "Save lab marker",
            "load": "Load stored marker as HTML", "clear": "Delete stored lab marker",
            "inline": "Inline script", "external": "Dynamic external script",
            "jsonp": "Load JSONP callback",
            "eval": "eval", "function": "Function constructor",
            "timer": "String timer", "callback": "Callback timer (control)",
            "connect": "Fetch local ping",
        }
        buttons = " ".join(f'<button type="button" data-action="{k}">{v}</button>' for k, v in names.items())
        self.send(f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Harmless CSP / XSS lab</title>
<body><h1>Harmless CSP / XSS lab</h1><nav>{links}</nav>
<p>Mode: {mode}. Reflected output: {"RAW HTML" if raw else "escaped text"}.</p>
<h2>Evidence</h2><div id="results" role="log"></div>
{boot}
<script nonce="{nonce}">hit('CSP_NONCE_MATCH');</script>
<script nonce="incorrect-lab-nonce">hit('CSP_NONCE_WRONG');</script>
<script>{HASH_BODY}</script>
<script>{HASH_BODY} </script>
<script src="/parser.js"></script>
<h2>Reflected input</h2>
<form method="get" action="/">
<label>Policy <select name="mode">{options}</select></label>
<label>Output <select name="render"><option value="text">escaped text</option><option value="raw">raw HTML</option></select></label>
<label>Input <input name="q" maxlength="2000"></label><button>Submit</button>
</form><div id="reflected">{reflected}</div>
<h2>DOM and CSP actions</h2>
<label>Lab payload <textarea id="payload" rows="3" cols="70" maxlength="2000"></textarea></label>
<p>{buttons}</p>
<p><button type="button" onclick="hit('CSP_HANDLER')">Inline handler</button>
<a href="javascript:void(hit('CSP_JS_URL'))">JavaScript URL</a></p>
<div id="sink"></div>
</body></html>''', headers=headers)

if __name__ == "__main__":
    with HTTPServer((HOST, PORT), Handler) as server:
        print(f"Open http://{HOST}:{PORT}/ ; stop with Ctrl+C", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
```

### Lab walkthrough

1. Open `/?mode=off`. Confirm `CSP_BOOT_OK`; the nonce-match, wrong-nonce, hash, and parser-external markers all execute because no CSP is set. The exact and whitespace-changed hash probes use the same marker, so it appears twice.
2. Paste HTML-body probe 2 or 3 into **Reflected input**. Submit once as **escaped text**, then as **raw HTML**. Only the raw version should execute in `off` mode. The form resets the output selector to escaped text on each response; the page states which mode produced the current result.
3. Use **Render unsafe HTML** with the prefilled image-error marker. Compare with **Render safe text**. The safe operation should display literal markup without creating an image element.
4. Use **Save lab marker**, reload, then **Load stored marker as HTML**. This models stored DOM XSS in this browser; it does not simulate a shared server database or a second user's session. Delete the marker when done.
5. To test a fragment source, navigate to the URL below and click **Render URL fragment as HTML**. The fragment is decoded once and is not sent to the server.

```text
http://127.0.0.1:8765/?mode=off#%3Cimg%20src%3D%22data%3Aimage%2Fpng%3Bbase64%2CAA%3D%3D%22%20alt%3D%22lab%22%20onerror%3D%22hit(%27XSS_FRAGMENT_MARKER%27)%22%3E
```

6. Repeat in `self`, `nonce`, `hash`, `dynamic`, `report`, and `tt` modes. Click one action at a time and inspect the marker and any violation. Reload between tests if the evidence becomes cluttered.
7. For the string timer, wait for its asynchronous marker or violation. A callback timer is the positive control and should run in every lab mode.

### Expected CSP results for this exact lab

`Yes` means the marker runs. `No` means it should not. These predictions assume a browser implementing the relevant directives. Record unsupported features as skipped, not passed.

| Probe | off | self | nonce | hash | dynamic | report | tt (1) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `CSP_BOOT_OK` / callback timer | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Correct nonce inline script | Yes | No | Yes | No | Yes | Yes | Yes |
| Incorrect nonce inline script | Yes | No | No | No | No | Yes | No |
| Exact hash script | Yes | No | No | Yes | No | Yes | No |
| Same hash script plus one space | Yes | No | No | No | No | Yes | No |
| Parser-inserted `/parser.js`, no nonce | Yes | Yes | No | No | No | Yes | No |
| Dynamic `/probe.js`, no nonce | Yes | Yes | No | No | Yes | Yes | No |
| Dynamic JSONP callback, no nonce | Yes | Yes | No | No | Yes | Yes | No |
| Parser-inserted JSONP, no nonce (raw input) | Yes | Yes | No | No | No | Yes | No |
| Dynamic inline script, no nonce/hash | Yes | No | No | No | Yes (2) | Yes | No |
| Inline handler / JavaScript URL | Yes | No | No | No | No | Yes | No |
| `eval`, `Function`, string timer | Yes | No | No | No | No | Yes | No |
| Fetch `/ping` | Yes | No | No | No | No | Yes | No |

(1) In `tt` mode, supporting browsers also reject raw strings at covered DOM/script sinks, such as `innerHTML`, with a `TypeError`. This lab permits no Trusted Types policies. Unsupported browsers may still enforce its nonce CSP, so blocked execution alone does not prove Trusted Types enforcement. An HTML source already parsed from the server response is a different path. [MDN: require-trusted-types-for](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/require-trusted-types-for).

Nonce values are generated independently for each response. Hashes cover exact UTF-8 script contents, excluding the surrounding tags. [MDN: script-src](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/script-src).

(2) The current CSP3 Working Draft's matching algorithm permits non-parser-inserted script elements under `strict-dynamic`, including the inline script created by this lab's trusted bootstrap. This was observed in the browser validation below; older implementations can differ. Parser-inserted inline scripts without an accepted nonce/hash and event attributes remain blocked here. Audit trusted script creation paths rather than treating their execution as a bypass. [W3C CSP3: matching elements to source lists](https://www.w3.org/TR/CSP/#match-element-to-source-list).

The `report` mode keeps all these operations executable and records local violation events where supported. It deliberately configures no report collector; it does not test HTTP report delivery. A deployed report pipeline needs configured reporting endpoints and separate verification. Report-only CSP is delivered as a response header, not a meta element. [MDN: Report-Only](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy-Report-Only).

### Validation performed

On 18 October 2026, the updated Python lab extracted from this Markdown was run locally and checked in headless Chrome 155.0.8059.80. All seven modes passed 98 execution assertions, including dynamic and parser-inserted JSONP, plus checks for exact versus changed hashes, safe DOM text, Trusted Types rejection, reflected escaping, fragment rendering, stored-marker reload and deletion, fresh response nonces, and error routes. All five JSONP callback validation cases passed. Python and standalone JavaScript blocks were syntax-checked.

The upload generator produced ten distinct files on Windows. Local HTTP browser checks verified PNG decoding, HTML/SVG markers in document contexts, disabled SVG scripting in image mode, HTML script blocking in a sandboxed frame, and the JavaScript marker loaded as a script source. These were fixture-serving checks, not submissions to a real upload application; acceptance rules, authentication, CSRF, and storage behavior must be checked against your app.

The browser checks triggered the lab's own handlers with CSP enforcement active; they did not enable a CSP bypass. This validates this fixture in that browser. Individual application-context snippets, additional directives, other browsers, and framework/sanitizer-specific behavior require separate testing.

## CSP diagnostics for your own application

### Inspect the response that actually rendered

In the browser Network panel, inspect the final document response after redirects, including both CSP header names and any HTML meta policy. Check authenticated pages, error pages, and alternate routes separately. Multiple enforced policies constrain the document together; one permissive policy does not cancel a stricter one. A fetch made later can receive a different policy or nonce from the original navigation. [MDN: CSP header reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy).

For the local lab, this PowerShell command performs one GET and prints its CSP headers:

```powershell
$response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8765/?mode=nonce'
foreach ($headerName in @('Content-Security-Policy', 'Content-Security-Policy-Report-Only')) {
    Write-Output ($headerName + ': ' + $response.Headers[$headerName])
}
```

### Install an allowed violation observer before your probes

Place this in a script already authorized by your application CSP. An observer that CSP itself blocks cannot collect evidence. This logs only event metadata to the local console, with no network transport:

```javascript
document.addEventListener('securitypolicyviolation', (event) => {
  console.table({
    directive: event.effectiveDirective,
    disposition: event.disposition,
    blocked: event.blockedURI,
    line: event.lineNumber,
    column: event.columnNumber
  });
});
```

Events can be asynchronous and multiple policies can produce multiple violations. Observe browser diagnostics too; correlate one probe at a time. [MDN: securitypolicyviolation event](https://developer.mozilla.org/en-US/docs/Web/API/Element/securitypolicyviolation_event).

### Calculate an exact inline-script hash

Run locally; paste the printed expression into a lab response's `script-src` and use exactly the printed script body between script tags. Even a newline changes the digest.

```python
import base64
import hashlib

body = "console.log('CSP_TEST_HASH_21');"
value = base64.b64encode(hashlib.sha256(body.encode('utf-8')).digest()).decode('ascii')
print("script-src 'sha256-" + value + "'")
print(body)
```

Then change one byte in the HTML script body without updating the header and confirm rejection. The lab already demonstrates this with a trailing space.

## Additional CSP coverage checklist

The runnable lab focuses on script execution and a local fetch. These additional checks need their own controlled fixture or application path; they are not automatically tested by the lab.

| Control | Harmless test and interpretation |
| --- | --- |
| `script-src-elem` vs `script-src-attr` | Compare a script element and a clicked handler. Explicit directives override their fallback for that category. A correct script nonce does not authorize an event attribute. |
| Event-handler hashes | In a disposable policy, hash the exact handler body and compare behavior with/without `'unsafe-hashes'`. Prefer `addEventListener` in application code. |
| `'unsafe-inline'` | Compare a policy without nonces/hashes with the same policy containing a valid nonce/hash source. Do not infer behavior from the keyword's mere presence. |
| `'unsafe-eval'` | In a lab policy only, compare the three fixed string-evaluation actions with and without it. Keep callback timers as controls. |
| `data:` / `blob:` script sources | In a separate lab, serve only a fixed console marker. Compare absent/present scheme permission without `strict-dynamic`; revoke created blob URLs. Other controls may also reject the load. |
| `worker-src` | Load a same-origin worker whose only action is `postMessage('CSP_WORKER_MARKER')`; record its message or violation, then terminate it. Worker creation and the worker's own execution policy are separate concerns. |
| WebAssembly | In applications using Wasm, compile a tiny empty module and compare the intended policy with the restrictive policy. Account for browser support and `'wasm-unsafe-eval'` versus broader `'unsafe-eval'`. |
| `base-uri` | In a disposable document, attempt a `<base href="/lab-base/">` and inspect `document.baseURI`; perform no navigation. |
| `object-src` | Attempt an object embedding a static, same-origin marker page. Confirm the specific violation rather than relying on missing visible content. |
| `frame-src` | Embed a static same-origin child marker page; check whether the parent permits the child load. |
| `frame-ancestors` | Try embedding the protected document from a separate local parent page. This governs who may embed the document, not which children it can load. Test via response headers. |
| `form-action` | Submit a dummy value to a dedicated local endpoint with no persistent effects. Check the destination policy separately from connection policy. |
| `img-src`, `style-src`, `font-src`, `media-src` | Use tiny local assets and compare load success with the matching directive violation. These are resource-control checks, not by themselves XSS evidence. |
| CSP `sandbox` | Compare a dedicated sandboxed document with its unsandboxed control. Avoid broad permissions that invalidate the intended sandbox test. |
| Multiple policies and meta CSP | Compare the actual combined enforcement. A meta policy applies only after it is parsed and supports fewer features. |
| Nonce caching and deployment | Reload separate document responses and verify fresh nonces plus matching intended script tags. Never automatically copy a nonce to every script found in untrusted markup. |
| Reports | Trigger one fixed marker violation and confirm receipt at an owned reporting endpoint. No sensitive query data or script samples are needed. |

Directive fallbacks differ: for example, `frame-ancestors`, `base-uri`, and `form-action` do not inherit `default-src`. For worker loading, check the `worker-src` / `child-src` / `script-src` / `default-src` fallback chain. [MDN: CSP directives](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy). Element/attribute script controls are described in [MDN: script-src-attr](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/script-src-attr).

## Record, repair, and retest

Use this compact record for each source/sink pair:

```text
Test ID:
Application route / local fixture:
Input source and delivery steps:
Output context / sink:
Exact harmless input:
Browser and version:
Enforced CSP and report-only CSP:
Required interaction (click, reload, later view):
Positive control result:
Observed marker / DOM / exception / CSP violation:
Outcome: executed | blocked | reported-only | safe-text | inconclusive | unsupported
Repair and repeat-test result:
Cleanup performed:
```

Repair the unsafe data-to-code transition: use `textContent` for text, context-aware template escaping, validated URL schemes, structured data serialization, and maintained sanitization where HTML is intentional. Add regression cases for the real rendering path. Deploy CSP as a second layer and verify legitimate behavior as well as blocked probes. [OWASP: CSP guidance](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html).
