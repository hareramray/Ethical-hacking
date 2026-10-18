"""HTTP policy contracts; browser tests establish actual refusal and clicks."""
import json
from urllib.parse import parse_qs, urlencode, urlsplit

from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.test import Client, SimpleTestCase, override_settings
from django.urls import path

from . import framing_lab as lesson


def csrf_bootstrap(request):
    return JsonResponse({"csrfToken": get_token(request)})


urlpatterns = [
    path("api/bootstrap", csrf_bootstrap),
    path("api/framing/prepare/", lesson.framing_prepare),
    path("peer/framing/", lesson.framing_peer),
    path("peer/framing/boot.js", lesson.framing_peer_script),
    path("lab/framing/target/", lesson.framing_target),
    path("lab/framing/target.js", lesson.framing_target_script),
]
MAIN = "http://127.0.0.1:8766"
PEER = "http://127.0.0.1:8767"
RUN = "a" * 24


@override_settings(ROOT_URLCONF=__name__, LAB_ROLE="main", LAB_MAIN_ORIGIN=MAIN, LAB_PEER_ORIGIN=PEER)
class FramingHTTPTests(SimpleTestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True, HTTP_HOST="127.0.0.1:8766")
        self.csrf = self.client.get("/api/bootstrap").json()["csrfToken"]

    def prepare(self, data=None, path="/api/framing/prepare/"):
        return self.client.post(path, json.dumps({"fixture": "csp-self"} if data is None else data), content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf, HTTP_ORIGIN=MAIN)

    def target(self, fixture="csp-self", mode="fixed"):
        return "/lab/framing/target/?" + urlencode({"run": RUN, "fixture": fixture, "mode": mode})

    def test_preparation_produces_fresh_fixed_companion_urls(self):
        runs = set()
        for fixture in lesson.FIXTURES:
            response = self.prepare({"fixture": fixture["id"]})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertRegex(data["runId"], r"^[A-Za-z0-9_-]{24}$")
            runs.add(data["runId"])
            self.assertEqual(data["mainOrigin"], MAIN)
            for mode, url in data["harnesses"].items():
                parsed = urlsplit(url)
                self.assertEqual(parsed.netloc, "127.0.0.1:8767")
                self.assertEqual(parsed.path, "/peer/framing/")
                self.assertEqual(parse_qs(parsed.query), {"run": [data["runId"]], "fixture": [fixture["id"]], "mode": [mode]})
        self.assertEqual(len(runs), len(lesson.FIXTURES))

    def test_preparation_requires_post_csrf_and_configured_main_origin(self):
        self.assertEqual(self.client.get("/api/framing/prepare/").status_code, 405)
        self.assertEqual(self.client.post("/api/framing/prepare/", '{"fixture":"csp-self"}', content_type="application/json").status_code, 403)
        self.assertEqual(self.client.post("/api/framing/prepare/", '{"fixture":"csp-self"}', content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf, HTTP_ORIGIN=PEER).status_code, 403)
        with override_settings(LAB_MAIN_ORIGIN="http://localhost:8766"):
            self.assertEqual(self.prepare().status_code, 400)

    def test_preparation_only_accepts_bounded_unique_fixture_selector(self):
        for value in ({}, [], {"fixture": []}, {"fixture": "custom"}, {"fixture": "csp-self", "url": "https://example.invalid"}, {"fixture": "x" * 300}):
            with self.subTest(value=value):
                self.assertIn(self.prepare(value).status_code, {400, 413})
        self.assertEqual(self.prepare(path="/api/framing/prepare/?extra=1").status_code, 400)
        for raw in ('{"fixture":"csp-self","fixture":"allowed-integration"}', '{', '[' * 300):
            response = self.client.post("/api/framing/prepare/", raw, content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf)
            self.assertIn(response.status_code, {400, 413})

    def test_unprotected_target_does_not_gain_implicit_framing_policy(self):
        for fixture in lesson.FIXTURES:
            response = self.client.get(self.target(fixture["id"], "vulnerable"))
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("frame-ancestors", response["Content-Security-Policy"])
            self.assertNotIn("X-Frame-Options", response)
            self.assertIn("default-src 'none'", response["Content-Security-Policy"])
            self.assertIn("sandbox allow-scripts allow-same-origin", response["Content-Security-Policy"])

    def test_fixed_targets_use_independent_csp_xfo_and_explicit_allow_policies(self):
        csp = self.client.get(self.target())
        self.assertIn("frame-ancestors 'self'", csp["Content-Security-Policy"])
        self.assertNotIn("X-Frame-Options", csp)
        xfo = self.client.get(self.target("xfo-sameorigin"))
        self.assertEqual(xfo["X-Frame-Options"], "SAMEORIGIN")
        self.assertNotIn("frame-ancestors", xfo["Content-Security-Policy"])
        allowed = self.client.get(self.target("allowed-integration"))
        self.assertIn(f"frame-ancestors {MAIN} {PEER}", allowed["Content-Security-Policy"])
        self.assertNotIn("X-Frame-Options", allowed)

    def test_documents_reject_repeated_unknown_and_injected_query_fields(self):
        for path in (self.target(), self.target().replace("/lab/framing/target/", "/peer/framing/")):
            role = "peer" if path.startswith("/peer/") else "main"
            with override_settings(LAB_ROLE=role):
                for bad in (path + "&mode=vulnerable", path + "&html=anything", path.replace(RUN, "bad"), path.replace("csp-self", "%3Cscript%3E"), path.replace("fixed", "custom"), path.split("?")[0]):
                    self.assertEqual(self.client.get(bad).status_code, 400)

    def test_companion_harness_has_fixed_target_and_restrictive_policy(self):
        path = self.target().replace("/lab/framing/target/", "/peer/framing/")
        self.assertEqual(self.client.get(path).status_code, 404)
        with override_settings(LAB_ROLE="peer"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            policy = response["Content-Security-Policy"]
            for part in (f"frame-src {MAIN}", f"frame-ancestors {MAIN}", "connect-src 'none'", "form-action 'none'", "sandbox allow-scripts allow-same-origin"):
                self.assertIn(part, policy)
            self.assertEqual(response["X-Content-Type-Options"], "nosniff")
            self.assertEqual(response["Cache-Control"], "no-store")
            self.assertNotIn(b"<script>", response.content)

    def test_scripts_are_role_scoped_and_reject_parameters(self):
        for role, path, source in (("main", "/lab/framing/target.js", lesson.TARGET_SCRIPT), ("peer", "/peer/framing/boot.js", lesson.PEER_SCRIPT)):
            with override_settings(LAB_ROLE=role):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content.decode(), source)
                self.assertEqual(self.client.get(path + "?code=custom").status_code, 400)
                self.assertEqual(self.client.post(path, "{}", content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf).status_code, 405)
        self.assertEqual(self.client.get("/peer/framing/boot.js").status_code, 404)

    def test_peer_cannot_serve_main_targets_or_application_apis(self):
        with override_settings(LAB_ROLE="peer"):
            for path in ("/api/bootstrap", self.target(), "/lab/framing/target.js"):
                self.assertEqual(self.client.get(path).status_code, 404)
            self.assertEqual(self.prepare().status_code, 404)
