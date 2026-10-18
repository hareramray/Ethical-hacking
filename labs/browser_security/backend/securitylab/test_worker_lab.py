"""Worker policy headers, session ownership, and bounded HTTP collector contracts."""
import json
import re
from unittest.mock import patch

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import path

from . import worker_lab as lab

urlpatterns = [path("api/worker/prepare/", lab.worker_prepare), path("api/worker/state/", lab.worker_state),
               path("lab/worker/frame/", lab.worker_frame), path("lab/worker/marker.js", lab.worker_script),
               path("api/worker/report/", lab.worker_report)]


@override_settings(ROOT_URLCONF=__name__, LAB_MAIN_ORIGIN="http://testserver")
class WorkerLabTests(TestCase):
    def setUp(self):
        with lab.LOCK:
            lab.RUNS.clear()

    def prepare(self, fixture="enforce", client=None):
        response = (client or self.client).post("/api/worker/prepare/", {"fixture": fixture}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def frame(self, prepared, mode="experiment", client=None):
        return (client or self.client).get("/lab/worker/frame/", {"run": prepared["run"], "mode": mode})

    def report(self, prepared, mode="experiment"):
        response = self.frame(prepared, mode)
        policy = response.get("Content-Security-Policy-Report-Only", response["Content-Security-Policy"])
        destination = policy.split("report-uri ")[1]
        document, script = lab.paths(prepared["run"], mode)
        body = {"csp-report": {"document-uri": settings.LAB_MAIN_ORIGIN + document,
                "blocked-uri": settings.LAB_MAIN_ORIGIN + script, "effective-directive": "worker-src",
                "violated-directive": "worker-src", "original-policy": policy, "status-code": 200,
                "disposition": "report" if prepared["fixture"] == "report" and mode == "experiment" else "enforce",
                "referrer": "", "script-sample": "", "line-number": 20, "column-number": 14}}
        return destination, body

    def post_report(self, destination, body, client=None):
        return (client or self.client).post(destination, json.dumps(body), content_type="application/csp-report")

    def state(self, prepared, client=None):
        return (client or self.client).get("/api/worker/state/", {"run": prepared["run"]})

    def test_three_policy_fixtures_have_fresh_nonces_and_explicit_worker_policies(self):
        self.assertEqual({item["id"] for item in lab.worker_metadata()["fixtures"]}, {"allow", "enforce", "report"})
        for fixture in lab.FIXTURES:
            prepared = self.prepare(fixture)
            for mode in lab.MODES:
                response = self.frame(prepared, mode)
                self.assertEqual(response.status_code, 200)
                policy = response["Content-Security-Policy"]
                nonce = re.search(r"script-src 'nonce-([^']+)'", policy).group(1)
                self.assertEqual(response.content.decode().count('nonce="' + nonce + '"'), 2)
                self.assertNotIn(nonce, self.frame(prepared, mode)["Content-Security-Policy"])
                self.assertIn("worker-src " + ("'none'" if mode == "experiment" and fixture == "enforce" else "'self'"), policy)
                self.assertEqual("Content-Security-Policy-Report-Only" in response, fixture == "report" and mode == "experiment")
                if fixture == "report" and mode == "experiment":
                    self.assertTrue(response["Content-Security-Policy-Report-Only"].startswith("worker-src 'none'; report-uri /api/worker/report/"))
                for directive in ("connect-src 'none'", "frame-src 'none'", "base-uri 'none'", "form-action 'none'", "sandbox allow-scripts allow-same-origin"):
                    self.assertIn(directive, policy)
                self.assertEqual(response["Cache-Control"], "no-store")
                self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_worker_response_is_fixed_and_restricts_its_own_network_imports(self):
        prepared = self.prepare("allow")
        response = self.client.get("/lab/worker/marker.js", {"run": prepared["run"], "mode": "experiment"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "'use strict'; self.postMessage('HARMLESS_WORKER_MARKER'); self.close();\n")
        self.assertIn("application/javascript", response["Content-Type"])
        self.assertIn("connect-src 'none'", response["Content-Security-Policy"])
        self.assertIn("script-src 'none'", response["Content-Security-Policy"])

    def test_real_callback_contract_does_not_require_session_and_returns_normalized_data_only(self):
        for fixture in ("enforce", "report"):
            prepared = self.prepare(fixture)
            destination, body = self.report(prepared)
            self.assertEqual(self.state(prepared).json()["modes"]["experiment"], {"count": 0, "reports": []})
            # This unit test verifies parsing only; browser tests establish actual browser delivery.
            anonymous = Client(enforce_csrf_checks=True)
            self.assertEqual(self.post_report(destination, body, anonymous).status_code, 204)
            state = self.state(prepared).json()
            self.assertEqual(state["modes"]["control"], {"count": 0, "reports": []})
            self.assertEqual(state["modes"]["experiment"]["count"], 1)
            self.assertEqual(state["modes"]["experiment"]["reports"], [{"directive": "worker-src", "disposition": "report" if fixture == "report" else "enforce", "blockedPath": "/lab/worker/marker.js", "status": 200}])
            self.assertNotIn("cap", json.dumps(state))
            self.assertNotIn("original-policy", json.dumps(state))

    def test_forged_mismatched_oversize_and_duplicate_reports_do_not_increment_counts(self):
        prepared = self.prepare()
        destination, body = self.report(prepared)
        for field, value in {"document-uri": settings.LAB_MAIN_ORIGIN + "/", "blocked-uri": "http://example.invalid/worker.js", "effective-directive": "script-src", "original-policy": "worker-src 'none'", "disposition": "report", "status-code": 201, "extra": "field", "script-sample": "x" * 4097, "line-number": True}.items():
            with self.subTest(field=field):
                altered = {"csp-report": {**body["csp-report"], field: value}}
                self.assertEqual(self.post_report(destination, altered).status_code, 400)
        for invalid in ([], {}, {"csp-report": []}, {"csp-report": {}}, {"csp-report": body["csp-report"], "extra": True}):
            self.assertEqual(self.post_report(destination, invalid).status_code, 400)
        for raw in ("{", '{"csp-report":{},"csp-report":{}}', " " * 8193):
            self.assertEqual(self.client.post(destination, raw, content_type="application/csp-report").status_code, 400)
        self.assertEqual(self.client.post(destination, json.dumps(body), content_type="application/json").status_code, 400)
        self.assertEqual(self.post_report(destination.rsplit("=", 1)[0] + "=" + "0" * 48, body).status_code, 404)
        self.assertEqual(self.post_report(destination + "&mode=experiment", body).status_code, 400)
        self.assertEqual(self.state(prepared).json()["modes"]["experiment"]["count"], 0)

    def test_control_rejects_reports_and_per_run_limit_bounds_memory(self):
        prepared = self.prepare()
        destination, body = self.report(prepared, "control")
        self.assertEqual(self.post_report(destination, body).status_code, 400)
        destination, body = self.report(prepared)
        for _ in range(lab.MAX_REPORTS):
            self.assertEqual(self.post_report(destination, body).status_code, 204)
        self.assertEqual(self.post_report(destination, body).status_code, 429)
        self.assertEqual(self.state(prepared).json()["modes"]["experiment"]["count"], lab.MAX_REPORTS)

    def test_new_run_revokes_previous_capability_and_other_sessions_cannot_read_or_render(self):
        first = self.prepare()
        destination, body = self.report(first)
        other = Client()
        self.assertEqual(self.frame(first, client=other).status_code, 404)
        self.assertEqual(self.state(first, client=other).status_code, 404)
        self.assertEqual(other.get("/lab/worker/marker.js", {"run": first["run"], "mode": "control"}).status_code, 404)
        second = self.prepare("report")
        self.assertNotEqual(first["run"], second["run"])
        self.assertEqual(self.state(first).status_code, 404)
        self.assertEqual(self.post_report(destination, body).status_code, 404)
        self.assertEqual(self.state(second).status_code, 200)

    def test_store_expires_and_evicts_oldest_runs(self):
        with patch.object(lab.time, "monotonic", return_value=1000):
            prepared = self.prepare()
            destination, body = self.report(prepared)
        with patch.object(lab.time, "monotonic", return_value=1000 + lab.RUN_TTL):
            self.assertEqual(self.state(prepared).status_code, 404)
            self.assertEqual(self.post_report(destination, body).status_code, 404)
        first = self.prepare()
        with patch.object(lab, "MAX_RUNS", 2):
            self.prepare(client=Client())
            last = self.prepare(client=Client())
        self.assertEqual(len(lab.RUNS), 2)
        self.assertNotIn(first["run"], lab.RUNS)
        self.assertIn(last["run"], lab.RUNS)

    def test_strict_selectors_queries_and_methods(self):
        for body in ({}, [], {"fixture": []}, {"fixture": "missing"}, {"fixture": "allow", "code": "arbitrary"}, '{"fixture":"allow","fixture":"report"}', " " * 1025):
            self.assertEqual(self.client.post("/api/worker/prepare/", body, content_type="application/json").status_code, 400)
        prepared = self.prepare()
        for endpoint in ("/lab/worker/frame/", "/lab/worker/marker.js"):
            for query in ({}, {"run": prepared["run"], "mode": "other"}, {"run": "../bad", "mode": "control"}, {"run": [prepared["run"]] * 2, "mode": "control"}, {"run": prepared["run"], "mode": "control", "extra": "x"}):
                self.assertEqual(self.client.get(endpoint, query).status_code, 400)
            self.assertEqual(self.client.post(endpoint).status_code, 405)
        self.assertEqual(self.client.get("/api/worker/state/", {"run": [prepared["run"]] * 2}).status_code, 400)
        self.assertEqual(self.client.post("/api/worker/state/").status_code, 405)
        for endpoint in ("/api/worker/prepare/", "/api/worker/report/"):
            self.assertEqual(self.client.get(endpoint).status_code, 405)

    def test_only_report_protocol_exempts_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/api/worker/prepare/", {"fixture": "allow"}, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        self.assertEqual(client.post("/api/worker/prepare/", {"fixture": "allow"}, content_type="application/json", HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(client.post("/api/worker/prepare/", {"fixture": "allow"}, content_type="application/json", HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN=settings.LAB_PEER_ORIGIN).status_code, 403)

    def test_alias_hosts_and_wrong_scheme_fail_with_clear_origin_error(self):
        for endpoint in ("/api/worker/prepare/", "/api/worker/state/", "/api/worker/report/", "/lab/worker/frame/", "/lab/worker/marker.js"):
            for options in ({"HTTP_HOST": "localhost"}, {"secure": True}):
                response = self.client.get(endpoint, **options)
                self.assertEqual(response.status_code, 400)
                self.assertIn("configured main lab origin", response.json()["error"])

    @override_settings(LAB_ROLE="peer")
    def test_peer_cannot_host_this_lesson(self):
        for endpoint in ("/api/worker/prepare/", "/api/worker/state/", "/api/worker/report/", "/lab/worker/frame/", "/lab/worker/marker.js"):
            self.assertEqual(self.client.get(endpoint).status_code, 404)
