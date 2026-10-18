"""HTTP contracts for a real preflight; browser tests verify browser decisions."""
import json
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit

from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.test import Client, TestCase, override_settings
from django.urls import path

from . import preflight_lab as lesson


def csrf_bootstrap(request):
    return JsonResponse({"csrfToken": get_token(request)})


urlpatterns = [
    path("api/bootstrap", csrf_bootstrap),
    path("api/preflight/prepare/", lesson.preflight_prepare),
    path("api/preflight/state/", lesson.preflight_state),
    path("api/preflight/probe/<str:mode>/", lesson.preflight_probe),
    path("peer/preflight/", lesson.preflight_peer),
    path("peer/preflight/boot.js", lesson.preflight_peer_script),
]
MAIN = "http://127.0.0.1:8766"
PEER = "http://127.0.0.1:8767"


@override_settings(ROOT_URLCONF=__name__, LAB_ROLE="main", LAB_MAIN_ORIGIN=MAIN, LAB_PEER_ORIGIN=PEER)
class PreflightHTTPTests(TestCase):
    def setUp(self):
        with lesson._lock:
            lesson._runs.clear()
        self.client = Client(enforce_csrf_checks=True, HTTP_HOST="127.0.0.1:8766")
        self.csrf = self.client.get("/api/bootstrap").json()["csrfToken"]

    def prepare(self, fixture="allowed", raw=None, **kwargs):
        return self.client.post("/api/preflight/prepare/", raw if raw is not None else json.dumps({"fixture": fixture}), content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf, HTTP_ORIGIN=MAIN, **kwargs)

    def run_id(self, fixture="allowed"):
        response = self.prepare(fixture)
        self.assertEqual(response.status_code, 200)
        return response.json()["runId"]

    def url(self, run, mode="fixed"):
        return "/api/preflight/probe/" + mode + "/?" + urlencode({"run": run})

    def options(self, run, mode="fixed", client=None, method="POST", headers="content-type,x-lab-marker"):
        return (client or self.client).options(self.url(run, mode), HTTP_ORIGIN=PEER, HTTP_ACCESS_CONTROL_REQUEST_METHOD=method, HTTP_ACCESS_CONTROL_REQUEST_HEADERS=headers)

    def actual(self, run, mode="fixed", client=None, method="post", raw='{"action":"increment"}', origin=PEER, **headers):
        return getattr(client or self.client, method)(self.url(run, mode), raw, content_type="application/json", HTTP_ORIGIN=origin, HTTP_X_LAB_MARKER=lesson.MARKER, **headers)

    def state(self, run):
        return self.client.get("/api/preflight/state/", {"run": run}).json()["modes"]

    def test_prepare_requires_csrf_main_origin_and_fixed_unique_selector(self):
        self.assertEqual(self.client.get("/api/preflight/prepare/").status_code, 405)
        self.assertEqual(self.client.post("/api/preflight/prepare/", '{"fixture":"allowed"}', content_type="application/json").status_code, 403)
        for raw in ('{}', '[]', '{"fixture":[]}', '{"fixture":"custom"}', '{"fixture":"allowed","url":"https://example.invalid"}', '{"fixture":"allowed","fixture":"denied-origin"}', '{', '[' * 300):
            with self.subTest(raw=raw):
                self.assertIn(self.prepare(raw=raw).status_code, {400, 413})
        self.assertEqual(self.client.post("/api/preflight/prepare/?extra=1", '{"fixture":"allowed"}', content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf).status_code, 400)
        with override_settings(LAB_MAIN_ORIGIN="http://localhost:8766"):
            self.assertEqual(self.prepare().status_code, 400)

    def test_fresh_runs_are_fixed_peer_urls_and_owned_independent_counters(self):
        first = self.prepare().json()
        second = self.prepare().json()
        self.assertNotEqual(first["runId"], second["runId"])
        parsed = urlsplit(first["harness"])
        self.assertEqual(parsed.netloc, "127.0.0.1:8767")
        self.assertEqual(parsed.path, "/peer/preflight/")
        self.assertEqual(parse_qs(parsed.query), {"run": [first["runId"]], "fixture": ["allowed"]})
        self.assertNotIn("owner", first)
        self.assertEqual(self.actual(first["runId"]).status_code, 200)
        self.assertEqual(self.state(first["runId"])["fixed"]["mutations"], 1)
        self.assertEqual(self.state(second["runId"])["fixed"]["mutations"], 0)

    def test_cookie_free_preflight_succeeds_then_owned_actual_mutates_once(self):
        run = self.run_id()
        anonymous = Client(HTTP_HOST="127.0.0.1:8766")
        response = self.options(run, client=anonymous)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["Access-Control-Allow-Origin"], PEER)
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")
        self.assertEqual(response["Access-Control-Max-Age"], "0")
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(self.actual(run).status_code, 200)
        state = self.state(run)["fixed"]
        self.assertEqual((state["preflights"], state["actualRequests"], state["mutations"]), (1, 1, 1))
        self.assertFalse(state["preflightHadCookie"])
        self.assertEqual(self.actual(run).status_code, 409)
        self.assertEqual(self.state(run)["fixed"]["mutations"], 1)

    def test_policy_denials_omit_only_the_relevant_grant(self):
        for fixture in ("denied-method", "denied-header", "denied-origin"):
            run = self.run_id(fixture)
            method = "PUT" if fixture == "denied-method" else "POST"
            headers = "content-type,x-lab-marker,x-lab-extra" if fixture == "denied-header" else "content-type,x-lab-marker"
            vulnerable = self.options(run, "vulnerable", method=method, headers=headers)
            fixed = self.options(run, method=method, headers=headers)
            self.assertEqual(vulnerable.status_code, 204)
            self.assertEqual(vulnerable["Access-Control-Allow-Origin"], PEER)
            self.assertIn("PUT", vulnerable["Access-Control-Allow-Methods"])
            self.assertIn("X-Lab-Extra", vulnerable["Access-Control-Allow-Headers"])
            if fixture == "denied-method":
                self.assertEqual(fixed["Access-Control-Allow-Methods"], "POST")
            elif fixture == "denied-header":
                self.assertNotIn("X-Lab-Extra", fixed["Access-Control-Allow-Headers"])
            else:
                self.assertEqual(fixed["Access-Control-Allow-Origin"], MAIN)
            self.assertEqual(self.state(run)["fixed"]["actualRequests"], 0)

    def test_missing_actual_cors_headers_do_not_prevent_handler_mutation(self):
        run = self.run_id("missing-response-cors")
        for mode in lesson.MODES:
            self.assertEqual(self.options(run, mode)["Access-Control-Allow-Origin"], PEER)
            response = self.actual(run, mode)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.state(run)[mode]["mutations"], 1)
            if mode == "vulnerable":
                self.assertNotIn("Access-Control-Allow-Origin", response)
            else:
                self.assertEqual(response["Access-Control-Allow-Origin"], PEER)

    def test_permission_check_is_independent_of_cors_grants(self):
        run = self.run_id("auth-denied")
        for mode in lesson.MODES:
            self.assertEqual(self.options(run, mode).status_code, 204)
            response = self.actual(run, mode)
            self.assertEqual(response["Access-Control-Allow-Origin"], PEER)
            self.assertEqual(response.status_code, 403 if mode == "fixed" else 200)
        states = self.state(run)
        self.assertEqual(states["vulnerable"]["mutations"], 1)
        self.assertEqual(states["fixed"]["actualRequests"], 1)
        self.assertEqual(states["fixed"]["mutations"], 0)
        self.assertEqual(states["fixed"]["authorization"], "denied")

    def test_other_sessions_cannot_mutate_or_read_even_with_known_run(self):
        run = self.run_id()
        stranger = Client(HTTP_HOST="127.0.0.1:8766")
        for mode in lesson.MODES:
            self.assertEqual(self.actual(run, mode, client=stranger).status_code, 403)
        self.assertEqual(stranger.get("/api/preflight/state/", {"run": run}).status_code, 404)
        self.assertEqual(self.state(run)["fixed"]["actualRequests"], 0)

    def test_actual_requests_reject_unbounded_or_arbitrary_inputs_and_origins(self):
        run = self.run_id()
        for raw in ('{}', '[]', '{"action":"other"}', '{"action":"increment","action":"increment"}', '{"action":"increment","extra":true}', '{', 'x' * 129):
            self.assertIn(self.actual(run, raw=raw).status_code, {400, 413})
        self.assertEqual(self.actual(run, origin=MAIN).status_code, 403)
        self.assertEqual(self.actual(run, origin="null").status_code, 403)
        self.assertEqual(self.actual(run, method="put").status_code, 400)
        self.assertEqual(self.actual(run, HTTP_X_LAB_EXTRA="unexpected").status_code, 400)
        self.assertEqual(self.client.post(self.url(run), '{"action":"increment"}', content_type="application/json", HTTP_ORIGIN=PEER).status_code, 400)
        self.assertEqual(self.state(run)["fixed"]["mutations"], 0)

    def test_probe_rejects_duplicate_selectors_and_unknown_preflight_headers(self):
        run = self.run_id()
        self.assertEqual(self.options(run, headers="content-type,x-lab-marker,x-other").status_code, 400)
        self.assertEqual(self.options(run, headers="content-type,x-lab-marker,x-lab-marker").status_code, 400)
        self.assertEqual(self.options(run, method="DELETE").status_code, 400)
        for suffix in ("&run=" + run, "&url=https://example.invalid"):
            self.assertEqual(self.client.options(self.url(run) + suffix, HTTP_ORIGIN=PEER).status_code, 404)
        self.assertEqual(self.client.get(self.url(run)).status_code, 405)
        self.assertEqual(self.actual(run, mode="arbitrary").status_code, 404)

    def test_expiry_capacity_and_preflight_budget_are_bounded(self):
        run = self.run_id()
        for _ in range(3):
            self.assertEqual(self.options(run).status_code, 204)
        self.assertEqual(self.options(run).status_code, 409)
        with patch.object(lesson, "MAX_RUNS", 2):
            self.run_id()
            latest = self.run_id()
            self.assertEqual(len(lesson._runs), 2)
            self.assertNotIn(run, lesson._runs)
        lesson._runs[latest]["created"] -= lesson.RUN_TTL + 1
        self.assertEqual(self.client.get("/api/preflight/state/", {"run": latest}).status_code, 404)
        self.assertNotIn(latest, lesson._runs)

    def test_cors_is_not_an_application_authorization_gate(self):
        run = self.run_id("denied-origin")
        # A non-browser client with the owning session can call the handler.
        # Browser-only CORS permission never substitutes for authorization.
        response = self.actual(run)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.state(run)["fixed"]["mutations"], 1)

    def test_peer_is_fixed_role_scoped_and_restrictively_sandboxed(self):
        prepared = self.prepare().json()
        peer_path = "/peer/preflight/?" + urlsplit(prepared["harness"]).query
        self.assertEqual(self.client.get(peer_path).status_code, 404)
        with override_settings(LAB_ROLE="peer"):
            peer_client = Client(HTTP_HOST="127.0.0.1:8767")
            self.assertEqual(self.client.get(peer_path).status_code, 404)
            response = peer_client.get(peer_path)
            self.assertEqual(response.status_code, 200)
            for part in ("default-src 'none'", "script-src 'self'", f"connect-src {MAIN}", f"frame-ancestors {MAIN}", "sandbox allow-scripts allow-same-origin", "form-action 'none'"):
                self.assertIn(part, response["Content-Security-Policy"])
            self.assertEqual(peer_client.get("/peer/preflight/boot.js").content.decode(), lesson.PEER_SCRIPT)
            self.assertEqual(peer_client.get("/peer/preflight/boot.js?code=custom").status_code, 400)
            for suffix in ("&fixture=allowed", "&code=custom"):
                self.assertEqual(peer_client.get(peer_path + suffix).status_code, 400)
            for path in ("/api/bootstrap", "/api/preflight/state/?run=" + prepared["runId"], "/api/preflight/prepare/", self.url(prepared["runId"])):
                self.assertEqual(self.client.get(path).status_code, 404)
