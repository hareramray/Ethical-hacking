"""Real named DOM access in an opaque, network-free comparison document."""
import json
import re
import secrets

from django.conf import settings
from django.http import HttpResponse, JsonResponse

SESSION_KEY = "clobber_lesson_v1"
MODES = ("vulnerable", "fixed")
FIXTURES = {
    "normal": {
        "label": "Control: ordinary note markup",
        "source": '<p>A formatted <strong>ordinary note</strong>.</p>',
        "placement": "note content",
        "expectation": "Both versions show Standard view and method post. The legitimate note field still works. No named-property collision is present.",
    },
    "named-config": {
        "label": "Named form replaces a window config fallback",
        "source": '<form id="labConfig"><input name="preview" value="true" aria-label="Fixture preview value"></form>',
        "placement": "note content",
        "expectation": "window.labConfig becomes an HTMLFormElement and its preview property becomes an HTMLInputElement. The vulnerable truthiness check enables Preview mode; the fixed lexical configuration retains Standard view.",
    },
    "form-property": {
        "label": "Named input shadows a form property",
        "source": '<input name="method" value="HARMLESS_METHOD_MARKER" aria-label="Fixture method value">',
        "placement": "inside the existing note form",
        "expectation": "The input named method shadows the form.method string with an HTMLInputElement. The vulnerable label displays that object type; the fixed version reads and validates the explicit method attribute, preserving post.",
    },
}


def clobber_metadata():
    return {"mainOrigin": settings.LAB_MAIN_ORIGIN,
            "fixtures": [{"id": key, **value} for key, value in FIXTURES.items()]}


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


def clobber_prepare(request):
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
    fixture = body["fixture"]
    if not isinstance(fixture, str) or fixture not in FIXTURES:
        return invalid("Choose a listed DOM clobbering fixture.")
    run = {"run": secrets.token_hex(16), "fixture": fixture}
    request.session[SESSION_KEY] = run
    return JsonResponse(run)


OBSERVER = r"""
(() => {
  'use strict';
  const run = __CONFIG__;
  const trustedConfig = Object.freeze({preview: false});
  const form = document.querySelector('form[data-owned-form="note"]');
  const note = form.querySelector('input[data-owned-note]');
  const typeOf = value => value === undefined ? 'undefined' : Object.prototype.toString.call(value).slice(8, -1);
  const namedConfig = window.labConfig;
  const methodProperty = form.method;
  const collision = namedConfig instanceof HTMLElement || methodProperty instanceof HTMLElement;
  let previewEnabled, method, noteText;
  if (run.mode === 'vulnerable') {
    // A truthy named element replaces the intended plain configuration object.
    const selectedConfig = window.labConfig || trustedConfig;
    previewEnabled = Boolean(selectedConfig.preview);
    // Named form controls can take precedence over this built-in property.
    method = String(form.method);
    noteText = form.elements.namedItem('note').value;
  } else {
    // Keep trusted data lexical and read this application's explicit DOM contract.
    previewEnabled = trustedConfig.preview === true;
    if (!(form instanceof HTMLFormElement) || !(note instanceof HTMLInputElement) || note.type !== 'text') {
      throw new Error('The owned note form has an unexpected shape.');
    }
    const attribute = form.getAttribute('method');
    method = attribute === 'post' ? attribute : 'invalid';
    noteText = note.value.slice(0, 80);
  }
  const label = (previewEnabled ? 'Preview mode' : 'Standard view') + ' | method: ' + method;
  const output = document.getElementById('observed-label');
  output.textContent = label;
  document.getElementById('observed-note').textContent = noteText;
  const evidence = {
    namedConfigType: typeOf(namedConfig),
    previewPropertyType: typeOf(namedConfig?.preview),
    formMethodType: typeOf(methodProperty),
    collision, previewEnabled, method,
    label: output.textContent, note: document.getElementById('observed-note').textContent,
  };
  parent.postMessage({type: 'clobber-observation', run: run.run, mode: run.mode, evidence}, run.mainOrigin);
})();
"""


def clobber_frame(request):
    if request.method != "GET":
        return method_error("GET")
    if set(request.GET) != {"run", "fixture", "mode"} or any(len(request.GET.getlist(key)) != 1 for key in request.GET):
        return invalid("Provide exactly one run, fixture, and mode.")
    run, fixture, mode = request.GET["run"], request.GET["fixture"], request.GET["mode"]
    if re.fullmatch(r"[0-9a-f]{32}", run) is None or fixture not in FIXTURES or mode not in MODES:
        return invalid("Invalid comparison identifier.")
    if request.session.get(SESSION_KEY) != {"run": run, "fixture": fixture}:
        return invalid("This comparison is unavailable in this browser session.", 404)
    nonce = secrets.token_urlsafe(24)
    config = json.dumps({"run": run, "mode": mode, "mainOrigin": settings.LAB_MAIN_ORIGIN}).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    content = FIXTURES[fixture]["source"] if fixture != "form-property" else '<p>An ordinary note with an extra form control below.</p>'
    form_extra = FIXTURES[fixture]["source"] if fixture == "form-property" else ""
    document = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>DOM clobbering fixture</title>'
        '<style nonce="' + nonce + '">body{font:14px/1.6 system-ui,sans-serif;margin:20px;color:#203337;overflow-wrap:anywhere}'
        'input{box-sizing:border-box;display:block;max-width:100%;padding:6px;margin:6px 0;border:1px solid #b8cdbb;border-radius:4px}'
        '#observed-label{padding:12px;background:#edf3e7;border-radius:6px}label{display:block;font-size:12px}</style></head><body>'
        '<article data-note-content>' + content + '</article>'
        '<form data-owned-form="note" method="post"><label>Legitimate note field'
        '<input data-owned-note name="note" type="text" value="Hello from a scoped field" readonly></label>'
        + form_extra + '</form><p id="observed-label">Waiting for observation.</p><p id="observed-note"></p>'
        '<script nonce="' + nonce + '">' + OBSERVER.replace("__CONFIG__", config) + '</script></body></html>'
    )
    response = HttpResponse(document, content_type="text/html; charset=utf-8")
    response["Content-Security-Policy"] = (
        "default-src 'none'; script-src 'nonce-" + nonce + "'; style-src 'nonce-" + nonce + "'; "
        "connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; "
        "frame-ancestors " + settings.LAB_MAIN_ORIGIN + "; sandbox allow-scripts"
    )
    return response
