"""Small, server-owned ZIPs: unsafe joins versus preflighted extraction."""
import io
import json
import re
import stat
import tempfile
import warnings
import zipfile
from pathlib import Path, PureWindowsPath
from threading import BoundedSemaphore

from django.http import JsonResponse

BUDGETS = {"entries": 3, "entryExpandedBytes": 128, "totalExpandedBytes": 192,
           "entryCompressedBytes": 96, "totalCompressedBytes": 160, "archiveBytes": 4096}
# A separate, looser envelope also contains the deliberately vulnerable branch.
OUTER_BUDGETS = {"entries": 8, "entryExpandedBytes": 512, "totalExpandedBytes": 2048,
                 "entryCompressedBytes": 512, "totalCompressedBytes": 2048, "archiveBytes": 8192}
MARKER = "ZIP_SIBLING_MARKER"
FIXTURES = {
    "normal": {"label": "Control: a nested text file", "expectation": "Both handlers create extract/docs/hello.txt with the same marker."},
    "traversal": {"label": "Parent path: ../outside.txt", "expectation": "The unsafe join writes a sibling file inside the disposable workspace. Fixed extraction rejects the parent component."},
    "backslash": {"label": "Backslash parent path", "expectation": "Both handlers explicitly normalize backslashes. The unsafe join escapes the extraction folder; fixed validation rejects it."},
    "absolute": {"label": "Absolute member name", "expectation": "Both refuse this fixture: the outer lab boundary prevents any absolute destination from being opened."},
    "drive": {"label": "Windows drive member name", "expectation": "Both refuse a drive-qualified member on every platform."},
    "mixed": {"label": "Valid file followed by traversal", "expectation": "The vulnerable handler writes both files. Fixed whole-archive validation writes neither."},
    "count": {"label": "Four tiny files exceed a three-entry budget", "expectation": "The vulnerable handler writes four tiny files. Fixed extraction rejects the count before writing."},
    "expanded": {"label": "Two files exceed the total expanded-byte budget", "expectation": "Two 112-byte files exceed the fixed 192-byte total. These are tiny fixtures, not archive bombs."},
    "entry": {"label": "One file exceeds the per-entry expanded budget", "expectation": "A 160-byte file exceeds the fixed 128-byte entry limit."},
    "compressed": {"label": "Stored member exceeds the compressed-byte budget", "expectation": "A 110-byte stored member is below the expanded limit but above the 96-byte compressed-entry limit."},
    "duplicate": {"label": "Duplicate destination", "expectation": "The vulnerable handler overwrites the first marker. Fixed extraction rejects duplicate destinations before any writes."},
    "collision": {"label": "File and parent-directory collision", "expectation": "The vulnerable handler leaves a partial file before its next write fails. Fixed preflight rejects the collision with zero writes."},
    "symlink": {"label": "Symlink metadata", "expectation": "The vulnerable handler ignores member type and writes ordinary text. Fixed extraction rejects symlink metadata. Neither branch creates a symlink."},
}
ARCHIVE_METADATA = {"fixtures": [{"id": key, **value} for key, value in FIXTURES.items()], "budgets": BUDGETS}
SLOTS = BoundedSemaphore(2)


class ExtractionBlocked(ValueError):
    pass


def build_archive(fixture):
    """Never accepts bytes or member names supplied by an HTTP caller."""
    entries = {
        "normal": [("docs/hello.txt", "ZIP_NORMAL_MARKER")],
        "traversal": [("../outside.txt", MARKER)],
        "backslash": [("..\\outside.txt", MARKER)],
        "absolute": [("/lab-absolute-marker.txt", MARKER)],
        "drive": [("C:/lab-drive-marker.txt", MARKER)],
        "mixed": [("docs/hello.txt", "ZIP_NORMAL_MARKER"), ("../outside.txt", MARKER)],
        "count": [(f"file-{index}.txt", f"TINY_{index}") for index in range(4)],
        "expanded": [("one.txt", "A" * 112), ("two.txt", "B" * 112)],
        "entry": [("large.txt", "A" * 160)],
        "compressed": [("stored.txt", "S" * 110)],
        "duplicate": [("note.txt", "FIRST_MARKER"), ("note.txt", "SECOND_MARKER")],
        "collision": [("docs", "FILE_MARKER"), ("docs/hello.txt", "CHILD_MARKER")],
        "symlink": [("link.txt", "../outside.txt")],
    }[fixture]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", allowZip64=False) as archive:
        for name, value in entries:
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            kind = stat.S_IFLNK if fixture == "symlink" else stat.S_IFREG
            info.external_attr = (kind | 0o600) << 16
            info.compress_type = zipfile.ZIP_STORED if fixture == "compressed" else zipfile.ZIP_DEFLATED
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)  # Intentional duplicate-name fixture.
                archive.writestr(info, value.encode("ascii"))
    return buffer.getvalue()


