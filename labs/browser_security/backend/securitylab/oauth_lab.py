"""Disposable local OIDC code flows; OAuthlib owns protocol checks and PKCE.

HTTP browser redirects are real. The confidential client hands a serialized
token request to OAuthlib in-process; there is no outbound HTTP or token API.
"""
import base64
import hashlib
import html
import json
import re
import secrets
import threading
import time
from collections import OrderedDict
from types import SimpleNamespace
from urllib.parse import urlencode

import jwt
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from oauthlib.oauth2 import OAuth2Error
from oauthlib.openid import RequestValidator, Server

FIXTURES = [
    {"id": "valid", "label": "Control: valid code flow", "expectation": "Both clients complete the redirects, exchange the code, validate the signed ID token, and show the fictional identity marker."},
    {"id": "wrong-verifier", "label": "Wrong PKCE verifier", "expectation": "The vulnerable provider loses the stored PKCE binding. The fixed provider rejects the wrong verifier at token exchange."},
    {"id": "state-mismatch", "label": "Callback state does not match", "expectation": "The vulnerable client ignores the unexpected state. The fixed client refuses before token exchange."},
    {"id": "nonce-mismatch", "label": "ID-token nonce does not match", "expectation": "Both exchanges succeed. The fixed client rejects the signed token because its nonce differs from the original transaction."},
    {"id": "reused-code", "label": "Redeem the same authorization code twice", "expectation": "The first exchange succeeds in both modes. Only the vulnerable provider accepts a second redemption of the same code."},
    {"id": "invalid-redirect", "label": "Unregistered local callback", "expectation": "The vulnerable provider sends a code to a second owned callback. The fixed provider rejects the redirect URI before issuing a code."},
]
FIXTURE_IDS = {item["id"] for item in FIXTURES}
MODES = ("vulnerable", "fixed")
CLIENT_ID = "local-oidc-client"
SUBJECT = "fictional-reader"
RUN_RE = re.compile(r"^[A-Za-z0-9_-]{24}$")
WIRE_VALUE_RE = re.compile(r"^[A-Za-z0-9_-]{16,128}$")
SESSION_KEY = "oauth_lesson_owner"
RUN_TTL = 300
CODE_TTL = 60
MAX_RUNS = 128
MAX_OWNER_RUNS = 8
RUNS = OrderedDict()
LOCK = threading.RLock()


def oauth_metadata():
    return {"fixtures": FIXTURES, "mainOrigin": settings.LAB_MAIN_ORIGIN,
            "library": "OAuthlib 4.0.0 + PyJWT", "tokenTransport": "in-process"}


def invalid(message, status=400):
    return JsonResponse({"error": message}, status=status)


def main_request(request):
    return settings.LAB_ROLE == "main" and request.scheme + "://" + request.get_host() == settings.LAB_MAIN_ORIGIN


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def prune(now):
    for run, record in list(RUNS.items()):
        if record["expires"] <= now:
            del RUNS[run]
    while len(RUNS) >= MAX_RUNS:
        RUNS.popitem(last=False)


def digest(value, half=False):
    hashed = hashlib.sha256(value.encode("ascii")).digest()
    return base64.urlsafe_b64encode(hashed[:16] if half else hashed).rstrip(b"=").decode("ascii")


def new_transaction(run, mode, fixture):
    query = urlencode({"run": run, "mode": mode})
    base = settings.LAB_MAIN_ORIGIN
    return {"runId": run, "mode": mode, "fixture": fixture, "phase": "prepared",
            "state": secrets.token_urlsafe(24), "nonce": secrets.token_urlsafe(24),
            "verifier": secrets.token_urlsafe(48), "secret": secrets.token_urlsafe(48),
            "redirect": base + "/lab/oauth/callback/?" + query,
            "alternate": base + "/lab/oauth/alternate-callback/?" + query,
            "issuer": base + "/lab/oauth/provider/", "codes": {}, "tokenStatuses": [],
            "steps": [], "issued": 0}


def authorize_parameters(tx):
    return {"run": tx["runId"], "mode": tx["mode"], "response_type": "code",
            "client_id": CLIENT_ID, "scope": "openid", "code_challenge_method": "S256",
            "code_challenge": digest(tx["verifier"]),
            "state": "unexpected-" + tx["state"] if tx["fixture"] == "state-mismatch" else tx["state"],
            "nonce": "unexpected-" + tx["nonce"] if tx["fixture"] == "nonce-mismatch" else tx["nonce"],
            "redirect_uri": tx["alternate"] if tx["fixture"] == "invalid-redirect" else tx["redirect"]}


