# 07. Build small programs whose failures are understandable

[Index](README.md) | [Complete source curriculum](curriculum/07-programming-and-automation.md) | [Original roadmap](../roadmaps/07-programming-and-automation.md)

## Prerequisites and study order

Use computing foundations, basic Linux/Windows commands, a new local project directory, and an installed Python 3 interpreter. Start with language-independent reasoning, then Python, Bash/PowerShell, browser JavaScript and SQL, then C. Secondary languages initially require reading depth. All fixtures below are synthetic and local. Record runtime versions; follow each installed tool's help for setup instead of copying package commands for another platform.

Your end product is a tested log-summary CLI and a two-role local notes application, with clear inputs, authorization rules, limits, errors, and installation instructions. A successful happy-path demonstration is only one case.

## 1. Trace input through distinct decisions

Variables name values or references. Lists preserve order, maps/dictionaries associate keys with values, sets deduplicate, and optional/null values express absence. Mutable objects can have aliases: if `b = a` refers to a list, changing it through `b` also affects `a`; a separate copy changes that relationship. Test missing, empty, whitespace, zero, and false separately instead of assuming they mean the same thing.

Use conditionals for decisions, loops for repeated work, functions for named input/output transformations, and modules for reusable boundaries. Keep pure transformations separate from filesystem/network/database/clock operations. Scope determines which bindings are visible; lifetime determines how long state exists. Recursion solves a problem through smaller instances but needs a termination condition and bounded depth. A nested search can scale roughly quadratically, while constructing and querying a dictionary can improve many repeated lookups at a memory cost. Measure the real workload.

The input path has several different checks:

```text
bytes → decode text → parse structure → validate fields → normalize policy
      → authenticate actor → authorize operation → mutate state → encode output
```

Valid JSON may contain the wrong fields. A valid integer may exceed a resource limit. A valid login may not own the record. Output safe as text may be unsafe when parsed as HTML. These distinctions determine where the fix belongs.

Use timezone-aware timestamps and explicit encodings. Character count differs from byte length; float rounding affects equality; fixed-width integers can overflow; regular expressions suit bounded patterns but are not a universal parser. Preserve meaningful errors and exit codes without logging passwords, tokens, or entire sensitive records.

## 2. Write a bounded Python log summarizer

Create `events.jsonl` with one JSON object per line:

```json
{"id":"e1","time":"2026-01-01T10:00:00+00:00","user":"alice","outcome":"ok"}
{"id":"e2","time":"2026-01-01T15:30:00+05:30","user":"bob","outcome":"denied"}
{"id":"e1","time":"2026-01-01T10:00:00+00:00","user":"alice","outcome":"ok"}
not-json
{"id":"e3","time":"2026-01-01T10:01:00+00:00","user":"alice"}
```

Save this as `summarize.py`:

```python
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

def summarize(path: Path) -> dict:
    totals = Counter()
    seen = set()
    bad = duplicates = 0
    with path.open("rb") as stream:
        for number in range(1, 10001):
            raw = stream.readline(4098)
            if not raw:
                break
            if len(raw) > 4096:
                raise ValueError(f"record {number} exceeds 4096 bytes")
            try:
                row = json.loads(raw.decode("utf-8"))
                if not isinstance(row, dict):
                    raise ValueError("object required")
                if not all(isinstance(row.get(k), str) and row[k]
                           for k in ("id", "time", "user", "outcome")):
                    raise ValueError("nonempty string fields required")
                if row["outcome"] not in {"ok", "denied"}:
                    raise ValueError("unknown outcome")
                timestamp = datetime.fromisoformat(row["time"])
                if timestamp.tzinfo is None:
                    raise ValueError("timezone required")
                timestamp = timestamp.astimezone(timezone.utc)
            except (ValueError, UnicodeError):
                bad += 1
                continue
            if row["id"] in seen:
                duplicates += 1
                continue
            seen.add(row["id"])
            totals[row["outcome"]] += 1
        else:
            if stream.read(1):
                raise ValueError("input exceeds 10000 records")
    return {"totals": dict(totals), "bad": bad, "duplicates": duplicates}

def main():
    parser = argparse.ArgumentParser(description="Summarize synthetic auth events")
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        result = summarize(args.input)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"summary failed: {exc}\n")
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
```

