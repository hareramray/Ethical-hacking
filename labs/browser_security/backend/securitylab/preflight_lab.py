"""Real browser preflights against a bounded, session-owned synthetic counter."""
import html
import json
import re
import secrets
import threading
import time
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods

FIXTURES = [
    {"id": "allowed", "label": "Allowed JSON and custom header", "expectation": "Both modes receive OPTIONS, then POST, increment once, and expose the synthetic response to the companion."},
    {"id": "denied-method", "label": "PUT absent from the method allowlist", "expectation": "The broad grant allows PUT. The explicit policy lists POST only, so the browser sends OPTIONS but no actual PUT."},
    {"id": "denied-header", "label": "Extra header absent from the header allowlist", "expectation": "The broad grant allows X-Lab-Extra. The explicit policy omits it, so the actual request never reaches its handler."},
    {"id": "denied-origin", "label": "Companion absent from the origin allowlist", "expectation": "The broad grant permits the companion. The explicit policy permits only the main origin, so its preflight fails."},
    {"id": "missing-response-cors", "label": "Preflight succeeds but actual response omits CORS", "expectation": "Both actual requests increment once. The misconfigured response is unreadable; the corrected response includes the required CORS headers."},
    {"id": "auth-denied", "label": "CORS allowed, application permission denied", "expectation": "Both preflights succeed and both responses are readable. The vulnerable handler skips fictional permission checking; the fixed handler returns 403 and does not mutate."},
]
FIXTURE_IDS = {item["id"] for item in FIXTURES}
RUN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{24}$")
MODES = ("vulnerable", "fixed")
MARKER = "PREFLIGHT_LOCAL_MARKER"
RUN_TTL = 300
MAX_RUNS = 192
_runs = {}
_lock = threading.RLock()


def preflight_metadata():
    return {"fixtures": FIXTURES, "mainOrigin": settings.LAB_MAIN_ORIGIN, "peerOrigin": settings.LAB_PEER_ORIGIN}


def invalid(message, status=400):
    return JsonResponse({"error": message}, status=status)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def valid_query(request, keys):
    return set(request.GET) == keys and all(len(request.GET.getlist(key)) == 1 for key in keys)


def main_request(request):
    return settings.LAB_ROLE == "main" and request.scheme + "://" + request.get_host() == settings.LAB_MAIN_ORIGIN


def peer_request(request):
    return settings.LAB_ROLE == "peer" and request.scheme + "://" + request.get_host() == settings.LAB_PEER_ORIGIN


def prune_runs():
    now = time.monotonic()
    for key in list(_runs):
        if now - _runs[key]["created"] > RUN_TTL:
            del _runs[key]


def find_run(request):
    if not valid_query(request, {"run"}) or not RUN_PATTERN.fullmatch(request.GET["run"]):
        return None
    prune_runs()
    return _runs.get(request.GET["run"])


def owner_matches(request, run):
    return bool(run and request.session.get("preflight_owner") == run["owner"])


@require_POST
def preflight_prepare(request):
    if not main_request(request):
        return invalid("Open the printed main lab URL for this exercise.")
    if request.GET or request.content_type != "application/json":
        return invalid("Send one predefined fixture as JSON without query parameters.")
    if len(request.body) > 256:
        return invalid("Fixture selection is too large.", 413)
    try:
        data = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeError, RecursionError):
        return invalid("Invalid fixture selection.")
    if not isinstance(data, dict) or set(data) != {"fixture"} or not isinstance(data["fixture"], str) or data["fixture"] not in FIXTURE_IDS:
        return invalid("Choose one predefined preflight fixture.")
    owner = request.session.get("preflight_owner")
    if not owner:
        owner = secrets.token_urlsafe(24)
        request.session["preflight_owner"] = owner
    run_id = secrets.token_urlsafe(18)
    with _lock:
        prune_runs()
        if len(_runs) >= MAX_RUNS:
            del _runs[next(iter(_runs))]
        _runs[run_id] = {"owner": owner, "created": time.monotonic(), "fixture": data["fixture"], "modes": {
            mode: {"preflights": 0, "actualRequests": 0, "mutations": 0, "authorization": "not reached", "requestedMethod": None, "requestedHeaders": [], "preflightHadCookie": False}
            for mode in MODES
        }}
    return JsonResponse({"runId": run_id, "fixture": data["fixture"], "harness": settings.LAB_PEER_ORIGIN + "/peer/preflight/?" + urlencode({"run": run_id, "fixture": data["fixture"]}), **preflight_metadata()})


