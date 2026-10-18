"""Actual Django rendering of a small, predeclared template fixture set."""
import json

from django.http import JsonResponse
from django.template import Context, Engine

MARKER = "TEMPLATE_CONTEXT_SENTINEL"
FIXED_SOURCE = "Hello, {{ name }}."
FIXTURES = {
    "normal": {"label": "Control: an ordinary name", "input": "Ada", "expectation": "Both render Hello, Ada. The repair preserves ordinary input."},
    "marker": {"label": "Resolve a context variable", "input": "{{ marker }}", "expectation": "Concatenation resolves the synthetic marker. Passing the same text as data preserves the template braces."},
    "conditional": {"label": "Evaluate a condition and filter", "input": "{% if enabled %}{{ marker|lower }}{% endif %}", "expectation": "Concatenation evaluates Django's conditional and lower filter. The fixed template keeps their syntax as literal data."},
    "html": {"label": "Control: HTML text and autoescaping", "input": '<strong id="TEMPLATE_TEXT_ONLY">Ada & Bea</strong>', "expectation": "Literal template source keeps its markup; variable data is HTML-escaped. This dashboard displays both outputs as inert text."},
}
TEMPLATE_METADATA = {
    "engine": "Django template language",
    "fixtures": [{"id": key, **value} for key, value in FIXTURES.items()],
}


def fixture_engine():
    """No filesystem/app loaders, request context, or custom tag libraries."""
    return Engine(dirs=[], app_dirs=False, loaders=[], context_processors=[],
                  libraries={}, builtins=[], debug=False, autoescape=True)


def render_comparison(fixture_id):
    fixture = FIXTURES[fixture_id]
    value = fixture["input"]
    engine = fixture_engine()
    results = {}
    for mode in ("vulnerable", "fixed"):
        context = {"marker": MARKER, "enabled": True}
        if mode == "fixed":
            source = FIXED_SOURCE
            context["name"] = value
        else:
            # Intentionally unsafe construction, bounded by predeclared fixtures.
            source = "Hello, " + value + "."
        rendered = engine.from_string(source).render(Context(context, autoescape=True))
        marker_exposed = MARKER.casefold() in rendered.casefold()
        outcome = "evaluated" if marker_exposed else (
            "unchanged" if rendered == "Hello, " + value + "." else "escaped"
        )
        results[mode] = {
            "source": source, "context": context, "rendered": rendered,
            "markerExposed": marker_exposed, "outcome": outcome,
            "reason": (
                "Input became template source before Django compiled it. HTML autoescaping does not stop template expressions from being evaluated."
                if mode == "vulnerable" else
                "Django compiled a fixed template and received name as context data. The value is not compiled again, and HTML autoescaping remains enabled."
            ),
        }
    return {"fixture": fixture_id, "input": value, "results": results,
            "expectation": fixture["expectation"]}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def template_compare(request):
    """CSRF protection remains enabled; callers select a fixture, never code."""
    def invalid(reason, status=400):
        return JsonResponse({"error": reason}, status=status)

    if request.method != "POST":
        response = invalid("Use POST with a JSON fixture identifier.", 405)
        response["Allow"] = "POST"
        return response
    if request.GET or request.content_type != "application/json":
        return invalid("Use application/json without query parameters.")
    if len(request.body) > 2048:
        return invalid("The fixture request is too large.")
    try:
        body = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return invalid("Invalid JSON or duplicate fields.")
    if not isinstance(body, dict) or set(body) != {"fixture"}:
        return invalid("Provide exactly fixture; template source is not accepted.")
    if not isinstance(body["fixture"], str) or body["fixture"] not in FIXTURES:
        return invalid("Choose a listed template fixture.")
    return JsonResponse(render_comparison(body["fixture"]))
