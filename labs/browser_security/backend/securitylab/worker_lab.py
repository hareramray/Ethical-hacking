"""Fixed dedicated workers and actual CSP report-uri delivery on loopback only."""
import json
import re
import secrets
import threading
import time
from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

SESSION_KEY = "worker_lesson_v1"
MODES = ("control", "experiment")
MAX_RUNS, MAX_REPORTS, RUN_TTL = 128, 8, 300
RUNS = {}
LOCK = threading.RLock()
FIXTURES = {
    "allow": {"label": "Control: explicitly allow the local worker", "policy": "worker-src 'self'", "expectation": "Both workers return HARMLESS_WORKER_MARKER. No worker-src violation or HTTP report is expected."},
    "enforce": {"label": "Enforce: deny the local worker", "policy": "Content-Security-Policy: worker-src 'none'", "expectation": "The control worker runs. The experiment is blocked, emits a local worker-src event, and sends an enforcement report to Django."},
    "report": {"label": "Report-only: observe without blocking", "policy": "Content-Security-Policy-Report-Only: worker-src 'none'", "expectation": "Both workers run. The experiment emits a report-only event and sends an HTTP report even though HARMLESS_WORKER_MARKER arrives."},
}


def worker_metadata():
    return {"mainOrigin": settings.LAB_MAIN_ORIGIN, "expiresSeconds": RUN_TTL,
            "fixtures": [{"id": key, **value} for key, value in FIXTURES.items()]}


def invalid(reason, status=400):
    return JsonResponse({"error": reason}, status=status)


def method_error(method):
    response = invalid("Use " + method + ".", 405)
    response["Allow"] = method
    return response


def main_origin(view):
    @wraps(view)
    def checked(request, *args, **kwargs):
        if settings.LAB_ROLE != "main":
            return invalid("This lesson belongs to the main lab origin.", 404)
        if request.scheme + "://" + request.get_host() != settings.LAB_MAIN_ORIGIN:
            return invalid("Open this lesson at the configured main lab origin: " + settings.LAB_MAIN_ORIGIN)
        return view(request, *args, **kwargs)
    return checked


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def prune():
    now = time.monotonic()
    for key in list(RUNS):
        if RUNS[key]["expires"] <= now:
            del RUNS[key]


def exact_query(request, fields):
    return set(request.GET) == set(fields) and all(len(request.GET.getlist(field)) == 1 for field in fields)


def valid_run(run):
    return isinstance(run, str) and re.fullmatch(r"[a-f0-9]{32}", run) is not None


def owned(request, run):
    """Call while holding LOCK. Session ownership is not needed by report delivery."""
    prune()
    entry = RUNS.get(run)
    session = request.session.get(SESSION_KEY, {})
    if not isinstance(session, dict) or session.get("run") != run or not entry:
        return None
    return entry if secrets.compare_digest(session.get("owner", ""), entry["owner"]) else None


def paths(run, mode):
    query = urlencode({"run": run, "mode": mode})
    return "/lab/worker/frame/?" + query, "/lab/worker/marker.js?" + query


@main_origin
def worker_prepare(request):
    if request.method != "POST":
        return method_error("POST")
    if request.GET or request.content_type != "application/json" or len(request.body) > 1024:
        return invalid("Use a bounded application/json fixture request without query parameters.")
    try:
        body = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return invalid("Invalid JSON or duplicate fields.")
    if not isinstance(body, dict) or set(body) != {"fixture"} or not isinstance(body["fixture"], str) or body["fixture"] not in FIXTURES:
        return invalid("Choose exactly one listed fixture; arbitrary worker code is not accepted.")
    run, owner = secrets.token_hex(16), secrets.token_hex(16)
    with LOCK:
        prune()
        old = request.session.get(SESSION_KEY, {})
        if isinstance(old, dict):
            RUNS.pop(old.get("run"), None)
        while len(RUNS) >= MAX_RUNS:
            del RUNS[next(iter(RUNS))]
        RUNS[run] = {"owner": owner, "fixture": body["fixture"], "expires": time.monotonic() + RUN_TTL,
                     "modes": {mode: {"cap": secrets.token_hex(24), "reports": [], "policy": None} for mode in MODES}}
    request.session[SESSION_KEY] = {"run": run, "owner": owner}
    return JsonResponse({"run": run, "fixture": body["fixture"]})


