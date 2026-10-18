"""Persist real parser/sanitizer output, then observe it in an opaque sandbox."""
import json
import re
import secrets

import nh3
from markdown_it import MarkdownIt

from django.conf import settings
from django.http import HttpResponse, JsonResponse

SESSION_KEY = "sanitizer_lesson_v1"
MODES = ("vulnerable", "fixed")
IMAGE = '<img src="data:image/png;base64,AA==" alt="Harmless broken image" onerror="window.sanitizerMark()">'
FIXTURES = {
    "normal": {
        "label": "Control: Markdown formatting", "format": "markdown",
        "source": "**Bold stays** and *emphasis stays*.\n\n- One item\n- Another item\n\n`<tag> stays text`",
        "expectation": "Both stored versions retain bold, emphasis, a list, and literal code. Neither executes a marker.",
    },
    "markdown-html": {
        "label": "Markdown with embedded HTML", "format": "markdown",
        "source": "**Markdown formatting** and *emphasis*.\n\n" + IMAGE,
        "expectation": "The Markdown parser preserves embedded HTML. The unsanitized version executes a harmless image-error marker; the sanitized version keeps formatting and removes the event handler and image URL.",
    },
    "rich-html": {
        "label": "Rich HTML with an event attribute", "format": "html",
        "source": '<p><strong>Rich formatting</strong> and <em>emphasis</em>.</p>' + IMAGE,
        "expectation": "Rich HTML skips Markdown parsing, but still needs HTML sanitization before storage and rendering. The fixed version retains strong/emphasis and removes the event attribute.",
    },
    "encoded": {
        "label": "Control: encoded markup is text", "format": "markdown",
        "source": '**Literal example**\n\n&lt;img src="data:image/png;base64,AA==" onerror="window.sanitizerMark()"&gt;',
        "expectation": "Encoded markup stays visible text in both versions. Neither creates an image element or executes a marker. The app does not decode or compile the stored HTML again.",
    },
}


def sanitizer_metadata():
    return {"mainOrigin": settings.LAB_MAIN_ORIGIN,
            "fixtures": [{"id": key, **value} for key, value in FIXTURES.items()]}


def clean_html(rendered):
    """A small product policy implemented by nh3's maintained HTML parser."""
    return nh3.clean(
        rendered,
        tags={"p", "strong", "em", "ul", "ol", "li", "code", "pre", "blockquote", "br", "img"},
        attributes={"img": {"alt"}},
        clean_content_tags={"script", "style"},
        url_schemes=set(), url_relative="deny", strip_comments=True,
    )


def make_saved(fixture_id):
    fixture = FIXTURES[fixture_id]
    source = fixture["source"]
    rendered = MarkdownIt("commonmark", {"html": True}).render(source) if fixture["format"] == "markdown" else source
    return {
        "run": secrets.token_hex(16), "fixture": fixture_id,
        "source": source, "format": fixture["format"], "rendered": rendered,
        "results": {"vulnerable": {"html": rendered}, "fixed": {"html": clean_html(rendered)}},
        "expectation": fixture["expectation"],
    }


def invalid(reason, status=400):
    return JsonResponse({"error": reason}, status=status)


def method_error(method):
    response = invalid("Use " + method + ".", 405)
    response["Allow"] = method
    return response


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def sanitizer_save(request):
    if request.method != "POST":
        return method_error("POST")
    if request.GET or request.content_type != "application/json":
        return invalid("Use application/json without query parameters.")
    if len(request.body) > 1024:
        return invalid("The fixture request is too large.")
    try:
        body = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return invalid("Invalid JSON or duplicate fields.")
    if not isinstance(body, dict) or set(body) != {"fixture"}:
        return invalid("Provide exactly fixture; arbitrary markup is not accepted.")
    fixture_id = body["fixture"]
    if not isinstance(fixture_id, str) or fixture_id not in FIXTURES:
        return invalid("Choose a listed sanitization fixture.")
    saved = make_saved(fixture_id)
    # Replace this lesson's single pair only; other lessons retain their state.
    request.session[SESSION_KEY] = saved
    return JsonResponse({"saved": saved})


def sanitizer_state(request):
    if request.method != "GET":
        return method_error("GET")
    if request.GET:
        return invalid("This state endpoint has no query parameters.")
    return JsonResponse({"saved": request.session.get(SESSION_KEY)})


OBSERVER = r"""
(() => {
  const config = __CONFIG__;
  let markerCount = 0;
  window.sanitizerMark = () => { markerCount = Math.min(10, markerCount + 1); };
  function observe() {
    const root = document.getElementById('saved-content');
    const elements = [...root.querySelectorAll('*')];
    const evidence = {
      markerCount,
      strongCount: root.querySelectorAll('strong').length,
      emphasisCount: root.querySelectorAll('em').length,
      imageCount: root.querySelectorAll('img').length,
      eventAttributeCount: elements.reduce((n, el) => n + [...el.attributes].filter(a => /^on/i.test(a.name)).length, 0),
      text: root.textContent.slice(0, 1000),
    };
    document.getElementById('observation').textContent = 'Marker executions observed: ' + markerCount;
    parent.postMessage({type: 'sanitizer-observation', run: config.run, mode: config.mode, evidence}, config.mainOrigin);
  }
  addEventListener('load', () => { observe(); setTimeout(observe, 100); setTimeout(observe, 300); }, {once: true});
})();
"""


def sanitizer_frame(request):
    if request.method != "GET":
        return method_error("GET")
    if set(request.GET) != {"run", "mode"} or any(len(request.GET.getlist(key)) != 1 for key in request.GET):
        return invalid("Provide exactly one run and mode.")
    run, mode = request.GET["run"], request.GET["mode"]
    if re.fullmatch(r"[0-9a-f]{32}", run) is None or mode not in MODES:
        return invalid("Invalid saved frame identifier.")
    saved = request.session.get(SESSION_KEY)
    if not saved or saved["run"] != run:
        return invalid("This saved comparison is unavailable in this browser session.", 404)
    config = json.dumps({"run": run, "mode": mode, "mainOrigin": settings.LAB_MAIN_ORIGIN}).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    observer = OBSERVER.replace("__CONFIG__", config)
    document = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Saved sanitization fixture</title>'
        '<style>body{font:14px/1.6 system-ui,sans-serif;margin:20px;color:#203337;overflow-wrap:anywhere}'
        'code{background:#edf3e7;padding:2px 4px}#observation{font-size:12px;color:#597761;border-top:1px solid #dce7d7;padding-top:12px;margin-top:20px}</style>'
        '<script>' + observer + '</script></head><body><article id="saved-content">'
        + saved["results"][mode]["html"]
        + '</article><p id="observation">Waiting for the browser observation.</p></body></html>'
    )
    response = HttpResponse(document, content_type="text/html; charset=utf-8")
    # Identical policies make the sanitizer, rather than CSP, the comparison variable.
    # Response-level sandboxing also applies when this URL is opened directly.
    response["Content-Security-Policy"] = (
        "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; "
        "base-uri 'none'; form-action 'none'; frame-ancestors " + settings.LAB_MAIN_ORIGIN + "; sandbox allow-scripts"
    )
    return response
