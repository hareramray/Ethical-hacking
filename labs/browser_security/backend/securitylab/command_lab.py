"""Execute only server-owned command fixtures, never a caller-provided command."""
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

from django.http import JsonResponse

TIMEOUT_SECONDS = 3
OUTPUT_LIMIT = 2048
BODY_LIMIT = 1024
RUN_SLOTS = threading.BoundedSemaphore(2)
# Use the base interpreter to avoid the Windows virtualenv launcher shim. The
# recorder needs only the standard library, with site/environment loading off.
PYTHON = str(Path(getattr(sys, "_base_executable", sys.executable)).resolve())
RECORDER = str(Path(__file__).with_name("command_fixture.py").resolve())
WINDOWS = os.name == "nt"
SEPARATOR_INPUT = "Alice & echo COMMAND_SEPARATOR_MARKER" if WINDOWS else "Alice; printf '%s\\n' COMMAND_SEPARATOR_MARKER"
FIXTURES = {
    "normal": {"label": "Ordinary name", "input": "Alice", "scenario": "shell"},
    "separator": {"label": "Shell separator prints a second marker", "input": SEPARATOR_INPUT, "scenario": "shell"},
    "argument": {"label": "Splitting creates an extra option", "input": "Alice --flag", "scenario": "argument"},
    "leading-option": {"label": "A name starts with an option prefix", "input": "--flag", "scenario": "argument"},
}
# Complete strings, not templates: HTTP input is never interpolated here.
SHELL_SCRIPTS = {
    "normal": "echo Alice" if WINDOWS else "printf '%s\\n' Alice",
    "separator": "echo Alice & echo COMMAND_SEPARATOR_MARKER" if WINDOWS else "printf '%s\\n' Alice; printf '%s\\n' COMMAND_SEPARATOR_MARKER",
}
COMMAND_METADATA = {
    "fixtures": [{"id": key, **value} for key, value in FIXTURES.items()],
    "platform": "Windows cmd.exe" if WINDOWS else "POSIX /bin/sh",
    "timeoutSeconds": TIMEOUT_SECONDS,
    "outputLimit": OUTPUT_LIMIT,
}


def shell_executable():
    if WINDOWS:
        # Ask Windows, rather than trusting COMSPEC, PATH, or SystemRoot input.
        buffer = ctypes.create_unicode_buffer(32768)
        length = ctypes.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer))
        if not length or length >= len(buffer):
            raise OSError("Windows system directory unavailable")
        return str(Path(buffer.value) / "cmd.exe")
    return str(Path("/bin/sh").resolve(strict=True))


def invocation(fixture_id, mode):
    fixture = FIXTURES[fixture_id]
    if mode == "vulnerable" and fixture["scenario"] == "shell":
        flags = ["/d", "/q", "/v:off", "/c"] if WINDOWS else ["-c"]
        return [shell_executable(), *flags, SHELL_SCRIPTS[fixture_id]]
    # Even shell=False can give the target program unintended options.
    operands = fixture["input"].split() if mode == "vulnerable" else ["--", fixture["input"]]
    return [PYTHON, "-I", "-S", RECORDER, *operands]


def bounded_text(value):
    if isinstance(value, bytes):
        return value[:OUTPUT_LIMIT].decode("utf-8", errors="replace")
    return (value or "")[:OUTPUT_LIMIT]


def run_fixture(fixture_id, mode):
    result = {"mode": mode, "outcome": "unavailable", "invocation": [],
              "stdout": "", "stderr": "", "returnCode": None, "effect": None, "reason": ""}
    try:
        argv = invocation(fixture_id, mode)
        result["invocation"] = argv
        with tempfile.TemporaryDirectory(prefix="command-lesson-") as directory:
            # Only constant echo/printf scripts and our JSON recorder can run.
            # Their output is inherently small; stdin cannot trigger more work.
            # run() kills and waits for its child if the timeout expires.
            completed = subprocess.run(
                argv, shell=False, cwd=directory, stdin=subprocess.DEVNULL,
                capture_output=True, timeout=TIMEOUT_SECONDS, check=False,
                env={}, creationflags=subprocess.CREATE_NO_WINDOW if WINDOWS else 0,
            )
        result.update(stdout=bounded_text(completed.stdout), stderr=bounded_text(completed.stderr),
                      returnCode=completed.returncode)
        if completed.returncode:
            result["reason"] = "The fixed demonstration program did not complete successfully."
            return result
        fixture = FIXTURES[fixture_id]
        if mode == "vulnerable" and fixture["scenario"] == "shell":
            effect = "COMMAND_SEPARATOR_MARKER" in {line.strip() for line in result["stdout"].splitlines()}
            reason = "A shell interprets the predeclared string; a separator can start another builtin."
        else:
            recorded = json.loads(result["stdout"])
            effect = recorded["flag"] is True
            reason = ("Splitting the name produced program arguments that the recorder can interpret as options."
                      if mode == "vulnerable" else
                      "The name remains one operand after --, and no shell parses it.")
        result.update(outcome="completed", effect=effect, reason=reason)
    except subprocess.TimeoutExpired:
        result.update(outcome="timeout", reason="The child exceeded the time limit and was stopped.")
    except (OSError, ValueError, KeyError):
        result["reason"] = "The fixed demonstration program is unavailable or returned invalid output."
    return result


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate field")
        result[key] = value
    return result


def command_compare(request):
    """Django's standard CSRF middleware protects this fixture-only POST."""
    def invalid(reason, status=400):
        return JsonResponse({"outcome": "invalid", "reason": reason}, status=status)

    if request.method != "POST":
        response = invalid("Use POST with an application/json body.", 405)
        response["Allow"] = "POST"
        return response
    if request.GET or request.content_type != "application/json":
        return invalid("Use a JSON body without query parameters.")
    if len(request.body) > BODY_LIMIT:
        return invalid("The request body exceeds the fixture selector limit.")
    try:
        data = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return invalid("Invalid JSON or duplicate fields.")
    if not isinstance(data, dict) or set(data) != {"fixture"}:
        return invalid("Provide exactly one fixture field; custom commands and arguments are not accepted.")
    fixture_id = data["fixture"]
    if not isinstance(fixture_id, str) or fixture_id not in FIXTURES:
        return invalid("Select a known demonstration fixture.")
    if not RUN_SLOTS.acquire(blocking=False):
        return JsonResponse({"outcome": "busy", "reason": "Two comparisons are already running. Try again shortly."}, status=429)
    try:
        fixture = FIXTURES[fixture_id]
        result = {"fixture": fixture_id, "input": fixture["input"], "scenario": fixture["scenario"],
                  "results": {mode: run_fixture(fixture_id, mode) for mode in ("vulnerable", "fixed")}}
        return JsonResponse(result)
    finally:
        RUN_SLOTS.release()