OBSERVER = r"""
(() => {
  'use strict';
  const config = __CONFIG__;
  let status = 'waiting', marker = '', errors = 0, events = [];
  const output = document.getElementById('worker-status');
  function publish() {
    output.textContent = marker || status;
    parent.postMessage({type:'worker-observation',run:config.run,mode:config.mode,
      evidence:{status,marker,errors,events:events.slice()}}, config.mainOrigin);
  }
  document.addEventListener('securitypolicyviolation', event => {
    if (event.effectiveDirective !== 'worker-src' || !['enforce','report'].includes(event.disposition)) return;
    if (events.length < 8) events.push({directive:'worker-src',disposition:event.disposition});
    publish();
  });
  let worker;
  const timer = setTimeout(() => { if(status === 'waiting') { status='inconclusive'; publish(); worker?.terminate(); } }, 6000);
  try {
    worker = new Worker(config.workerUrl);
    worker.onmessage = event => {
      if (event.data !== 'HARMLESS_WORKER_MARKER') return;
      status='executed'; marker=event.data; clearTimeout(timer); publish(); worker.terminate();
    };
    worker.onerror = event => { event.preventDefault(); errors=1; status='error'; clearTimeout(timer); publish(); worker.terminate(); };
  } catch (error) { errors=1; status='error'; clearTimeout(timer); publish(); }
  window.addEventListener('pagehide', () => { clearTimeout(timer); worker?.terminate(); }, {once:true});
})();
"""


@main_origin
def worker_frame(request):
    if request.method != "GET":
        return method_error("GET")
    if not exact_query(request, ("run", "mode")) or not valid_run(request.GET["run"]) or request.GET["mode"] not in MODES:
        return invalid("Provide exactly one valid run and mode.")
    run, mode = request.GET["run"], request.GET["mode"]
    with LOCK:
        entry = owned(request, run)
        if entry is None:
            return invalid("This run has expired or belongs to another browser session.", 404)
        fixture = "allow" if mode == "control" else entry["fixture"]
        state = entry["modes"][mode]
        nonce = secrets.token_urlsafe(24)
        report_url = "/api/worker/report/?" + urlencode({"run": run, "mode": mode, "cap": state["cap"]})
        base = ("default-src 'none'; script-src 'nonce-" + nonce + "'; style-src 'nonce-" + nonce + "'; "
                "connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; "
                "frame-ancestors " + settings.LAB_MAIN_ORIGIN + "; sandbox allow-scripts allow-same-origin; ")
        enforced = base + "worker-src " + ("'none'" if fixture == "enforce" else "'self'") + "; report-uri " + report_url
        report_only = "worker-src 'none'; report-uri " + report_url if fixture == "report" else None
        state.update(policy=report_only or enforced, reports=[])
    _, worker_url = paths(run, mode)
    config = json.dumps({"run": run, "mode": mode, "workerUrl": worker_url, "mainOrigin": settings.LAB_MAIN_ORIGIN}).replace("<", "\\u003c")
    document = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Fixed worker fixture</title>'
                '<style nonce="' + nonce + '">body{font:14px/1.6 system-ui,sans-serif;margin:20px;color:#203337;overflow-wrap:anywhere}output{display:block;padding:12px;background:#edf3e7;border-radius:6px}</style>'
                '</head><body><p>Trusted local dedicated worker</p><output id="worker-status">waiting</output>'
                '<script nonce="' + nonce + '">' + OBSERVER.replace("__CONFIG__", config) + '</script></body></html>')
    response = HttpResponse(document, content_type="text/html; charset=utf-8")
    response["Content-Security-Policy"] = enforced
    if report_only:
        response["Content-Security-Policy-Report-Only"] = report_only
    return response


