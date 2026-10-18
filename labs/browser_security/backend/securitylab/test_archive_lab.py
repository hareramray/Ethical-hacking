"""Real ZIP reads and isolated filesystem writes, including failure cleanup."""
import io
import json
import stat
import tempfile
from pathlib import Path
from unittest.mock import patch
import zipfile

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, SimpleTestCase, override_settings
from django.urls import path

from . import archive_lab as lab

urlpatterns = [path("api/archive/compare/", lab.archive_compare)]


@override_settings(ROOT_URLCONF=__name__)
class ArchiveLabTests(SimpleTestCase):
    def compare(self, fixture):
        return self.client.post("/api/archive/compare/", {"fixture": fixture}, content_type="application/json")

    def test_nested_file_positive_control_has_real_content_in_both_workspaces(self):
        response = self.compare("normal")
        self.assertEqual(response.status_code, 200)
        for result in response.json()["results"].values():
            self.assertEqual(result["outcome"], "extracted")
            self.assertEqual(result["before"], [])
            self.assertEqual(result["after"], [{"path": "extract/docs/hello.txt", "content": "ZIP_NORMAL_MARKER", "bytes": 17, "outsideExtraction": False}])
            self.assertEqual(result["filesWritten"], 1)

    def test_parent_and_backslash_write_actual_sibling_only_in_vulnerable_branch(self):
        for fixture in ("traversal", "backslash", "mixed"):
            with self.subTest(fixture=fixture):
                results = self.compare(fixture).json()["results"]
                self.assertTrue(results["vulnerable"]["outsideExtraction"])
                sibling = next(item for item in results["vulnerable"]["after"] if item["path"] == "outside.txt")
                self.assertEqual(sibling["content"], lab.MARKER)
                self.assertTrue(sibling["outsideExtraction"])
                self.assertEqual(results["fixed"]["outcome"], "blocked")
                self.assertEqual(results["fixed"]["after"], [])
                self.assertEqual(results["fixed"]["written"], [])

    def test_absolute_and_drive_paths_are_blocked_by_both_boundaries(self):
        for fixture in ("absolute", "drive"):
            for result in self.compare(fixture).json()["results"].values():
                self.assertEqual(result["outcome"], "blocked")
                self.assertEqual(result["after"], [])

    def test_tiny_budget_fixtures_have_no_fixed_partial_writes(self):
        for fixture, reason in (("count", "Entry-count"), ("expanded", "Total expanded"), ("entry", "Per-entry expanded"), ("compressed", "Per-entry compressed")):
            with self.subTest(fixture=fixture):
                results = self.compare(fixture).json()["results"]
                self.assertEqual(results["vulnerable"]["outcome"], "extracted")
                self.assertEqual(results["fixed"]["outcome"], "blocked")
                self.assertIn(reason, results["fixed"]["reason"])
                self.assertEqual(results["fixed"]["after"], [])
                self.assertEqual(results["fixed"]["expandedBytesRead"], 0)

    def test_duplicate_overwrite_and_file_directory_collision_are_observable(self):
        results = self.compare("duplicate").json()["results"]
        self.assertEqual(results["vulnerable"]["filesWritten"], 2)
        self.assertEqual([item["content"] for item in results["vulnerable"]["written"]], ["FIRST_MARKER", "SECOND_MARKER"])
        self.assertEqual(results["vulnerable"]["after"][0]["content"], "SECOND_MARKER")
        self.assertEqual(results["fixed"]["after"], [])
        results = self.compare("collision").json()["results"]
        self.assertEqual(results["vulnerable"]["outcome"], "error")
        self.assertEqual(results["vulnerable"]["after"][0]["path"], "extract/docs")
        self.assertEqual(results["fixed"]["outcome"], "blocked")
        self.assertEqual(results["fixed"]["after"], [])

    def test_symlink_metadata_never_creates_an_actual_link(self):
        with patch.object(Path, "symlink_to", side_effect=AssertionError("No symlinks allowed")):
            results = self.compare("symlink").json()["results"]
        self.assertEqual(results["vulnerable"]["after"][0]["content"], "../outside.txt")
        self.assertFalse(results["vulnerable"]["outsideExtraction"])
        self.assertEqual(results["fixed"]["outcome"], "blocked")
        self.assertEqual(results["fixed"]["after"], [])

    def test_no_destination_outside_outer_workspace_even_with_internal_bad_fixture(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary).resolve()
            workspace = parent / "workspace"
            workspace.mkdir()
            root = workspace / "extract"
            root.mkdir()
            for name in ("../../outside.txt", "../../../outside.txt", "/outside.txt", "C:/outside.txt", "C:outside.txt", "\\\\server\\share\\outside.txt"):
                with self.subTest(name=name), self.assertRaises(lab.ExtractionBlocked):
                    lab.bounded_destination(zipfile.ZipInfo(name), root, workspace)
            self.assertFalse((parent / "outside.txt").exists())

    def test_strict_components_types_and_casefolded_collisions(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve()
            root = workspace / "extract"
            root.mkdir()
            for name in ("a/../b.txt", "a//b.txt", "./file.txt", "CON.txt", "file:stream", "trailing.", "space name.txt", "a\x00b", "folder/"):
                with self.subTest(name=name), self.assertRaises(lab.ExtractionBlocked):
                    lab.fixed_destinations([zipfile.ZipInfo(name)], root, workspace)
            for mode in (stat.S_IFLNK, stat.S_IFIFO, stat.S_IFCHR):
                info = zipfile.ZipInfo("special.txt")
                info.external_attr = mode << 16
                with self.assertRaises(lab.ExtractionBlocked):
                    lab.fixed_destinations([info], root, workspace)
            for names in (("A.txt", "a.txt"), ("Docs", "docs/file.txt"), ("a/b", "a")):
                with self.assertRaises(lab.ExtractionBlocked):
                    lab.fixed_destinations([zipfile.ZipInfo(name) for name in names], root, workspace)

    def test_declared_compressed_total_and_archive_limits(self):
        first, second = zipfile.ZipInfo("a.txt"), zipfile.ZipInfo("b.txt")
        for info in (first, second):
            info.file_size = 88
            info.compress_size = 88
        with self.assertRaisesRegex(lab.ExtractionBlocked, "Total compressed"):
            lab.check_sizes([first, second], 300, lab.BUDGETS)
        with self.assertRaisesRegex(lab.ExtractionBlocked, "Archive-byte"):
            lab.check_sizes([], lab.BUDGETS["archiveBytes"] + 1, lab.BUDGETS)

    def test_actual_streamed_limits_and_size_mismatch_close_members(self):
        class StreamArchive:
            def __init__(self, payload):
                self.stream = io.BytesIO(payload)

            def open(self, info):
                return self.stream

        info = zipfile.ZipInfo("small.txt")
        info.file_size = 1
        for payload, used, reason in ((b"A" * 129, 0, "Actual streamed"), (b"AB", 191, "Actual streamed"), (b"AB", 0, "declared size")):
            archive = StreamArchive(payload)
            with self.assertRaisesRegex(lab.ExtractionBlocked, reason):
                lab.read_member(archive, info, lab.BUDGETS, [used])
            self.assertTrue(archive.stream.closed)

    def test_staged_read_failure_does_not_write_any_fixed_files(self):
        actual = lab.read_member
        count = [0]

        def failing_second(*args):
            count[0] += 1
            if count[0] == 2:
                raise lab.ExtractionBlocked("Actual streamed expanded-byte budget exceeded.")
            return actual(*args)

        # Two legitimate distinct destinations are constructed from finite constants.
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("one.txt", "FIRST")
            archive.writestr("two.txt", "SECOND")
        with tempfile.TemporaryDirectory() as temporary, patch.object(lab, "read_member", side_effect=failing_second):
            result = lab.extract_comparison(buffer.getvalue(), "fixed", Path(temporary).resolve() / "fixed")
        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(result["after"], [])

    def test_workspaces_are_removed_after_success_block_and_unexpected_failure(self):
        original = tempfile.TemporaryDirectory
        created = []

        def tracked(*args, **kwargs):
            context = original(*args, **kwargs)
            created.append(Path(context.name))
            return context

        with patch.object(lab.tempfile, "TemporaryDirectory", side_effect=tracked):
            for fixture in ("normal", "mixed", "collision"):
                lab.compare_archive(fixture)
            with patch.object(lab, "extract_comparison", side_effect=RuntimeError("synthetic failure")), self.assertRaises(RuntimeError):
                lab.compare_archive("normal")
        self.assertEqual(len(created), 4)
        self.assertTrue(all(not path.exists() for path in created))

    def test_every_server_fixture_fits_the_outer_envelope_and_returns_no_host_path(self):
        for fixture in lab.FIXTURES:
            response = self.compare(fixture)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertLessEqual(data["archiveBytes"], lab.OUTER_BUDGETS["archiveBytes"])
            for result in data["results"].values():
                self.assertEqual(result["before"], [])
                for item in result["after"]:
                    self.assertFalse(Path(item["path"]).is_absolute())
                    self.assertNotIn("..", item["path"].split("/"))
                self.assertLessEqual(result["expandedBytesRead"], lab.OUTER_BUDGETS["totalExpandedBytes"])

    def test_selector_schema_recursion_method_and_media_type_reject_before_zip_work(self):
        with patch.object(lab, "build_archive") as build:
            for body in ({}, [], {"fixture": None}, {"fixture": []}, {"fixture": "missing"}, {"fixture": "normal", "archive": "bytes"}):
                self.assertEqual(self.client.post("/api/archive/compare/", body, content_type="application/json").status_code, 400)
            for raw in ("{", '{"fixture":"normal","fixture":"mixed"}', " " * 2049, "[" * 1000 + "]" * 1000):
                self.assertEqual(self.client.post("/api/archive/compare/", raw, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/archive/compare/?fixture=normal", {"fixture": "normal"}, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/archive/compare/", {"fixture": "normal"}).status_code, 400)
            build.assert_not_called()
        response = self.client.get("/api/archive/compare/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")

    def test_csrf_and_bounded_concurrency(self):
        client = Client(enforce_csrf_checks=True)
        body = json.dumps({"fixture": "normal"})
        self.assertEqual(client.post("/api/archive/compare/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        self.assertEqual(client.post("/api/archive/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(client.post("/api/archive/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)
        lab.SLOTS.acquire()
        lab.SLOTS.acquire()
        try:
            self.assertEqual(self.compare("normal").status_code, 429)
        finally:
            lab.SLOTS.release()
            lab.SLOTS.release()
