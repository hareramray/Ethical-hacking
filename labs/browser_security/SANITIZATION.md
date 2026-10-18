# Stored rich-text and Markdown sanitization

This Vue + Django lesson follows formatted input through parsing, sanitization, persistence, and browser rendering. One path stores the parser's HTML unchanged. The fixed path applies an explicit HTML policy using nh3, stores the sanitized result, and renders that stored value without further transformations. The browser measures harmless marker execution and the elements that remain.

Start the [browser security lab](README.md) from the repository root:

```powershell
python labs/browser_security/run_lab.py --setup
python labs/browser_security/run_lab.py
```

`--setup` installs the pinned Markdown and HTML-sanitizer dependencies. Open **http://127.0.0.1:8766/**, select **Sanitization**, choose a fixture, and click **Save and render both versions**. The app reads the saved pair back from Django, then each isolated preview reads its stored HTML from the same browser session.

| Fixture | Stored without sanitization | Sanitized before storage |
| --- | --- | --- |
| Markdown formatting | Preserves strong, emphasis, a list, and literal code | Preserves the same useful formatting |
| Markdown with embedded HTML | Image-error event executes one harmless marker | Removes the event attribute and image URL; preserves formatting |
| Rich HTML with an event attribute | Image-error event executes one harmless marker | Removes the event attribute and image URL; preserves formatting |
| Encoded markup is text | Displays the literal image tag without creating an image element | Displays the same literal text without creating an image element |

The two controls matter: blocking every tag would lose formatting, while decoding the encoded example after sanitization could create fresh markup. Look at **Stored HTML**, the preview, and **Marker executions**, **Strong / emphasis**, **Image elements**, and **Event attributes** together.

## Follow the full pipeline

The [backend implementation](backend/securitylab/sanitizer_lab.py) uses the real Markdown parser:

```python
rendered = MarkdownIt("commonmark", {"html": True}).render(source)
```

The rich-HTML fixture enters at the HTML stage instead. Embedded HTML is deliberately enabled for the Markdown examples so the lesson demonstrates why Markdown parsing alone is insufficient. The parser's [security documentation](https://markdown-it-py.readthedocs.io/en/latest/security.html) describes both strategies: disable embedded HTML, or sanitize the generated HTML when allowing it.