@require_GET
def preflight_state(request):
    if not main_request(request):
        return invalid("This evidence belongs to the main origin.", 404)
    with _lock:
        run = find_run(request)
        if not owner_matches(request, run):
            return invalid("This run expired or belongs to another session. Start a new comparison.", 404)
        return JsonResponse({"runId": request.GET["run"], "fixture": run["fixture"], "modes": run["modes"]})


def cors_headers(response, fixture, mode, preflight=False):
    if not preflight and mode == "vulnerable" and fixture == "missing-response-cors":
        return response
    response["Access-Control-Allow-Origin"] = settings.LAB_MAIN_ORIGIN if mode == "fixed" and fixture == "denied-origin" else settings.LAB_PEER_ORIGIN
    response["Access-Control-Allow-Credentials"] = "true"
    response["Vary"] = "Origin"
    if preflight:
        response["Access-Control-Allow-Methods"] = "POST" if mode == "fixed" and fixture == "denied-method" else "POST, PUT"
        headers = "Content-Type, X-Lab-Marker"
        if not (mode == "fixed" and fixture == "denied-header"):
            headers += ", X-Lab-Extra"
        response["Access-Control-Allow-Headers"] = headers
        response["Access-Control-Max-Age"] = "0"
        response["Vary"] = "Origin, Access-Control-Request-Method, Access-Control-Request-Headers"
    return response


# Only this bounded teaching endpoint is exempt. Preparation retains Django CSRF
# protection; the actual request still requires the owning session, exact peer
# Origin, fixed JSON action and fixed custom marker. OPTIONS has no cookies.
@csrf_exempt
@require_http_methods(["OPTIONS", "POST", "PUT"])
def preflight_probe(request, mode):
    if not main_request(request) or mode not in MODES:
        return invalid("Unknown local preflight endpoint.", 404)
    if request.headers.get("Origin") != settings.LAB_PEER_ORIGIN:
        return invalid("Only the configured companion may initiate this experiment.", 403)
    with _lock:
        run = find_run(request)
        if run is None:
            return invalid("Unknown or expired run.", 404)
        fixture, state = run["fixture"], run["modes"][mode]
        expected_method = "PUT" if fixture == "denied-method" else "POST"
        expected_headers = {"content-type", "x-lab-marker"}
        if fixture == "denied-header":
            expected_headers.add("x-lab-extra")
        if request.method == "OPTIONS":
            requested_headers = request.headers.get("Access-Control-Request-Headers", "")
            if len(requested_headers) > 128 or request.headers.get("Access-Control-Request-Method") != expected_method:
                return invalid("Unexpected preflight shape.")
            header_names = [item.strip().lower() for item in requested_headers.split(",")]
            if set(header_names) != expected_headers or len(header_names) != len(expected_headers):
                return invalid("Unexpected requested headers.")
            if state["preflights"] >= 3:
                return invalid("Start a new comparison to repeat this probe.", 409)
            state["preflights"] += 1
            state["requestedMethod"] = expected_method
            state["requestedHeaders"] = sorted(header_names)
            state["preflightHadCookie"] = bool(request.headers.get("Cookie"))
            return cors_headers(HttpResponse(status=204), fixture, mode, preflight=True)
        if not owner_matches(request, run):
            return invalid("The actual request requires the session that prepared this run.", 403)
        if request.method != expected_method or request.content_type != "application/json" or request.headers.get("X-Lab-Marker") != MARKER:
            return invalid("Unexpected actual request shape.")
        if (fixture == "denied-header" and request.headers.get("X-Lab-Extra") != "fixed-extra") or (fixture != "denied-header" and request.headers.get("X-Lab-Extra") is not None):
            return invalid("Unexpected extra header.")
        if len(request.body) > 128:
            return invalid("Probe body is too large.", 413)
        try:
            data = json.loads(request.body, object_pairs_hook=unique_object)
        except (ValueError, UnicodeError, RecursionError):
            return invalid("Invalid fixed action.")
        if data != {"action": "increment"}:
            return invalid("Only the fixed counter action is available.")
        if state["actualRequests"] >= 1:
            return cors_headers(invalid("This mode already ran. Start a new comparison.", 409), fixture, mode)
        state["actualRequests"] += 1
        denied = fixture == "auth-denied" and mode == "fixed"
        state["authorization"] = "denied" if denied else "skipped (vulnerable)" if fixture == "auth-denied" else "allowed"
        if not denied:
            state["mutations"] += 1
        response = JsonResponse({"marker": MARKER if not denied else "PREFLIGHT_PERMISSION_DENIED", "mutations": state["mutations"]}, status=403 if denied else 200)
        return cors_headers(response, fixture, mode)


