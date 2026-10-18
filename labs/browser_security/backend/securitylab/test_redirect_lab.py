"""Redirect response and containment contracts; browsers verify navigation."""
import json
from urllib.parse import parse_qs, urlencode, urlsplit

from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.test import Client, SimpleTestCase, override_settings
from django.urls import path

from . import redirect_lab as lesson


def bootstrap(request):
    return JsonResponse({"csrfToken": get_token(request)})


urlpatterns = [
    path("api/bootstrap", bootstrap),
    path("api/redirect/prepare/", lesson.redirect_prepare),
    path("lab/redirect/go/", lesson.redirect_go),
    path("lab/redirect/landing/", lesson.redirect_landing),
    path("peer/redirect/landing/", lesson.redirect_peer_landing),
]
MAIN = "http://127.0.0.1:8766"
PEER = "http://127.0.0.1:8767"
RUN = "a" * 24


@override_settings(ROOT_URLCONF=__name__, LAB_ROLE="main", LAB_MAIN_ORIGIN=MAIN, LAB_PEER_ORIGIN=PEER)
class RedirectHTTPTests(SimpleTestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True, HTTP_HOST="127.0.0.1:8766")
        self.csrf = self.client.get("/api/bootstrap").json()["csrfToken"]

    def prepare(self, data=None, path="/api/redirect/prepare/", raw=None, content_type="application/json"):
        payload = raw if raw is not None else json.dumps({"fixture": "allowed"} if data is None else data)
        return self.client.post(path, payload, content_type=content_type, HTTP_X_CSRFTOKEN=self.csrf, HTTP_ORIGIN=MAIN)

    def url(self, fixture="allowed", mode="vulnerable", path="/lab/redirect/go/"):
        return path + "?" + urlencode({"run": RUN, "fixture": fixture, "mode": mode})

    def test_prepare_makes_fresh_main_handler_urls_for_only_named_fixtures(self):
        runs = set()
        for fixture in lesson.FIXTURES:
            response = self.prepare({"fixture": fixture["id"]})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertRegex(data["runId"], r"^[A-Za-z0-9_-]{24}$")
            runs.add(data["runId"])
            self.assertEqual(data["candidate"], lesson.candidate_for(fixture["id"]))
            for mode, url in data["navigations"].items():
                parsed = urlsplit(url)
                self.assertEqual(parsed.netloc, "127.0.0.1:8766")
                self.assertEqual(parsed.path, "/lab/redirect/go/")
                self.assertEqual(parse_qs(parsed.query), {"run": [data["runId"]], "fixture": [fixture["id"]], "mode": [mode]})
        self.assertEqual(len(runs), len(lesson.FIXTURES))

    def test_prepare_requires_post_csrf_main_host_and_role(self):
        self.assertEqual(self.client.get("/api/redirect/prepare/").status_code, 405)
        self.assertEqual(self.client.post("/api/redirect/prepare/", '{"fixture":"allowed"}', content_type="application/json").status_code, 403)
        self.assertEqual(self.client.post("/api/redirect/prepare/", '{"fixture":"allowed"}', content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf, HTTP_ORIGIN=PEER).status_code, 403)
        with override_settings(LAB_MAIN_ORIGIN="http://localhost:8766"):
            self.assertEqual(self.prepare().status_code, 400)
        with override_settings(LAB_ROLE="peer"):
            self.assertEqual(self.prepare().status_code, 404)

    def test_prepare_rejects_custom_url_shapes_duplicates_and_large_payloads(self):
        for value in ({}, [], {"fixture": []}, {"fixture": "unknown"}, {"fixture": "allowed", "next": "https://example.invalid"}, {"fixture": "x" * 300}):
            with self.subTest(value=value):
                self.assertIn(self.prepare(value).status_code, {400, 413})
        for raw in ('{"fixture":"allowed","fixture":"absolute-peer"}', '{', '[' * 270):
            self.assertIn(self.prepare(raw=raw).status_code, {400, 413})
        self.assertEqual(self.prepare(path="/api/redirect/prepare/?next=anything").status_code, 400)
        self.assertEqual(self.prepare(content_type="text/plain").status_code, 400)

    def test_vulnerable_handlers_emit_real_owned_302_locations(self):
        for fixture in lesson.FIXTURES:
            response = self.client.get(self.url(fixture["id"]))
            self.assertEqual(response.status_code, 302)
            candidate, query = response["Location"].split("?", 1)
            self.assertEqual(candidate, lesson.candidate_for(fixture["id"]))
            self.assertEqual(parse_qs(query), {"run": [RUN], "fixture": [fixture["id"]], "mode": ["vulnerable"]})
            self.assertEqual(response["Cache-Control"], "no-store")
            self.assertEqual(response["Referrer-Policy"], "no-referrer")

    def test_fixed_retains_legitimate_navigation_and_refuses_other_candidates(self):
        good = self.client.get(self.url("allowed", "fixed"))
        self.assertEqual(good.status_code, 302)
        self.assertTrue(good["Location"].startswith("/lab/redirect/landing/?"))
        for fixture in ("absolute-peer", "scheme-relative-peer", "normalized-path"):
            response = self.client.get(self.url(fixture, "fixed"))
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("Location", response)
            self.assertIn(b'RETURN_URL_REJECTED', response.content)
            self.assertIn("sandbox allow-scripts", response["Content-Security-Policy"])
            self.assertNotIn("allow-same-origin", response["Content-Security-Policy"])

    def test_return_rule_rejects_parser_ambiguity_and_nonpermitted_local_paths(self):
        self.assertTrue(lesson.permitted_return_path("/lab/redirect/landing/"))
        values = (None, [], "", "https://example.invalid/", "//example.invalid/", "///example.invalid/", "javascript:alert(1)",
                  "\\\\example.invalid\\", "/\\example.invalid/", " /lab/redirect/landing/", "\n/lab/redirect/landing/",
                  "/lab/redirect/lan\tding/", "/lab/redirect/landing/\x00", "/lab/redirect/landing/\x7f",
                  "/lab/redirect/%6canding/", "/lab/redirect/%2e/landing/", "/lab/redirect/../landing/",
                  "/lab/redirect/discard/../landing/", "/lab/redirect/landing/?next=anything", "/lab/redirect/landing/#part",
                  "/admin/", "http://[broken", "/" + "a" * 300)
        for value in values:
            with self.subTest(value=value):
                self.assertFalse(lesson.permitted_return_path(value))

    def test_main_landing_has_a_fixed_marker_and_nonce_script_only(self):
        for fixture, mode in (("allowed", "vulnerable"), ("allowed", "fixed"), ("normalized-path", "vulnerable")):
            response = self.client.get(self.url(fixture, mode, "/lab/redirect/landing/"))
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'MAIN_RETURN_MARKER', response.content)
            policy = response["Content-Security-Policy"]
            self.assertIn("script-src 'nonce-", policy)
            self.assertIn("connect-src 'none'", policy)
            self.assertIn(f"frame-ancestors {MAIN}", policy)
            self.assertNotIn("allow-same-origin", policy)
        first = self.client.get(self.url(path="/lab/redirect/landing/"))
        second = self.client.get(self.url(path="/lab/redirect/landing/"))
        self.assertNotEqual(first["Content-Security-Policy"], second["Content-Security-Policy"])

    def test_companion_serves_only_matching_fixed_marker_not_main_apis(self):
        with override_settings(LAB_ROLE="peer"):
            peer = Client(HTTP_HOST="127.0.0.1:8767")
            for fixture in ("absolute-peer", "scheme-relative-peer"):
                response = peer.get(self.url(fixture, path="/peer/redirect/landing/"))
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'COMPANION_RETURN_MARKER', response.content)
                self.assertEqual(peer.get(self.url(fixture, "fixed", "/peer/redirect/landing/")).status_code, 400)
            self.assertEqual(peer.get(self.url("allowed", path="/peer/redirect/landing/")).status_code, 400)
            for path_value in ("/api/bootstrap", "/api/redirect/prepare/", self.url(), self.url(path="/lab/redirect/landing/")):
                self.assertEqual(peer.get(path_value).status_code, 404)
            self.assertEqual(self.client.get(self.url("absolute-peer", path="/peer/redirect/landing/")).status_code, 404)

    def test_markers_cannot_claim_inconsistent_fixture_results(self):
        self.assertEqual(self.client.get(self.url("absolute-peer", path="/lab/redirect/landing/")).status_code, 400)
        self.assertEqual(self.client.get(self.url("normalized-path", "fixed", "/lab/redirect/landing/")).status_code, 400)
        self.assertEqual(self.client.get(self.url("absolute-peer", path="/peer/redirect/landing/")).status_code, 404)

    def test_documents_validate_query_fields_host_scheme_and_methods(self):
        for path_value in (self.url(), self.url(path="/lab/redirect/landing/")):
            for malformed in (path_value + "&mode=fixed", path_value + "&next=https://example.invalid", path_value.replace(RUN, "short"), path_value.replace("allowed", "%3Cscript%3E"), path_value.split("?")[0]):
                self.assertEqual(self.client.get(malformed).status_code, 400)
            self.assertEqual(self.client.get(path_value, HTTP_HOST="localhost:8766").status_code, 404)
            self.assertEqual(self.client.get(path_value, secure=True).status_code, 404)
            self.assertEqual(self.client.post(path_value, HTTP_X_CSRFTOKEN=self.csrf).status_code, 405)