@main_origin
def worker_script(request):
    if request.method != "GET":
        return method_error("GET")
    if not exact_query(request, ("run", "mode")) or not valid_run(request.GET["run"]) or request.GET["mode"] not in MODES:
        return invalid("Provide exactly one valid run and mode.")
    with LOCK:
        if owned(request, request.GET["run"]) is None:
            return invalid("This worker run is unavailable.", 404)
    response = HttpResponse("'use strict'; self.postMessage('HARMLESS_WORKER_MARKER'); self.close();\n", content_type="application/javascript; charset=utf-8")
    response["Content-Security-Policy"] = "default-src 'none'; script-src 'none'; connect-src 'none'; worker-src 'none'"
    return response


@csrf_exempt
@main_origin
def worker_report(request):
    """Browser-protocol callback. Never accepts arbitrary HTML, code, or destinations."""
    if request.method != "POST":
        return method_error("POST")
    if not exact_query(request, ("run", "mode", "cap")) or not valid_run(request.GET["run"]) or request.GET["mode"] not in MODES or re.fullmatch(r"[a-f0-9]{48}", request.GET["cap"]) is None:
        return invalid("Invalid report destination.")
    if request.content_type != "application/csp-report" or len(request.body) > 8192:
        return invalid("Use a bounded application/csp-report document.")
    try:
        body = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return invalid("Invalid report JSON.")
    if not isinstance(body, dict) or set(body) != {"csp-report"} or not isinstance(body["csp-report"], dict):
        return invalid("Expected one csp-report object.")
    report = body["csp-report"]
    allowed = {"document-uri", "referrer", "violated-directive", "effective-directive", "original-policy", "disposition", "blocked-uri", "line-number", "column-number", "source-file", "status-code", "script-sample"}
    required = {"document-uri", "effective-directive", "original-policy", "disposition", "blocked-uri", "status-code"}
    if not required <= set(report) <= allowed:
        return invalid("Unexpected report fields.")
    for key, value in report.items():
        if key in {"line-number", "column-number", "status-code"}:
            if type(value) is not int or not 0 <= value <= 1000000:
                return invalid("Invalid report number.")
        elif not isinstance(value, str) or len(value) > 4096:
            return invalid("Invalid report text.")
    run, mode = request.GET["run"], request.GET["mode"]
    with LOCK:
        prune()
        entry = RUNS.get(run)
        if not entry or not secrets.compare_digest(request.GET["cap"], entry["modes"][mode]["cap"]):
            return invalid("This report destination is unavailable.", 404)
        state = entry["modes"][mode]
        fixture = "allow" if mode == "control" else entry["fixture"]
        frame_url, worker_url = paths(run, mode)
        disposition = "report" if fixture == "report" else "enforce"
        if (fixture == "allow" or state["policy"] is None or report["document-uri"] != settings.LAB_MAIN_ORIGIN + frame_url
                or report["blocked-uri"] != settings.LAB_MAIN_ORIGIN + worker_url or report["effective-directive"] != "worker-src"
                or report["disposition"] != disposition or report["original-policy"] != state["policy"] or report["status-code"] != 200):
            return invalid("The report does not describe this fixed worker policy.")
        if len(state["reports"]) >= MAX_REPORTS:
            return invalid("The report limit for this run has been reached.", 429)
        state["reports"].append({"directive": "worker-src", "disposition": disposition, "blockedPath": "/lab/worker/marker.js", "status": 200})
    return HttpResponse(status=204)


@main_origin
def worker_state(request):
    if request.method != "GET":
        return method_error("GET")
    if not exact_query(request, ("run",)) or not valid_run(request.GET["run"]):
        return invalid("Provide exactly one valid run.")
    with LOCK:
        entry = owned(request, request.GET["run"])
        if entry is None:
            return invalid("This run has expired or belongs to another browser session.", 404)
        data = {mode: {"count": len(entry["modes"][mode]["reports"]), "reports": list(entry["modes"][mode]["reports"])} for mode in MODES}
    return JsonResponse({"run": request.GET["run"], "modes": data})