def normalized_name(info):
    return info.filename.replace("\\", "/")


def bounded_destination(info, extraction_root, workspace):
    """Outer lab containment is enforced even for the unsafe demonstration."""
    name = normalized_name(info)
    if name.startswith("/") or PureWindowsPath(name).drive:
        raise ExtractionBlocked("Absolute and drive-qualified names are blocked by the lab boundary.")
    destination = (extraction_root / name).resolve()
    if not destination.is_relative_to(workspace) or destination == workspace:
        raise ExtractionBlocked("The lab boundary forbids leaving its disposable workspace.")
    return destination


def check_sizes(infos, archive_bytes, limits):
    if archive_bytes > limits["archiveBytes"]:
        raise ExtractionBlocked("Archive-byte budget exceeded.")
    if len(infos) > limits["entries"]:
        raise ExtractionBlocked("Entry-count budget exceeded.")
    if any(info.file_size > limits["entryExpandedBytes"] for info in infos):
        raise ExtractionBlocked("Per-entry expanded-byte budget exceeded.")
    if sum(info.file_size for info in infos) > limits["totalExpandedBytes"]:
        raise ExtractionBlocked("Total expanded-byte budget exceeded.")
    if any(info.compress_size > limits["entryCompressedBytes"] for info in infos):
        raise ExtractionBlocked("Per-entry compressed-byte budget exceeded.")
    if sum(info.compress_size for info in infos) > limits["totalCompressedBytes"]:
        raise ExtractionBlocked("Total compressed-byte budget exceeded.")


def fixed_destinations(infos, extraction_root, workspace):
    destinations = []
    known = []
    for info in infos:
        name = normalized_name(info)
        parts = name.split("/")
        if info.orig_filename != info.filename or len(name) > 180 or len(parts) > 8:
            raise ExtractionBlocked("Invalid or overlong member name.")
        if any(part in ("", ".", "..") or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", part)
               or part.endswith(".") or re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part)
               for part in parts):
            raise ExtractionBlocked("Unsafe path component: empty, parent, reserved, or unsupported characters.")
        if info.flag_bits & 1 or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise ExtractionBlocked("Encrypted or unsupported compression is not allowed.")
        # This lesson accepts regular files only, with implicit parent folders.
        if info.is_dir() or stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG):
            raise ExtractionBlocked("Only regular-file members are allowed; links and special entries are rejected.")
        destination = bounded_destination(info, extraction_root, workspace)
        if destination == extraction_root or not destination.is_relative_to(extraction_root):
            raise ExtractionBlocked("Resolved destination is outside the extraction root.")
        key = tuple(part.casefold() for part in parts)
        if any(key == prior or key[:len(prior)] == prior or prior[:len(key)] == key for prior in known):
            raise ExtractionBlocked("Duplicate or colliding destinations are not allowed.")
        known.append(key)
        destinations.append(destination)
    return destinations


def read_member(archive, info, limits, consumed):
    """Count actual streamed output as well as declared ZIP header sizes."""
    output = bytearray()
    with archive.open(info) as source:
        while True:
            remaining = min(limits["entryExpandedBytes"] - len(output), limits["totalExpandedBytes"] - consumed[0])
            chunk = source.read(min(64, remaining + 1))
            if not chunk:
                break
            consumed[0] += len(chunk)
            output.extend(chunk)
            if len(output) > limits["entryExpandedBytes"] or consumed[0] > limits["totalExpandedBytes"]:
                raise ExtractionBlocked("Actual streamed expanded-byte budget exceeded.")
    if len(output) != info.file_size:
        raise ExtractionBlocked("Actual member size differs from its declared size.")
    return bytes(output)


