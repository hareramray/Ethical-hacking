"""Exercise the real filesystem lesson and its independent outer lab boundary."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase

from .traversal import FIXTURE_CONTENTS


class TraversalTests(SimpleTestCase):
    def read(self, path, mode="fixed"):
        return self.client.get("/api/traversal/", {"mode": mode, "path": path})

    def test_public_downloads_remain_readable_in_both_handlers(self):
        for mode in ("vulnerable", "fixed"):
            for path, marker in (("readme.txt", "PUBLIC_README_OK\n"),
                                 ("nested/notes.txt", "NESTED_NOTES_OK\n"),
                                 ("nested/../readme.txt", "PUBLIC_README_OK\n")):
                with self.subTest(mode=mode, path=path):
                    response = self.read(path, mode)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json()["outcome"], "read")
                    self.assertEqual(response.json()["content"], marker)
                    self.assertTrue(response.json()["resolvedPath"].startswith("public/"))

    def test_parent_backslash_and_prefix_sibling_escape_only_vulnerable_root(self):
        for path, resolved, marker in (
            ("../private/sentinel.txt", "private/sentinel.txt", "PRIVATE_SENTINEL_ONLY_FOR_LAB\n"),
            ("..\\private\\sentinel.txt", "private/sentinel.txt", "PRIVATE_SENTINEL_ONLY_FOR_LAB\n"),
            ("../public-notes/sibling.txt", "public-notes/sibling.txt", "SIBLING_PREFIX_SENTINEL\n"),
        ):
            with self.subTest(path=path):
                vulnerable = self.read(path, "vulnerable")
                self.assertEqual(vulnerable.status_code, 200)
                self.assertEqual(vulnerable.json()["content"], marker)
                fixed = self.read(path)
                self.assertEqual(fixed.status_code, 403)
                self.assertEqual(fixed.json()["outcome"], "blocked")
                self.assertIsNone(fixed.json()["content"])
                self.assertEqual(fixed.json()["resolvedPath"], resolved)

    def test_default_is_fixed_and_normal_public_file(self):
        result = self.client.get("/api/traversal/").json()
        self.assertEqual(result["mode"], "fixed")
        self.assertEqual(result["content"], "PUBLIC_README_OK\n")

    def test_missing_files_and_directories_do_not_return_content(self):
        for mode in ("vulnerable", "fixed"):
            for path in ("missing.txt", ".", "nested"):
                with self.subTest(mode=mode, path=path):
                    response = self.read(path, mode)
                    self.assertEqual(response.status_code, 404)
                    self.assertEqual(response.json()["outcome"], "not_found")
                    self.assertIsNone(response.json()["content"])

    def test_outer_boundary_blocks_existing_external_sentinel_before_content_read(self):
        # This is a test-owned harmless file outside the per-request lab root.
        with TemporaryDirectory(prefix="traversal-test-parent-") as parent:
            outside = Path(parent) / "outside-sentinel.txt"
            outside.write_text("OUTSIDE_TEST_MUST_NOT_BE_READ", encoding="utf-8")
            created = []

            def fixture_directory(**kwargs):
                directory = TemporaryDirectory(dir=parent, **kwargs)
                created.append(Path(directory.name))
                return directory

            with patch("securitylab.traversal.TemporaryDirectory", side_effect=fixture_directory):
                with patch.object(Path, "read_text", side_effect=AssertionError("Unexpected content read")) as read:
                    for mode in ("vulnerable", "fixed"):
                        result = self.read("../../outside-sentinel.txt", mode)
                        self.assertEqual(result.status_code, 403)
                        self.assertEqual(result.json()["outcome"], "blocked")
                        self.assertIsNone(result.json()["content"])
                        self.assertIsNone(result.json()["resolvedPath"])
                        self.assertNotIn(parent, result.content.decode())
                    read.assert_not_called()
            self.assertTrue(all(not directory.exists() for directory in created))
            self.assertEqual(outside.read_text(encoding="utf-8"), "OUTSIDE_TEST_MUST_NOT_BE_READ")

    def test_invalid_paths_never_create_fixtures_or_read_files(self):
        paths = ("", "x" * 257, "bad\x00name", "bad\nname", "/outside.txt",
                 "\\outside.txt", "C:\\outside.txt", "C:outside.txt", "//host/share/file",
                 "\\\\host\\share\\file", "readme.txt:stream")
        with patch("securitylab.traversal.TemporaryDirectory") as directory:
            for mode in ("vulnerable", "fixed"):
                for path in paths:
                    with self.subTest(mode=mode, path=path):
                        response = self.read(path, mode)
                        self.assertEqual(response.status_code, 400)
                        self.assertEqual(response.json()["outcome"], "invalid")
                        self.assertIsNone(response.json()["content"])
            directory.assert_not_called()

    def test_query_is_decoded_once_without_an_extra_application_decode(self):
        for mode in ("vulnerable", "fixed"):
            single = self.client.get(f"/api/traversal/?mode={mode}&path=%2e%2e%2fprivate%2fsentinel.txt")
            self.assertEqual(single.json()["requestedPath"], "../private/sentinel.txt")
            self.assertEqual(single.status_code, 200 if mode == "vulnerable" else 403)
            double = self.client.get(f"/api/traversal/?mode={mode}&path=%252e%252e%252fprivate%252fsentinel.txt")
            self.assertEqual(double.status_code, 404)
            self.assertEqual(double.json()["requestedPath"], "%2e%2e%2fprivate%2fsentinel.txt")
            self.assertIsNone(double.json()["content"])

    def test_unknown_or_duplicate_parameters_and_methods_are_rejected(self):
        for query in ("mode=unknown", "path=readme.txt&path=../private/sentinel.txt",
                      "mode=fixed&mode=vulnerable", "unexpected=1"):
            with self.subTest(query=query):
                response = self.client.get("/api/traversal/?" + query)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["outcome"], "invalid")
        response = self.client.post("/api/traversal/", {})
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "GET")

    def test_real_fixture_reads_are_bounded_and_temporary_directory_is_removed(self):
        created = []
        original_read = Path.read_text

        def fixture_directory(**kwargs):
            directory = TemporaryDirectory(**kwargs)
            created.append(Path(directory.name).resolve())
            return directory

        def checked_read(path, *args, **kwargs):
            self.assertTrue(path.is_relative_to(created[-1]))
            self.assertIn(path.relative_to(created[-1]).as_posix(), FIXTURE_CONTENTS)
            return original_read(path, *args, **kwargs)

        with patch("securitylab.traversal.TemporaryDirectory", side_effect=fixture_directory):
            with patch.object(Path, "read_text", autospec=True, side_effect=checked_read) as read:
                response = self.read("../private/sentinel.txt", "vulnerable")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(read.call_count, 1)
        self.assertTrue(all(not directory.exists() for directory in created))
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
