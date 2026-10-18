"""Real bounded ASGI WebSockets over fictional tenant events, never user data."""
import asyncio
import html
import ipaddress
import json
import re
import secrets
import threading
import time
from http.cookies import SimpleCookie, CookieError
from importlib import import_module
from urllib.parse import parse_qs, urlencode, urlsplit

from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST

FIXTURES = [
    {"id": "allowed", "label": "Allowed origin and tenant subscription", "expectation": "Both sockets upgrade and receive one fictional alpha event."},
    {"id": "wrong-origin", "label": "Companion origin absent from the allowlist", "expectation": "The vulnerable socket upgrades from the companion. The fixed socket refuses the handshake before messages are accepted."},
    {"id": "foreign-tenant", "label": "Subscribe to another fictional tenant", "expectation": "The vulnerable socket delivers the beta marker. The fixed socket upgrades but denies the tenant subscription."},
    {"id": "forbidden-action", "label": "Reader attempts a publish action", "expectation": "The vulnerable socket acknowledges a fictional publish. The fixed socket checks the message action and refuses it."},
    {"id": "permission-revoked", "label": "Permission revoked while subscribed", "expectation": "Both sockets subscribe first. After a separate HTTP revocation, the vulnerable socket delivers again; the fixed socket rechecks permission before delivery and refuses."},
]
FIXTURE_IDS = {item["id"] for item in FIXTURES}
MODES = ("vulnerable", "fixed")
HEX = re.compile(r"^[a-f0-9]{32}$")
CAP = re.compile(r"^[a-f0-9]{48}$")
MAX_RUNS = 128
RUN_TTL = 300
SOCKET_TTL = 12
MAX_MESSAGES = 3
MAX_BYTES = 512
_runs = {}
_lock = threading.RLock()


def websocket_metadata():
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


def exact_main(request):
    return settings.LAB_ROLE == "main" and request.scheme + "://" + request.get_host() == settings.LAB_MAIN_ORIGIN


def exact_query(request, keys):
    return set(request.GET) == keys and all(len(request.GET.getlist(key)) == 1 for key in keys)


def prune():
    for run_id in list(_runs):
        if time.monotonic() - _runs[run_id]["created"] > RUN_TTL:
            del _runs[run_id]


def read_json(request, keys):
    if request.GET or request.content_type != "application/json" or len(request.body) > 256:
        return None
    try:
        data = json.loads(request.body, object_pairs_hook=unique_object)
        return data if isinstance(data, dict) and set(data) == keys else None
    except (ValueError, UnicodeError, RecursionError):
        return None


def owned(request, run):
    return bool(run and request.session.get("websocket_owner") == run["owner"])


def public_state(run):
    return {mode: {key: value for key, value in run["modes"][mode].items() if key not in {"capability", "used"}} for mode in MODES}


@require_POST
def websocket_prepare(request):
    if not exact_main(request):
        return invalid("Use the printed main lab URL.", 404)
    data = read_json(request, {"fixture"})
    if data is None or not isinstance(data["fixture"], str) or data["fixture"] not in FIXTURE_IDS:
        return invalid("Choose one predefined WebSocket fixture.")
    owner = request.session.get("websocket_owner")
    if not owner:
        owner = secrets.token_hex(24)
        request.session["websocket_owner"] = owner
    run_id = secrets.token_hex(16)
    with _lock:
        prune()
        # Keep at most four recent runs per owning browser session.
        previous = [key for key, value in _runs.items() if value["owner"] == owner]
        while len(previous) >= 4:
            del _runs[previous.pop(0)]
        if len(_runs) >= MAX_RUNS:
            del _runs[next(iter(_runs))]
        run = {"owner": owner, "fixture": data["fixture"], "created": time.monotonic(), "permission": True,
               "modes": {mode: {"capability": secrets.token_hex(24), "used": False, "handshake": "not attempted", "messages": 0,
                                "deliveries": 0, "subscribed": False, "outcome": "not reached", "closed": False} for mode in MODES}}
        _runs[run_id] = run
        query = urlencode({"run": run_id, "fixture": data["fixture"], "v": run["modes"]["vulnerable"]["capability"], "f": run["modes"]["fixed"]["capability"]})
    origin = settings.LAB_PEER_ORIGIN if data["fixture"] == "wrong-origin" else settings.LAB_MAIN_ORIGIN
    path = "/peer/websocket/" if data["fixture"] == "wrong-origin" else "/lab/websocket/frame/"
    return JsonResponse({"runId": run_id, "fixture": data["fixture"], "harness": origin + path + "?" + query, **websocket_metadata()})