def resolve(request, keys):
    if not main_request(request) or set(request.GET) != set(keys) or any(len(request.GET.getlist(key)) != 1 for key in request.GET):
        return None
    run, mode = request.GET.get("run", ""), request.GET.get("mode", "")
    if not RUN_RE.fullmatch(run) or mode not in MODES:
        return None
    record = RUNS.get(run)
    owner = request.session.get(SESSION_KEY)
    if not record or record["expires"] <= time.monotonic() or not isinstance(owner, str) or not secrets.compare_digest(owner, record["owner"]):
        return None
    return record["transactions"][mode]


def bounded_callback_values(request):
    return all(WIRE_VALUE_RE.fullmatch(request.GET.get(key, "")) for key in ("code", "state"))


@require_POST
def oauth_prepare(request):
    if not main_request(request):
        return invalid("Open the printed main lab URL.", 404)
    if request.GET or request.content_type != "application/json" or len(request.body) > 256:
        return invalid("Send one predefined OAuth fixture as JSON.")
    try:
        data = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeError, RecursionError):
        return invalid("Invalid fixture selection.")
    if not isinstance(data, dict) or set(data) != {"fixture"} or not isinstance(data["fixture"], str) or data["fixture"] not in FIXTURE_IDS:
        return invalid("Choose a predefined OAuth fixture.")
    owner = request.session.get(SESSION_KEY)
    if not isinstance(owner, str):
        owner = secrets.token_urlsafe(24)
        request.session[SESSION_KEY] = owner
    run = secrets.token_urlsafe(18)
    with LOCK:
        prune(time.monotonic())
        owned = [key for key, record in RUNS.items() if record["owner"] == owner]
        for key in owned[:max(0, len(owned) - MAX_OWNER_RUNS + 1)]:
            del RUNS[key]
        RUNS[run] = {"owner": owner, "expires": time.monotonic() + RUN_TTL,
                     "transactions": {mode: new_transaction(run, mode, data["fixture"]) for mode in MODES}}
    return JsonResponse({"runId": run, "fixture": data["fixture"],
                         "navigations": {mode: settings.LAB_MAIN_ORIGIN + "/lab/oauth/start/?" + urlencode({"run": run, "mode": mode}) for mode in MODES},
                         **oauth_metadata()})


class LocalValidator(RequestValidator):
    """Explicit fixture defects live in storage/client policy, not OAuthlib."""
    def __init__(self, tx):
        self.tx = tx

    def validate_client_id(self, client_id, request, *args, **kwargs):
        request.client = SimpleNamespace(client_id=CLIENT_ID)
        return client_id == CLIENT_ID

    def validate_redirect_uri(self, client_id, redirect_uri, request, *args, **kwargs):
        permitted = {self.tx["redirect"]}
        if self.tx["mode"] == "vulnerable":
            permitted.add(self.tx["alternate"])
        return client_id == CLIENT_ID and redirect_uri in permitted

    def get_default_redirect_uri(self, client_id, request, *args, **kwargs):
        return self.tx["redirect"]

    def validate_response_type(self, client_id, response_type, client, request, *args, **kwargs):
        return response_type == "code"

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        return scopes == ["openid"]

    def get_default_scopes(self, client_id, request, *args, **kwargs):
        return ["openid"]

    def validate_user_match(self, id_token_hint, scopes, claims, request):
        # Synthetic identity is predetermined; the fixture has no login form,
        # identity hints, requested claims, or consent negotiation.
        return request.user == SUBJECT and id_token_hint is None and claims is None

    def is_pkce_required(self, client_id, request):
        return self.tx["mode"] == "fixed"

    def save_authorization_code(self, client_id, code, request, *args, **kwargs):
        self.tx["codes"][code["code"]] = {"client_id": client_id, "redirect": request.redirect_uri,
            "challenge": request.code_challenge, "method": request.code_challenge_method,
            "nonce": request.nonce, "scopes": list(request.scopes), "expires": time.monotonic() + CODE_TTL}
        self.tx["steps"].append("Provider issued an authorization code.")

    def client_authentication_required(self, request, *args, **kwargs):
        return True

    def authenticate_client(self, request, *args, **kwargs):
        request.client = SimpleNamespace(client_id=CLIENT_ID)
        return request.client_id == CLIENT_ID and isinstance(request.client_secret, str) and secrets.compare_digest(request.client_secret, self.tx["secret"])

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        return grant_type == "authorization_code"

    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        grant = self.tx["codes"].get(code)
        if not grant or grant["expires"] <= time.monotonic() or grant["client_id"] != client_id:
            return False
        request.user, request.scopes = SUBJECT, grant["scopes"]
        return True

    def get_code_challenge(self, code, request):
        # Deliberate vulnerable storage integration: forget the saved binding.
        return self.tx["codes"].get(code, {}).get("challenge") if self.tx["mode"] == "fixed" else None

    def get_code_challenge_method(self, code, request):
        return self.tx["codes"].get(code, {}).get("method")

    def confirm_redirect_uri(self, client_id, code, redirect_uri, client, request, *args, **kwargs):
        return redirect_uri == self.tx["codes"].get(code, {}).get("redirect")

    def get_authorization_code_scopes(self, client_id, code, redirect_uri, request):
        return self.tx["codes"].get(code, {}).get("scopes", [])

    def get_authorization_code_nonce(self, client_id, code, redirect_uri, request):
        return self.tx["codes"].get(code, {}).get("nonce")

    def finalize_id_token(self, id_token, token, token_handler, request):
        claims = {**id_token, "iss": self.tx["issuer"], "sub": SUBJECT, "exp": int(time.time()) + CODE_TTL}
        return jwt.encode(claims, self.tx["secret"], algorithm="HS256")

    def save_bearer_token(self, token, request, *args, **kwargs):
        # No resource server or persistent account session exists in this lab.
        self.tx["issued"] += 1

    def invalidate_authorization_code(self, client_id, code, request, *args, **kwargs):
        if self.tx["mode"] == "fixed":
            self.tx["codes"].pop(code, None)