Run `python summarize.py events.jsonl` using your environment's Python command. Expected output is `{"bad": 2, "duplicates": 1, "totals": {"denied": 1, "ok": 1}}`. The first two timestamps denote the same instant despite different offsets. Deduplication uses event IDs, not user names. The maximum record/input counts bound memory used by the set; limits are example policy choices, not universal logging limits.

Context managers close files. `pathlib` models paths. Iteration processes records sequentially, while JSON provides format-aware parsing. The exception policy counts malformed records but aborts on oversized input or file failure, so partial output cannot silently appear complete. CSV uses its own parser and newline handling; do not split quoted CSV on commas. Comprehensions are concise transformations when readable; classes/data classes help model stable structures, but annotations do not validate runtime data automatically.

Introduce a bug by counting before checking `seen`. Run `python -m pdb summarize.py events.jsonl`, set a breakpoint near the duplicate check, step through, and inspect `row`, `seen`, and `totals`. The call stack/traceback locates execution; local variables expose the false assumption. Repair the order and keep a regression test asserting the documented totals. Add empty input, malformed UTF-8, timezone-less timestamp, unknown outcome, too-long record, missing file, directory-as-input, and exactly-at-limit cases. Use temporary directories and synthetic fixtures; mock only external boundaries, then integration-test real file parsing.

## 3. Package automation deliberately

Use a virtual environment for Python project dependencies, verify the interpreter selected by editor/terminal/tests, and record reproducible versions/lockfiles and provenance. Minimal standard-library projects still need supported runtime instructions. Maintain dependencies instead of treating a pinned vulnerable version as permanently acceptable.

A useful CLI has help, explicit configuration, validated paths, structured data output, separate diagnostics, cancellation, and bounded resources. State-changing commands need a real dry-run path and explicit overwrite policy. A network helper needs an allowlist for initial hosts and every redirect/discovered endpoint, timeouts, response validation, capped pagination, and bounded retry/backoff. Do not retry an ambiguous non-idempotent write as though nothing happened. An idempotency key only helps when the server honors its documented semantics.

Prefer `subprocess.run([program, arg1, arg2], check=True, timeout=5, cwd=...)` over shell command strings. Bound captured output when designing real helpers. Start with loopback only. Threads, processes, and async tasks have different concurrency models; all still need bounded queues, shared-state protection, cancellation, and evidence that concurrency helps.

## 4. Use Bash for simple orchestration

Bash variables usually hold strings; arrays preserve argument groups. Functions, loops, conditionals, positional arguments, arithmetic, redirections, subshells, and job waiting compose commands. State that Bash is required when using Bash-specific syntax. Never use `eval` to turn a filename or log record into code.

This Linux example copies an explicit synthetic file list into a newly created destination and records digests. Run from your practice directory after creating `one.txt` and `two words.txt`:

```bash
#!/usr/bin/env bash
set -u
sources=("one.txt" "two words.txt")
destination="backup-demo"
if [[ -e "$destination" ]]; then
    printf '%s\n' 'destination already exists' >&2
    exit 2
fi
mkdir -- "$destination" || exit 2
for source in "${sources[@]}"; do
    if [[ ! -f "$source" ]] || ! cp -- "$source" "$destination/$source"; then
        printf 'incomplete backup: %s\n' "$source" >&2
        exit 1
    fi
done
(cd -- "$destination" && sha256sum -- "${sources[@]}" > manifest.sha256) || exit 1
```

Verify from the destination with `sha256sum -c manifest.sha256`, then restore to a fresh folder and compare. A failure leaves an explicitly incomplete directory for inspection rather than deleting unknown paths. Test missing/unreadable sources, existing destination, and spaces. For temporary resources use a suitable `mktemp` pattern and a narrowly scoped `trap` cleanup after verifying the exact created path. Null-delimited interfaces support arbitrary filenames; line-based command output does not. Pipeline status defaults to the final command unless `pipefail` is enabled; `set -e` is not a substitute for explicit important checks.

## 5. Use PowerShell objects for administration

Cmdlets, modules, custom objects, arrays, hashtables, and script blocks support structured work. Use `Get-Member`, filter/select before formatting, and export intentional CSV/JSON properties. Keep incidental messages out of an object pipeline; use diagnostics appropriately. `-LiteralPath` avoids wildcard interpretation, and native command argument behavior varies with shell edition.

