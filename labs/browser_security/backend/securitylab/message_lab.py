"""Actual browser messages between fixed local frame documents."""
import html
import json
import re
import secrets
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST

FIXTURES = [
    {"id": "normal", "label": "Trusted sender and plain text", "expectation": "Both receivers accept the expected sender and show the plain-text greeting."},
    {"id": "wrong-origin", "label": "Expected window, wrong origin", "expectation": "The sender occupies the expected frame but is on the peer origin. Only the vulnerable receiver accepts it."},
    {"id": "wrong-source", "label": "Trusted origin, wrong window", "expectation": "A second frame has the correct origin but is not the authorized window. Only the vulnerable receiver accepts it."},
    {"id": "wrong-shape", "label": "Trusted sender, invalid message shape", "expectation": "The trusted sender sends an array and an extra key. The fixed receiver rejects the message schema."},
    {"id": "markup", "label": "Trusted sender, harmless HTML marker", "expectation": "Both authorize this message. Only the vulnerable innerHTML sink runs the fixed image-error marker; textContent displays the markup literally."},
]
FIXTURE_IDS = {item["id"] for item in FIXTURES}
RUN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{24}$")


def message_metadata():
    return {"fixtures": FIXTURES, "mainOrigin": settings.LAB_MAIN_ORIGIN, "peerOrigin": settings.LAB_PEER_ORIGIN}


def invalid(message, status=400):
    return JsonResponse({"error": message}, status=status)


def exact_query(request, fields):
    return set(request.GET) == set(fields) and all(len(request.GET.getlist(key)) == 1 for key in request.GET)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


@require_POST
def message_prepare(request):
    if settings.LAB_ROLE != "main" or request.scheme + "://" + request.get_host() != settings.LAB_MAIN_ORIGIN:
        return invalid("Open the printed main lab URL for this two-origin exercise.", 400)
    if request.GET or request.content_type != "application/json":
        return invalid("Send one fixture identifier as JSON, with no query parameters.")
    if len(request.body) > 256:
        return invalid("Fixture selection is too large.", 413)
    try:
        data = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeError, RecursionError):
        return invalid("Invalid JSON fixture selection.")
    if not isinstance(data, dict) or set(data) != {"fixture"} or not isinstance(data["fixture"], str) or data["fixture"] not in FIXTURE_IDS:
        return invalid("Select one of the predefined message fixtures.")
    run_id = secrets.token_urlsafe(18)
    receivers = {
        mode: settings.LAB_PEER_ORIGIN + "/peer/message/?" + urlencode({"run": run_id, "fixture": data["fixture"], "mode": mode})
        for mode in ("vulnerable", "fixed")
    }
    return JsonResponse({"runId": run_id, "fixture": data["fixture"], "receivers": receivers, **message_metadata()})


def document(config, title, script, body):
    encoded = html.escape(json.dumps(config), quote=True)
    return HttpResponse(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>' + title + '</title></head>'
        '<body data-config="' + encoded + '">' + body + '<script src="' + script + '"></script></body></html>',
        content_type="text/html; charset=utf-8",
    )


@require_GET
def message_receiver(request):
    if settings.LAB_ROLE != "peer":
        return invalid("This receiver belongs to the companion origin.", 404)
    if not exact_query(request, {"run", "fixture", "mode"}) or not RUN_PATTERN.fullmatch(request.GET.get("run", "")) or request.GET.get("fixture") not in FIXTURE_IDS or request.GET.get("mode") not in {"vulnerable", "fixed"}:
        return invalid("Choose a predefined receiver from the main lab.")
    config = {"runId": request.GET["run"], "fixture": request.GET["fixture"], "mode": request.GET["mode"], "mainOrigin": settings.LAB_MAIN_ORIGIN, "peerOrigin": settings.LAB_PEER_ORIGIN}
    response = document(config, "Fixed postMessage receiver fixture", "/peer/message/receiver.js", '<p id="status">Waiting for a sender.</p><div id="output"></div><div id="senders" hidden></div>')
    response["Content-Security-Policy"] = (
        "default-src 'none'; script-src 'self' 'unsafe-inline'; img-src data:; "
        "connect-src 'none'; base-uri 'none'; object-src 'none'; form-action 'none'; "
        "sandbox allow-scripts allow-same-origin; "
        f"frame-src {settings.LAB_MAIN_ORIGIN} {settings.LAB_PEER_ORIGIN}; frame-ancestors {settings.LAB_MAIN_ORIGIN}"
    )
    return response


@require_GET
def message_sender(request):
    if not exact_query(request, {"run", "fixture", "slot"}) or not RUN_PATTERN.fullmatch(request.GET.get("run", "")) or request.GET.get("fixture") not in FIXTURE_IDS or request.GET.get("slot") not in {"trusted", "secondary"}:
        return invalid("Choose a predefined sender from the main lab.")
    config = {"runId": request.GET["run"], "fixture": request.GET["fixture"], "slot": request.GET["slot"], "peerOrigin": settings.LAB_PEER_ORIGIN}
    response = document(config, "Fixed postMessage sender fixture", "/lab/message/sender.js", '<p>Fixed local sender.</p>')
    response["Content-Security-Policy"] = (
        "default-src 'none'; script-src 'self'; connect-src 'none'; base-uri 'none'; object-src 'none'; form-action 'none'; "
        "sandbox allow-scripts allow-same-origin; "
        f"frame-ancestors {settings.LAB_MAIN_ORIGIN} {settings.LAB_PEER_ORIGIN}"
    )
    return response


