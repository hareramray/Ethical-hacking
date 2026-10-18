# ZIP extraction: bounded file-write traversal

This Vue + Django lesson reads actual ZIP members and writes harmless marker files. It compares an unsafe join-and-write loop with validation of the whole archive before extraction. Every run uses fresh temporary directories, and all generated files are removed before the response returns.

Start the [browser security lab](README.md) from the repository root:

```powershell
python labs/browser_security/run_lab.py
```

Open **http://127.0.0.1:8766/**, select **Archive extraction**, choose a fixture, and click **Compare extraction**. Read the member names, the successful-write count, and the final file snapshot. Paths shown in the UI are relative to that handler's disposable workspace.

| Fixture | Join and write | Whole-archive validation |
| --- | --- | --- |
| Normal nested text file | Writes `extract/docs/hello.txt` | Writes the same marker |
| `../outside.txt` | Writes a sibling of `extract` | Rejects the parent component |
| `..\outside.txt` | Explicit normalization makes the same sibling write on every platform | Rejects the normalized parent component |
| Absolute or drive-qualified name | Outer lab boundary rejects it | Rejects it |
| Normal member followed by traversal | Writes both members | Rejects the whole archive with zero writes |
| Four tiny members | Writes all four | Rejects the three-entry limit |
| Two 112-byte members | Writes 224 expanded bytes | Rejects the 192-byte total |
| One 160-byte member | Writes it | Rejects the 128-byte per-file limit |
| One stored 110-byte member | Writes it | Rejects the 96-byte compressed-entry limit |
| Duplicate name | Second marker overwrites the first | Rejects duplicate destinations before writing |
| File named `docs`, then `docs/hello.txt` | First file remains when the next write fails | Rejects the file/directory collision before writing |
| Symlink member metadata | Ignores the type and writes ordinary text | Rejects non-regular members |

The symlink fixture never creates a link. Its content is just `../outside.txt`. Likewise, budget fixtures contain at most a few hundred expanded bytes; they demonstrate enforcement without creating an archive bomb.

## Follow the write boundary

Each handler gets this initial layout:

```text
disposable-workspace/
  extract/                 intended destination, initially empty
```

The vulnerable implementation in [archive_lab.py](backend/securitylab/archive_lab.py) replaces backslashes with forward slashes, joins the name to `extract`, resolves it, and writes each member sequentially. The traversal fixture resolves to `disposable-workspace/outside.txt`. A separate outer guard refuses anything outside `disposable-workspace`; absolute and drive-qualified names are refused before any destination is opened.

That outer guard contains this exercise. It does not repair the intended extraction boundary: the sibling write still demonstrates a file landing outside `extract`. The server accepts only identifiers for predefined archives, never uploaded bytes or arbitrary member names.

This is an explicitly unsafe application loop, not a claim that Python's `ZipFile.extract()` always permits traversal. Python documents normalization of absolute prefixes and parent components in that method, and separately warns about extracting untrusted archives. This lesson calls `ZipFile.open()` and performs its own writes to make the application boundary visible. See the [Python 3.13 ZIP extraction documentation](https://docs.python.org/3.13/library/zipfile.html#zipfile.ZipFile.extract).

## What the fixed handler checks

The fixed branch validates all members before writing any file:

1. Check archive size, entry count, declared per-entry sizes, and declared compressed/expanded totals.
2. Normalize backslashes explicitly. Require short ASCII path components; reject parent/empty components, drive and absolute paths, reserved Windows names, colons, and trailing dots. This deliberately strict lesson policy is narrower than all valid ZIP filenames.
3. Permit regular files with implicit parent directories only. Reject explicit directory entries, symlinks, special file metadata, encryption, and compression methods other than stored/deflated.
4. Resolve each destination and require it to remain under `extract`. Reject duplicate destinations, case-insensitive aliases, and file/directory prefix collisions.
5. Read every member in small chunks into a bounded staging buffer. Count actual expanded bytes, enforce per-entry and total limits while reading, and check the final size against the declared size. Reading to EOF also lets `zipfile` check the ZIP member's integrity.
6. Only after all checks and reads succeed, create parent folders and open destinations exclusively for writing.

