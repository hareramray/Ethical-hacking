"""Two owned origins: observable CSRF side effects and browser CORS reads."""
import html
import json
import re
import secrets

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.cache import patch_vary_headers
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

SESSION_KEY = "cross_origin_lesson"
RUN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{24,64}$")


def metadata():
    return {"mainOrigin": settings.LAB_MAIN_ORIGIN, "peerOrigin": settings.LAB_PEER_ORIGIN}


def invalid(message, status=400):
    return JsonResponse({"error": message}, status=status)


def valid_query(request, keys):
    return set(request.GET).issubset(keys) and all(len(request.GET.getlist(key)) == 1 for key in request.GET)


def active_run(request):
    if not valid_query(request, {"run"}):
        return None
    run_id = request.GET.get("run", "")
    if not RUN_PATTERN.fullmatch(run_id):
        return None
    saved = request.session.get(SESSION_KEY)
    return saved if saved and secrets.compare_digest(saved["runId"], run_id) else None


@require_POST
def prepare(request):
    if request.scheme + "://" + request.get_host() != settings.LAB_MAIN_ORIGIN:
        return invalid("Open the printed main lab URL for this two-origin exercise.")
    if request.GET or request.content_type != "application/json":
        return invalid("Send an empty JSON object with no query parameters.")
    try:
        body = json.loads(request.body)
    except (ValueError, UnicodeError):
        return invalid("Invalid JSON.")
    if body != {}:
        return invalid("Send an empty JSON object to prepare fresh synthetic counters.")
    saved = {"runId": secrets.token_urlsafe(18), "counts": {"vulnerable": 0, "fixed": 0}}
    request.session[SESSION_KEY] = saved
    return JsonResponse({**saved, **metadata(), "peerUrl": settings.LAB_PEER_ORIGIN + "/peer/"})


@require_GET
def state(request):
    if not valid_query(request, {"run"}):
        return invalid("Use only one run parameter.")
    saved = active_run(request)
    return JsonResponse(saved) if saved else invalid("No active lesson matches this browser session and run.", 404)


def change(request, mode):
    # This is a bounded synthetic counter, never a real account setting. The
    # run identifier is intentionally shared with the peer; it is NOT a CSRF
    # secret and is only a fixture selector within the current session.
    if not valid_query(request, {"run"}):
        return invalid("Use only one run parameter.")
    if request.headers.get("Origin") not in {settings.LAB_MAIN_ORIGIN, settings.LAB_PEER_ORIGIN}:
        return invalid("Use one of the two configured lesson origins.", 403)
    saved = active_run(request)
    if not saved:
        return invalid("No active lesson matches this browser session and run.", 404)
    if request.content_type != "application/x-www-form-urlencoded" or dict(request.POST.lists()) != {"action": ["increment"]}:
        return invalid("Send the single form field action=increment.")
    if saved["counts"][mode] >= 10:
        return invalid("Prepare a new lesson run to reset its bounded counters.", 409)
    saved["counts"][mode] += 1
    request.session[SESSION_KEY] = saved
    return JsonResponse(saved)


@csrf_exempt
@require_POST
def csrf_vulnerable(request):
    # The exemption is deliberately limited to this synthetic lesson route.
    return change(request, "vulnerable")


@require_POST
def csrf_fixed(request):
    # Ordinary Django middleware verifies Origin and the CSRF token first.
    return change(request, "fixed")


@require_GET
def cors_data(request, mode):
    if not valid_query(request, {"run"}):
        return invalid("Use only one run parameter.")
    if mode not in {"vulnerable", "fixed"}:
        return invalid("Unknown policy.")
    saved = active_run(request)
    if not saved:
        return invalid("No active lesson matches this browser session and run.", 404)
    response = JsonResponse({"runId": saved["runId"], "marker": "CORS_SYNTHETIC_SECRET", "synthetic": True})
    origin = request.headers.get("Origin")
    if mode == "vulnerable" and origin == settings.LAB_PEER_ORIGIN:
        response["Access-Control-Allow-Origin"] = origin
        response["Access-Control-Allow-Credentials"] = "true"
    # Fixed mode sends no cross-origin permission. The GET is read-only; lack
    # of ACAO prevents the peer reading its body, not the request being sent.
    patch_vary_headers(response, ["Origin"])
    return response


@require_GET
def peer_page(request):
    if settings.LAB_ROLE != "peer":
        return invalid("This document belongs to the companion origin.", 404)
    run_id, lesson = request.GET.get("run", ""), request.GET.get("lesson", "")
    if not valid_query(request, {"run", "lesson"}) or not RUN_PATTERN.fullmatch(run_id) or lesson not in {"csrf", "cors"}:
        return invalid("Choose an active lesson from the main application.")
    config = html.escape(json.dumps({"runId": run_id, "lesson": lesson, "mainOrigin": settings.LAB_MAIN_ORIGIN}), quote=True)
    response = HttpResponse(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Local companion origin</title>'
        f'<body data-config="{config}"><p id="status">Running the fixed companion script…</p>'
        '<script src="/peer/boot.js"></script></body></html>', content_type="text/html; charset=utf-8",
    )
    response["Content-Security-Policy"] = (
        "default-src 'none'; script-src 'self'; base-uri 'none'; object-src 'none'; form-action 'none'; "
        f"connect-src {settings.LAB_MAIN_ORIGIN}; frame-ancestors {settings.LAB_MAIN_ORIGIN}"
    )
    return response


PEER_SCRIPT = r"""(() => {
  'use strict';
  const config = JSON.parse(document.body.dataset.config);
  async function probe(mode) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    const kind = config.lesson === 'csrf' ? 'change' : 'data';
    const url = config.mainOrigin + '/api/cross-origin/' + kind + '/' + mode + '/?run=' + encodeURIComponent(config.runId);
    try {
      const options = {credentials: 'include', signal: controller.signal};
      if (config.lesson === 'csrf') {
        options.method = 'POST';
        options.body = new URLSearchParams({action: 'increment'});
      }
      const response = await fetch(url, options);
      const body = await response.json();
      return {mode, readable: true, status: response.status,
        marker: typeof body.marker === 'string' ? body.marker : null};
    } catch (_) {
      return {mode, readable: false, status: null, marker: null};
    } finally { clearTimeout(timeout); }
  }
  (async () => {
    // Sequential mutations avoid concurrent saves of the Django session.
    const results = [];
    for (const mode of ['vulnerable', 'fixed']) results.push(await probe(mode));
    document.getElementById('status').textContent = 'Companion requests complete. Inspect the results in the main lab.';
    parent.postMessage({channel: 'cross-origin-lab', runId: config.runId,
      lesson: config.lesson, results}, config.mainOrigin);
  })();
})();"""


@require_GET
def peer_script(request):
    if settings.LAB_ROLE != "peer":
        return invalid("This script belongs to the companion origin.", 404)
    return HttpResponse(PEER_SCRIPT, content_type="text/javascript; charset=utf-8")
