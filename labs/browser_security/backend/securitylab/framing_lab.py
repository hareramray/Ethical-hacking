"""Fixed local documents demonstrate browser-enforced framing policies."""
import html
import json
import re
import secrets
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST

FIXTURES = [
    {"id": "csp-self", "label": "CSP: same-origin ancestors only", "expectation": "The unprotected target loads. The fixed target's frame-ancestors 'self' rejects the companion ancestor, even though the top dashboard shares the target's origin."},
    {"id": "xfo-sameorigin", "label": "X-Frame-Options: SAMEORIGIN", "expectation": "The unprotected target loads. The fixed target rejects the cross-origin companion with X-Frame-Options: SAMEORIGIN. Its CSP deliberately omits frame-ancestors to test XFO separately."},
    {"id": "allowed-integration", "label": "CSP: explicitly allowed integration", "expectation": "Both targets load. The fixed target permits both exact ancestor origins. An allowed embedder can still overlay the target, so allowlist only trusted integrations."},
]
FIXTURE_IDS = {item["id"] for item in FIXTURES}
RUN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{24}$")
BASE_POLICY = "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; object-src 'none'; form-action 'none'; sandbox allow-scripts allow-same-origin"


def framing_metadata():
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


def config_from_request(request):
    if set(request.GET) != {"run", "fixture", "mode"} or any(len(request.GET.getlist(key)) != 1 for key in request.GET):
        return None
    if not RUN_PATTERN.fullmatch(request.GET["run"]) or request.GET["fixture"] not in FIXTURE_IDS or request.GET["mode"] not in {"vulnerable", "fixed"}:
        return None
    return {"runId": request.GET["run"], "fixture": request.GET["fixture"], "mode": request.GET["mode"], "mainOrigin": settings.LAB_MAIN_ORIGIN, "peerOrigin": settings.LAB_PEER_ORIGIN}


@require_POST
def framing_prepare(request):
    if settings.LAB_ROLE != "main" or request.scheme + "://" + request.get_host() != settings.LAB_MAIN_ORIGIN:
        return invalid("Open the printed main lab URL for this two-origin exercise.")
    if request.GET or request.content_type != "application/json":
        return invalid("Send one fixture identifier as JSON, without query parameters.")
    if len(request.body) > 256:
        return invalid("Fixture selection is too large.", 413)
    try:
        data = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeError, RecursionError):
        return invalid("Invalid JSON fixture selection.")
    if not isinstance(data, dict) or set(data) != {"fixture"} or not isinstance(data["fixture"], str) or data["fixture"] not in FIXTURE_IDS:
        return invalid("Select a predefined framing fixture.")
    run_id = secrets.token_urlsafe(18)
    harnesses = {mode: settings.LAB_PEER_ORIGIN + "/peer/framing/?" + urlencode({"run": run_id, "fixture": data["fixture"], "mode": mode}) for mode in ("vulnerable", "fixed")}
    return JsonResponse({"runId": run_id, "fixture": data["fixture"], "harnesses": harnesses, **framing_metadata()})


def document(config, title, script, body, style):
    return HttpResponse(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>' + title + '</title><style>' + style + '</style></head>'
        '<body data-config="' + html.escape(json.dumps(config), quote=True) + '">' + body + '<script src="' + script + '"></script></body></html>',
        content_type="text/html; charset=utf-8",
    )


@require_GET
def framing_peer(request):
    if settings.LAB_ROLE != "peer":
        return invalid("This harness belongs to the companion origin.", 404)
    config = config_from_request(request)
    if config is None:
        return invalid("Choose a predefined framing fixture from the main lab.")
    response = document(config, "Harmless framing overlay demonstration", "/peer/framing/boot.js",
        '<p class="notice">Local practice only. The pretend label below covers a real counter button.</p>'
        '<label><input id="overlay-toggle" type="checkbox" checked> Show pretend label</label>'
        '<div id="stage"><iframe id="target" title="Main-origin practice counter"></iframe><div id="pretend" aria-hidden="true">Pretend label: preview a card</div></div>'
        '<p id="status" role="status">Waiting for target readiness.</p>',
        'body{font:14px/1.45 system-ui,sans-serif;margin:12px;color:#24384c}*{box-sizing:border-box}.notice{margin:0 0 10px}label{display:block;margin-bottom:10px}#stage{position:relative}#target{display:block;width:100%;height:140px;border:1px solid #b3bfd0;border-radius:8px}#pretend{position:absolute;top:1px;left:1px;right:1px;height:72px;background:#e4eeffff;color:#20365a;display:flex;align-items:center;justify-content:center;text-align:center;padding:8px;pointer-events:none;border-radius:8px 8px 0 0}#pretend[hidden]{display:none}#status{margin:10px 0 0;overflow-wrap:anywhere}')
    response["Content-Security-Policy"] = BASE_POLICY + f"; frame-src {settings.LAB_MAIN_ORIGIN}; frame-ancestors {settings.LAB_MAIN_ORIGIN}"
    return response


