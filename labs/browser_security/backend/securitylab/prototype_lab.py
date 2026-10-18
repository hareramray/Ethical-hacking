"""Run bounded JavaScript merges in disposable, opaque browser realms."""
import json
import re
import secrets

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST

SESSION_KEY = "prototype_lesson_v1"
FIXTURES = {
    "normal": {
        "label": "Control: allowed preferences",
        "payload": {"preferences": {"labTheme": "ocean", "fontSize": "large"}},
        "expectation": "Both versions accept the own ocean/large preferences. Object.prototype stays unchanged.",
    },
    "proto": {
        "label": "Inherited preference through __proto__",
        "payload": {"__proto__": {"labTheme": "polluted-marker"}},
        "expectation": "The unsafe merge writes a harmless theme marker onto its frame's Object.prototype. An otherwise empty preference object inherits it. The fixed version rejects the key before copying anything.",
    },
    "constructor": {
        "label": "Inherited preference through constructor.prototype",
        "payload": {"constructor": {"prototype": {"labTheme": "polluted-marker"}}},
        "expectation": "The unsafe merge follows the inherited Object constructor to its prototype. Blocking only __proto__ would miss this route. The fixed version rejects it and keeps the default theme.",
    },
    "mixed": {
        "label": "Allowed preference followed by a dangerous key",
        "payload": {"preferences": {"labTheme": "sunset", "fontSize": "large"}, "__proto__": {"labTheme": "polluted-marker"}},
        "expectation": "The unsafe version both sets an own sunset preference and pollutes Object.prototype. The fixed version validates the entire input first, so rejection leaves even the allowed preference unapplied.",
    },
    "nested": {
        "label": "Dangerous key nested inside preferences",
        "payload": {"preferences": {"__proto__": {"labTheme": "polluted-marker"}}},
        "expectation": "A nested unsafe merge still reaches Object.prototype. The fixed validation checks every nested key before copying allowed preference fields.",
    },
    "invalid-type": {
        "label": "Control: wrong preference type",
        "payload": {"preferences": {"labTheme": "ocean", "fontSize": 42}},
        "expectation": "The unsafe merge stores the number without validation. The fixed version rejects the entire input: no partial ocean preference remains and neither prototype changes.",
    },
}


def fixture_source(fixture_id):
    return json.dumps(FIXTURES[fixture_id]["payload"], indent=2)


def prototype_metadata():
    return {"fixtures": [{"id": key, "label": value["label"], "source": fixture_source(key), "expectation": value["expectation"]} for key, value in FIXTURES.items()]}


def invalid(message, status=400):
    return JsonResponse({"error": message}, status=status)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


@require_POST
def prototype_prepare(request):
    if request.GET or request.content_type != "application/json":
        return invalid("Send application/json without query parameters.")
    if len(request.body) > 1024:
        return invalid("Fixture selection is too large.")
    try:
        data = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeError, RecursionError):
        return invalid("Invalid JSON or duplicate fields.")
    if not isinstance(data, dict) or set(data) != {"fixture"} or not isinstance(data["fixture"], str) or data["fixture"] not in FIXTURES:
        return invalid("Select exactly one listed fixture; arbitrary JSON payloads are not accepted.")
    fixture_id = data["fixture"]
    run = secrets.token_hex(16)
    request.session[SESSION_KEY] = {"run": run, "fixture": fixture_id}
    return JsonResponse({"run": run, "fixture": fixture_id, "source": fixture_source(fixture_id), "expectation": FIXTURES[fixture_id]["expectation"]})


