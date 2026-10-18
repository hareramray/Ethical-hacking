"""Real file reads inside a fresh, disposable path-traversal demonstration.

The outer fixture boundary is a lab guardrail, not the demonstrated application
fix. Only ``fixed`` mode enforces the intended public download directory.
"""
import os
import unicodedata
from pathlib import Path, PureWindowsPath
from tempfile import TemporaryDirectory

from django.http import JsonResponse


MAX_PATH_CHARACTERS = 256
FIXTURE_CONTENTS = {
    "public/readme.txt": "PUBLIC_README_OK\n",
    "public/nested/notes.txt": "NESTED_NOTES_OK\n",
    "private/sentinel.txt": "PRIVATE_SENTINEL_ONLY_FOR_LAB\n",
    "public-notes/sibling.txt": "SIBLING_PREFIX_SENTINEL\n",
}
TRAVERSAL_FIXTURES = [
    {"id": "readme", "label": "Public readme", "path": "readme.txt"},
    {"id": "nested", "label": "Nested public file", "path": "nested/notes.txt"},
    {"id": "parent", "label": "Parent directory traversal", "path": "../private/sentinel.txt"},
    {"id": "backslash", "label": "Backslash traversal", "path": "..\\private\\sentinel.txt"},
    {"id": "prefix", "label": "Sibling with a matching prefix", "path": "../public-notes/sibling.txt"},
    {"id": "missing", "label": "Missing file", "path": "missing.txt"},
]
TRAVERSAL_TREE = (
    "disposable-lab/\n"
    "  public/                  <- intended download root\n"
    "    readme.txt\n"
    "    nested/notes.txt\n"
    "  private/sentinel.txt\n"
    "  public-notes/sibling.txt"
)
TRAVERSAL_METADATA = {"fixtures": TRAVERSAL_FIXTURES, "tree": TRAVERSAL_TREE}


def traversal(request):
    """Compare a missing directory boundary with resolved-path containment."""
    mode = request.GET.get("mode", "fixed")
    requested = request.GET.get("path", "readme.txt")
    normalized = requested.replace("\\", "/")
    result = {
        "mode": mode,
        "requestedPath": requested,
        "normalizedPath": normalized,
        "resolvedPath": None,
        "allowedRoot": "public/",
        "outcome": "invalid",
        "reason": "",
        "content": None,
    }

    def respond(outcome, reason, status, *, resolved=None, content=None):
        result.update(outcome=outcome, reason=reason, resolvedPath=resolved, content=content)
        response = JsonResponse(result, status=status)
        response["Cache-Control"] = "no-store"
        return response

    if request.method != "GET":
        response = respond("invalid", "Use GET for this read-only exercise.", 405)
        response["Allow"] = "GET"
        return response
    if any(key not in {"mode", "path"} or len(request.GET.getlist(key)) != 1
           for key in request.GET):
        return respond("invalid", "Use only one mode and one path parameter.", 400)
    if mode not in {"vulnerable", "fixed"}:
        return respond("invalid", "Mode must be vulnerable or fixed.", 400)
    if not requested or len(requested) > MAX_PATH_CHARACTERS:
        return respond("invalid", "Path must contain 1 to 256 characters.", 400)
    if any(unicodedata.category(char) == "Cc" for char in requested):
        return respond("invalid", "Control characters, including NUL, are not accepted.", 400)
    if normalized.startswith("/") or PureWindowsPath(requested).drive or ":" in requested:
        return respond("invalid", "Use a relative path; absolute paths, drives, and streams are disabled.", 400)

    # Django has decoded the query string once. Do not unquote it again.
    # Backslashes are explicitly treated as separators on every host OS so the
    # Windows-style preset behaves identically in this portable exercise.
    with TemporaryDirectory(prefix="browser-security-traversal-") as directory:
        lab_root = Path(directory).resolve()
        public_root = lab_root / "public"
        for relative, content in FIXTURE_CONTENTS.items():
            fixture = lab_root / relative
            fixture.parent.mkdir(parents=True, exist_ok=True)
            fixture.write_text(content, encoding="utf-8")

        # Normalize lexical parent segments before resolve() so paths outside
        # the disposable tree do not cause filesystem lookups elsewhere.
        try:
            lexical = Path(os.path.abspath(public_root / normalized))
            if not lexical.is_relative_to(lab_root):
                return respond(
                    "blocked", "The outer disposable lab boundary blocked this path. "
                    "This guardrail limits the exercise; it is not the production fix.", 403,
                )
            candidate = lexical.resolve()
        except (OSError, ValueError, RuntimeError):
            return respond("invalid", "The path could not be resolved inside the disposable lab.", 400)

        if not candidate.is_relative_to(lab_root):
            return respond(
                "blocked", "The outer disposable lab boundary blocked the resolved path. "
                "This guardrail limits the exercise; it is not the production fix.", 403,
            )
        relative = candidate.relative_to(lab_root).as_posix()
        if mode == "fixed" and not candidate.is_relative_to(public_root):
            return respond(
                "blocked", "Fixed mode requires the resolved path to stay inside public/.",
                403, resolved=relative,
            )

        # An additional fixture allowlist means the demonstration cannot read
        # any file other than the four small files created above.
        if relative not in FIXTURE_CONTENTS:
            return respond("not_found", "No readable fixture exists at this path.", 404, resolved=relative)
        content = candidate.read_text(encoding="utf-8")
        reason = (
            "Vulnerable mode reads a fixture outside public/ because its intended directory boundary is missing."
            if not candidate.is_relative_to(public_root)
            else "The resolved fixture is inside public/."
        )
        return respond("read", reason, 200, resolved=relative, content=content)