The vulnerable value is `rendered`. The fixed value is produced by the maintained [nh3 HTML sanitizer](https://nh3.readthedocs.io/en/latest/), with a deliberately small product policy:

```python
nh3.clean(
    rendered,
    tags={"p", "strong", "em", "ul", "ol", "li", "code", "pre", "blockquote", "br", "img"},
    attributes={"img": {"alt"}},
    clean_content_tags={"script", "style"},
    url_schemes=set(),
    url_relative="deny",
    strip_comments=True,
)
```

This policy keeps image descriptions but removes image URLs, event attributes, styles, IDs, and other attributes. It does not provide links, arbitrary classes, SVG, or embedded media. Choose a policy around an actual product's needs; the teaching policy is intentionally small. The version pins are in [requirements.txt](requirements.txt), with `markdown-it-py==4.2.0` and `nh3==0.3.7` verified against their [Markdown parser release](https://pypi.org/project/markdown-it-py/4.2.0/) and [sanitizer release](https://pypi.org/project/nh3/0.3.7/).

Both output strings, the source, and a fresh random run identifier are saved under one lesson-specific Django session key. Each save replaces that key; it does not clear other lessons. The session uses the lab's database-backed session configuration, so the browser holds a session identifier rather than the stored HTML itself.

The frame retrieves that saved value and inserts it into the document once. It does not render Markdown again, compile a template from it, unescape entities, or combine it with later untrusted HTML. A read is therefore an actual persistence check, not a repeated simulation that recomputes the expected output.

## Observe persistence and isolation

1. Save **Rich HTML with an event attribute**. The vulnerable frame should report one marker execution; the fixed frame should report zero and retain one strong and one emphasis element.
2. Click **Load saved pair again**. The saved run identifier remains the same, and fresh frames render the stored pair again.
3. Refresh the whole page, then return to the sanitization tab. The run and saved fixture are restored from the same session.
4. Open the lab in a separate private browsing session. It starts without that saved pair.
5. Save **Markdown formatting**. The new random run replaces the old one. A frame URL for the previous run returns 404, even in the original session.

This stores only predefined, bounded fixtures. It is not a public rich-text editor, multi-user document store, or general-purpose HTML testing endpoint.

## Browser evidence and containment

The active examples contain a broken `data:` image and an `onerror` handler that calls a marker function. The marker only increments an in-memory count. It does not read cookies, collect data, make network requests, or navigate.

The trusted observer is installed before the fixture markup. After the frame loads, it inspects the actual DOM and reports counts to the parent. Both previews use the same policy:

```text
default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline';
img-src data:; base-uri 'none'; form-action 'none';
frame-ancestors <configured main origin>; sandbox allow-scripts
```

The inline-script permission lets both the observer and the deliberately vulnerable fixture execute. The policy is identical in the two modes, so sanitization is the changed variable. Do not copy this policy as a production CSP recommendation.

The frame also has `sandbox="allow-scripts"` in the Vue template. It never receives `allow-same-origin`, forms, popups, or top-navigation permissions. The response-level sandbox continues to apply when a frame URL is opened directly. Default resource loading is denied, and only inline styles/scripts and `data:` images are enabled for these finite documents.

The [Vue component](frontend/src/SanitizerLab.vue) accepts observations only from the current frame's `contentWindow`, with the expected opaque origin (`"null"`), matching run and mode, and a bounded exact message shape. A null origin alone is not a trusted identity. This receiver binds the message to a particular frame and run. Source, parser output, and stored HTML appear in the dashboard through Vue text interpolation; none use `v-html`.

The counts are observations for these particular documents during load, not proof that every possible future interaction is safe. The fixtures are predeclared, so their marker cannot forge the observer's report or mutate the parent. This is not a generic hostile-frame telemetry protocol.

## HTTP contract and validation

| Route | Contract |
| --- | --- |
| `POST /api/sanitizer/save/` | Same-origin CSRF protection; JSON containing exactly `fixture`; body at most 1,024 bytes; one of four server-owned fixture IDs |
| `GET /api/sanitizer/state/` | Returns `{saved: null}` or the current session's saved pair; accepts no query parameters |
| `GET /lab/sanitizer/frame/?run=...&mode=...` | Exactly one 32-character hexadecimal run and one `vulnerable`/`fixed` mode; requires the current session's matching saved pair |

Unexpected fields, duplicate JSON keys, raw markup, extra query parameters, stale runs, and other-session runs are rejected. All responses use the lab's no-store headers. The companion origin cannot access this lesson's APIs or frame endpoint.

Run the focused checks from `labs/browser_security`:

```powershell
.venv/Scripts/python.exe backend/manage.py test securitylab.test_sanitizer_lab
```

For browser tests, stop the interactive lab first, then from `labs/browser_security/frontend`:

```powershell
$env:LAB_BROWSER_CHANNEL = 'chrome'
npx playwright test tests/sanitizer.spec.js
```

The [backend tests](backend/securitylab/test_sanitizer_lab.py) exercise real parser/sanitizer output, session persistence and separation, fixture validation, CSRF, and frame headers. The [browser tests](frontend/tests/sanitizer.spec.js) verify actual event execution, preserved formatting, encoded text, page-refresh persistence, direct-navigation sandboxing, stale frame invalidation, and rejection of forged or stale observations.

## What remains outside this lesson

This exercise is not universal sanitizer certification. It does not exhaust mutation XSS, every HTML parser differential, Markdown plugins, CSS sanitization, DOM clobbering, arbitrary URI policies, editable-document frameworks, or downstream transformations. The separate [DOM clobbering lesson](DOM_CLOBBERING.md) demonstrates named-element collisions and explicit-reference repairs. Changes to a sanitizer policy, parser, renderer, or plugin require relevant regression cases. If stored sanitized HTML is retained across policy upgrades, plan how it will be reprocessed or invalidated; this small session fixture does not implement a content migration system.

Continue with the [XSS and CSP examples](../../CSP_XSS_HARMLESS_TESTS.md) and the [browser lab overview](README.md).
