"""Parser output, persisted state, session isolation, and sandbox boundaries."""
import json
from html.parser import HTMLParser
from unittest.mock import patch

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, TestCase, override_settings

from .sanitizer_lab import FIXTURES, SESSION_KEY, clean_html


class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.text = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)


class SanitizerLabTests(TestCase):
    def save(self, fixture="normal", client=None):
        response = (client or self.client).post("/api/sanitizer/save/", {"fixture": fixture}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        return response.json()["saved"]

    def frame(self, saved, mode="fixed", client=None):
        return (client or self.client).get("/lab/sanitizer/frame/", {"run": saved["run"], "mode": mode})

    def test_markdown_formatting_survives_real_render_and_sanitizer(self):
        saved = self.save()
        self.assertNotEqual(saved["source"], saved["rendered"])
        self.assertEqual(saved["rendered"], saved["results"]["vulnerable"]["html"])
        for mode in ("vulnerable", "fixed"):
            parsed = Elements(saved["results"][mode]["html"])
            tags = [tag for tag, _ in parsed.elements]
            for tag in ("strong", "em", "ul", "li", "code"):
                self.assertIn(tag, tags)
            self.assertIn("<tag> stays text", parsed.text)

    def test_embedded_html_and_richtext_remove_event_attributes_but_keep_formatting(self):
        for fixture in ("markdown-html", "rich-html"):
            with self.subTest(fixture=fixture):
                saved = self.save(fixture)
                vulnerable = Elements(saved["results"]["vulnerable"]["html"])
                fixed = Elements(saved["results"]["fixed"]["html"])
                self.assertTrue(any(attrs.get("onerror") == "window.sanitizerMark()" for _, attrs in vulnerable.elements))
                self.assertFalse(any(attr.startswith("on") or attr == "src" for _, attrs in fixed.elements for attr in attrs))
                self.assertIn(("img", {"alt": "Harmless broken image"}), fixed.elements)
                self.assertIn(("strong", {}), fixed.elements)
                self.assertIn(("em", {}), fixed.elements)

    def test_encoded_markup_is_text_without_a_second_decode(self):
        saved = self.save("encoded")
        for mode in ("vulnerable", "fixed"):
            parsed = Elements(saved["results"][mode]["html"])
            self.assertNotIn("img", [tag for tag, _ in parsed.elements])
            self.assertIn('<img src="data:image/png;base64,AA==" onerror="window.sanitizerMark()">', "".join(parsed.text))

    def test_policy_uses_parser_to_remove_active_content_and_non_policy_attributes(self):
        cleaned = clean_html('<p id="name" style="color:red" onclick="fixture()"><strong>Keep</strong><script>REMOVE_SCRIPT</script><style>REMOVE_STYLE</style><a href="javascript:fixture()">Label</a></p>')
        parsed = Elements(cleaned)
        self.assertEqual(parsed.elements, [("p", {}), ("strong", {})])
        self.assertEqual("".join(parsed.text), "KeepLabel")

    def test_saved_pair_is_read_from_session_and_replaces_only_its_own_key(self):
        self.assertEqual(self.client.get("/api/sanitizer/state/").json(), {"saved": None})
        session = self.client.session
        session["other_lesson"] = {"keep": True}
        session.save()
        first = self.save("markdown-html")
        with patch("securitylab.sanitizer_lab.make_saved", side_effect=AssertionError("Do not regenerate stored output")):
            self.assertEqual(self.client.get("/api/sanitizer/state/").json()["saved"], first)
            self.assertContains(self.frame(first, "vulnerable"), first["results"]["vulnerable"]["html"])
        second = self.save("normal")
        self.assertNotEqual(first["run"], second["run"])
        self.assertEqual(self.client.session[SESSION_KEY], second)
        self.assertEqual(self.client.session["other_lesson"], {"keep": True})
        self.assertEqual(self.frame(first).status_code, 404)
        self.assertEqual(self.frame(second).status_code, 200)
        self.assertLess(len(json.dumps(second)), 6000)

    def test_other_sessions_cannot_read_saved_html_even_with_known_run(self):
        saved = self.save("rich-html")
        other = Client()
        self.assertEqual(other.get("/api/sanitizer/state/").json(), {"saved": None})
        self.assertEqual(self.frame(saved, client=other).status_code, 404)
        own = self.save("normal", client=other)
        self.assertNotEqual(saved["run"], own["run"])
        self.assertEqual(self.client.get("/api/sanitizer/state/").json()["saved"], saved)

    def test_both_frames_have_identical_response_sandbox_and_no_network_sources(self):
        saved = self.save("rich-html")
        vulnerable, fixed = self.frame(saved, "vulnerable"), self.frame(saved)
        self.assertEqual(vulnerable["Content-Security-Policy"], fixed["Content-Security-Policy"])
        policy = fixed["Content-Security-Policy"]
        for value in ("default-src 'none'", "sandbox allow-scripts", "img-src data:", "form-action 'none'", "base-uri 'none'", "frame-ancestors " + settings.LAB_MAIN_ORIGIN):
            self.assertIn(value, policy)
        for token in ("allow-same-origin", "allow-top-navigation", "allow-popups", "allow-forms"):
            self.assertNotIn(token, policy)
        self.assertEqual(fixed["Cache-Control"], "no-store")
        self.assertEqual(fixed["X-Content-Type-Options"], "nosniff")
        document = vulnerable.content.decode()
        self.assertLess(document.index("window.sanitizerMark ="), document.index('<article id="saved-content">'))
        self.assertIn("parent.postMessage", document)

    def test_rejects_unlisted_input_and_ambiguous_frame_queries(self):
        invalid_bodies = ({}, [], {"fixture": []}, {"fixture": "missing"}, {"fixture": "normal", "source": "arbitrary"})
        with patch("securitylab.sanitizer_lab.make_saved") as render:
            for body in invalid_bodies:
                self.assertEqual(self.client.post("/api/sanitizer/save/", body, content_type="application/json").status_code, 400)
            for body in ('{', '{"fixture":"normal","fixture":"encoded"}', ' ' * 1025):
                self.assertEqual(self.client.post("/api/sanitizer/save/", body, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/sanitizer/save/?fixture=normal", {"fixture": "normal"}, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/sanitizer/save/", {"fixture": "normal"}).status_code, 400)
            render.assert_not_called()
        saved = self.save()
        for query in ({}, {"run": saved["run"], "mode": "invalid"}, {"run": "../fixture", "mode": "fixed"},
                      {"run": [saved["run"], saved["run"]], "mode": "fixed"}, {"run": saved["run"], "mode": "fixed", "html": "x"}):
            self.assertEqual(self.client.get("/lab/sanitizer/frame/", query).status_code, 400)
        self.assertEqual(self.client.get("/api/sanitizer/state/?run=x").status_code, 400)
        self.assertEqual(self.client.get("/api/sanitizer/save/")["Allow"], "POST")
        self.assertEqual(self.client.post("/api/sanitizer/state/")["Allow"], "GET")
        self.assertEqual(self.client.post("/lab/sanitizer/frame/")["Allow"], "GET")

    def test_csrf_required_for_save_but_valid_same_origin_control_works(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/api/sanitizer/save/", {"fixture": "normal"}, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        self.assertEqual(client.post("/api/sanitizer/save/", {"fixture": "normal"}, content_type="application/json", HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(client.post("/api/sanitizer/save/", {"fixture": "normal"}, content_type="application/json", HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)

    @override_settings(LAB_ROLE="peer")
    def test_peer_origin_cannot_use_sanitizer_apis_or_render_saved_frames(self):
        for path in ("/api/sanitizer/state/", "/api/sanitizer/save/", "/lab/sanitizer/frame/"):
            self.assertEqual(self.client.get(path).status_code, 404)