@require_GET
def websocket_state(request):
    if not exact_main(request) or not exact_query(request, {"run"}) or not HEX.fullmatch(request.GET["run"]):
        return invalid("Unknown WebSocket evidence.", 404)
    with _lock:
        prune()
        run = _runs.get(request.GET["run"])
        if not owned(request, run):
            return invalid("This run expired or belongs to another session.", 404)
        return JsonResponse({"runId": request.GET["run"], "fixture": run["fixture"], "permission": run["permission"], "modes": public_state(run)})


@require_POST
def websocket_revoke(request):
    if not exact_main(request):
        return invalid("Unknown local endpoint.", 404)
    data = read_json(request, {"run"})
    if data is None or not isinstance(data["run"], str) or not HEX.fullmatch(data["run"]):
        return invalid("Select a prepared run.")
    with _lock:
        prune()
        run = _runs.get(data["run"])
        if not owned(request, run):
            return invalid("This run expired or belongs to another session.", 404)
        if run["fixture"] != "permission-revoked" or not run["permission"] or not all(state["subscribed"] and not state["closed"] for state in run["modes"].values()):
            return invalid("Both live subscriptions are required before this one-time revocation.", 409)
        run["permission"] = False
        return JsonResponse({"runId": data["run"], "permission": False})


def frame_response(request, peer):
    origin = settings.LAB_PEER_ORIGIN if peer else settings.LAB_MAIN_ORIGIN
    if settings.LAB_ROLE != ("peer" if peer else "main") or request.scheme + "://" + request.get_host() != origin:
        return invalid("Wrong local harness origin.", 404)
    if not exact_query(request, {"run", "fixture", "v", "f"}) or not HEX.fullmatch(request.GET["run"]) or not all(CAP.fullmatch(request.GET[key]) for key in ("v", "f")) or request.GET["fixture"] not in FIXTURE_IDS or (request.GET["fixture"] == "wrong-origin") != peer:
        return invalid("Unknown fixed harness.")
    if not peer:
        with _lock:
            prune()
            run = _runs.get(request.GET["run"])
            if not owned(request, run) or run["fixture"] != request.GET["fixture"] or any(not secrets.compare_digest(run["modes"][mode]["capability"], request.GET[key]) for mode, key in (("vulnerable", "v"), ("fixed", "f"))):
                return invalid("Unknown owned harness.", 404)
    script_path = "/peer/websocket/boot.js" if peer else "/lab/websocket/boot.js"
    body = '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Fixed local WebSocket harness</title></head><body data-main="' + html.escape(settings.LAB_MAIN_ORIGIN, quote=True) + '"><p id="status">Opening two bounded local WebSockets...</p><script src="' + script_path + '"></script></body></html>'
    response = HttpResponse(body)
    ws_origin = settings.LAB_MAIN_ORIGIN.replace("http://", "ws://", 1)
    response["Content-Security-Policy"] = f"default-src 'none'; script-src 'self'; connect-src {ws_origin}; base-uri 'none'; form-action 'none'; frame-ancestors {settings.LAB_MAIN_ORIGIN}; object-src 'none'"
    return response


@require_GET
def websocket_frame(request):
    return frame_response(request, False)


@require_GET
def websocket_peer(request):
    return frame_response(request, True)


