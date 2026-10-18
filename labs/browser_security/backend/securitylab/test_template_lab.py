"""Template evaluation, data separation, and HTTP fixture boundaries."""
import json
from unittest.mock import patch

from django.conf import settings
from django.middleware.csrf import get_token
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.test import Client, RequestFactory, SimpleTestCase

from .template_lab import FIXED_SOURCE, FIXTURES, MARKER, fixture_engine


class TemplateLabTests(SimpleTestCase):
    def compare(self, fixture):
        return self.client.post("/api/template/compare/", {"fixture": fixture}, content_type="application/json")

    def test_ordinary_name_renders_successfully_in_both_handlers(self):
        response = self.compare("normal")
        self.assertEqual(response.status_code, 200)
        for result in response.json()["results"].values():
            self.assertEqual(result["rendered"], "Hello, Ada.")
            self.assertEqual(result["outcome"], "unchanged")
            self.assertFalse(result["markerExposed"])

    def test_context_variable_is_evaluated_only_when_compiled_as_source(self):
        results = self.compare("marker").json()["results"]
        self.assertEqual(results["vulnerable"]["rendered"], f"Hello, {MARKER}.")
        self.assertTrue(results["vulnerable"]["markerExposed"])
        self.assertEqual(results["vulnerable"]["outcome"], "evaluated")
        self.assertEqual(results["fixed"]["rendered"], "Hello, {{ marker }}.")
        self.assertFalse(results["fixed"]["markerExposed"])
        self.assertEqual(results["fixed"]["source"], FIXED_SOURCE)
        self.assertEqual(results["fixed"]["context"]["name"], "{{ marker }}")

    def test_actual_django_condition_and_lower_filter_execute(self):
        results = self.compare("conditional").json()["results"]
        self.assertEqual(results["vulnerable"]["rendered"], f"Hello, {MARKER.lower()}.")
        self.assertTrue(results["vulnerable"]["markerExposed"])
        self.assertEqual(results["fixed"]["rendered"], "Hello, " + FIXTURES["conditional"]["input"] + ".")
        self.assertFalse(results["fixed"]["markerExposed"])

    def test_autoescape_applies_to_data_independently_of_template_evaluation(self):
        results = self.compare("html").json()["results"]
        self.assertIn('<strong id="TEMPLATE_TEXT_ONLY">', results["vulnerable"]["rendered"])
        self.assertEqual(results["fixed"]["rendered"], 'Hello, &lt;strong id=&quot;TEMPLATE_TEXT_ONLY&quot;&gt;Ada &amp; Bea&lt;/strong&gt;.')
        self.assertEqual(results["fixed"]["outcome"], "escaped")
        self.assertFalse(results["vulnerable"]["markerExposed"])
        # Autoescaping was also on in the vulnerable marker comparison.
        self.assertTrue(self.compare("marker").json()["results"]["vulnerable"]["markerExposed"])

    def test_engine_has_no_loaders_or_custom_libraries_and_only_scalar_context(self):
        engine = fixture_engine()
        self.assertEqual(engine.template_loaders, [])
        self.assertEqual(engine.context_processors, [])
        self.assertEqual(engine.libraries, {})
        self.assertFalse(engine.app_dirs)
        with self.assertRaises(TemplateDoesNotExist):
            engine.get_template("fixture-not-present.html")
        with self.assertRaises(TemplateSyntaxError):
            engine.from_string("{% load static %}")
        # Django syntax is intentionally distinct from Jinja arithmetic syntax.
        with self.assertRaises(TemplateSyntaxError):
            engine.from_string("{{ 7*7 }}")
        for fixture in FIXTURES:
            for result in self.compare(fixture).json()["results"].values():
                self.assertTrue(all(type(value) in (str, bool) for value in result["context"].values()))
                self.assertLess(len(result["source"]), 256)
                self.assertLess(len(result["rendered"]), 512)

    def test_invalid_input_cannot_reach_template_compilation(self):
        invalid_bodies = ({}, [], {"fixture": "missing"}, {"fixture": None}, {"fixture": []},
                          {"fixture": "normal", "input": "{{ marker }}"}, {"fixture": "{{ marker }}"})
        with patch("securitylab.template_lab.fixture_engine") as engine:
            for body in invalid_bodies:
                with self.subTest(body=body):
                    self.assertEqual(self.client.post("/api/template/compare/", body, content_type="application/json").status_code, 400)
            for raw in ('{', '{"fixture":"normal","fixture":"marker"}', ' ' * 2049,
                        '[' * 1000 + ']' * 1000):
                self.assertEqual(self.client.post("/api/template/compare/", raw, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/template/compare/?fixture=normal", {"fixture": "normal"}, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/template/compare/", {"fixture": "normal"}).status_code, 400)
            engine.assert_not_called()
        response = self.client.get("/api/template/compare/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")

    def test_csrf_is_required_and_same_origin_token_allows_positive_control(self):
        client = Client(enforce_csrf_checks=True)
        body = json.dumps({"fixture": "normal"})
        self.assertEqual(client.post("/api/template/compare/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        response = client.post("/api/template/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"]["fixed"]["rendered"], "Hello, Ada.")
        self.assertEqual(client.post("/api/template/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token,
                                     HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)