@require_GET
def framing_target(request):
    if settings.LAB_ROLE != "main":
        return invalid("This target belongs to the main origin.", 404)
    config = config_from_request(request)
    if config is None:
        return invalid("Choose a predefined framing target from the main lab.")
    response = document(config, "Harmless practice counter target", "/lab/framing/target.js",
        '<button id="practice" type="button">Practice action: increment local counter</button><p>Local clicks: <output id="clicks">0</output></p>',
        'body{font:14px/1.4 system-ui,sans-serif;margin:0;color:#24384c}*{box-sizing:border-box}button{width:100%;height:72px;border:0;background:#e4fff0;color:#164732;font:600 14px/1.3 system-ui,sans-serif;padding:10px;cursor:pointer}button:focus-visible{outline:3px solid #2957c8;outline-offset:-4px}p{padding:0 12px}')
    policy = BASE_POLICY
    if config["mode"] == "fixed":
        if config["fixture"] == "csp-self":
            policy += "; frame-ancestors 'self'"
        elif config["fixture"] == "xfo-sameorigin":
            response["X-Frame-Options"] = "SAMEORIGIN"
        else:
            policy += f"; frame-ancestors {settings.LAB_MAIN_ORIGIN} {settings.LAB_PEER_ORIGIN}"
    response["Content-Security-Policy"] = policy
    return response


PEER_SCRIPT = r"""(() => {
  'use strict';
  const config = JSON.parse(document.body.dataset.config);
  const target = document.getElementById('target');
  const status = document.getElementById('status');
  let ready = false, clicks = 0;
  function exact(data, keys) {
    return data !== null && typeof data === 'object' && !Array.isArray(data)
      && Object.keys(data).sort().join(',') === keys.sort().join(',');
  }
  function report(trustedClick) {
    parent.postMessage({channel: 'framing-lesson-result', runId: config.runId, fixture: config.fixture, mode: config.mode,
      result: {outcome: ready ? 'ready' : 'no-readiness', ready, clicks, trustedClick}}, config.mainOrigin);
  }
  const timer = setTimeout(() => {
    if (ready) return;
    status.textContent = 'No target readiness observed. Check response headers and the browser console; absence alone does not prove blocking.';
    report(false);
  }, 2500);
  window.addEventListener('message', event => {
    const data = event.data;
    if (event.source !== target.contentWindow || event.origin !== config.mainOrigin
        || !exact(data, ['channel', 'runId', 'mode', 'clicks', 'trustedClick'])
        || data.channel !== 'framing-target-state' || data.runId !== config.runId || data.mode !== config.mode
        || !Number.isInteger(data.clicks) || data.clicks < clicks || data.clicks > 20
        || typeof data.trustedClick !== 'boolean' || data.trustedClick !== (data.clicks > 0)) return;
    clearTimeout(timer);
    ready = true;
    clicks = data.clicks;
    status.textContent = clicks ? `Target observed ${clicks} trusted click(s). Only its local counter changed.` : 'Target ready. Click the pretend label, then hide it to reveal the actual button.';
    report(data.trustedClick);
  });
  document.getElementById('overlay-toggle').addEventListener('change', event => {
    document.getElementById('pretend').hidden = !event.target.checked;
  });
  window.addEventListener('pagehide', () => clearTimeout(timer), {once: true});
  target.src = config.mainOrigin + '/lab/framing/target/?' + new URLSearchParams({run: config.runId, fixture: config.fixture, mode: config.mode});
})();"""

TARGET_SCRIPT = r"""(() => {
  'use strict';
  const config = JSON.parse(document.body.dataset.config);
  let clicks = 0;
  function report(trustedClick) {
    parent.postMessage({channel: 'framing-target-state', runId: config.runId, mode: config.mode, clicks, trustedClick}, config.peerOrigin);
  }
  document.getElementById('practice').addEventListener('click', event => {
    if (!event.isTrusted || clicks >= 20) return;
    clicks += 1;
    document.getElementById('clicks').textContent = String(clicks);
    report(true);
  });
  report(false);
})();"""


@require_GET
def framing_peer_script(request):
    if settings.LAB_ROLE != "peer":
        return invalid("This script belongs to the companion origin.", 404)
    if request.GET:
        return invalid("The fixed script does not accept parameters.")
    return HttpResponse(PEER_SCRIPT, content_type="text/javascript; charset=utf-8")


@require_GET
def framing_target_script(request):
    if settings.LAB_ROLE != "main":
        return invalid("This script belongs to the main origin.", 404)
    if request.GET:
        return invalid("The fixed script does not accept parameters.")
    return HttpResponse(TARGET_SCRIPT, content_type="text/javascript; charset=utf-8")
