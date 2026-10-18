"""Session-bound fixture inputs, opaque frame CSP, and local sanitizer delivery."""
import base64
import hashlib
import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import path

from . import trusted_lab as lab

urlpatterns = [path("api/trusted/prepare/", lab.trusted_prepare), path("lab/trusted/frame/", lab.trusted_frame)]


@override_settings(ROOT_URLCONF=__name__, LAB_MAIN_ORIGIN="http://testserver")
class TrustedTypesLabTests(TestCase):
    def prepare(self, fixture="event", client=None):
        response = (client or self.client).post("/api/trusted/prepare/", {"fixture": fixture}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def frame(self, prepared, mode="fixed", client=None):
        return (client or self.client).get("/lab/trusted/frame/", {"run": prepared["run"], "mode": mode})

    def test_all_fixtures_render_with_distinct_enforced_policy_allowlists(self):
        self.assertEqual({item["id"] for item in lab.trusted_metadata()["fixtures"]}, {"formatting", "text", "event", "raw-string", "forbidden-policy"})
        for fixture in lab.FIXTURES:
            prepared = self.prepare(fixture)
            for mode in lab.MODES:
                response = self.frame(prepared, mode)
                self.assertEqual(response.status_code, 200)
                policy = response["Content-Security-Policy"]
                self.assertIn("require-trusted-types-for 'script'", policy)
                self.assertIn("trusted-types " + ("lab-sanitize dompurify" if mode == "fixed" else "lab-pass"), policy)
                self.assertNotIn("'allow-duplicates'", policy)
                self.assertNotIn("trusted-types default", policy)
                for value in ("sandbox allow-scripts;", "connect-src 'none'", "worker-src 'none'", "frame-src 'none'", "object-src 'none'", "base-uri 'none'", "form-action 'none'", "img-src data:"):
                    self.assertIn(value, policy)
                self.assertNotIn("allow-same-origin", policy)
                self.assertEqual(response["Cache-Control"], "no-store")
                self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_pinned_local_sanitizer_and_nonce_are_delivered_only_in_fixed_frame(self):
        prepared = self.prepare("formatting")
        fixed = self.frame(prepared)
        text = fixed.content.decode()
        self.assertIn("DOMPurify " + lab.SANITIZER_VERSION, text)
        self.assertIn("Released under the Apache license", text)
        self.assertNotIn('<script src=', text)
        nonce = re.search(r"script-src 'nonce-([^']+)'", fixed["Content-Security-Policy"]).group(1)
        self.assertEqual(text.count('nonce="' + nonce + '"'), 3)
        self.assertNotIn(nonce, self.frame(prepared)["Content-Security-Policy"])
        self.assertNotIn("DOMPurify " + lab.SANITIZER_VERSION, self.frame(prepared, "vulnerable").content.decode())

    def test_only_exact_marker_handler_hash_is_allowed_without_unsafe_inline(self):
        prepared = self.prepare()
        expected_hash = base64.b64encode(hashlib.sha256(lab.HANDLER.encode()).digest()).decode()
        for mode in lab.MODES:
            policy = self.frame(prepared, mode)["Content-Security-Policy"]
            self.assertIn("script-src-attr 'unsafe-hashes' 'sha256-" + expected_hash + "'", policy)
            self.assertNotIn("'unsafe-inline'", policy)
            self.assertNotIn("'unsafe-eval'", policy)
        self.assertIn('src="data:,"', lab.FIXTURES["event"]["html"])
        self.assertIn(lab.HANDLER, lab.FIXTURES["event"]["html"])

    def test_fixture_payload_is_json_encoded_not_inserted_as_document_markup(self):
        prepared = self.prepare()
        source = self.frame(prepared, "vulnerable").content.decode()
        self.assertNotIn('<img src="data:,"', source)
        self.assertIn(r'\u003cimg', source)
        self.assertIn("RETURN_TRUSTED_TYPE:false", source)
        self.assertIn("ALLOWED_TAGS:['p','strong','em','code']", source)
        self.assertIn("ALLOWED_ATTR:[]", source)

    def test_missing_or_unexpected_asset_has_actionable_error_and_never_falls_back(self):
        prepared = self.prepare()
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with override_settings(FRONTEND_DIR=directory):
                response = self.frame(prepared)
                self.assertEqual(response.status_code, 503)
                self.assertIn("npm run build", response.json()["error"])
                for content in ("wrong version", "DOMPurify " + lab.SANITIZER_VERSION + " </script>", "DOMPurify " + lab.SANITIZER_VERSION + "x" * 200001):
                    (directory / "trusted-sanitizer.js").write_text(content, encoding="utf-8")
                    self.assertEqual(self.frame(prepared).status_code, 503)
                self.assertEqual(self.frame(prepared, "vulnerable").status_code, 200)

    def test_run_is_session_owned_and_new_preparation_revokes_old_frame(self):
        first = self.prepare()
        self.assertEqual(self.frame(first, client=Client()).status_code, 404)
        second = self.prepare("text")
        self.assertNotEqual(first["run"], second["run"])
        self.assertEqual(self.frame(first).status_code, 404)
        self.assertEqual(self.frame(second).status_code, 200)
        self.assertEqual(set(self.client.session[lab.SESSION_KEY]), {"run", "fixture", "expires"})

    def test_expiry_blocks_existing_frame_url(self):
        prepared = self.prepare()
        expires = self.client.session[lab.SESSION_KEY]["expires"]
        with patch.object(lab.time, "time", return_value=expires):
            self.assertEqual(self.frame(prepared).status_code, 404)

    def test_strict_fixture_body_query_and_method_contract(self):
        for body in ({}, [], {"fixture": []}, {"fixture": "unknown"}, {"fixture": "text", "html": "arbitrary"}, '{"fixture":"text","fixture":"event"}', "{" , " " * 1025):
            self.assertEqual(self.client.post("/api/trusted/prepare/", body, content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/api/trusted/prepare/?x=y", {"fixture": "text"}, content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/api/trusted/prepare/", json.dumps({"fixture": "text"}), content_type="text/plain").status_code, 400)
        prepared = self.prepare()
        for query in ({}, {"run": prepared["run"], "mode": "other"}, {"run": "../bad", "mode": "fixed"}, {"run": [prepared["run"]] * 2, "mode": "fixed"}, {"run": prepared["run"], "mode": "fixed", "extra": "x"}):
            self.assertEqual(self.client.get("/lab/trusted/frame/", query).status_code, 400)
        for method, endpoint, expected in (("get", "/api/trusted/prepare/", "POST"), ("post", "/lab/trusted/frame/", "GET")):
            response = getattr(self.client, method)(endpoint)
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], expected)

    def test_prepare_requires_csrf_and_rejects_companion_origin(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/api/trusted/prepare/", {"fixture": "text"}, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        self.assertEqual(client.post("/api/trusted/prepare/", {"fixture": "text"}, content_type="application/json", HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(client.post("/api/trusted/prepare/", {"fixture": "text"}, content_type="application/json", HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN=settings.LAB_PEER_ORIGIN).status_code, 403)

    def test_exact_origin_and_main_role_are_required(self):
        for endpoint in ("/api/trusted/prepare/", "/lab/trusted/frame/"):
            for options in ({"HTTP_HOST": "localhost"}, {"secure": True}):
                response = self.client.get(endpoint, **options)
                self.assertEqual(response.status_code, 400)
                self.assertIn("configured main lab origin", response.json()["error"])
            with override_settings(LAB_ROLE="peer"):
                self.assertEqual(self.client.get(endpoint).status_code, 404)
