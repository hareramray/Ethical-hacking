"""Actual fixture execution and the command lesson's HTTP/process boundaries."""
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, SimpleTestCase, override_settings
from django.urls import path

from . import command_lab

urlpatterns = [path("api/command/compare/", command_lab.command_compare)]


@override_settings(ROOT_URLCONF=__name__)
class CommandLabTests(SimpleTestCase):
    def compare(self, fixture="normal", **extra):
        return self.client.post("/api/command/compare/", {"fixture": fixture, **extra}, content_type="application/json")

    def test_ordinary_name_completes_without_unintended_effect(self):
        response = self.compare()
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        for result in results.values():
            self.assertEqual(result["outcome"], "completed")
            self.assertEqual(result["returnCode"], 0)
            self.assertFalse(result["effect"])
        self.assertEqual(results["vulnerable"]["stdout"].strip(), "Alice")
        self.assertEqual(json.loads(results["fixed"]["stdout"])["names"], ["Alice"])

    def test_separator_is_interpreted_only_by_the_explicit_shell(self):
        result = self.compare("separator").json()
        vulnerable, fixed = result["results"]["vulnerable"], result["results"]["fixed"]
        self.assertEqual(vulnerable["outcome"], "completed")
        self.assertTrue(vulnerable["effect"])
        self.assertIn("COMMAND_SEPARATOR_MARKER", vulnerable["stdout"].splitlines())
        self.assertEqual(fixed["outcome"], "completed")
        self.assertFalse(fixed["effect"])
        self.assertEqual(json.loads(fixed["stdout"])["names"], [result["input"]])

    def test_splitting_an_operand_creates_an_option_even_without_a_shell(self):
        result = self.compare("argument").json()["results"]
        vulnerable = json.loads(result["vulnerable"]["stdout"])
        fixed = json.loads(result["fixed"]["stdout"])
        self.assertEqual(vulnerable, {"argv": ["Alice", "--flag"], "names": ["Alice"], "flag": True, "marker": "ARGUMENT_FLAG_MARKER"})
        self.assertEqual(fixed, {"argv": ["--", "Alice --flag"], "names": ["Alice --flag"], "flag": False, "marker": None})
        self.assertTrue(result["vulnerable"]["effect"])
        self.assertFalse(result["fixed"]["effect"])

    def test_end_of_options_preserves_a_legitimate_option_like_name(self):
        result = self.compare("leading-option").json()["results"]
        self.assertTrue(result["vulnerable"]["effect"])
        self.assertEqual(json.loads(result["vulnerable"]["stdout"])["names"], [])
        self.assertFalse(result["fixed"]["effect"])
        self.assertEqual(json.loads(result["fixed"]["stdout"])["names"], ["--flag"])

    def test_invocations_use_absolute_trusted_programs_and_disposable_directories(self):
        run = subprocess.run
        directories = []

        def tracked_run(argv, **kwargs):
            self.assertIsInstance(argv, list)
            self.assertTrue(Path(argv[0]).is_absolute())
            self.assertFalse(kwargs["shell"])
            self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
            self.assertEqual(kwargs["timeout"], command_lab.TIMEOUT_SECONDS)
            self.assertEqual(kwargs["env"], {})
            self.assertTrue(kwargs["capture_output"])
            directory = Path(kwargs["cwd"])
            self.assertTrue(directory.is_dir())
            self.assertEqual(list(directory.iterdir()), [])
            directories.append(directory)
            if argv[0] == command_lab.PYTHON:
                self.assertEqual(argv[1:4], ["-I", "-S", command_lab.RECORDER])
            elif command_lab.WINDOWS:
                self.assertEqual(argv[1:5], ["/d", "/q", "/v:off", "/c"])
                self.assertIn(argv[-1], command_lab.SHELL_SCRIPTS.values())
            else:
                self.assertEqual(argv[1], "-c")
                self.assertIn(argv[-1], command_lab.SHELL_SCRIPTS.values())
            completed = run(argv, **kwargs)
            self.assertEqual(list(directory.iterdir()), [])
            return completed

        with patch("securitylab.command_lab.subprocess.run", side_effect=tracked_run):
            self.compare("separator")
            self.compare("argument")
        self.assertEqual(len(directories), 4)
        self.assertEqual(len(set(directories)), 4)
        self.assertTrue(all(not directory.exists() for directory in directories))

    def test_unknown_and_custom_inputs_never_start_a_process(self):
        with patch("securitylab.command_lab.subprocess.run") as run:
            for fixture in ("", "unknown", "echo test", [], None, 1, "normal; echo test"):
                with self.subTest(fixture=fixture):
                    self.assertEqual(self.compare(fixture).status_code, 400)
            for field in ("command", "input", "executable", "cwd", "args", "mode"):
                self.assertEqual(self.compare(**{field: "test"}).status_code, 400)
            for raw in ("{", "[]", "null", "{}", "[" * 1024, '{"fixture":"normal","fixture":"separator"}',
                        json.dumps({"fixture": "x" * 1100})):
                response = self.client.post("/api/command/compare/", raw, content_type="application/json")
                self.assertEqual(response.status_code, 400)
            run.assert_not_called()

    def test_method_query_and_content_type_are_restricted(self):
        response = self.client.get("/api/command/compare/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")
        self.assertEqual(self.client.post("/api/command/compare/", {"fixture": "normal"}).status_code, 400)
        self.assertEqual(self.client.post("/api/command/compare/?fixture=separator", {"fixture": "normal"}, content_type="application/json").status_code, 400)

    def test_csrf_token_and_trusted_origin_are_required(self):
        client = Client(enforce_csrf_checks=True)
        body = json.dumps({"fixture": "normal"})
        self.assertEqual(client.post("/api/command/compare/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        self.assertEqual(client.post("/api/command/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(client.post("/api/command/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token,
                                     HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)

    def test_concurrency_limit_rejects_without_executing_and_releases_slots(self):
        self.assertTrue(command_lab.RUN_SLOTS.acquire(blocking=False))
        self.assertTrue(command_lab.RUN_SLOTS.acquire(blocking=False))
        try:
            with patch("securitylab.command_lab.subprocess.run") as run:
                self.assertEqual(self.compare().status_code, 429)
                run.assert_not_called()
        finally:
            command_lab.RUN_SLOTS.release()
            command_lab.RUN_SLOTS.release()
        self.assertEqual(self.compare().status_code, 200)

    def test_real_timeout_stops_the_direct_child_and_removes_working_directory(self):
        popen = subprocess.Popen
        children, directories = [], []

        def tracked_popen(*args, **kwargs):
            child = popen(*args, **kwargs)
            children.append(child)
            directories.append(Path(kwargs["cwd"]))
            return child

        # A test-owned sleeping child makes the timeout deterministic, rather
        # than racing a recorder that can complete before the parent is scheduled.
        sleeper = [command_lab.PYTHON, "-I", "-S", "-c", "import time; time.sleep(10)"]
        with patch("securitylab.command_lab.TIMEOUT_SECONDS", 0.02), \
                patch("securitylab.command_lab.invocation", return_value=sleeper), \
                patch("subprocess.Popen", side_effect=tracked_popen):
            result = command_lab.run_fixture("argument", "fixed")
        self.assertEqual(result["outcome"], "timeout")
        self.assertEqual(result["stdout"], "")
        self.assertIsNone(result["effect"])
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].poll())
        self.assertTrue(all(not directory.exists() for directory in directories))

    def test_missing_program_and_excess_output_are_reported_without_unbounded_text(self):
        with patch("securitylab.command_lab.subprocess.run", side_effect=FileNotFoundError):
            result = self.compare().json()["results"]
        self.assertTrue(all(item["outcome"] == "unavailable" for item in result.values()))
        completed = subprocess.CompletedProcess([], 1, b"x" * 10000, b"y" * 10000)
        with patch("securitylab.command_lab.subprocess.run", return_value=completed):
            result = self.compare().json()["results"]["fixed"]
        self.assertEqual(len(result["stdout"]), command_lab.OUTPUT_LIMIT)
        self.assertEqual(len(result["stderr"]), command_lab.OUTPUT_LIMIT)
        self.assertIsNone(result["effect"])
        self.assertEqual(self.compare().status_code, 200)