FRAME_SCRIPT = r"""
(() => {
  'use strict';
  const config = __CONFIG__;
  // JSON.parse creates an own __proto__ data property; parsing alone does not pollute.
  const input = JSON.parse(config.source);
  const prototypeBefore = Object.hasOwn(Object.prototype, 'labTheme') ? Object.prototype.labTheme : null;
  const objectLike = value => value !== null && (typeof value === 'object' || typeof value === 'function');
  function unsafeMerge(target, source) {
    for (const key of Object.keys(source)) {
      const value = source[key];
      if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
        // Deliberately follows inherited values, including Object and Object.prototype.
        if (!objectLike(target[key])) target[key] = {};
        unsafeMerge(target[key], value);
      } else target[key] = value;
    }
  }
  function preflight(value) {
    const forbidden = new Set(['__proto__', 'constructor', 'prototype']);
    let keysSeen = 0;
    function scan(node, depth) {
      if (depth > 5) throw new Error('Rejected: nesting limit.');
      if (node === null || typeof node !== 'object') return;
      if (Array.isArray(node)) throw new Error('Rejected: arrays are outside the preference schema.');
      for (const key of Object.keys(node)) {
        if (++keysSeen > 24) throw new Error('Rejected: key limit.');
        if (forbidden.has(key)) throw new Error('Rejected: dangerous key ' + key + '. No preferences were copied.');
        scan(node[key], depth + 1);
      }
    }
    scan(value, 0);
    if (value === null || typeof value !== 'object' || Object.keys(value).join(',') !== 'preferences')
      throw new Error('Rejected: expected exactly preferences.');
    const prefs = value.preferences;
    if (prefs === null || typeof prefs !== 'object' || Array.isArray(prefs))
      throw new Error('Rejected: preferences must be an object.');
    const keys = Object.keys(prefs);
    if (keys.some(key => !['labTheme', 'fontSize'].includes(key)))
      throw new Error('Rejected: unknown preference field.');
    if (Object.hasOwn(prefs, 'labTheme') && !['ocean', 'sunset'].includes(prefs.labTheme))
      throw new Error('Rejected: theme must be an allowed string. No preferences were copied.');
    if (Object.hasOwn(prefs, 'fontSize') && !['normal', 'large'].includes(prefs.fontSize))
      throw new Error('Rejected: font size must be an allowed string. No preferences were copied.');
    return prefs;
  }
  const state = config.mode === 'fixed' ? Object.create(null) : {};
  state.preferences = config.mode === 'fixed' ? Object.create(null) : {};
  let accepted = true;
  let reason = 'Merged without checking inherited targets or input keys and types.';
  try {
    if (config.mode === 'vulnerable') unsafeMerge(state, input);
    else {
      // Full preflight finishes before the first preference assignment.
      const allowed = preflight(input);
      if (Object.hasOwn(allowed, 'labTheme')) state.preferences.labTheme = allowed.labTheme;
      if (Object.hasOwn(allowed, 'fontSize')) state.preferences.fontSize = allowed.fontSize;
      reason = 'Validated all keys and types, then copied allowed own fields into a null-prototype object.';
    }
  } catch (failure) { accepted = false; reason = failure.message; }
  const prefs = state.preferences;
  const themeIsOwn = Object.hasOwn(prefs, 'labTheme');
  const inheritedTheme = !themeIsOwn && 'labTheme' in prefs;
  const evidence = {
    accepted, reason,
    prototypeBefore,
    prototypeAfter: Object.hasOwn(Object.prototype, 'labTheme') ? Object.prototype.labTheme : null,
    preferenceSource: themeIsOwn ? 'own' : inheritedTheme ? 'inherited' : 'default',
    selectedTheme: String(prefs.labTheme ?? 'default'),
    selectedFontSize: String(prefs.fontSize ?? 'normal'),
    fontSizeType: typeof prefs.fontSize,
    ownPreferenceKeys: Object.keys(prefs).sort(),
    nullPrototype: Object.getPrototypeOf(prefs) === null,
    frameOrigin: window.origin,
  };
  document.getElementById('theme').textContent = 'Theme: ' + evidence.selectedTheme;
  document.getElementById('status').textContent = reason;
  document.getElementById('prototype-evidence').textContent = JSON.stringify(evidence, null, 2);
  const report = () => parent.postMessage({type: 'prototype-observation', run: config.run, mode: config.mode, evidence}, config.mainOrigin);
  report();
  setTimeout(report, 100);
})();
"""


@require_GET
def prototype_frame(request):
    if set(request.GET) != {"run", "fixture", "mode"} or any(len(request.GET.getlist(key)) != 1 for key in request.GET):
        return invalid("Provide exactly one run, fixture, and mode.")
    run, fixture_id, mode = request.GET["run"], request.GET["fixture"], request.GET["mode"]
    if not re.fullmatch(r"[0-9a-f]{32}", run) or fixture_id not in FIXTURES or mode not in {"vulnerable", "fixed"}:
        return invalid("Invalid predefined frame selection.")
    if request.session.get(SESSION_KEY) != {"run": run, "fixture": fixture_id}:
        return invalid("Prepare a fresh comparison in this browser session.", 404)
    config = json.dumps({"run": run, "mode": mode, "source": fixture_source(fixture_id), "mainOrigin": settings.LAB_MAIN_ORIGIN})
    config = config.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    nonce = secrets.token_urlsafe(24)
    response = HttpResponse(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Isolated prototype comparison</title>'
        '<style nonce="' + nonce + '">body{font:14px/1.6 system-ui,sans-serif;margin:20px;color:#203337;overflow-wrap:anywhere}'
        'pre{font-size:11px;white-space:pre-wrap;overflow-wrap:anywhere}h1{font-size:18px}</style></head>'
        '<body><h1 id="theme">Waiting for the merge.</h1><p id="status"></p><details><summary>Observed frame state</summary>'
        '<pre id="prototype-evidence"></pre></details><script nonce="' + nonce + '">' + FRAME_SCRIPT.replace("__CONFIG__", config)
        + '</script></body></html>', content_type="text/html; charset=utf-8",
    )
    # The HTTP sandbox persists even when the document is opened directly.
    response["Content-Security-Policy"] = (
        "default-src 'none'; script-src 'nonce-" + nonce + "'; style-src 'nonce-" + nonce + "'; "
        "connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; "
        "frame-ancestors " + settings.LAB_MAIN_ORIGIN + "; sandbox allow-scripts"
    )
    return response
