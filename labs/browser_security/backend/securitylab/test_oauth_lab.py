"""Exercise real redirects, OAuthlib exchanges and OIDC validation in isolation."""
import html
import json
import re
from urllib.parse import parse_qs, urlencode, urlsplit
from unittest.mock import patch

from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.test import Client, TestCase, override_settings
from django.urls import path

from . import oauth_lab as lesson


def bootstrap(request):
    return JsonResponse({"csrfToken": get_token(request)})


urlpatterns = [
    path("api/bootstrap", bootstrap), path("api/oauth/prepare/", lesson.oauth_prepare),
    path("lab/oauth/start/", lesson.oauth_start),
    path("lab/oauth/provider/authorize/", lesson.oauth_authorize),
    path("lab/oauth/callback/", lesson.oauth_callback),
    path("lab/oauth/alternate-callback/", lesson.oauth_alternate_callback),
]
MAIN = "http://127.0.0.1:8766"


def result(response):
    match = re.search(r'data-config="([^"]+)"', response.content.decode())
    return json.loads(html.unescape(match.group(1)))["message"]["evidence"]


@override_settings(ROOT_URLCONF=__name__, LAB_ROLE="main", LAB_MAIN_ORIGIN=MAIN)
class OAuthFlowTests(TestCase):
    def setUp(self):
        lesson.RUNS.clear()
        self.client = Client(enforce_csrf_checks=True, HTTP_HOST="127.0.0.1:8766")
        self.csrf = self.client.get("/api/bootstrap").json()["csrfToken"]

    def prepare(self, fixture="valid", data=None, raw=None):
        return self.client.post("/api/oauth/prepare/", raw if raw is not None else json.dumps(data if data is not None else {"fixture": fixture}),
                                content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf, HTTP_ORIGIN=MAIN)

    def flow(self, fixture, mode, data=None):
        data = data or self.prepare(fixture).json()
        response = self.client.get(data["navigations"][mode])
        chain = []
        while response.status_code == 302 and len(chain) < 4:
            chain.append((response["Location"], response.status_code))
            # Django's auto-follow strips the non-default port from HTTP_HOST.
            response = self.client.get(response["Location"])
        response.redirect_chain = chain
        self.assertEqual(response.status_code, 200, response.content[:400])
        return result(response), response

    def test_valid_flow_uses_real_redirects_signed_identity_and_one_exchange(self):
        data = self.prepare().json()
        for mode in lesson.MODES:
            evidence, response = self.flow("valid", mode, data)
            self.assertEqual(evidence["outcome"], "accepted")
            self.assertEqual(evidence["marker"], "FICTIONAL_READER_ACCEPTED")
            self.assertEqual(evidence["tokenStatuses"], [200])
            self.assertEqual(len(response.redirect_chain), 2)
            self.assertIn("/provider/authorize/?", response.redirect_chain[0][0])
            self.assertIn("/callback/?", response.redirect_chain[1][0])
            self.assertEqual(lesson.RUNS[data["runId"]]["transactions"][mode]["issued"], 1)
            self.assertEqual(lesson.RUNS[data["runId"]]["transactions"][mode]["codes"], {})
            self.assertNotIn(b"access_token", response.content)
            self.assertNotIn(b"client_secret", response.content)

    def test_failure_occurs_at_the_responsible_boundary(self):
        cases = {"wrong-verifier": ("Provider code exchange", [400]), "state-mismatch": ("Client state", []),
                 "nonce-mismatch": ("Client ID-token validation", [200])}
        for fixture, (boundary, statuses) in cases.items():
            with self.subTest(fixture=fixture):
                data = self.prepare(fixture).json()
                vulnerable, _ = self.flow(fixture, "vulnerable", data)
                fixed, _ = self.flow(fixture, "fixed", data)
                self.assertEqual(vulnerable["outcome"], "accepted")
                self.assertEqual(vulnerable["tokenStatuses"], [200])
                self.assertEqual(fixed["outcome"], "rejected")
                self.assertEqual(fixed["boundary"], boundary)
                self.assertEqual(fixed["tokenStatuses"], statuses)

    def test_code_reuse_really_mints_twice_only_for_vulnerable_storage(self):
        data = self.prepare("reused-code").json()
        for mode, statuses, issued in (("vulnerable", [200, 200], 2), ("fixed", [200, 400], 1)):
            evidence, _ = self.flow("reused-code", mode, data)
            self.assertEqual(evidence["tokenStatuses"], statuses)
            self.assertEqual(lesson.RUNS[data["runId"]]["transactions"][mode]["issued"], issued)
            self.assertEqual(evidence["boundary"], "Provider code reuse")

    def test_provider_rejects_unregistered_redirect_before_code_issuance(self):
        data = self.prepare("invalid-redirect").json()
        vulnerable, response = self.flow("invalid-redirect", "vulnerable", data)
        self.assertEqual(vulnerable["outcome"], "redirected")
        self.assertIn("/alternate-callback/?", response.redirect_chain[-1][0])
        self.assertEqual(vulnerable["tokenStatuses"], [])
        fixed, response = self.flow("invalid-redirect", "fixed", data)
        self.assertEqual(fixed["boundary"], "Provider redirect URI")
        self.assertEqual(fixed["outcome"], "rejected")
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(lesson.RUNS[data["runId"]]["transactions"]["fixed"]["issued"], 0)
        self.assertNotIn("Provider issued an authorization code.", fixed["steps"])

    def test_prepare_requires_csrf_post_exact_fixture_and_main_origin(self):
        self.assertEqual(self.client.get("/api/oauth/prepare/").status_code, 405)
        self.assertEqual(self.client.post("/api/oauth/prepare/", '{"fixture":"valid"}', content_type="application/json").status_code, 403)
        for value in ({}, [], {"fixture": []}, {"fixture": "unknown"}, {"fixture": "valid", "redirect_uri": "https://example.invalid"}):
            self.assertEqual(self.prepare(data=value).status_code, 400)
        self.assertEqual(self.prepare(raw='{"fixture":"valid","fixture":"reused-code"}').status_code, 400)
        self.assertEqual(self.prepare(raw="x" * 300).status_code, 400)
        with override_settings(LAB_ROLE="peer"):
            self.assertEqual(self.prepare().status_code, 404)

    def test_transactions_are_owned_expiring_bounded_and_preserve_other_session_data(self):
        session = self.client.session
        session["other_lesson"] = "kept"
        session.save()
        first = self.prepare().json()
        stranger = Client(HTTP_HOST="127.0.0.1:8766")
        self.assertEqual(stranger.get(first["navigations"]["fixed"]).status_code, 404)
        for _ in range(lesson.MAX_OWNER_RUNS):
            self.prepare()
        self.assertNotIn(first["runId"], lesson.RUNS)
        self.assertEqual(len(lesson.RUNS), lesson.MAX_OWNER_RUNS)
        self.assertEqual(self.client.session["other_lesson"], "kept")
        data = self.prepare().json()
        lesson.RUNS[data["runId"]]["expires"] = 0
        self.assertEqual(self.client.get(data["navigations"]["fixed"]).status_code, 404)

    def test_only_prepared_authorization_parameters_and_one_callback_are_accepted(self):
        data = self.prepare().json()
        start = self.client.get(data["navigations"]["fixed"])
        self.assertEqual(self.client.get(data["navigations"]["fixed"]).status_code, 404)
        parsed = urlsplit(start["Location"])
        params = {key: values[0] for key, values in parse_qs(parsed.query).items()}
        params["redirect_uri"] = "https://example.invalid/"
        self.assertEqual(self.client.get(parsed.path + "?" + urlencode(params)).status_code, 404)
        self.assertEqual(self.client.get(start["Location"] + "&scope=openid").status_code, 404)
        authorization = self.client.get(start["Location"])
        callback = authorization["Location"]
        callback_url = urlsplit(callback)
        callback_params = {key: values[0] for key, values in parse_qs(callback_url.query).items()}
        for malformed in ("é" * 24, "x" * 129, ""):
            self.assertEqual(self.client.get(callback_url.path + "?" + urlencode({**callback_params, "state": malformed})).status_code, 404)
        self.assertEqual(self.client.get(callback).status_code, 200)
        self.assertEqual(self.client.get(callback).status_code, 404)

    def test_library_validates_secret_code_expiry_redirect_and_signature(self):
        data = self.prepare().json()
        start = self.client.get(data["navigations"]["fixed"])
        authorization = self.client.get(start["Location"])
        code = parse_qs(urlsplit(authorization["Location"]).query)["code"][0]
        tx = lesson.RUNS[data["runId"]]["transactions"]["fixed"]
        server = lesson.protocol_server(tx)
        body = {"grant_type": "authorization_code", "client_id": lesson.CLIENT_ID,
                "client_secret": "wrong", "code": code, "redirect_uri": tx["redirect"], "code_verifier": tx["verifier"]}
        self.assertEqual(server.create_token_response(tx["issuer"] + "token/", http_method="POST", body=urlencode(body))[2], 401)
        body["client_secret"] = tx["secret"]
        body["redirect_uri"] = tx["alternate"]
        self.assertEqual(server.create_token_response(tx["issuer"] + "token/", http_method="POST", body=urlencode(body))[2], 400)
        tx["codes"][code]["expires"] = 0
        self.assertEqual(lesson.exchange(tx, code)[0], 400)
        tx["codes"][code]["expires"] = lesson.time.monotonic() + 60
        status, token = lesson.exchange(tx, code)
        self.assertEqual(status, 200)
        self.assertNotIn("refresh_token", token)
        lesson.verify_identity(tx, token)
        with patch.dict(tx, secret="different-secret-that-is-at-least-thirty-two-bytes"):
            with self.assertRaises(lesson.jwt.InvalidSignatureError):
                lesson.verify_identity(tx, token)
        self.assertEqual(lesson.exchange(tx, code)[0], 400)

    def test_results_have_nonce_csp_opaque_origin_no_store_and_no_protocol_secrets(self):
        data = self.prepare().json()
        _, response = self.flow("valid", "fixed", data)
        self.assertIn("script-src 'nonce-", response["Content-Security-Policy"])
        self.assertIn("sandbox allow-scripts", response["Content-Security-Policy"])
        self.assertNotIn("allow-same-origin", response["Content-Security-Policy"])
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response["Referrer-Policy"], "no-referrer")
        tx = lesson.RUNS[data["runId"]]["transactions"]["fixed"]
        for key in ("state", "nonce", "verifier", "secret"):
            self.assertNotIn(tx[key].encode(), response.content)
