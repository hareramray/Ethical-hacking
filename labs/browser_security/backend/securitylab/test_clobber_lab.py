"""Finite fixture selection, session ownership, and document boundaries."""
import json
import re
from html.parser import HTMLParser

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import path

from .clobber_lab import FIXTURES, SESSION_KEY, clobber_frame, clobber_metadata, clobber_prepare

urlpatterns = [path("api/clobber/prepare/", clobber_prepare), path("lab/clobber/frame/", clobber_frame)]


class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


@override_settings(ROOT_URLCONF=__name__)
class ClobberLabTests(TestCase):
    def prepare(self, fixture="normal", client=None):
        response = (client or self.client).post("/api/clobber/prepare/", {"fixture": fixture}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def frame(self, prepared, mode="fixed", client=None):
        return (client or self.client).get("/lab/clobber/frame/", {**prepared, "mode": mode})

    def test_metadata_and_fixtures_are_bounded_non_script_html(self):
        metadata = clobber_metadata()
        self.assertEqual(metadata["mainOrigin"], settings.LAB_MAIN_ORIGIN)
        self.assertEqual({item["id"] for item in metadata["fixtures"]}, {"normal", "named-config", "form-property"})
        for fixture in FIXTURES.values():
            self.assertLess(len(fixture["source"]), 250)
            for tag, attrs in Elements(fixture["source"]).elements:
                self.assertIn(tag, {"p", "strong", "form", "input"})
                self.assertFalse(any(key.startswith("on") or key in {"src", "href", "action"} for key in attrs))

    def test_run_is_fresh_bounded_and_replaces_only_its_session_key(self):
        session = self.client.session
        session["other_lesson"] = {"keep": True}
        session.save()
        first = self.prepare("named-config")
        self.assertEqual(set(first), {"run", "fixture"})
        self.assertRegex(first["run"], r"^[a-f0-9]{32}$")
        self.assertEqual(self.frame(first).status_code, 200)
        second = self.prepare()
        self.assertNotEqual(first["run"], second["run"])
        self.assertEqual(self.client.session[SESSION_KEY], second)
        self.assertEqual(self.client.session["other_lesson"], {"keep": True})
        self.assertEqual(self.frame(first).status_code, 404)
        self.assertEqual(self.frame(second).status_code, 200)
        self.assertLess(len(json.dumps(second)), 100)

    def test_runs_are_bound_to_session_and_fixture(self):
        prepared = self.prepare("named-config")
        self.assertEqual(self.frame(prepared, client=Client()).status_code, 404)
        self.assertEqual(self.frame({**prepared, "fixture": "normal"}).status_code, 404)
        self.assertEqual(self.frame({**prepared, "run": "0" * 32}).status_code, 404)

    def test_both_modes_receive_same_markup_and_legitimate_owned_controls(self):
        for fixture_id, fixture in FIXTURES.items():
            prepared = self.prepare(fixture_id)
            for mode in ("vulnerable", "fixed"):
                document = self.frame(prepared, mode).content.decode()
                self.assertIn(fixture["source"], document)
                parsed = Elements(document).elements
                self.assertIn(("form", {"data-owned-form": "note", "method": "post"}), parsed)
                self.assertTrue(any(tag == "input" and "data-owned-note" in attrs and attrs.get("name") == "note" for tag, attrs in parsed))
                self.assertIn("output.textContent = label", document)
                self.assertIn("parent.postMessage", document)

    def test_nonce_csp_sandbox_protects_embedded_and_direct_documents(self):
        prepared = self.prepare("named-config")
        policies = []
        for mode in ("vulnerable", "fixed"):
            response = self.frame(prepared, mode)
            policy = response["Content-Security-Policy"]
            nonce = re.search(r"script-src 'nonce-([^']+)'", policy).group(1)
            self.assertGreaterEqual(len(nonce), 24)
            for tag, attrs in Elements(response.content.decode()).elements:
                if tag in {"script", "style"}:
                    self.assertEqual(attrs["nonce"], nonce)
            for directive in ("default-src 'none'", "connect-src 'none'", "frame-src 'none'", "object-src 'none'", "base-uri 'none'", "form-action 'none'", "frame-ancestors " + settings.LAB_MAIN_ORIGIN, "sandbox allow-scripts"):
                self.assertIn(directive, policy)
            for token in ("unsafe-inline", "unsafe-eval", "allow-same-origin", "allow-top-navigation", "allow-popups", "allow-forms"):
                self.assertNotIn(token, policy)
            self.assertEqual(response["Cache-Control"], "no-store")
            self.assertEqual(response["X-Content-Type-Options"], "nosniff")
            policies.append(policy.replace(nonce, "RANDOM_NONCE"))
        self.assertEqual(policies[0], policies[1])

    def test_prepare_rejects_ambiguous_unlisted_or_arbitrary_input(self):
        first = self.prepare()
        for body in ({}, [], {"fixture": []}, {"fixture": "missing"}, {"fixture": "normal", "html": "arbitrary"}, '{', '{"fixture":"normal","fixture":"named-config"}', ' ' * 1025):
            self.assertEqual(self.client.post("/api/clobber/prepare/", body, content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/api/clobber/prepare/?fixture=normal", {"fixture": "normal"}, content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/api/clobber/prepare/", {"fixture": "normal"}).status_code, 400)
        self.assertEqual(self.client.session[SESSION_KEY], first)

    def test_frame_rejects_unknown_duplicate_or_malformed_queries_and_wrong_methods(self):
        prepared = self.prepare()
        query = {**prepared, "mode": "fixed"}
        for invalid in ({}, {**query, "mode": "other"}, {**query, "fixture": "other"}, {**query, "run": "../fixture"}, {**query, "run": [prepared["run"], prepared["run"]]}, {**query, "mode": ["fixed", "fixed"]}, {**query, "fixture": ["normal", "normal"]}, {**query, "html": "extra"}):
            self.assertEqual(self.client.get("/lab/clobber/frame/", invalid).status_code, 400)
        for method in ("get", "put", "delete"):
            response = getattr(self.client, method)("/api/clobber/prepare/")
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "POST")
        response = self.client.post("/lab/clobber/frame/", query)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "GET")

    def test_normal_csrf_protection_and_same_origin_control(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/api/clobber/prepare/", {"fixture": "normal"}, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        self.assertEqual(client.post("/api/clobber/prepare/", {"fixture": "normal"}, content_type="application/json", HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(client.post("/api/clobber/prepare/", {"fixture": "normal"}, content_type="application/json", HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN=settings.LAB_PEER_ORIGIN).status_code, 403)

    @override_settings(LAB_ROLE="peer")
    def test_peer_origin_has_no_lesson_endpoints(self):
        for endpoint in ("/api/clobber/prepare/", "/lab/clobber/frame/"):
            self.assertEqual(self.client.get(endpoint).status_code, 404)
