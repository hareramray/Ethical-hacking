"""Fixed TrustedHTML policy comparisons in opaque, network-restricted frames."""
import base64
import hashlib
import json
import re
import secrets
import time
from functools import wraps

from django.conf import settings
from django.http import HttpResponse, JsonResponse

SESSION_KEY = "trusted_lesson_v1"
RUN_TTL = 300
MODES = ("vulnerable", "fixed")
SANITIZER_VERSION = "3.4.16"
HANDLER = "document.getElementById('event-marker').textContent='HARMLESS_TT_MARKER'"
HANDLER_HASH = base64.b64encode(hashlib.sha256(HANDLER.encode()).digest()).decode()
FIXTURES = {
    "formatting": {"label": "Positive control: keep useful formatting", "html": "<p>Hello <strong>reader</strong>, keep <em>useful</em> <code>formatting</code>.</p>", "expectation": "Both named policies produce TrustedHTML accepted by innerHTML. Strong, emphasis, and code elements remain."},
    "text": {"label": "Inert text: encoded markup stays text", "html": "&lt;strong&gt;just text&lt;/strong&gt;", "expectation": "Both policies preserve literal <strong> text without creating a strong element or running a marker."},
    "event": {"label": "Harmless event: pass-through versus sanitizer", "html": '<p>Keep <strong>reader</strong>.</p><img src="data:," onerror="' + HANDLER + '">', "expectation": "Both policies produce accepted TrustedHTML. The pass-through image sets HARMLESS_TT_MARKER; DOMPurify removes the image and event attribute while retaining strong formatting."},
    "raw-string": {"label": "Sink guard: reject a raw string", "html": "<strong>raw string control</strong>", "expectation": "Both enforced frames reject a raw string at innerHTML with TypeError. No policy conversion or HTML rendering occurs."},
    "forbidden-policy": {"label": "Policy guard: reject an unlisted name", "html": "<strong>forbidden policy control</strong>", "expectation": "Both frames reject createPolicy('lab-forbidden'). The innerHTML assignment is never attempted."},
}


def trusted_metadata():
    return {"mainOrigin": settings.LAB_MAIN_ORIGIN, "expiresSeconds": RUN_TTL,
            "sanitizer": "DOMPurify " + SANITIZER_VERSION,
            "fixtures": [{"id": key, **value} for key, value in FIXTURES.items()]}


def invalid(reason, status=400):
    return JsonResponse({"error": reason}, status=status)


def main_origin(view):
    @wraps(view)
    def checked(request, *args, **kwargs):
        if settings.LAB_ROLE != "main":
            return invalid("This lesson belongs to the main lab origin.", 404)
        if request.scheme + "://" + request.get_host() != settings.LAB_MAIN_ORIGIN:
            return invalid("Open this lesson at the configured main lab origin: " + settings.LAB_MAIN_ORIGIN)
        return view(request, *args, **kwargs)
    return checked


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


@main_origin
def trusted_prepare(request):
    if request.method != "POST":
        return method_error("POST")
    if request.GET or request.content_type != "application/json" or len(request.body) > 1024:
        return invalid("Use a bounded application/json fixture request without query parameters.")
    try:
        body = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return invalid("Invalid JSON or duplicate fields.")
    if not isinstance(body, dict) or set(body) != {"fixture"} or not isinstance(body["fixture"], str) or body["fixture"] not in FIXTURES:
        return invalid("Choose exactly one listed fixture; arbitrary HTML and policy code are not accepted.")
    run = secrets.token_hex(16)
    request.session[SESSION_KEY] = {"run": run, "fixture": body["fixture"], "expires": time.time() + RUN_TTL}
    return JsonResponse({"run": run, "fixture": body["fixture"]})


