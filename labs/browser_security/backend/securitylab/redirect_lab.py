"""Bounded return-URL fixtures produce real redirects to owned marker pages."""
import html
import json
import re
import secrets
from urllib.parse import urlencode, urlsplit

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_GET, require_POST

FIXTURES = [
    {"id": "allowed", "label": "Allowed relative return path", "expectation": "Both handlers send a real 302 to the permitted main-origin marker page."},
    {"id": "absolute-peer", "label": "Absolute URL to the companion", "expectation": "The vulnerable handler navigates to the companion marker. The fixed handler refuses this destination."},
    {"id": "scheme-relative-peer", "label": "Scheme-relative URL to the companion", "expectation": "A leading double slash supplies an authority, not a local path. The vulnerable handler reaches the companion; the fixed handler refuses it."},
    {"id": "normalized-path", "label": "Dot segments in a relative path", "expectation": "The browser normalizes the vulnerable Location to the main marker page. The fixed handler requires the exact canonical path and refuses the alternate spelling."},
]
FIXTURE_IDS = {item["id"] for item in FIXTURES}
RUN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{24}$")
ALLOWED_PATHS = frozenset({"/lab/redirect/landing/"})


def redirect_metadata():
    return {"fixtures": FIXTURES, "mainOrigin": settings.LAB_MAIN_ORIGIN, "peerOrigin": settings.LAB_PEER_ORIGIN}


def invalid(message, status=400):
    return JsonResponse({"error": message}, status=status)


def on_origin(request, role):
    origin = settings.LAB_MAIN_ORIGIN if role == "main" else settings.LAB_PEER_ORIGIN
    return settings.LAB_ROLE == role and request.scheme + "://" + request.get_host() == origin


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate key")
        result[key] = value
    return result


def candidate_for(fixture):
    # Fixed fixtures are containment. Never replace this lookup with a raw URL
    # request parameter: that would create a usable open-redirect service.
    if fixture == "absolute-peer":
        return settings.LAB_PEER_ORIGIN + "/peer/redirect/landing/"
    if fixture == "scheme-relative-peer":
        return "//" + urlsplit(settings.LAB_PEER_ORIGIN).netloc + "/peer/redirect/landing/"
    if fixture == "normalized-path":
        return "/lab/redirect/discard/../landing/"
    return "/lab/redirect/landing/"


def permitted_return_path(candidate):
    """An intentionally narrow business rule, not a general URL sanitizer."""
    if not isinstance(candidate, str) or not candidate or len(candidate) > 256:
        return False
    # Reject ambiguous spelling before parsing: urlsplit can remove controls.
    if any(ord(char) <= 32 or ord(char) == 127 for char in candidate) or "\\" in candidate or "%" in candidate:
        return False
    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return False
    return (not parsed.scheme and not parsed.netloc and not parsed.query and not parsed.fragment
            and candidate.startswith("/") and not candidate.startswith("//")
            and candidate in ALLOWED_PATHS)


def config_from_request(request):
    if set(request.GET) != {"run", "fixture", "mode"} or any(len(request.GET.getlist(key)) != 1 for key in request.GET):
        return None
    if not RUN_PATTERN.fullmatch(request.GET["run"]) or request.GET["fixture"] not in FIXTURE_IDS or request.GET["mode"] not in {"vulnerable", "fixed"}:
        return None
    return {"runId": request.GET["run"], "fixture": request.GET["fixture"], "mode": request.GET["mode"]}


