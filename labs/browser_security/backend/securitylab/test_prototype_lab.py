"""Fixture selection, session binding, response sandboxing, and CSRF boundaries."""
import json
import re

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import path

from .prototype_lab import FIXTURES, SESSION_KEY, prototype_frame, prototype_metadata, prototype_prepare

urlpatterns = [
    path("api/prototype/prepare/", prototype_prepare),
    path("lab/prototype/frame/", prototype_frame),
]


@override_settings(ROOT_URLCONF=__name__)
class PrototypeLabTests(TestCase):
    def prepare(self, fixture="normal", client=None):
        response = (client or self.client).post("/api/prototype/prepare/", {"fixture": fixture}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def frame(self, prepared, mode="fixed", client=None):
        return (client or self.client).get("/lab/prototype/frame/", {"run": prepared["run"], "fixture": prepared["fixture"], "mode": mode})

    def test_metadata_and_preparation_expose_only_the_bounded_server_fixtures(self):
        metadata = prototype_metadata()
        self.assertEqual({fixture["id"] for fixture in metadata["fixtures"]}, set(FIXTURES))
        for fixture in metadata["fixtures"]:
            prepared = self.prepare(fixture["id"])
            self.assertEqual(set(prepared), {"run", "fixture", "source", "expectation"})
            self.assertRegex(prepared["run"], r"^[0-9a-f]{32}$")
            self.assertEqual(prepared["source"], fixture["source"])
            self.assertEqual(json.loads(prepared["source"]), FIXTURES[fixture["id"]]["payload"])
            self.assertLess(len(prepared["source"]), 512)
            for mode in ("vulnerable", "fixed"):
                self.assertEqual(self.frame(prepared, mode).status_code, 200)

    def test_session_contains_one_small_selection_and_new_run_invalidates_old_frames(self):
        session = self.client.session
        session["other_lesson"] = {"keep": True}
        session.save()
        first = self.prepare("proto")
        second = self.prepare("normal")
        self.assertNotEqual(first["run"], second["run"])
        self.assertEqual(self.client.session[SESSION_KEY], {"run": second["run"], "fixture": "normal"})
        self.assertEqual(self.client.session["other_lesson"], {"keep": True})
        self.assertLess(len(json.dumps(self.client.session[SESSION_KEY])), 100)
        self.assertEqual(self.frame(first).status_code, 404)
        self.assertEqual(self.frame(second).status_code, 200)

    def test_frames_are_bound_to_session_and_fixture_even_with_a_known_run(self):
        prepared = self.prepare("proto")
        other = Client()
        self.assertEqual(self.frame(prepared, client=other).status_code, 404)
        changed_fixture = {**prepared, "fixture": "constructor"}
        self.assertEqual(self.frame(changed_fixture).status_code, 404)
        own = self.prepare("normal", client=other)
        self.assertEqual(self.frame(own, client=other).status_code, 200)
        self.assertEqual(self.frame(prepared).status_code, 200)

    def test_frames_use_fresh_nonces_and_a_response_level_opaque_sandbox(self):
        prepared = self.prepare("proto")
        nonces = set()
        for mode in ("vulnerable", "fixed"):
            response = self.frame(prepared, mode)
            document = response.content.decode()
            nonce = re.search(r'<script nonce="([A-Za-z0-9_-]+)">', document).group(1)
            self.assertGreaterEqual(len(nonce), 32)
            nonces.add(nonce)
            policy = response["Content-Security-Policy"]
            for directive in ("default-src 'none'", "script-src 'nonce-" + nonce + "'", "style-src 'nonce-" + nonce + "'",
                              "connect-src 'none'", "frame-src 'none'", "object-src 'none'", "base-uri 'none'", "form-action 'none'",
                              "sandbox allow-scripts", "frame-ancestors " + settings.LAB_MAIN_ORIGIN):
                self.assertIn(directive, policy)
            for token in ("allow-same-origin", "unsafe-inline", "unsafe-eval", "allow-popups", "allow-forms", "allow-top-navigation"):
                self.assertNotIn(token, policy)
            self.assertEqual(response["Cache-Control"], "no-store")
            self.assertEqual(response["X-Content-Type-Options"], "nosniff")
            self.assertIn("JSON.parse(config.source)", document)
            self.assertIn('"mode": "' + mode + '"', document)
        self.assertEqual(len(nonces), 2)

    def test_rejects_arbitrary_payloads_and_ambiguous_json_without_creating_session_state(self):
        for body in ({}, [], {"fixture": []}, {"fixture": "missing"}, {"fixture": "normal", "payload": {"custom": "value"}},
                     '{"fixture":"normal","fixture":"proto"}', "{", " " * 1025, b"\xff"):
            with self.subTest(body=repr(body)[:80]):
                response = self.client.post("/api/prototype/prepare/", body, content_type="application/json")
                self.assertEqual(response.status_code, 400)
                self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertEqual(self.client.post("/api/prototype/prepare/?fixture=proto", {"fixture": "normal"}, content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/api/prototype/prepare/", {"fixture": "normal"}).status_code, 400)

    def test_rejects_missing_extra_duplicate_or_unknown_frame_parameters(self):
        prepared = self.prepare()
        valid = {"run": prepared["run"], "fixture": "normal", "mode": "fixed"}
        queries = [{}, {**valid, "run": "../outside"}, {**valid, "mode": "other"}, {**valid, "fixture": "other"},
                   {**valid, "payload": "arbitrary"}, {**valid, "run": [prepared["run"], prepared["run"]]},
                   {**valid, "fixture": ["normal", "proto"]}, {**valid, "mode": ["fixed", "vulnerable"]}]
        for query in queries:
            with self.subTest(query=query):
                self.assertEqual(self.client.get("/lab/prototype/frame/", query).status_code, 400)

    def test_http_methods_are_explicit(self):
        response = self.client.get("/api/prototype/prepare/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")
        response = self.client.post("/lab/prototype/frame/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "GET")

    def test_csrf_is_required_and_valid_same_origin_request_succeeds(self):
        client = Client(enforce_csrf_checks=True)
        body = {"fixture": "normal"}
        self.assertEqual(client.post("/api/prototype/prepare/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        self.assertEqual(client.post("/api/prototype/prepare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(client.post("/api/prototype/prepare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN=settings.LAB_PEER_ORIGIN).status_code, 403)

    @override_settings(LAB_ROLE="peer")
    def test_peer_role_cannot_prepare_or_render_prototype_frames(self):
        self.assertEqual(self.client.post("/api/prototype/prepare/", {"fixture": "normal"}, content_type="application/json").status_code, 404)
        self.assertEqual(self.client.get("/lab/prototype/frame/").status_code, 404)