BOOT = r"""'use strict';
(() => {
  const main = document.body.dataset.main, params = new URLSearchParams(location.search);
  const runId = params.get('run'), fixture = params.get('fixture');
  const sockets = new Map(), results = {}, ready = new Set();
  let ended = false, revoking = false;
  const post = (type, extra = {}) => parent.postMessage({channel:'websocket-lesson', runId, fixture, type, ...extra}, main);
  const finish = () => {
    if (ended || Object.keys(results).length !== 2) return;
    ended = true; clearTimeout(timer);
    document.getElementById('status').textContent = 'Finished. Compare browser messages with independent server evidence above.';
    post('complete', {results});
  };
  const timer = setTimeout(() => {
    for (const [mode, socket] of sockets) {
      if (!results[mode]) results[mode] = {opened:socket.readyState === WebSocket.OPEN, marker:null, outcome:'timeout', closeCode:null};
      socket.close();
    }
    finish();
  }, 10000);
  function connect(mode, key) {
    const endpoint = new URL(main); endpoint.protocol = 'ws:';
    endpoint.pathname = '/ws/security/' + mode + '/';
    endpoint.search = new URLSearchParams({run:runId, cap:params.get(key)}).toString();
    const socket = new WebSocket(endpoint.href); sockets.set(mode, socket);
    const observation = {opened:false, marker:null, outcome:'transport failure', closeCode:null};
    socket.addEventListener('open', () => {
      observation.opened = true;
      socket.send(JSON.stringify({action:fixture === 'forbidden-action' ? 'publish' : 'subscribe', tenant:fixture === 'foreign-tenant' ? 'beta' : 'alpha'}));
    });
    socket.addEventListener('message', event => {
      let data; try { data = JSON.parse(event.data); } catch { socket.close(); return; }
      if (!data || !['event','denied','published'].includes(data.kind) || !['HARMLESS_ALPHA_EVENT','HARMLESS_BETA_EVENT','FICTIONAL_PUBLISH_ACCEPTED','WS_PERMISSION_DENIED','WS_TENANT_DENIED','WS_ACTION_DENIED'].includes(data.marker)) { socket.close(); return; }
      observation.marker = data.marker; observation.outcome = data.kind;
      if (fixture === 'permission-revoked' && !revoking && data.kind === 'event') {
        ready.add(mode);
        if (ready.size === 2) { revoking = true; post('ready-to-revoke'); }
      } else socket.close(1000, 'fixture complete');
    });
    socket.addEventListener('close', event => {
      observation.closeCode = event.code;
      results[mode] = observation; finish();
    });
    socket.addEventListener('error', () => { /* A failed upgrade does not expose its HTTP status to browser JS. */ });
  }
  addEventListener('message', event => {
    const data = event.data;
    if (ended || !revoking || event.source !== parent || event.origin !== main || !data || Object.keys(data).sort().join(',') !== 'channel,runId,type' || data.channel !== 'websocket-lesson' || data.runId !== runId || data.type !== 'permission-revoked') return;
    for (const socket of sockets.values()) if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({action:'deliver', tenant:'alpha'}));
  });
  addEventListener('pagehide', () => { ended = true; clearTimeout(timer); for (const socket of sockets.values()) socket.close(); });
  connect('vulnerable', 'v'); connect('fixed', 'f');
})();
"""


def script_response(request, peer):
    expected = settings.LAB_PEER_ORIGIN if peer else settings.LAB_MAIN_ORIGIN
    if settings.LAB_ROLE != ("peer" if peer else "main") or request.scheme + "://" + request.get_host() != expected or request.GET:
        return invalid("Wrong fixed script origin.", 404)
    response = HttpResponse(BOOT, content_type="application/javascript")
    response["Content-Security-Policy"] = "default-src 'none'; sandbox"
    return response


@require_GET
def websocket_script(request):
    return script_response(request, False)


@require_GET
def websocket_peer_script(request):
    return script_response(request, True)


def connection_parameters(scope):
    """Validate transport independently: Django HTTP middleware does not see WS."""
    try:
        if settings.LAB_ROLE != "main" or scope.get("scheme") != "ws" or not ipaddress.ip_address(scope["client"][0]).is_loopback:
            return None
        raw_headers = scope.get("headers", [])
        headers = {}
        for name, value in raw_headers:
            name = name.lower()
            if name in {b"host", b"origin", b"cookie"}:
                if name in headers:
                    return None
                headers[name] = value.decode("latin1")
        if headers.get(b"host") != urlsplit(settings.LAB_MAIN_ORIGIN).netloc or headers.get(b"origin") not in {settings.LAB_MAIN_ORIGIN, settings.LAB_PEER_ORIGIN}:
            return None
        match = re.fullmatch(r"/ws/security/(vulnerable|fixed)/", scope.get("path", ""))
        query = scope.get("query_string", b"")
        if not match or len(query) > 128:
            return None
        data = parse_qs(query.decode("ascii"), strict_parsing=True)
        if set(data) != {"run", "cap"} or any(len(value) != 1 for value in data.values()) or not HEX.fullmatch(data["run"][0]) or not CAP.fullmatch(data["cap"][0]):
            return None
        cookies = SimpleCookie()
        cookies.load(headers.get(b"cookie", ""))
        cookie = cookies.get(settings.SESSION_COOKIE_NAME)
        if cookie is None or not re.fullmatch(r"[a-z0-9]{32}", cookie.value):
            return None
        return match[1], data["run"][0], data["cap"][0], headers[b"origin"], cookie.value
    except (ValueError, KeyError, IndexError, UnicodeError, CookieError, TypeError):
        return None


