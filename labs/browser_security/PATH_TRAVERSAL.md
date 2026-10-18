# Reading files through path traversal: Vue + Django lab

This lesson demonstrates a server returning a file outside its intended download directory, followed by a repair that preserves legitimate downloads. It uses real file reads from four disposable marker files. The exercise's outer boundary prevents reading workspace files, application data, or operating-system files.

Path traversal happens when a caller-controlled filename escapes an intended directory. Its real-world reach depends on the server process's filesystem permissions. Reading a file is distinct from executing it or interpreting it as a template. See [OWASP's path traversal overview](https://owasp.org/www-community/attacks/Path_Traversal).

## Start and compare

From the repository root, run setup once, then start the application:

```powershell
python labs/browser_security/run_lab.py --setup
python labs/browser_security/run_lab.py
```

If the lab is already installed, rebuild Vue after this update with `python labs/browser_security/run_lab.py --build`, stop the old server, and restart it. Open **http://127.0.0.1:8766/** and select **Path traversal**. Full prerequisites and test commands are in the [lab guide](README.md).

Each handler request creates this fresh directory and removes it when the request finishes:

```text
disposable-lab/
  public/                      intended download root
    readme.txt                 PUBLIC_README_OK
    nested/notes.txt           NESTED_NOTES_OK
  private/sentinel.txt         PRIVATE_SENTINEL_ONLY_FOR_LAB
  public-notes/sibling.txt     SIBLING_PREFIX_SENTINEL
```

1. Choose **Public readme** and press **Compare handlers**. Both results should be HTTP 200 with `PUBLIC_README_OK`.
2. Choose **Parent directory traversal**. The path is `../private/sentinel.txt`. Predict the result before comparing.
3. The vulnerable handler returns HTTP 200 and `PRIVATE_SENTINEL_ONLY_FOR_LAB`. The resolved path is `private/sentinel.txt`, outside `public/`.
4. The fixed handler returns HTTP 403 with no file content. It rejects the resolved location outside its intended directory.
5. Choose **Nested public file**. Both handlers should still read `NESTED_NOTES_OK`. A fix that disables every download has not preserved the feature.

The result cards show the received input, separator normalization, resolved path relative to the disposable lab, HTTP status, decision, and returned content. Vue renders these values as text. No browser script execution or CSP setting is needed for this server-side lesson.

## Small comparison matrix

| Input in the form | Vulnerable handler | Fixed handler | Lesson |
| --- | --- | --- | --- |
| `readme.txt` | 200, public marker | 200, public marker | Ordinary download remains usable |
| `nested/notes.txt` | 200, nested marker | 200, nested marker | Legitimate subdirectories work |
| `nested/../readme.txt` | 200, public marker | 200, public marker | The resolved destination determines containment |
| `../private/sentinel.txt` | 200, private sentinel | 403, no content | Missing intended-directory boundary |
| `..\private\sentinel.txt` | 200, private sentinel | 403, no content | This lab explicitly maps backslashes to separators on every OS |
| `../public-notes/sibling.txt` | 200, sibling sentinel | 403, no content | `public-notes` is not inside `public` despite a shared string prefix |
| `missing.txt` | 404, no content | 404, no content | Missing data is not a successful boundary test |
| `../../outside-sentinel.txt` | 403, no content | 403, no content | The separate outer lab boundary stops both handlers |
| An absolute, drive, UNC, or stream path | 400, no content | 400, no content | These forms are outside this exercise's supported inputs |

Paths are limited to 256 characters. Empty paths, control characters, duplicate parameters, and unknown parameters are rejected. The endpoint defaults to the fixed handler and `readme.txt` if those parameters are omitted.

## Observe URL decoding separately

The HTTP endpoint is `GET /api/traversal/?mode=fixed&path=readme.txt`. The Vue form sends its input with `URLSearchParams`; Django decodes the query string once. The application does not call an additional URL decoder.

These PowerShell requests address only the running local lab. `-i` displays the HTTP status and headers, including expected 403/404 outcomes:

```powershell
curl.exe -i 'http://127.0.0.1:8766/api/traversal/?mode=vulnerable&path=%2e%2e%2fprivate%2fsentinel.txt'
curl.exe -i 'http://127.0.0.1:8766/api/traversal/?mode=fixed&path=%2e%2e%2fprivate%2fsentinel.txt'
curl.exe -i 'http://127.0.0.1:8766/api/traversal/?mode=vulnerable&path=%252e%252e%252fprivate%252fsentinel.txt'
```

The first two requests become `../private/sentinel.txt`: expect 200 with the marker, then 403 without content. The third becomes the literal text `%2e%2e%2fprivate%2fsentinel.txt` after one decode and returns 404. Typing that already percent-encoded text into the Vue form also sends literal percent signs after the normal transport round trip; it is not the same as supplying the first raw HTTP query above.

## Inspect the repair

Read [the Django handler](backend/securitylab/traversal.py). Both modes resolve the requested location, but only fixed mode enforces the intended `public/` directory before reading. This is the essential check, shown separately from input handling and the outer lab boundary:

```python
public_root = public_root.resolve()
candidate = (public_root / normalized_input).resolve()
if not candidate.is_relative_to(public_root):
    # Return 403 without opening the file.
    raise PermissionError("Outside intended download directory")
```

`resolve()` handles parent components and symbolic links; `is_relative_to()` alone is a lexical path relationship check. Perform the containment check on resolved paths. A string-prefix check can confuse a sibling directory such as `public-notes` with the intended root. See the Python documentation for [resolution](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve) and [path relationships](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.is_relative_to).

The complete lab also checks its outer disposable root and permits only its four known fixtures. Those limits constrain the demonstration; they do not repair the vulnerable handler's missing `public/` check. Returned paths are relative labels, not machine-specific absolute paths.

In a production download feature, prefer authorized record IDs mapped to server-controlled storage names, enforce ownership separately, and limit filesystem permissions. Resolved-path validation followed by a later open is not atomic against concurrent link replacement. Storage writable by an adversary needs platform-specific safe file-opening and link policies. This lab uses freshly created fixtures that the browser cannot modify; it does not exercise symlink races, archive extraction, remote inclusion, or unrestricted host-file access.

## Retest and record evidence

Run the full Django and browser checks from the repository root after stopping the lab on ports 8766 and 8767:

```powershell
$env:LAB_BROWSER_CHANNEL = 'chrome'
python labs/browser_security/run_lab.py --test
Remove-Item Env:LAB_BROWSER_CHANNEL
```

If Chrome is unavailable, follow the [Chromium installation instructions](README.md#check-the-implementation). Backend cases are in [test_traversal.py](backend/securitylab/test_traversal.py); UI cases are in [traversal.spec.js](frontend/tests/traversal.spec.js).

Record the requested path, resolved relative path, each handler's status and content, the missing check, and the successful normal download after the fix. No cleanup button is needed: traversal fixtures are removed after every request and do not use the upload collection or stored-XSS records.