def protocol_server(tx):
    server = Server(LocalValidator(tx), token_expires_in=CODE_TTL)
    server.auth_grant.refresh_token = False
    server.openid_connect_auth.refresh_token = False
    return server


def exchange(tx, code, verifier=None):
    body = urlencode({"grant_type": "authorization_code", "client_id": CLIENT_ID,
                      "client_secret": tx["secret"], "code": code, "redirect_uri": tx["redirect"],
                      "code_verifier": verifier if verifier is not None else tx["verifier"]})
    _headers, payload, status = protocol_server(tx).create_token_response(
        tx["issuer"] + "token/", http_method="POST", body=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    tx["tokenStatuses"].append(status)
    tx["steps"].append(f"In-process token exchange returned HTTP-style status {status}.")
    return status, json.loads(payload)


def verify_identity(tx, token):
    claims = jwt.decode(token["id_token"], tx["secret"], algorithms=["HS256"],
                        issuer=tx["issuer"], audience=CLIENT_ID,
                        options={"require": ["iss", "aud", "sub", "exp", "iat", "nonce", "at_hash"]})
    if claims["sub"] != SUBJECT or not secrets.compare_digest(claims["at_hash"], digest(token["access_token"], half=True)):
        raise ValueError("Identity or access-token binding failed")
    if tx["mode"] == "fixed" and not secrets.compare_digest(claims["nonce"], tx["nonce"]):
        raise ValueError("ID-token nonce differs from the saved client transaction")
    return claims


RESULT_SCRIPT = """(() => { 'use strict'; const config = JSON.parse(document.body.dataset.config); parent.postMessage(config.message, config.mainOrigin); })();"""


def finish(tx, outcome, boundary, detail, marker="OAUTH_REFUSED"):
    tx["phase"] = "complete"
    tx["codes"].clear()
    evidence = {"outcome": outcome, "boundary": boundary, "detail": detail, "marker": marker,
                "tokenStatuses": list(tx["tokenStatuses"]), "steps": list(tx["steps"])}
    data = {"mainOrigin": settings.LAB_MAIN_ORIGIN, "message": {"channel": "oauth-lesson-result",
            "runId": tx["runId"], "fixture": tx["fixture"], "mode": tx["mode"], "evidence": evidence}}
    nonce = secrets.token_urlsafe(24)
    body = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Local OAuth result</title><style>body{font:15px/1.5 system-ui;margin:18px;color:#24384c}h1{font-size:18px}code{overflow-wrap:anywhere}</style></head><body data-config="' + html.escape(json.dumps(data), quote=True) + '"><h1>' + html.escape(boundary) + '</h1><p><code id="marker">' + marker + '</code></p><p>' + html.escape(detail) + '</p><script nonce="' + nonce + '">' + RESULT_SCRIPT + '</script></body></html>'
    response = HttpResponse(body, content_type="text/html; charset=utf-8")
    response["Content-Security-Policy"] = f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'unsafe-inline'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors {settings.LAB_MAIN_ORIGIN}; sandbox allow-scripts"
    return response


@require_GET
def oauth_start(request):
    with LOCK:
        tx = resolve(request, {"run", "mode"})
        if not tx or tx["phase"] != "prepared":
            return invalid("This OAuth transaction is unavailable. Prepare a fresh comparison.", 404)
        tx["phase"] = "started"
        tx["steps"].append("Browser requested the client start URL.")
        response = HttpResponseRedirect(settings.LAB_MAIN_ORIGIN + "/lab/oauth/provider/authorize/?" + urlencode(authorize_parameters(tx)))
        response["Content-Security-Policy"] = "default-src 'none'; base-uri 'none'; form-action 'none'"
        return response


@require_GET
def oauth_authorize(request):
    with LOCK:
        keys = {"run", "mode", "response_type", "client_id", "scope", "code_challenge_method", "code_challenge", "state", "nonce", "redirect_uri"}
        tx = resolve(request, keys)
        if not tx or tx["phase"] != "started" or request.GET.dict() != authorize_parameters(tx):
            return invalid("Only the prepared authorization request is permitted.", 404)
        tx["steps"].append("Browser reached the local synthetic provider.")
        try:
            headers, _body, status = protocol_server(tx).create_authorization_response(
                request.build_absolute_uri(), scopes=["openid"], credentials={"user": SUBJECT})
        except OAuth2Error as error:
            return finish(tx, "rejected", "Provider redirect URI", "OAuthlib refused the unregistered callback (" + error.error + "); no code was issued.")
        if status != 302 or "Location" not in headers:
            return finish(tx, "rejected", "Provider authorization", "The provider did not issue an authorization redirect.")
        tx["phase"] = "authorized"
        response = HttpResponseRedirect(headers["Location"])
        response["Content-Security-Policy"] = "default-src 'none'; base-uri 'none'; form-action 'none'"
        return response


@require_GET
def oauth_callback(request):
    with LOCK:
        tx = resolve(request, {"run", "mode", "code", "state"})
        if not tx or tx["phase"] != "authorized" or tx["fixture"] == "invalid-redirect" or not bounded_callback_values(request):
            return invalid("This callback does not match an active client transaction.", 404)
        tx["phase"] = "callback"
        tx["steps"].append("Browser reached the registered client callback.")
        if tx["mode"] == "fixed" and not secrets.compare_digest(request.GET["state"], tx["state"]):
            return finish(tx, "rejected", "Client state", "The callback state did not match. No token exchange was attempted.")
        verifier = "wrong-" + tx["verifier"] if tx["fixture"] == "wrong-verifier" else tx["verifier"]
        status, token = exchange(tx, request.GET["code"], verifier)
        if status != 200:
            return finish(tx, "rejected", "Provider code exchange", "OAuthlib rejected the code exchange (" + token.get("error", "unknown") + "). No identity token was accepted.")
        try:
            verify_identity(tx, token)
        except (jwt.PyJWTError, ValueError, KeyError, TypeError):
            return finish(tx, "rejected", "Client ID-token validation", "The ID token failed identity validation against the saved client transaction. Token issuance is not successful login.")
        tx["steps"].append("Client verified signature, issuer, audience, time, subject and access-token hash.")
        if tx["fixture"] == "reused-code":
            replay_status, replay = exchange(tx, request.GET["code"])
            if replay_status != 200:
                return finish(tx, "rejected", "Provider code reuse", "First exchange succeeded; OAuthlib refused the second redemption (" + replay.get("error", "unknown") + ").", "FIRST_LOGIN_OK_REPLAY_REFUSED")
            verify_identity(tx, replay)
            return finish(tx, "accepted", "Provider code reuse", "Both exchanges issued tokens because the vulnerable provider failed to consume the code.", "REUSED_CODE_ACCEPTED")
        return finish(tx, "accepted", "Client identity", "The fictional identity was accepted. Compare the saved state, nonce and PKCE checks for this fixture.", "FICTIONAL_READER_ACCEPTED")


@require_GET
def oauth_alternate_callback(request):
    with LOCK:
        tx = resolve(request, {"run", "mode", "code", "state"})
        if not tx or tx["phase"] != "authorized" or tx["mode"] != "vulnerable" or tx["fixture"] != "invalid-redirect" or not bounded_callback_values(request) or request.GET["code"] not in tx["codes"]:
            return invalid("This alternate callback is only a predefined local marker.", 404)
        tx["steps"].append("Browser delivered the code to the unregistered owned callback.")
        return finish(tx, "redirected", "Provider redirect URI", "A real authorization code arrived at the alternate local callback. It is not exchanged and no identity is accepted.", "ALTERNATE_CALLBACK_CODE_MARKER")