OBSERVER = r"""
(() => {
  'use strict';
  const config = __CONFIG__;
  const target = document.getElementById('fixture-output');
  const marker = document.getElementById('event-marker');
  const evidence = {status:'complete',rawGuard:'not-tested',policy:'not-attempted',sink:'not-attempted',trusted:false,formatting:false,text:'',marker:'',events:[],detail:''};
  const allowedEvents = ['require-trusted-types-for','trusted-types','script-src-attr'];
  let finished = false, timer;
  function publish() {
    evidence.formatting = !!target.querySelector('strong');
    evidence.text = target.textContent.slice(0,400);
    evidence.marker = marker.textContent === 'HARMLESS_TT_MARKER' ? marker.textContent : '';
    document.getElementById('frame-status').textContent = evidence.detail;
    parent.postMessage({type:'trusted-observation',run:config.run,mode:config.mode,evidence:{...evidence,events:evidence.events.slice()}},config.mainOrigin);
  }
  document.addEventListener('securitypolicyviolation', event => {
    if (event.disposition === 'enforce' && allowedEvents.includes(event.effectiveDirective) && evidence.events.length < 8) {
      evidence.events.push(event.effectiveDirective);
      if (finished) publish();
    }
  });
  function finish() { finished = true; publish(); }
  try {
    if (!window.trustedTypes || typeof trustedTypes.createPolicy !== 'function') {
      evidence.status='unsupported'; evidence.detail='Trusted Types API unavailable; no unprotected fixture was inserted.'; finish(); return;
    }
    // A real sink probe distinguishes an API-shaped object from actual enforcement.
    try { document.createElement('div').innerHTML = '<b>guard probe</b>'; evidence.rawGuard='accepted'; }
    catch (failure) { if (!(failure instanceof TypeError)) throw failure; evidence.rawGuard='blocked'; }
    if (evidence.rawGuard !== 'blocked') {
      evidence.status='unsupported'; evidence.detail='Raw strings were accepted: required Trusted Types enforcement is unavailable.'; finish(); return;
    }
    if (config.fixture === 'raw-string') {
      try { target.innerHTML=config.html; evidence.sink='accepted'; evidence.detail='Unexpected raw-string acceptance.'; }
      catch (failure) { if (!(failure instanceof TypeError)) throw failure; evidence.sink='rejected'; evidence.detail='Raw string rejected at innerHTML with TypeError.'; }
    } else if (config.fixture === 'forbidden-policy') {
      try { trustedTypes.createPolicy('lab-forbidden',{createHTML:value=>value}); evidence.policy='created'; evidence.detail='Unexpected forbidden-policy creation.'; }
      catch (failure) { if (!(failure instanceof TypeError)) throw failure; evidence.policy='rejected'; evidence.detail='Unlisted policy name rejected with TypeError; sink not attempted.'; }
    } else {
      if (config.mode === 'fixed' && (!window.DOMPurify || !DOMPurify.isSupported || DOMPurify.version !== config.sanitizerVersion)) {
        throw new Error('The pinned sanitizer did not initialize.');
      }
      const policy = trustedTypes.createPolicy(config.mode === 'fixed' ? 'lab-sanitize' : 'lab-pass', {
        createHTML: config.mode === 'fixed'
          ? value => DOMPurify.sanitize(value,{ALLOWED_TAGS:['p','strong','em','code'],ALLOWED_ATTR:[],ALLOW_DATA_ATTR:false,ALLOW_ARIA_ATTR:false,RETURN_TRUSTED_TYPE:false})
          : value => value,
      });
      evidence.policy='created';
      const html = policy.createHTML(config.html);
      evidence.trusted=trustedTypes.isHTML(html);
      target.innerHTML=html;
      evidence.sink='accepted';
      evidence.detail=config.mode === 'fixed' ? 'Sanitizer-backed TrustedHTML accepted; inspect retained DOM and marker.' : 'Pass-through TrustedHTML accepted; its type alone does not make the HTML safe.';
    }
    timer=setTimeout(finish,600);
  } catch (failure) {
    evidence.status='error'; evidence.detail='Fixture failed before reliable comparison; inspect browser console and rebuild assets.'; finish();
  }
  window.addEventListener('pagehide',()=>clearTimeout(timer),{once:true});
})();
"""


@main_origin
def trusted_frame(request):
    if request.method != "GET":
        return method_error("GET")
    if set(request.GET) != {"run", "mode"} or any(len(request.GET.getlist(key)) != 1 for key in request.GET):
        return invalid("Provide exactly one run and mode.")
    run, mode = request.GET["run"], request.GET["mode"]
    if not re.fullmatch(r"[a-f0-9]{32}", run) or mode not in MODES:
        return invalid("Invalid comparison identifier or mode.")
    state = request.session.get(SESSION_KEY, {})
    if not isinstance(state, dict) or state.get("run") != run or state.get("fixture") not in FIXTURES or state.get("expires", 0) <= time.time():
        return invalid("This run has expired or belongs to another browser session.", 404)
    sanitizer = ""
    if mode == "fixed":
        try:
            sanitizer = (settings.FRONTEND_DIR / "trusted-sanitizer.js").read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return invalid("Build the local sanitizer asset: run npm ci and npm run build in frontend.", 503)
        if len(sanitizer) > 200000 or "DOMPurify " + SANITIZER_VERSION not in sanitizer or re.search(r"</script", sanitizer, re.I):
            return invalid("The local sanitizer asset is unexpected; reinstall pinned dependencies and rebuild frontend.", 503)
    nonce = secrets.token_urlsafe(24)
    config = json.dumps({"run": run, "mode": mode, "fixture": state["fixture"], "html": FIXTURES[state["fixture"]]["html"],
                         "mainOrigin": settings.LAB_MAIN_ORIGIN, "sanitizerVersion": SANITIZER_VERSION}).replace("<", "\\u003c")
    document = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Fixed Trusted Types fixture</title>'
                '<style nonce="' + nonce + '">body{font:14px/1.6 system-ui,sans-serif;margin:20px;color:#203337;overflow-wrap:anywhere}#fixture-output{padding:12px;background:#edf3e7;border-radius:6px;min-height:30px}output{display:block;margin-top:12px}</style>'
                '</head><body><p>Fixed HTML fixture</p><div id="fixture-output"></div><output id="event-marker"></output><p id="frame-status">Preparing fixture...</p>'
                + ('<script nonce="' + nonce + '">' + sanitizer + '\n</script>' if sanitizer else '')
                + '<script nonce="' + nonce + '">' + OBSERVER.replace("__CONFIG__", config) + '</script></body></html>')
    response = HttpResponse(document, content_type="text/html; charset=utf-8")
    response["Content-Security-Policy"] = (
        "default-src 'none'; script-src 'nonce-" + nonce + "'; script-src-attr 'unsafe-hashes' 'sha256-" + HANDLER_HASH + "'; "
        "style-src 'nonce-" + nonce + "'; img-src data:; connect-src 'none'; worker-src 'none'; frame-src 'none'; object-src 'none'; "
        "base-uri 'none'; form-action 'none'; frame-ancestors " + settings.LAB_MAIN_ORIGIN + "; sandbox allow-scripts; "
        "require-trusted-types-for 'script'; trusted-types " + ("lab-sanitize dompurify" if mode == "fixed" else "lab-pass"))
    return response