RECEIVER_SCRIPT = r"""(() => {
  'use strict';
  const config = JSON.parse(document.body.dataset.config);
  const output = document.getElementById('output');
  const trusted = document.createElement('iframe');
  const secondary = config.fixture === 'wrong-source' ? document.createElement('iframe') : null;
  const trustedOrigin = config.fixture === 'wrong-origin' ? config.peerOrigin : config.mainOrigin;
  const sender = secondary || trusted;
  const senderOrigin = secondary ? config.mainOrigin : trustedOrigin;
  let started = false, complete = false;
  window.__messageMarker = false;
  function schemaValid(data) {
    return data !== null && typeof data === 'object' && !Array.isArray(data)
      && Object.keys(data).sort().join(',') === 'channel,runId,text,type'
      && data.channel === 'message-lesson-payload' && data.runId === config.runId
      && data.type === 'greeting' && typeof data.text === 'string' && data.text.length <= 512;
  }
  function onMessage(event) {
    const data = event.data;
    if (data?.channel === 'message-lesson-ready') {
      if (!started && event.source === sender.contentWindow && event.origin === senderOrigin
          && data.runId === config.runId && data.slot === (secondary ? 'secondary' : 'trusted')) {
        started = true;
        event.source.postMessage({channel: 'message-lesson-start', runId: config.runId}, senderOrigin);
      }
      return;
    }
    // The channel/run filter selects this comparison; neither is a sender credential.
    if (complete || !started || data?.channel !== 'message-lesson-payload' || data.runId !== config.runId) return;
    complete = true;
    const originMatch = event.origin === config.mainOrigin;
    const sourceMatch = event.source === trusted.contentWindow;
    const validShape = schemaValid(data);
    const accepted = config.mode === 'vulnerable' || (originMatch && sourceMatch && validShape);
    let reason;
    if (config.mode === 'vulnerable') {
      output.innerHTML = String(data.text);
      reason = 'Accepted without origin, window, or schema checks; rendered through innerHTML.';
    } else if (!originMatch) reason = 'Rejected: the sender origin does not exactly match the configured main origin.';
    else if (!sourceMatch) reason = 'Rejected: this is not the authorized sender window.';
    else if (!validShape) reason = 'Rejected: message keys, type, or bounded text field do not match the schema.';
    else {
      output.textContent = data.text;
      reason = 'Origin, sender window, and schema matched; rendered through textContent.';
    }
    const sendResult = () => {
      window.removeEventListener('message', onMessage);
      document.getElementById('status').textContent = accepted ? 'Accepted fixture message.' : 'Rejected fixture message.';
      parent.postMessage({channel: 'message-lesson-result', runId: config.runId, fixture: config.fixture, mode: config.mode,
        result: {outcome: accepted ? 'accepted' : 'rejected', observedOrigin: event.origin,
          expectedOrigin: config.mainOrigin, sourceMatch, schemaValid: validShape, accepted,
          renderedText: output.textContent, markerObserved: window.__messageMarker === true, reason}}, config.mainOrigin);
    };
    // The invalid data image reports an actual error event. No external resource is requested.
    const markerImage = output.querySelector('img');
    if (markerImage && !markerImage.complete) {
      let sent = false;
      const settle = () => { if (!sent) { sent = true; clearTimeout(fallback); sendResult(); } };
      markerImage.addEventListener('error', settle, {once: true});
      markerImage.addEventListener('load', settle, {once: true});
      const fallback = setTimeout(settle, 1500);
    } else setTimeout(sendResult, 0);
  }
  window.addEventListener('message', onMessage);
  function attach(frame, origin, slot) {
    frame.title = slot + ' fixed sender';
    frame.src = origin + '/lab/message/sender/?' + new URLSearchParams({run: config.runId, fixture: config.fixture, slot});
    document.getElementById('senders').appendChild(frame);
  }
  attach(trusted, trustedOrigin, 'trusted');
  if (secondary) attach(secondary, config.mainOrigin, 'secondary');
})();"""

SENDER_SCRIPT = r"""(() => {
  'use strict';
  const config = JSON.parse(document.body.dataset.config);
  let sent = false;
  window.addEventListener('message', (event) => {
    if (sent || event.source !== parent || event.origin !== config.peerOrigin
        || event.data?.channel !== 'message-lesson-start' || event.data.runId !== config.runId) return;
    sent = true;
    const data = {channel: 'message-lesson-payload', runId: config.runId, type: 'greeting', text: 'Hello from the authorized message fixture.'};
    if (config.fixture === 'wrong-origin') data.text = 'WRONG_ORIGIN_MARKER';
    if (config.fixture === 'wrong-source') data.text = 'WRONG_WINDOW_MARKER';
    if (config.fixture === 'wrong-shape') { data.text = ['WRONG_SHAPE_MARKER']; data.extra = true; }
    if (config.fixture === 'markup') data.text = '<img src="data:image/png;base64,AA==" alt="Harmless marker" onerror="window.__messageMarker=true">MESSAGE_HTML_MARKER';
    parent.postMessage(data, config.peerOrigin);
  });
  parent.postMessage({channel: 'message-lesson-ready', runId: config.runId, slot: config.slot}, config.peerOrigin);
})();"""


@require_GET
def message_receiver_script(request):
    if settings.LAB_ROLE != "peer":
        return invalid("This script belongs to the companion origin.", 404)
    if request.GET:
        return invalid("The receiver script does not accept parameters.")
    return HttpResponse(RECEIVER_SCRIPT, content_type="text/javascript; charset=utf-8")


@require_GET
def message_sender_script(request):
    if request.GET:
        return invalid("The sender script does not accept parameters.")
    return HttpResponse(SENDER_SCRIPT, content_type="text/javascript; charset=utf-8")