def session_owner(session_key):
    store = import_module(settings.SESSION_ENGINE).SessionStore(session_key=session_key)
    return store.load().get("websocket_owner")


def process_message(run, mode, data):
    state = run["modes"][mode]
    if not isinstance(data, dict) or set(data) != {"action", "tenant"} or not isinstance(data["action"], str) or not isinstance(data["tenant"], str) or data["action"] not in {"subscribe", "publish", "deliver"} or data["tenant"] not in {"alpha", "beta"}:
        return None
    if mode == "fixed":
        reason = "permission" if not run["permission"] else "tenant" if data["tenant"] != "alpha" else "action" if data["action"] == "publish" else None
        if reason:
            state["outcome"] = reason + " refused"
            return {"kind": "denied", "marker": "WS_" + reason.upper() + "_DENIED"}
    if data["action"] == "publish":
        state["outcome"] = "fictional publish accepted"
        return {"kind": "published", "marker": "FICTIONAL_PUBLISH_ACCEPTED"}
    if data["action"] == "deliver" and (run["fixture"] != "permission-revoked" or not state["subscribed"] or run["permission"]):
        return None
    state["subscribed"] = True
    state["deliveries"] += 1
    state["outcome"] = "event delivered"
    return {"kind": "event", "marker": "HARMLESS_" + data["tenant"].upper() + "_EVENT"}


async def websocket_application(scope, receive, send):
    if (await receive()).get("type") != "websocket.connect":
        return
    parameters = connection_parameters(scope)
    if parameters is None:
        await send({"type": "websocket.close", "code": 1008})
        return
    mode, run_id, capability, origin, session_key = parameters
    owner = await sync_to_async(session_owner)(session_key)
    with _lock:
        prune()
        run = _runs.get(run_id)
        state = run["modes"][mode] if run else None
        valid = bool(run and owner and owner == run["owner"] and not state["used"] and secrets.compare_digest(capability, state["capability"]))
        if valid:
            state["used"] = True
            allowed_origin = settings.LAB_PEER_ORIGIN if run["fixture"] == "wrong-origin" else settings.LAB_MAIN_ORIGIN
            valid = origin == allowed_origin and (mode == "vulnerable" or origin == settings.LAB_MAIN_ORIGIN)
            state["handshake"] = "accepted" if valid else "origin refused"
            if not valid:
                state["closed"] = True
    if not valid:
        await send({"type": "websocket.close", "code": 1008})
        return
    await send({"type": "websocket.accept"})
    deadline = time.monotonic() + SOCKET_TTL
    try:
        for _ in range(MAX_MESSAGES):
            event = await asyncio.wait_for(receive(), max(0.001, deadline - time.monotonic()))
            if event["type"] == "websocket.disconnect":
                return
            text = event.get("text")
            if event["type"] != "websocket.receive" or not isinstance(text, str) or len(text.encode("utf-8")) > MAX_BYTES:
                await send({"type": "websocket.close", "code": 1008})
                return
            try:
                data = json.loads(text, object_pairs_hook=unique_object)
            except (ValueError, UnicodeError, RecursionError):
                data = None
            current_owner = await sync_to_async(session_owner)(session_key)
            with _lock:
                current = _runs.get(run_id)
                if current is not run or time.monotonic() - run["created"] > RUN_TTL or current_owner != run["owner"]:
                    result = None
                else:
                    state["messages"] += 1
                    result = process_message(run, mode, data)
            if result is None:
                await send({"type": "websocket.close", "code": 1008})
                return
            await send({"type": "websocket.send", "text": json.dumps(result, separators=(",", ":"))})
        await send({"type": "websocket.close", "code": 1008})
    except asyncio.TimeoutError:
        await send({"type": "websocket.close", "code": 1000})
    except OSError:
        pass  # The browser disconnected during a send.
    finally:
        with _lock:
            state["closed"] = True
