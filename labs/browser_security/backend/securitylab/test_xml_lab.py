"""Parser behavior, no-I/O boundaries, and HTTP checks for the XML lesson."""
import io
import json
from unittest.mock import patch

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, SimpleTestCase, override_settings
from django.urls import path

from .xml_lab import (
    FIXTURES, MARKER, MARKER_URI, MAX_DEPTH, MAX_TEXT, MAX_XML_BYTES,
    ExpatParser, LabBlocked, MarkerResolver, parse_fixture, xml_compare,
)

urlpatterns = [path("api/xml/compare/", xml_compare)]


@override_settings(ROOT_URLCONF=__name__)
class XMLLabTests(SimpleTestCase):
    def compare(self, fixture="normal", **extra):
        return self.client.post("/api/xml/compare/", {"fixture": fixture, **extra}, content_type="application/json")

    def test_normal_text_and_builtin_entities_remain_available(self):
        for fixture, expected in (("normal", "Hello from the XML fixture."), ("builtin", "Tea & biscuits <served>")):
            with self.subTest(fixture=fixture):
                response = self.compare(fixture)
                self.assertEqual(response.status_code, 200)
                for result in response.json()["results"].values():
                    self.assertEqual(result["outcome"], "parsed")
                    self.assertEqual(result["text"], expected)
                    self.assertEqual(result["resolverCalls"], [])

    def test_external_entity_uses_actual_resolver_and_only_vulnerable_output_contains_marker(self):
        results = self.compare("external").json()["results"]
        self.assertEqual(results["vulnerable"]["outcome"], "parsed")
        self.assertEqual(results["vulnerable"]["text"], MARKER)
        self.assertEqual(results["vulnerable"]["resolverCalls"], [{"systemId": MARKER_URI, "outcome": "in_memory_marker"}])
        self.assertEqual(results["fixed"]["outcome"], "blocked")
        self.assertEqual(results["fixed"]["text"], "")
        self.assertEqual(results["fixed"]["resolverCalls"], [])
        self.assertIn("DOCTYPE", results["fixed"]["reason"])

    def test_unknown_resource_is_rejected_instead_of_using_default_resolver(self):
        results = self.compare("unknown").json()["results"]
        for result in results.values():
            self.assertEqual(result["outcome"], "blocked")
            self.assertEqual(result["text"], "")
        self.assertEqual(results["vulnerable"]["resolverCalls"], [{"systemId": "urn:lab:unknown", "outcome": "blocked"}])
        self.assertEqual(results["fixed"]["resolverCalls"], [])

    def test_all_parsing_and_rejected_file_or_http_identifiers_perform_no_io(self):
        with patch("builtins.open", side_effect=AssertionError("No files")), \
                patch("urllib.request.urlopen", side_effect=AssertionError("No URLs")), \
                patch("socket.socket", side_effect=AssertionError("No sockets")):
            for fixture in FIXTURES:
                for mode in ("vulnerable", "fixed"):
                    parse_fixture(fixture, mode)
            for uri in ("file:///DO_NOT_OPEN_LAB_SENTINEL", "http://example.invalid/DO_NOT_FETCH", MARKER_URI + "/extra"):
                with self.subTest(uri=uri), patch.dict(FIXTURES, {"test-only": {"xml": f'<!DOCTYPE m [<!ENTITY e SYSTEM "{uri}">]><m>&e;</m>'}}):
                    result = parse_fixture("test-only", "vulnerable")
                    self.assertEqual(result["outcome"], "blocked")
                    self.assertEqual(result["resolverCalls"], [{"systemId": uri, "outcome": "blocked"}])
                    self.assertEqual(result["text"], "")
            with patch.dict(FIXTURES, {"test-only": {"xml": '<!DOCTYPE m SYSTEM "http://example.invalid/DO_NOT_FETCH"><m>Text</m>'}}):
                result = parse_fixture("test-only", "vulnerable")
                self.assertEqual(result["outcome"], "blocked")
                self.assertEqual(result["resolverCalls"], [])

    def test_input_and_entity_streams_close_after_success_and_errors(self):
        string_io = io.StringIO
        streams = []

        def tracked_stream(value):
            stream = string_io(value)
            streams.append(stream)
            return stream

        with patch("securitylab.xml_lab.io.StringIO", side_effect=tracked_stream):
            for fixture in FIXTURES:
                for mode in ("vulnerable", "fixed"):
                    parse_fixture(fixture, mode)
        self.assertEqual(len(streams), len(FIXTURES) * 2 + 1)
        self.assertTrue(all(stream.closed for stream in streams))

    def test_fixed_parser_rejects_doctype_at_parser_callback_and_external_dtd_is_never_resolved(self):
        for xml in ('<!DOCTYPE m><m>Text</m>', '<!DOCTYPE m [<!ENTITY e "text">]><m>&e;</m>'):
            with self.subTest(xml=xml), patch.dict(FIXTURES, {"test-only": {"xml": xml}}):
                result = parse_fixture("test-only", "fixed")
                self.assertEqual(result["outcome"], "blocked")
                self.assertEqual(result["resolverCalls"], [])
        with patch.dict(FIXTURES, {"test-only": {"xml": '<!DOCTYPE m SYSTEM "urn:lab:unknown"><m>Text</m>'}}):
            for mode in ("vulnerable", "fixed"):
                result = parse_fixture("test-only", mode)
                self.assertEqual(result["outcome"], "blocked")
                self.assertEqual(result["resolverCalls"], [])

    def test_malformed_xml_reports_parser_error_and_discards_partial_text(self):
        for result in self.compare("malformed").json()["results"].values():
            self.assertEqual(result["outcome"], "parse_error")
            self.assertIn("line 1", result["reason"])
            self.assertEqual(result["text"], "")
            self.assertEqual(result["resolverCalls"], [])

    def test_parser_limits_bound_fixture_input_output_depth_and_resolver_calls(self):
        xml_cases = (
            ("<m>" + "x" * MAX_XML_BYTES + "</m>", "byte budget"),
            ("<m>" + "x" * (MAX_TEXT + 1) + "</m>", "parsed-text"),
            ("<m>" * (MAX_DEPTH + 1) + "x" + "</m>" * (MAX_DEPTH + 1), "element-depth"),
        )
        for xml, reason in xml_cases:
            with self.subTest(reason=reason), patch.dict(FIXTURES, {"test-only": {"xml": xml}}):
                for mode in ("vulnerable", "fixed"):
                    result = parse_fixture("test-only", mode)
                    self.assertEqual(result["outcome"], "blocked")
                    self.assertIn(reason, result["reason"])
                    self.assertEqual(result["text"], "")
        resolver = MarkerResolver()
        source = resolver.resolveEntity(None, MARKER_URI)
        self.assertEqual(source.getCharacterStream().read(), MARKER)
        source.getCharacterStream().close()
        with self.assertRaisesRegex(LabBlocked, "one-resolution"):
            resolver.resolveEntity(None, MARKER_URI)
        with self.assertRaises(LabBlocked):
            MarkerResolver().resolveEntity("unexpected-public-id", MARKER_URI)

    def test_fresh_parser_per_mode_prevents_state_from_previous_runs(self):
        with patch("securitylab.xml_lab.ExpatParser", wraps=ExpatParser) as constructor:
            self.compare("external")
            result = self.compare("normal").json()
            self.assertEqual(constructor.call_count, 4)
        for outcome in result["results"].values():
            self.assertEqual(outcome["resolverCalls"], [])
            self.assertNotIn(MARKER, outcome["text"])

    def test_validation_rejects_raw_xml_unknown_extra_duplicate_and_oversized_input(self):
        with patch("securitylab.xml_lab.parse_fixture") as parse:
            for fixture in ("", "not-a-fixture", "<message>raw XML</message>", None, 1, [], {}):
                with self.subTest(fixture=fixture):
                    self.assertEqual(self.compare(fixture).status_code, 400)
            for body in ({}, [], {"fixture": "normal", "xml": "<m/>"}):
                self.assertEqual(self.client.post("/api/xml/compare/", body, content_type="application/json").status_code, 400)
            for raw in ('{', '{"fixture":"normal","fixture":"external"}', '{"fixture":"' + 'x' * 256 + '"}'):
                self.assertEqual(self.client.post("/api/xml/compare/", raw, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/xml/compare/?fixture=external", {"fixture": "normal"}, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/xml/compare/", {"fixture": "normal"}).status_code, 400)
            response = self.client.get("/api/xml/compare/")
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "POST")
            parse.assert_not_called()

    def test_csrf_protects_comparison_and_allows_legitimate_same_origin_request(self):
        client = Client(enforce_csrf_checks=True)
        body = json.dumps({"fixture": "normal"})
        self.assertEqual(client.post("/api/xml/compare/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        response = client.post("/api/xml/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"]["fixed"]["outcome"], "parsed")
        self.assertEqual(client.post("/api/xml/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token,
                                    HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)
