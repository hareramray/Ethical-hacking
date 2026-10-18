"""HTTP boundary tests; script execution is verified separately in Playwright."""

import io
import json
import re
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from PIL import Image, PngImagePlugin


def png_bytes():
    stream = io.BytesIO()
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("lab_metadata", "original file metadata")
    Image.new("RGB", (2, 2), "blue").save(stream, format="PNG", pnginfo=metadata)
    return stream.getvalue()


class LabHTTPTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.upload_directory = TemporaryDirectory(prefix="browser-security-test-")
        cls.upload_settings = override_settings(UPLOAD_DIR=cls.upload_directory.name)
        cls.upload_settings.enable()

    @classmethod
    def tearDownClass(cls):
        cls.upload_settings.disable()
        cls.upload_directory.cleanup()
        super().tearDownClass()

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.csrf = self.bootstrap(self.client)["csrfToken"]

    def bootstrap(self, client):
        response = client.get("/api/bootstrap")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def json_write(self, method, url, body=None, client=None, csrf=None):
        return getattr(client or self.client, method)(
            url,
            data=json.dumps(body or {}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf or self.csrf,
        )

    def upload(self, content, name, content_type, policy="lab", client=None, csrf=None):
        return (client or self.client).post(
            "/api/uploads/",
            {"file": SimpleUploadedFile(name, content, content_type), "policy": policy},
            HTTP_X_CSRFTOKEN=csrf or self.csrf,
        )

    def response_bytes(self, response):
        return b"".join(response.streaming_content) if response.streaming else response.content

    def test_bootstrap_exposes_available_modes_and_health(self):
        data = self.bootstrap(self.client)
        self.assertTrue(data["csrfToken"])
        self.assertIn("payloads", data)
        self.assertIn("stored", data)
        self.assertIn("uploads", data)
        self.assertEqual(self.client.get("/api/health").status_code, 200)

    def test_mutations_require_csrf_even_after_bootstrap(self):
        self.assertEqual(self.client.post("/api/stored/", data={"payload": "marker"}).status_code, 403)
        self.assertEqual(self.client.delete("/api/stored/").status_code, 403)
        self.assertEqual(self.client.post("/api/uploads/", data={"policy": "lab"}).status_code, 403)
        accepted = self.json_write("post", "/api/stored/", {"payload": "CSRF positive control"})
        self.assertIn(accepted.status_code, (200, 201))

    def test_stored_payload_is_session_scoped_and_can_be_deleted(self):
        payload = '<img src="data:," onerror="console.log(\'STORED_TEST\')">'
        response = self.json_write("post", "/api/stored/", {"payload": payload})
        self.assertIn(response.status_code, (200, 201))
        self.assertEqual(self.bootstrap(self.client)["stored"]["payload"], payload)
        other = Client(enforce_csrf_checks=True)
        self.assertNotIn(payload, json.dumps(self.bootstrap(other)))
        self.assertIn(self.json_write("delete", "/api/stored/").status_code, (200, 204))
        self.assertNotIn(payload, json.dumps(self.bootstrap(self.client)))

    def test_payload_length_and_malformed_json_are_rejected(self):
        oversized = self.json_write("post", "/api/stored/", {"payload": "x" * 2001})
        self.assertEqual(oversized.status_code, 400)
        malformed = self.client.post(
            "/api/stored/", data="{broken", content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf
        )
        self.assertEqual(malformed.status_code, 400)

    def test_jsonp_accepts_only_the_exact_single_callback(self):
        valid = self.client.get("/lab/jsonp.js?callback=labJsonp")
        self.assertEqual(valid.status_code, 200)
        self.assertIn("javascript", valid["Content-Type"])
        self.assertTrue(valid.content.startswith(b"labJsonp("))
        for query in (
            "",
            "?callback=alert",
            "?callback=labJsonp%3Bconsole.log%28%27BAD%27%29%3B",
            "?callback=labJsonp&callback=labJsonp",
            "?callback=labJsonp&unexpected=1",
        ):
            with self.subTest(query=query):
                self.assertEqual(self.client.get("/lab/jsonp.js" + query).status_code, 400)

    def test_every_frame_enforces_an_opaque_origin_sandbox(self):
        for mode in ("off", "self", "nonce", "hash", "dynamic", "report", "tt"):
            with self.subTest(mode=mode):
                response = self.client.get("/lab/frame/", {"mode": mode, "source": "reflected", "render": "text"})
                self.assertEqual(response.status_code, 200)
                enforced = response["Content-Security-Policy"]
                self.assertRegex(enforced, r"(?:^|;)\s*sandbox\s+allow-scripts(?:\s*;|$)")
                self.assertNotIn("allow-same-origin", enforced)
                if mode == "report":
                    self.assertIn("script-src", response["Content-Security-Policy-Report-Only"])

    def test_response_nonces_are_fresh_and_match_the_allowed_bootstrap(self):
        responses = [self.client.get("/lab/frame/", {"mode": "nonce"}) for _ in range(2)]
        nonces = []
        for response in responses:
            nonce = re.search(r"'nonce-([^']+)'", response["Content-Security-Policy"])
            self.assertIsNotNone(nonce)
            nonces.append(nonce.group(1))
            self.assertIn(f'nonce="{nonce.group(1)}"', response.content.decode())
            self.assertIn("no-store", response.get("Cache-Control", ""))
        self.assertNotEqual(nonces[0], nonces[1])

    def test_reflected_text_is_encoded_but_html_exercise_preserves_markup(self):
        payload = '<strong id="HTTP_TEXT_TEST">literal</strong>'
        safe = self.client.get("/lab/frame/", {"mode": "off", "source": "reflected", "render": "text", "payload": payload})
        unsafe = self.client.get("/lab/frame/", {"mode": "off", "source": "reflected", "render": "html", "payload": payload})
        self.assertNotIn(payload, safe.content.decode())
        self.assertIn("&lt;strong", safe.content.decode())
        self.assertIn(payload, unsafe.content.decode())

    def test_strict_upload_decodes_and_reencodes_real_pngs(self):
        original = png_bytes()
        response = self.upload(original, "image.png", "image/png", "strict")
        self.assertIn(response.status_code, (200, 201))
        record = response.json()["upload"]
        downloaded = self.client.get(record["downloadUrl"])
        self.assertEqual(downloaded.status_code, 200)
        self.assertIn("attachment", downloaded["Content-Disposition"])
        self.assertEqual(downloaded["X-Content-Type-Options"], "nosniff")
        rewritten = self.response_bytes(downloaded)
        with Image.open(io.BytesIO(rewritten)) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (2, 2))
            self.assertNotIn("lab_metadata", image.info)
        self.assertNotEqual(original, rewritten)

    def test_strict_upload_uses_decoded_content_instead_of_the_claimed_mime(self):
        response = self.upload(png_bytes(), "real.png", "text/html", "strict")
        self.assertEqual(response.status_code, 201)
        record = response.json()["upload"]
        self.assertEqual(record["contentType"], "image/png")
        self.assertEqual(record["submittedContentType"], "text/html")

    def test_strict_upload_rejects_spoofed_extensions_and_invalid_images(self):
        for name, mime, body in (
            ("fake.png", "image/png", b"<html>not a PNG</html>"),
            ("active.html", "text/html", b"<script>console.log('UPLOAD_TEST')</script>"),
            ("double.png.html", "image/png", png_bytes()),
        ):
            with self.subTest(name=name, mime=mime):
                self.assertEqual(self.upload(body, name, mime, "strict").status_code, 400)

    def test_upload_limits_and_validation_policies_are_enforced(self):
        self.assertIn(self.upload(b"x" * (64 * 1024 + 1), "large.txt", "text/plain").status_code, (400, 413))
        self.assertEqual(self.upload(b"marker", "marker.txt", "text/plain", "unknown").status_code, 400)
        self.assertEqual(self.upload(b"marker", "marker.exe", "application/octet-stream").status_code, 400)

    def test_upload_retrieval_and_delete_are_session_owned(self):
        body = b"<script>console.log('UPLOAD_SESSION_TEST')</script>"
        response = self.upload(body, "marker.html", "text/html")
        self.assertIn(response.status_code, (200, 201))
        record = response.json()["upload"]
        other = Client(enforce_csrf_checks=True)
        other_csrf = self.bootstrap(other)["csrfToken"]
        self.assertEqual(other.get("/api/uploads/").json()["uploads"], [])
        for field in ("downloadUrl", "previewUrl", "activePreviewUrl"):
            with self.subTest(field=field):
                self.assertEqual(other.get(record[field]).status_code, 404)
                own = self.client.get(record[field])
                self.assertEqual(own.status_code, 200)
                self.assertEqual(own["X-Content-Type-Options"], "nosniff")
                self.assertIn("sandbox", own["Content-Security-Policy"])
                self.assertNotIn("allow-same-origin", own["Content-Security-Policy"])
        delete_url = f'/api/uploads/{record["id"]}/'
        self.assertEqual(self.json_write("delete", delete_url, client=other, csrf=other_csrf).status_code, 404)
        self.assertEqual(self.client.delete(delete_url).status_code, 403)
        self.assertIn(self.json_write("delete", delete_url).status_code, (200, 204))
        self.assertEqual(self.client.get(record["downloadUrl"]).status_code, 404)

    def test_uploaded_filenames_cannot_select_filesystem_paths(self):
        for name in ("../../marker.html", "..\\..\\marker.html"):
            with self.subTest(name=name):
                response = self.upload(b"<p>NAME_TEST</p>", name, "text/html")
                self.assertIn(response.status_code, (200, 201))
                record = response.json()["upload"]
                self.assertNotIn("/", record["name"])
                self.assertNotIn("\\", record["name"])
                self.assertNotIn("..", record["id"])
                self.assertEqual(self.client.get(record["downloadUrl"]).status_code, 200)
