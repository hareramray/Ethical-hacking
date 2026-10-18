# Server-side template injection: runnable Django lesson

This lesson compares concatenating input into template source with passing the same input as context data. Both handlers actually compile and render Django templates. A synthetic context marker makes evaluation observable; the exercise has no request objects, application records, or file templates.

Start the [Vue + Django lab](README.md) from the repository root:

```powershell
python labs/browser_security/run_lab.py
```

Open **http://127.0.0.1:8766/**, select **Template injection**, and choose a fixture. Click **Compare rendering** to see the source, context, and rendered text from both handlers.

| Fixture | Input compiled as source | Input passed as data |
| --- | --- | --- |
| Ordinary name: `Ada` | `Hello, Ada.` | `Hello, Ada.` |
| Context variable: `{{ marker }}` | Resolves `TEMPLATE_CONTEXT_SENTINEL` | Keeps the template expression literally |
| Conditional with the `lower` filter | Evaluates the condition and renders the lowercase marker | Keeps the conditional and filter syntax literally |
| HTML text | Keeps literal markup in template source | Escapes markup supplied through the variable |

The marker is also shown in the teaching context. The observation is whether the **rendered text** resolves it. Every result is displayed through Vue text interpolation, so even the HTML control creates no dashboard elements.

## The repair

The [handler](backend/securitylab/template_lab.py) uses this intentionally vulnerable construction with a predeclared fixture value:

```python
source = "Hello, " + value + "."
rendered = engine.from_string(source).render(Context(context, autoescape=True))
```

For the marker fixture, the compiled source becomes `Hello, {{ marker }}.`. The supplied expression is part of the template program and resolves a context value. HTML autoescaping remains enabled; it does not prevent template syntax from being evaluated. The [OWASP prevention guidance](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Template_Injection_Prevention_Cheat_Sheet.html) recommends keeping untrusted input out of template source.

The fixed handler keeps the template constant and passes input through a named variable:

```python
source = "Hello, {{ name }}."
context["name"] = value
rendered = engine.from_string(source).render(Context(context, autoescape=True))
```

Django compiles the source, then renders it with a context. Context values are not recursively compiled as templates, and autoescaping applies to variable output. See [Django's template API](https://docs.djangoproject.com/en/6.0/ref/templates/api/). This lesson uses Django template syntax: a variable expression, an `if` tag, and the `lower` filter. Jinja-style `{{ 7*7 }}` is not valid Django template syntax, so an arithmetic probe alone would be misleading here.

The HTML fixture illustrates a separate issue. Markup inserted into template source remains markup; the same text provided as data is escaped. The dashboard shows the rendered strings as text to make this difference visible. A CSP setting does not repair the server-side compilation boundary.

## API and boundaries

The UI sends `POST /api/template/compare/` with JSON containing exactly `{"fixture":"marker"}` (or `normal`, `conditional`, `html`). Django CSRF protection remains enabled. Valid comparisons return HTTP 200 with `fixture`, `input`, `expectation`, and `results.vulnerable` / `results.fixed`. Each result contains `source`, `context`, `rendered`, `markerExposed`, `outcome`, and `reason`.

`outcome` describes the actual rendered output: `evaluated` when it resolves the marker, `escaped` when variable escaping changes the input text, or `unchanged` when the greeting preserves it. Unsupported identifiers, arbitrary source, extra or duplicate fields, query parameters, malformed JSON, and bodies over 2,048 bytes are rejected with HTTP 400. Missing CSRF validation produces HTTP 403; unsupported methods produce HTTP 405.

Only four short server-owned fixtures can reach compilation. Each comparison uses an explicitly configured `Engine` without filesystem or app template loaders, request context processors, or custom tag libraries. Context entries are fixed strings and a boolean, with the selected string added as `name` in the fixed branch. Django's built-in template tags and filters remain available; this configuration is **not a general sandbox for arbitrary template source**. Fixture selection is the exercise boundary. Keeping user input out of compiled template source is the repair being taught.

This lesson demonstrates expression evaluation and a synthetic context disclosure. It does not claim that this fixture permits remote code execution or that every template engine uses Django's syntax and security model.

## Verification

The [backend tests](backend/securitylab/test_template_lab.py) exercise actual rendering, a successful ordinary name, marker resolution, condition/filter execution, HTML escaping, unavailable loaders/custom libraries, input rejection before compilation, and CSRF. The [browser tests](frontend/tests/template.spec.js) compare the displayed evidence, clear prior evidence on fixture changes, and confirm inert HTML output.

Stop both lab servers on ports 8766 and 8767 before running the full suite:

```powershell
$env:LAB_BROWSER_CHANNEL = 'chrome'
python labs/browser_security/run_lab.py --test
Remove-Item Env:LAB_BROWSER_CHANNEL
```

Record the selected input, the two compiled sources, the rendered outputs, and which boundary changed. Repeat the ordinary-name control to show that the repair preserves intended behavior. Each comparison is independent and needs no reset.