def file_evidence(path, workspace, extraction_root):
    payload = path.read_bytes()
    return {"path": path.relative_to(workspace).as_posix(), "content": payload.decode("ascii", errors="replace"),
            "bytes": len(payload), "outsideExtraction": not path.is_relative_to(extraction_root)}


def extract_comparison(archive_bytes, mode, workspace):
    workspace.mkdir()
    extraction_root = workspace / "extract"
    extraction_root.mkdir()
    result = {"outcome": "extracted", "reason": "", "written": [], "before": [], "after": [],
              "outsideExtraction": False, "expandedBytesRead": 0, "filesWritten": 0}
    consumed = [0]
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes), "r", allowZip64=False) as archive:
            infos = archive.infolist()
            check_sizes(infos, len(archive_bytes), OUTER_BUDGETS)
            if mode == "fixed":
                check_sizes(infos, len(archive_bytes), BUDGETS)
                destinations = fixed_destinations(infos, extraction_root, workspace)
                # All names and all contents must pass before the first write.
                staged = [(destination, read_member(archive, info, BUDGETS, consumed))
                          for info, destination in zip(infos, destinations)]
            else:
                # Iteration deliberately writes one member before checking the next.
                staged = ((bounded_destination(info, extraction_root, workspace), read_member(archive, info, OUTER_BUDGETS, consumed)) for info in infos)
            for destination, payload in staged:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("xb" if mode == "fixed" else "wb") as output:
                    output.write(payload)
                result["written"].append(file_evidence(destination, workspace, extraction_root))
        result["reason"] = (
            "All names and sizes passed preflight; bounded reads completed before files were written."
            if mode == "fixed" else "Member names were joined to the destination and written sequentially, subject only to the outer lab boundary."
        )
    except ExtractionBlocked as error:
        result.update(outcome="blocked", reason=str(error))
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as error:
        # Do not expose host paths from OS errors in the response.
        result.update(outcome="error", reason=f"Extraction stopped with {type(error).__name__}; inspect the partial-write evidence.")
    result["after"] = [file_evidence(path, workspace, extraction_root) for path in sorted(workspace.rglob("*")) if path.is_file()]
    result["outsideExtraction"] = any(item["outsideExtraction"] for item in result["after"])
    result["expandedBytesRead"] = consumed[0]
    result["filesWritten"] = len(result["written"])
    return result


def compare_archive(fixture):
    payload = build_archive(fixture)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        entries = [{"name": info.filename, "kind": "symlink" if stat.S_ISLNK(info.external_attr >> 16) else "regular file",
                    "compressedBytes": info.compress_size, "expandedBytes": info.file_size} for info in archive.infolist()]
    with tempfile.TemporaryDirectory(prefix="archive-lesson-") as temporary:
        outer = Path(temporary).resolve()
        results = {mode: extract_comparison(payload, mode, outer / mode) for mode in ("vulnerable", "fixed")}
    return {"fixture": fixture, "entries": entries, "archiveBytes": len(payload), "budgets": BUDGETS,
            "expectation": FIXTURES[fixture]["expectation"], "results": results}


def unique_object(pairs):
    output = {}
    for key, value in pairs:
        if key in output:
            raise ValueError("Duplicate field")
        output[key] = value
    return output


def archive_compare(request):
    if request.method != "POST":
        response = JsonResponse({"error": "Use POST with a JSON fixture identifier."}, status=405)
        response["Allow"] = "POST"
        return response
    if request.GET or request.content_type != "application/json" or len(request.body) > 2048:
        return JsonResponse({"error": "Use a small JSON body without query parameters."}, status=400)
    try:
        body = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return JsonResponse({"error": "Invalid JSON or duplicate fields."}, status=400)
    if not isinstance(body, dict) or set(body) != {"fixture"} or not isinstance(body["fixture"], str) or body["fixture"] not in FIXTURES:
        return JsonResponse({"error": "Provide exactly one listed fixture identifier; archive uploads are not accepted."}, status=400)
    if not SLOTS.acquire(blocking=False):
        return JsonResponse({"error": "Two archive comparisons are already running. Try again."}, status=429)
    try:
        return JsonResponse(compare_archive(body["fixture"]))
    finally:
        SLOTS.release()