@require_GET
def preflight_peer(request):
    if not peer_request(request):
        return invalid("This harness belongs to the companion origin.", 404)
    if not valid_query(request, {"run", "fixture"}) or not RUN_PATTERN.fullmatch(request.GET["run"]) or request.GET["fixture"] not in FIXTURE_IDS:
        return invalid("Choose a predefined comparison from the main lab.")
    config = html.escape(json.dumps({"runId": request.GET["run"], "fixture": request.GET["fixture"], "mainOrigin": settings.LAB_MAIN_ORIGIN}), quote=True)
    response = HttpResponse('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Local preflight companion</title></head>'
        f'<body data-config="{config}"><p id="status">Running two real browser requests...</p><script src="/peer/preflight/boot.js"></script></body></html>', content_type="text/html; charset=utf-8")
    response["Content-Security-Policy"] = f"default-src 'none'; script-src 'self'; connect-src {settings.LAB_MAIN_ORIGIN}; frame-ancestors {settings.LAB_MAIN_ORIGIN}; base-uri 'none'; object-src 'none'; form-action 'none'; sandbox allow-scripts allow-same-origin"
    return response


PEER_SCRIPT = r"""(() => {
  'use strict';
  const config = JSON.parse(document.body.dataset.config);
  let stopped = false, activeController;
  window.addEventListener('pagehide', () => { stopped = true; activeController?.abort(); }, {once: true});
  async function probe(mode) {
    const controller = new AbortController();
    activeController = controller;
    const timer = setTimeout(() => controller.abort(), 6000);
    try {
      const headers = {'Content-Type': 'application/json', 'X-Lab-Marker': 'PREFLIGHT_LOCAL_MARKER'};
      if (config.fixture === 'denied-header') headers['X-Lab-Extra'] = 'fixed-extra';
      const response = await fetch(config.mainOrigin + '/api/preflight/probe/' + mode + '/?run=' + encodeURIComponent(config.runId), {
        method: config.fixture === 'denied-method' ? 'PUT' : 'POST', headers,
        credentials: 'include', body: JSON.stringify({action: 'increment'}), signal: controller.signal,
      });
      const body = await response.json();
      return {readable: true, status: response.status, marker: typeof body.marker === 'string' ? body.marker : null, outcome: 'response'};
    } catch (error) {
      return {readable: false, status: null, marker: null, outcome: error.name === 'AbortError' ? 'timeout' : 'fetch-error'};
    } finally { clearTimeout(timer); }
  }
  (async () => {
    for (const mode of ['vulnerable', 'fixed']) {
      if (stopped) return;
      const result = await probe(mode);
      if (stopped) return;
      parent.postMessage({channel: 'preflight-lesson-result', runId: config.runId, fixture: config.fixture, mode, result}, config.mainOrigin);
    }
    document.getElementById('status').textContent = 'Requests complete. Compare browser readability with the main server evidence above.';
  })();
})();"""


@require_GET
def preflight_peer_script(request):
    if not peer_request(request):
        return invalid("This script belongs to the companion origin.", 404)
    if request.GET:
        return invalid("This fixed script has no parameters.")
    return HttpResponse(PEER_SCRIPT, content_type="text/javascript; charset=utf-8")