| Fixed budget | Limit |
| --- | ---: |
| Archive bytes | 4,096 |
| Entries | 3 |
| Compressed bytes per entry | 96 |
| Total compressed bytes | 160 |
| Expanded bytes per entry | 128 |
| Total expanded bytes | 192 |

The vulnerable branch also has a separate outer envelope: 8 entries, 512 compressed/expanded bytes per entry, 2,048 total compressed/expanded bytes, and an 8,192-byte archive. A process-local semaphore allows at most two comparisons at once. These bounds protect the demonstration; the smaller fixed limits are the policy being compared. [OWASP's file-upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html#upload-and-download-limits) recommends limits that account for extracted/decompressed size when processing archives.

Every workspace is newly created and used only by this comparison. No symlinks are created, permissions are not restored from the ZIP, and files are never served or executed. The code does **not** claim that `resolve()` followed by `open()` prevents symlink replacement races in a directory writable by another actor. Production extraction needs an appropriate filesystem isolation and concurrency design. Staging prevents writes when preflight or member reading fails; it is not a transactional guarantee against a disk error during the later write phase. Temporary-directory cleanup still removes partial files before returning.

## API and evidence

The Vue component sends a CSRF-protected `POST /api/archive/compare/` with exactly `{"fixture":"mixed"}`. The other accepted identifiers are `normal`, `traversal`, `backslash`, `absolute`, `drive`, `count`, `expanded`, `entry`, `compressed`, `duplicate`, `collision`, and `symlink`.

HTTP 200 means the comparison ran; each handler reports `extracted`, `blocked`, or `error`. The response includes ZIP entry sizes, fixed budgets, and both handlers' snapshots:

- `before`: an empty file list from the fresh workspace.
- `written`: each successful write, including content and whether it is outside the intended extraction directory.
- `after`: files actually present after extraction, read back from disk before cleanup.
- `filesWritten`, `expandedBytesRead`, `outsideExtraction`, and `reason`: concise evidence of the operation.

Duplicate names demonstrate why successful-write counts can exceed final file counts. The collision fixture demonstrates why an error alone does not prove that no files were written.

Extra or duplicate JSON fields, arbitrary input, unknown fixture identifiers, query parameters, invalid JSON, and bodies over 2,048 bytes return HTTP 400. Missing CSRF validation returns 403, unsupported methods return 405, and a busy comparison limit returns 429. Displayed content uses Vue text interpolation and never becomes dashboard HTML.

## Verification

The [15 backend tests](backend/securitylab/test_archive_lab.py) check real nested/sibling writes, the outer boundary, no fixed partial extraction for invalid mixed archives, duplicate/collision behavior, link metadata, declared and actual byte budgets, case-insensitive aliases, stream closing, workspace cleanup on success and failures, strict API input, CSRF, and concurrency limits. The [browser tests](frontend/tests/archive.spec.js) cover the positive control, both separator styles, mixed archives, budgets, duplicate writes, collisions, link metadata, and absolute-path rejection.

Run focused backend checks from `labs/browser_security`:

```powershell
.venv/Scripts/python.exe backend/manage.py test securitylab.test_archive_lab
```

For the complete browser suite, stop both running lab servers first and run from the repository root:

```powershell
$env:LAB_BROWSER_CHANNEL = 'chrome'
python labs/browser_security/run_lab.py --test
Remove-Item Env:LAB_BROWSER_CHANNEL
```

Compare this write-oriented lesson with [path traversal reads](PATH_TRAVERSAL.md) and the upload controls in the [main lab](README.md). Repeat the normal fixture after the blocked cases to demonstrate that legitimate nested files still work.