```powershell
function New-LabNoteFolder {
    [CmdletBinding(SupportsShouldProcess)]
    param([Parameter(Mandatory)][ValidateNotNullOrEmpty()][string]$LiteralPath)
    if (Test-Path -LiteralPath $LiteralPath) {
        $existing = Get-Item -LiteralPath $LiteralPath -ErrorAction Stop
        if (-not $existing.PSIsContainer) { throw 'Existing path is not a directory' }
        return $existing
    }
    if ($PSCmdlet.ShouldProcess($LiteralPath, 'Create synthetic note directory')) {
        New-Item -ItemType Directory -Path $LiteralPath -ErrorAction Stop
    }
}
New-LabNoteFolder -LiteralPath (Join-Path $PWD 'ps-demo-notes') -WhatIf
```

`-WhatIf` should show a proposed creation without creating the folder. Test the real call, second run, and file-at-destination mismatch. This simple helper does not enforce an ACL policy; add an explicit intended-ACL check before using it for a security-sensitive directory. Idempotency means repetition preserves the intended state, not blindly accepting unexpected state. Use `try/catch/finally`, terminating error controls, and native exit codes deliberately. Keep a read-only service/event inventory separate from mutation helpers. Remoting requires explicit target and identity boundaries.

## 6. Trace browser behavior and server authority

HTML defines semantic forms, labels, buttons, and accessible status regions; CSS controls appearance. Hiding a button or disabling a field is not server authorization. JavaScript has primitive/object values, arrays, lexical scope, closures, prototypes, modules, and equality/coercion rules. A closure retains access to its lexical environment; a prototype supplies inherited object behavior. Predict missing/null values before manipulating responses.

For a local notes API, a typical browser handler is:

```javascript
async function showNote(id, signal) {
  const response = await fetch(`/api/notes/${encodeURIComponent(id)}`, { signal });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const note = await response.json();
  if (typeof note.body !== 'string') throw new Error('Unexpected response shape');
  document.querySelector('#note').textContent = note.body;
}
```

`fetch` can complete with an HTTP error, so check status. Promises/async-await sequence asynchronous work; event-loop scheduling and delayed responses can leave stale UI state. Use cancellation through `AbortController` and ensure an older response cannot overwrite a newer selection. `textContent` inserts text; `innerHTML` parses markup and requires different trust handling.

An origin is scheme, host, and port. Same-origin policy, CORS, cookies, browser storage, server sessions, and authorization are distinct mechanisms. Browser-readable storage and memory expose different lifetimes; cookies have transmission attributes and can refer to server-side session state. Use only synthetic credentials and trace event → request → server identity → database → response → DOM. Test the API directly, because UI restrictions and CORS do not replace server ownership checks.

## 7. Make database invariants explicit

This complete Python/SQLite example creates two users and notes, enables foreign keys, and authorizes a read through actor plus ownership:

```python
import sqlite3
db = sqlite3.connect(":memory:")
db.execute("PRAGMA foreign_keys = ON")
assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
db.executescript("""
CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE notes(id INTEGER PRIMARY KEY, owner INTEGER NOT NULL REFERENCES users(id),
                   body TEXT NOT NULL CHECK(length(body) BETWEEN 1 AND 1000));
INSERT INTO users VALUES(1,'alice'),(2,'bob');
INSERT INTO notes VALUES(10,1,'Alice note'),(20,2,'Bob note');
""")
def read_note(actor, note_id):
    return db.execute("SELECT body FROM notes WHERE id=? AND owner=?",
                      (note_id, actor)).fetchone()
assert read_note(1, 10) == ("Alice note",)
assert read_note(1, 20) is None
try:
    with db:
        db.execute("INSERT INTO notes VALUES(30,999,'orphan')")
except sqlite3.IntegrityError:
    print("orphan rejected")
db.close()
```

Expected output is `orphan rejected`; assertions test permitted and denied access. The actor value must come from trusted server authentication in a real app, not a client-supplied “user” field. Value placeholders protect query construction, while the ownership predicate enforces the application's rule. SQLite foreign-key enforcement must be enabled and verified per connection. [Python SQLite reference](https://docs.python.org/3/library/sqlite3.html), [SQLite foreign-key documentation](https://www.sqlite.org/foreignkeys.html)

