"""HTTP/configuration tests. Playwright verifies browser origin/source and sinks."""
import json
from urllib.parse import parse_qs, urlencode, urlsplit

from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.test import Client, SimpleTestCase, override_settings
from django.urls import path
from django.views.decorators.http import require_GET

from . import message_lab as lesson


@require_GET
def csrf_bootstrap(request):
    return JsonResponse({"csrfToken": get_token(request)})


urlpatterns = [
    path("api/bootstrap", csrf_bootstrap),
    path("api/message/prepare/", lesson.message_prepare),
    path("peer/message/", lesson.message_receiver),
    path("peer/message/receiver.js", lesson.message_receiver_script),
    path("lab/message/sender/", lesson.message_sender),
    path("lab/message/sender.js", lesson.message_sender_script),
]

MAIN = "http://127.0.0.1:8766"
PEER = "http://127.0.0.1:8767"
RUN = "a" * 24


@override_settings(ROOT_URLCONF=__name__, LAB_ROLE="main", LAB_MAIN_ORIGIN=MAIN, LAB_PEER_ORIGIN=PEER)
class MessageHTTPTests(SimpleTestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True, HTTP_HOST="127.0.0.1:8766")
        self.csrf = self.client.get("/api/bootstrap").json()["csrfToken"]

    def prepare(self, data=None, path="/api/message/prepare/"):
        return self.client.post(path, json.dumps(data if data is not None else {"fixture": "normal"}), content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf, HTTP_ORIGIN=MAIN)

    def test_preparation_returns_fresh_fixed_peer_urls_for_every_fixture(self):
        runs = set()
        for fixture in lesson.FIXTURES:
            response = self.prepare({"fixture": fixture["id"]})
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertRegex(body["runId"], r"^[A-Za-z0-9_-]{24}$")
            runs.add(body["runId"])
            self.assertEqual(body["mainOrigin"], MAIN)
            for mode, url in body["receivers"].items():
                parts = urlsplit(url)
                self.assertEqual(parts.netloc, "127.0.0.1:8767")
                self.assertEqual(parts.path, "/peer/message/")
                self.assertEqual(parse_qs(parts.query), {"fixture": [fixture["id"]], "mode": [mode], "run": [body["runId"]]})
        self.assertEqual(len(runs), len(lesson.FIXTURES))

    def test_preparation_requires_main_origin_post_and_csrf(self):
        self.assertEqual(self.client.get("/api/message/prepare/").status_code, 405)
        self.assertEqual(self.client.post("/api/message/prepare/", '{"fixture":"normal"}', content_type="application/json").status_code, 403)
        self.assertEqual(self.client.post("/api/message/prepare/", '{"fixture":"normal"}', content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf, HTTP_ORIGIN=PEER).status_code, 403)
        with override_settings(LAB_MAIN_ORIGIN="http://localhost:8766"):
            self.assertEqual(self.prepare().status_code, 400)

    def test_only_bounded_exact_fixture_selections_are_accepted(self):
        for value in ({}, [], {"fixture": []}, {"fixture": "custom"}, {"fixture": "normal", "html": "<b>custom</b>"}, {"fixture": "x" * 300}):
            with self.subTest(value=value):
                self.assertIn(self.prepare(value).status_code, {400, 413})
        self.assertEqual(self.prepare(path="/api/message/prepare/?extra=1").status_code, 400)
        for raw in ('{"fixture":"normal","fixture":"markup"}', '{', '[' * 2000):
            response = self.client.post("/api/message/prepare/", raw, content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf)
            self.assertIn(response.status_code, {400, 413})

    def test_receivers_exist_only_on_peer_with_strict_frame_and_resource_policy(self):
        url = "/peer/message/?" + urlencode({"run": RUN, "fixture": "markup", "mode": "vulnerable"})
        self.assertEqual(self.client.get(url).status_code, 404)
        with override_settings(LAB_ROLE="peer"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            csp = response["Content-Security-Policy"]
            for part in ("default-src 'none'", "connect-src 'none'", "form-action 'none'", "base-uri 'none'", "sandbox allow-scripts allow-same-origin", f"frame-ancestors {MAIN}"):
                self.assertIn(part, csp)
            self.assertEqual(response["X-Content-Type-Options"], "nosniff")
            self.assertEqual(response["Cache-Control"], "no-store")
            self.assertNotIn(b"onerror=", response.content)
            self.assertNotIn(b"<script>", response.content)

    def test_receiver_query_rejects_duplicates_extra_fields_and_injected_values(self):
        base = "/peer/message/?" + urlencode({"run": RUN, "fixture": "normal", "mode": "fixed"})
        with override_settings(LAB_ROLE="peer"):
            for url in (base + "&fixture=markup", base + "&html=anything", base.replace(RUN, "bad"), base.replace("normal", "%3Cscript%3E"), base.replace("fixed", "custom"), "/peer/message/"):
                self.assertEqual(self.client.get(url).status_code, 400)

    def test_fixed_sender_pages_are_available_on_both_roles_without_arbitrary_input(self):
        base = "/lab/message/sender/?" + urlencode({"run": RUN, "fixture": "markup", "slot": "trusted"})
        for role in ("main", "peer"):
            with self.subTest(role=role), override_settings(LAB_ROLE=role):
                response = self.client.get(base)
                self.assertEqual(response.status_code, 200)
                self.assertIn("script-src 'self';", response["Content-Security-Policy"])
                self.assertNotIn("unsafe-inline", response["Content-Security-Policy"])
                self.assertIn(f"frame-ancestors {MAIN} {PEER}", response["Content-Security-Policy"])
                self.assertNotIn(b"onerror=", response.content)
                for query in ("&slot=secondary", "&html=custom", "&origin=https://example.invalid"):
                    self.assertEqual(self.client.get(base + query).status_code, 400)

    def test_scripts_are_fixed_and_do_not_accept_interpolated_source(self):
        self.assertEqual(self.client.get("/peer/message/receiver.js").status_code, 404)
        for role in ("main", "peer"):
            with override_settings(LAB_ROLE=role):
                response = self.client.get("/lab/message/sender.js")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content.decode(), lesson.SENDER_SCRIPT)
                self.assertEqual(self.client.get("/lab/message/sender.js?code=anything").status_code, 400)
        with override_settings(LAB_ROLE="peer"):
            response = self.client.get("/peer/message/receiver.js")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.decode(), lesson.RECEIVER_SCRIPT)
            self.assertEqual(self.client.get("/peer/message/receiver.js?code=anything").status_code, 400)

    def test_peer_role_still_blocks_application_apis(self):
        with override_settings(LAB_ROLE="peer"):
            self.assertEqual(self.client.get("/api/bootstrap").status_code, 404)
            self.assertEqual(self.prepare().status_code, 404)