@require_POST
def redirect_prepare(request):
    if not on_origin(request, "main"):
        return invalid("Open the printed main lab URL for this exercise.")
    if request.GET or request.content_type != "application/json":
        return invalid("Send one predefined fixture as JSON without query parameters.")
    if len(request.body) > 256:
        return invalid("Fixture selection is too large.", 413)
    try:
        data = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeError, RecursionError):
        return invalid("Invalid JSON fixture selection.")
    if not isinstance(data, dict) or set(data) != {"fixture"} or not isinstance(data["fixture"], str) or data["fixture"] not in FIXTURE_IDS:
        return invalid("Select a predefined redirect fixture.")
    run_id = secrets.token_urlsafe(18)
    navigations = {mode: settings.LAB_MAIN_ORIGIN + "/lab/redirect/go/?" + urlencode({"run": run_id, "fixture": data["fixture"], "mode": mode}) for mode in ("vulnerable", "fixed")}
    return JsonResponse({"runId": run_id, "fixture": data["fixture"], "candidate": candidate_for(data["fixture"]), "navigations": navigations, **redirect_metadata()})


MARKER_SCRIPT = r"""(() => {
  'use strict';
  const config = JSON.parse(document.body.dataset.config);
  const evidence = {outcome: config.outcome, destination: config.destination,
    marker: document.getElementById('marker').textContent, finalUrl: location.href};
  parent.postMessage({channel: 'redirect-lesson-result', runId: config.runId,
    fixture: config.fixture, mode: config.mode, evidence}, config.mainOrigin);
})();"""


def marker_document(config, destination):
    rejected = destination == "rejected"
    marker = {"main": "MAIN_RETURN_MARKER", "peer": "COMPANION_RETURN_MARKER", "rejected": "RETURN_URL_REJECTED"}[destination]
    nonce = secrets.token_urlsafe(24)
    data = {**config, "destination": destination, "outcome": "rejected" if rejected else "landed", "mainOrigin": settings.LAB_MAIN_ORIGIN}
    title = "Return URL refused" if rejected else "Local redirect destination"
    reason = "The return URL is not an exact permitted relative path. No Location header was sent." if rejected else "The browser reached this owned marker page after the redirect. No login, data collection, or account action occurs here."
    body = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>' + title + '</title><style>body{font:15px/1.5 system-ui,sans-serif;color:#24384c;margin:18px}h1{font-size:18px}code{overflow-wrap:anywhere}</style></head><body data-config="' + html.escape(json.dumps(data), quote=True) + '"><h1>' + title + '</h1><p><code id="marker">' + marker + '</code></p><p>' + reason + '</p><script nonce="' + nonce + '">' + MARKER_SCRIPT + '</script></body></html>'
    response = HttpResponse(body, status=400 if rejected else 200, content_type="text/html; charset=utf-8")
    response["Content-Security-Policy"] = f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'unsafe-inline'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors {settings.LAB_MAIN_ORIGIN}; sandbox allow-scripts"
    return response


@require_GET
def redirect_go(request):
    if not on_origin(request, "main"):
        return invalid("This redirect handler belongs to the configured main origin.", 404)
    config = config_from_request(request)
    if config is None:
        return invalid("Choose a predefined return URL from the main lab.")
    candidate = candidate_for(config["fixture"])
    if config["mode"] == "fixed" and not permitted_return_path(candidate):
        return marker_document(config, "rejected")
    location = candidate + "?" + urlencode({"run": config["runId"], "fixture": config["fixture"], "mode": config["mode"]})
    response = HttpResponseRedirect(location)
    response["Content-Security-Policy"] = "default-src 'none'; base-uri 'none'; form-action 'none'; sandbox allow-scripts"
    return response


def landing(request, role):
    if not on_origin(request, role):
        return invalid("This marker belongs to a different configured origin.", 404)
    config = config_from_request(request)
    if config is None:
        return invalid("Choose a predefined return URL from the main lab.")
    expected_role = "peer" if config["fixture"] in {"absolute-peer", "scheme-relative-peer"} else "main"
    if expected_role != role or (config["mode"] == "fixed" and config["fixture"] != "allowed"):
        return invalid("This fixture cannot reach this marker in the selected mode.")
    return marker_document(config, role)


@require_GET
def redirect_landing(request):
    return landing(request, "main")


@require_GET
def redirect_peer_landing(request):
    return landing(request, "peer")