Primary/foreign keys, uniqueness, nullability, and checks enforce data integrity. NULL uses three-valued logic: `IS NULL` differs from `= NULL`; `COUNT(*)` counts rows while `COUNT(column)` omits NULL values. Inner joins keep matching relationships; outer joins retain designated unmatched rows. Predict duplicate expansion before joining one-to-many tables. Filtering, ordering, aggregation, grouping, and pagination should preserve the intended actor scope.

Transactions group operations into commit/rollback boundaries. Make a second operation fail and verify the first is rolled back. Isolation and concurrent updates require additional reasoning. Indexes speed selected lookups but cost writes/storage; inspect a query plan before adding one. Dynamic column/order identifiers need an allowlist, not ordinary value placeholders. Version schema migrations, back up and restore, and use least-privilege database identities. SQLite file access differs from a separate server's account model.

## 8. Learn C memory through repair

Preprocessing expands source directives, compilation translates, assembly produces object code, and linking combines definitions/libraries. Headers declare interfaces; object files, executables, and shared libraries serve different roles. Types, signedness, conversion, arrays, pointers, structs, and alignment affect representation. An address and the value stored there are different facts.

```c
#include <stdio.h>
#include <string.h>
int main(void) {
    const char input[] = "demo";
    char output[5];
    size_t length = strlen(input);
    if (length >= sizeof output) return 1;
    memcpy(output, input, length + 1);
    puts(output);
    return 0;
}
```

The fifth byte stores the string terminator. Build your own local program with supported warnings, debug information, and sanitizers, for example `clang -Wall -Wextra -g -fsanitize=address,undefined demo.c -o demo`. In a disposable copy, change the bound check incorrectly and shrink the destination to observe a sanitizer report; restore the correct size/check and retest. AddressSanitizer detects selected memory errors in instrumented builds, not every logic defect. [Clang AddressSanitizer documentation](https://clang.llvm.org/docs/AddressSanitizer.html)

Track automatic, static, and dynamic storage; for each allocation identify owner, borrowers, and free point. After free, former pointers are invalid. Check allocation/I/O failures, partial reads/writes, lengths, terminators, and numeric conversion errors. Integer overflow can invalidate size checks. Defined, implementation-defined, unspecified, and undefined behavior are distinct; one successful run does not prove portability. A full line-parser exercise adds empty, maximum-length, oversized, and invalid-numeric cases and ends with repair, not exploit construction.

## 9. Map secondary languages and engineering practice

| Track | Transfer the shared concepts through this exercise |
| --- | --- |
| Assembly | Compile your own function; map registers, operands, branches, stack frame, calling convention, and symbols to source |
| Java / C# | Trace route to database through objects, generics, exceptions, collections, runtime, packages/assemblies, build, serialization, and tests |
| Go | Build a bounded worker queue using slices/maps/interfaces, explicit errors, contexts, goroutines/channels; test cancellation and races |
| Rust | Rewrite the parser with ownership/borrowing/lifetimes, enums/matching, Result/Option, traits/crates; identify any unsafe boundary |
| PHP / Ruby / frameworks | Trace routing, templates, sessions, ORM/query construction, serialization, package management, and tests |

Memory safety does not supply correct authorization. Concurrency primitives do not remove shared-state errors. Read the actual project's build files, runtime requirements, normal request tests, and framework conventions before reviewing unfamiliar code.

Use Git commits, branches, diffs, reviews, merges, and a harmless conflict-resolution exercise. Ignore environments/generated files; inspect history/diffs for secrets rather than assuming an ignore rule removes tracked material. Static analysis, dependency checks, and CI complement tests; CI should repeat meaningful local checks in an isolated build. Test boundary inputs, parsing errors, ownership decisions, and known regressions rather than mirroring implementation lines.

Your capstone combines the local two-role notes application, parameterized queries, server-side ownership checks for read/list/update/delete/export, log CLI, synthetic fixtures, configuration example, meaningful errors, dependencies, and clean-install instructions. Test delayed/failed browser requests, invalid input, rollback, missing permissions, and denied cross-user operations. Repair one debugger-observed defect and prove the fix. Pass when another learner can install it cleanly and you can explain both successful and rejected input paths without a copied walkthrough.
