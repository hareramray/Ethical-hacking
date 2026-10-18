# 07. Programming and automation

[All topic roadmaps](README.md) | [Original master roadmap](../../ETHICAL_HACKING_ROADMAP.md#07-programming-and-automation)

<!-- TOPIC-TOC:START -->

## Contents

- [Common programming foundations](#common-programming-foundations)
- [Languages and development skills](#languages-and-development-skills)
- [Software engineering and secure automation](#software-engineering-and-secure-automation)
- [Safe practice and exit criteria](#safe-practice-and-exit-criteria)
- [Study order and depth](#study-order-and-depth)
- [Stage 1 — Shared programming fundamentals](#stage-1--shared-programming-fundamentals)
- [Stage 2 — Python: core practical track](#stage-2--python-core-practical-track)
  - [Language and data sequence](#language-and-data-sequence)
  - [Tooling and robust automation sequence](#tooling-and-robust-automation-sequence)
- [Stage 3 — Bash: precise local orchestration](#stage-3--bash-precise-local-orchestration)
- [Stage 4 — PowerShell: objects and repeatable administration](#stage-4--powershell-objects-and-repeatable-administration)
- [Stage 5 — JavaScript, HTML, and browser behavior](#stage-5--javascript-html-and-browser-behavior)
- [Stage 6 — SQL and data integrity](#stage-6--sql-and-data-integrity)
- [Stage 7 — C and memory: systems foundation](#stage-7--c-and-memory-systems-foundation)
- [Stage 8 — Secondary languages and deeper study](#stage-8--secondary-languages-and-deeper-study)
- [Engineering capstone and completion rubric](#engineering-capstone-and-completion-rubric)

<!-- TOPIC-TOC:END -->



**Prerequisites:** Section 03 plus basic Linux/Windows command-line skills. **Priority:** Python and shell basics are core; learn other languages to the depth required by your chosen systems.

## Common programming foundations

- [ ] Learn variables, types, control flow, functions, modules, data structures, exceptions, input/output, recursion, and basic algorithmic complexity.
- [ ] Understand bytes versus text, parsing versus validation, serialization formats, regular-expression limits, dates/time zones, and integer/length boundaries.
- [ ] Use a debugger: breakpoints, stepping, call stacks, local variables, and tracebacks. Reproduce a bug with the smallest useful input.
- [ ] Write readable code with explicit configuration, structured logs, useful errors, timeouts, resource limits, and safe cancellation.
- [ ] Understand dependencies, virtual environments, lockfiles, package provenance, version pinning, and updating vulnerable components.

## Languages and development skills

- [ ] **Python — core:** Collections, comprehensions, files, `pathlib`, JSON/CSV, regex, exceptions, logging, argument parsing, virtual environments, HTTP clients, sockets conceptually, and unit tests. Add concurrency only after understanding rate limits and shared state.
- [ ] **Bash — core:** Variables, arrays, conditionals, loops, functions, pipelines, exit-status handling, quoting, temporary files, and safe handling of filenames with spaces. Understand when a Python program is clearer than a shell script.
- [ ] **PowerShell — core:** Objects, cmdlets, functions, modules, parameter validation, errors, CSV/JSON, event queries, and repeatable administration. Understand Windows PowerShell versus modern PowerShell compatibility.
- [ ] **JavaScript/HTML — core for web:** DOM, forms, events, scope, closures, objects/prototypes, promises, async/await, fetch, JSON, browser storage, cookies, and client/server trust boundaries. Read enough CSS to navigate and inspect interfaces.
- [ ] **SQL — core:** Tables, keys, joins, filtering, aggregation, transactions, indexes, permissions, and parameterized queries. Understand relational constraints and why application validation cannot replace database integrity controls.
- [ ] **C — systems foundation:** Compilation/linking, types, pointers, arrays, strings, allocation/freeing, memory ownership, structs, integer conversion, and undefined behavior. Use warnings and sanitizers in your own small programs.
- [ ] **Advanced/specialization:** Assembly and calling conventions for binary analysis; Java/C# for enterprise applications; Go/Rust for relevant tooling; PHP/Ruby or framework-specific languages when the target codebase requires them.

Start with the [official Python tutorial](https://docs.python.org/3/tutorial/) and use [MDN's web-development curriculum](https://developer.mozilla.org/en-US/docs/Learn_web_development) for browser and JavaScript foundations.

## Software engineering and secure automation

- [ ] Use Git commits, branches, diffs, merges, conflict resolution, ignore files, and reviews. Keep credentials, private evidence, and generated secrets out of repositories.
- [ ] Write tests for boundary cases, invalid inputs, authorization decisions, parsing failures, and expected behavior after a fix.
- [ ] Understand HTTP APIs, pagination, authentication, status codes, retry/backoff, idempotency, rate limits, and response validation.
- [ ] Use explicit target allowlists, dry-run modes, bounded concurrency, timeouts, and output directories in assessment helpers; prevent accidental work outside the lab.
- [ ] Avoid constructing shell commands or database queries from untrusted strings; prefer structured APIs and parameterization.
- [ ] Learn code review, basic static analysis, dependency checks, CI concepts, and reproducible installation instructions.

## Safe practice and exit criteria

**Labs:** Write a parser that summarizes synthetic authentication logs; a configuration checker for your own VMs; and a local CRUD application with two user roles and a database. Add negative authorization tests. Repair a parsing bug with a debugger and a regression test. Compile a small C program and use a sanitizer to identify and fix a self-created memory error.

**Exit gate:** Read unfamiliar short code, explain its input-to-output path, change it safely, test failures, and package a documented script someone else can run in a clean environment.

**Common gaps:** Copying code without understanding dependencies; trusting AI-generated scripts; suppressing all exceptions; mixing byte/text encodings; logging secrets; using retries without bounds; considering a working demo production-ready.

## Study order and depth

Begin with common programming concepts, then build useful Python programs. Add Bash and PowerShell around operations you already understand. Study JavaScript/HTML and SQL together by building a local application. Learn C after you can debug a higher-level language. Secondary languages start at reading depth and become practical only when a selected application or specialization requires them. You do not need equal mastery of every language before beginning ethical security work.

For each language, progress from **read and predict**, to **write a small program**, to **debug a failure**, to **package a repeatable project**. Keep source code, synthetic fixtures, tests, and documentation together. A runnable program is the beginning of the exercise; explaining invalid inputs, failures, and access boundaries completes it.

## Stage 1 — Shared programming fundamentals

- [ ] Trace variables and expressions by hand. Distinguish a value, reference, mutable object, copy, and alias. Predict how changing one object can affect another variable that refers to it.
- [ ] Learn booleans, numbers, strings, bytes, lists/arrays, maps, sets, and optional/null values. Test empty, missing, zero, false, and whitespace values separately; languages do not treat these identically.
- [ ] Write conditionals, loops, functions, and modules with explicit inputs and outputs. Separate pure transformations from filesystem, network, database, and clock interactions so behavior is easier to test.
- [ ] Learn scope, lifetime, recursion, iteration, and complexity using small examples. Compare a nested-loop lookup with a dictionary lookup and explain the effect on larger inputs without reducing performance to one slogan.
- [ ] Separate parsing, validation, normalization, authorization, and output encoding. Successfully parsing a JSON object says nothing about whether its fields are allowed or its requested operation is authorized.
- [ ] Learn representation boundaries: bytes/text encoding, byte length versus character count, integer ranges, float rounding, local time versus UTC, and timezone-aware timestamps.
- [ ] Use a debugger to step through a short failing case, inspect locals, read a stack trace, and identify the first incorrect assumption. Avoid replacing every exception with a generic “failed” message.
- [ ] Design meaningful errors with context but without secrets. Choose exit codes and output formats that let another script distinguish success, invalid input, missing dependency, and partial failure.

## Stage 2 — Python: core practical track

### Language and data sequence

- [ ] Start with expressions, control flow, functions, and collections. Practice dictionaries for keyed records, sets for deduplication, and lists for ordered results. Explain when mutation is intentional and when a copied collection is required.
- [ ] Learn comprehensions after ordinary loops. Keep transformations readable; split nested conditions into named functions when that clarifies intent.
- [ ] Work with `pathlib`, context managers, explicit encodings, JSON, and CSV. Handle missing files, directories passed where files are expected, malformed rows, and output paths outside the intended directory.
- [ ] Study iterators and generators to process a large synthetic file in bounded memory. Add a maximum record length and explicit bad-record behavior rather than accepting unlimited input.
- [ ] Introduce classes and data classes when they express a useful data model. Learn composition, attributes, equality, and type annotations without assuming annotations automatically validate runtime input.
- [ ] Use regular expressions for bounded pattern tasks. Prefer format-aware parsers for structured formats; test patterns against long and malformed input before applying them to untrusted data.

### Tooling and robust automation sequence

- [ ] Create an isolated virtual environment, install only required dependencies, and record a reproducible dependency set. Verify the interpreter used by editor, terminal, and test runner is the same intended environment.
- [ ] Build a command-line interface with argument parsing, helpful usage text, validated paths, a dry-run option for changes, and structured logging. Keep data output separate from diagnostics.
- [ ] Use a maintained HTTP client with explicit connection/read or overall timeout behavior. Handle status codes, pagination, bounded retries, cancellation, and malformed responses. Do not retry a non-idempotent write blindly after an ambiguous timeout.
- [ ] Make target scope an explicit allowlist for any lab network helper. Validate redirects and discovered endpoints against that scope before following them. For the first projects, operate entirely on files or loopback services.
- [ ] Use subprocess argument arrays when a subprocess is needed; avoid asking a shell to interpret untrusted text. Define expected exit status, output size, timeout, and working directory.
- [ ] Learn unit tests, temporary directories, fixtures, dependency injection, and mocking only at external boundaries. Add integration tests for the real file/database interactions that unit tests cannot establish.
- [ ] Introduce concurrency last: contrast threads, processes, and async tasks; add bounded work queues, cancellation, and shared-state protection. Measure whether concurrency is useful before increasing it.

**Python lab:** Generate a small authentication-log fixture with valid rows, malformed rows, duplicate events, mixed time offsets, and missing fields. Write a streaming summary tool that produces documented JSON totals and an error count. Debug one wrong count with a breakpoint. Preserve the fixture, expected results, failing test, fix, and final test output. A malformed record should follow the documented policy rather than silently disappear. Reinstall and run the project in a fresh virtual environment to verify the instructions.

## Stage 3 — Bash: precise local orchestration

- [ ] Learn assignments, arrays, positional parameters, functions, conditionals, loops, and arithmetic. Understand that shell variables usually hold strings and that word splitting and filename expansion can change argument boundaries.
- [ ] Practice single/double quoting and array expansion with filenames containing spaces, tabs, glob characters, and leading dashes. Prefer arrays over a space-separated string of command arguments.
- [ ] Learn standard streams, redirection order, pipelines, subshells, exit codes, and background-job waiting. A pipeline's default status comes from its final command; `pipefail` changes that behavior. Read the [Bash pipeline reference](https://www.gnu.org/software/bash/manual/html_node/Pipelines) before relying on it.
- [ ] Study `set -e` and its context-dependent exceptions instead of treating it as complete error handling. Explicitly check operations whose failure changes the correctness or safety of later work.
- [ ] Create temporary resources with appropriate tools, preserve required permissions, and clean them with traps. Keep cleanup narrowly scoped to resources created by that invocation.
- [ ] Learn filename-safe traversal, null-delimited interfaces where supported, and why command output is not always a safe list of filenames. Avoid building an executable command in a string or using `eval` on external data.
- [ ] Distinguish Bash features from POSIX shell syntax. State the required interpreter and external utilities in the script's documentation.

**Bash lab:** Write a script that copies a small allowlisted set of synthetic configuration files into a new backup directory and produces a digest manifest. Test a missing source, unreadable source, existing destination, and filename containing spaces. Require explicit overwrite behavior and a nonzero result on an incomplete backup. Evidence includes the argument list, manifest, error output, and a verified restore. Move complicated parsing into Python when shell quoting overwhelms the task's intent.

## Stage 4 — PowerShell: objects and repeatable administration

- [ ] Learn commands, named parameters, arrays, hashtables, script blocks, functions, modules, and custom objects. Inspect types with `Get-Member` before guessing property names.
- [ ] Filter and select objects before formatting. Compare CSV with JSON for nested data and document property names, date representation, and encoding.
- [ ] Use parameter validation, explicit defaults, and clear function outputs. Avoid emitting incidental strings into a pipeline expected to contain structured records.
- [ ] Distinguish terminating/nonterminating errors, `try`/`catch`/`finally`, error preferences, and native-process exit codes. Verify failure behavior under the exact PowerShell edition you support.
- [ ] Learn `-LiteralPath`, wildcard behavior, quoting, and native argument passing. Use structured cmdlets for filesystem operations rather than constructing another shell's command text.
- [ ] Design state-changing helpers with `SupportsShouldProcess` where appropriate, and test `-WhatIf`. A preview is useful only if the implementation actually honors it for every mutation.
- [ ] Learn idempotency: rerunning an intended-state operation should not create duplicates or progressively weaken configuration. Detect unexpected existing state and report it rather than overwriting indiscriminately.
- [ ] Treat remoting as an identity and authorization boundary. Begin with local inventory; use only the separately authorized lab hosts when progressing to remote administration.

**PowerShell lab:** Export a read-only inventory of selected services and recent synthetic lab events to a typed report. Add bounded date parameters and tests for no results, inaccessible logs, and a missing property. Then write a separate helper that creates only an explicitly named synthetic directory and validates its intended permissions. Test preview, initial creation, second run, and mismatch reporting. Keep these projects separate so an inventory command does not unexpectedly change the machine.

## Stage 5 — JavaScript, HTML, and browser behavior

- [ ] Build semantic HTML with forms, labels, buttons, and accessible status messages. Learn enough CSS to distinguish layout, visibility, and disabled UI state from real server authorization.
- [ ] Study `let`/`const`, primitive values, objects, arrays, functions, scope, closures, prototypes, and modules. Compare equality/coercion behavior and learn how missing values propagate.
- [ ] Handle DOM events and update content through appropriate safe APIs. Explain when inserting text differs from parsing an HTML string.
- [ ] Learn promises, async/await, error propagation, the event loop, and request cancellation. Handle failed requests and stale responses so a slower earlier request does not overwrite a newer result.
- [ ] Use `fetch`, parse JSON, validate the expected response shape, and check HTTP status intentionally. A completed fetch can still represent a server error response.
- [ ] Define origin by scheme, host, and port. Learn same-origin policy, CORS, cookies, browser storage, and credentials behavior as distinct mechanisms. A hidden button and a CORS restriction do not replace server-side authorization.
- [ ] Trace user input through event handler, request, server handler, database, response, and DOM rendering. Use developer-tools breakpoints and network inspection to verify the complete route.
- [ ] Learn client-side storage lifetime and exposure. Use synthetic tokens only in exercises and explain why browser-readable storage, cookies, server sessions, and memory have different properties.

**Browser lab:** Build a local notes interface backed by a local API with two synthetic users. Let each user view and update only their own notes. Verify authorization directly at the API as well as through the UI. Test empty input, long input, delayed responses, malformed JSON, and an unavailable server. Evidence includes the data-flow diagram, browser/API observations, and negative tests. Repair failures at the responsible layer rather than hiding an error message.

## Stage 6 — SQL and data integrity

- [ ] Design tables for users and notes using primary keys, foreign keys, nullability, uniqueness, and check constraints. Explain which invariants belong in the database and which require application-level authorization.
- [ ] Practice `SELECT`, `WHERE`, ordering, pagination, grouping, aggregation, inner joins, and outer joins. Predict row counts and duplicate expansion before executing a join.
- [ ] Learn SQL NULL and three-valued logic. Test missing relationships and use aggregate functions deliberately; counting all rows and counting non-NULL values answer different questions.
- [ ] Use parameterized queries for values. Where identifiers or ordering choices must be dynamic, map to explicit allowed options; ordinary value parameters do not automatically parameterize table or column names.
- [ ] Learn transactions, commit/rollback, isolation concepts, concurrency conflicts, and durable recovery. Make a two-step update fail halfway and verify that rollback preserves the intended invariant.
- [ ] Inspect query plans and add an index for a demonstrated lookup need. Understand the write/storage cost of indexes and the effect of pagination on large tables.
- [ ] Learn schema migrations, backups, restores, and least-privilege database accounts. SQLite is a useful local database but its access model differs from a separate database server.
- [ ] If using SQLite, explicitly verify that foreign-key enforcement is enabled for the connection and test a rejected orphan record; do not assume declaring a constraint proves it is active. See [SQLite's foreign-key documentation](https://www.sqlite.org/foreignkeys.html).

**SQL lab:** Populate a synthetic two-user notes database. Write queries that return only the current user's records, parameterize values, and add constraints. Test duplicate keys, missing parent records, NULL fields, transaction rollback, and unauthorized ownership changes. Preserve a schema diagram, migration, fixture, expected result set, and restore verification. A fast query that returns another user's records still fails the exercise.

## Stage 7 — C and memory: systems foundation

- [ ] Follow preprocessing, compilation, assembly, and linking. Distinguish source, object files, executables, shared libraries, headers, declarations, and definitions.
- [ ] Learn integer types, signedness, conversions, arrays, pointers, pointer arithmetic, structs, and alignment. Trace values and addresses separately in a debugger.
- [ ] Distinguish array capacity, used length, and string terminator. Pass lengths with buffers and check both parsed values and conversion errors before using them as sizes or indexes.
- [ ] Study automatic, static, and dynamically allocated storage. Document who owns an allocation, who may borrow it, when it is freed, and which references become invalid afterward.
- [ ] Handle allocation and I/O failures, partial reads/writes, cleanup paths, and errors without leaking resources. Learn why integer overflow can make a size check meaningless.
- [ ] Distinguish defined behavior, implementation-defined behavior, unspecified behavior, and undefined behavior at reading depth. A successful run does not prove that undefined behavior is absent.
- [ ] Enable appropriate compiler warnings and debug information. Use AddressSanitizer for supported memory errors and an appropriate undefined-behavior sanitizer for additional checks; tooling coverage is partial. Follow the [Clang AddressSanitizer documentation](https://clang.llvm.org/docs/AddressSanitizer.html) for your toolchain's build requirements.

**C lab:** Write a small local line parser with an explicit maximum line length. In a disposable copy, introduce an off-by-one error, build with supported sanitizer instrumentation, and observe the diagnostic on a synthetic boundary input. Identify the source location, repair the length/termination logic, and add normal, empty, maximum-length, oversized, and invalid-numeric tests. Keep compiler flags, diagnostic, corrected ownership diagram, and regression results. The exercise ends at identifying and repairing the defect; weaponizing it adds no value to this foundation task.

## Stage 8 — Secondary languages and deeper study

- [ ] **Assembly:** After C, learn registers, instruction operands, stack frames, calling conventions, branches, and symbol/debug information for one architecture. Compile your own arithmetic and function-call examples and connect source to disassembly. Read one short function before studying binary-security tooling.
- [ ] **Java or C#:** Learn the language's object/type model, exceptions, collections, generics, runtime, packages/assemblies, build system, dependency management, serialization, and application framework. Trace one local HTTP handler from route to database, then inspect its validation and authorization tests.
- [ ] **Go:** Learn packages, slices, maps, interfaces, explicit error handling, contexts, goroutines, channels, and race detection. Build a bounded local worker queue and demonstrate cancellation; avoid assuming concurrency primitives remove shared-state mistakes.
- [ ] **Rust:** Learn ownership, borrowing, lifetimes, enums, pattern matching, `Result`/`Option`, traits, crates, and the boundary around `unsafe`. Rewrite a small parser and compare how resource ownership is expressed. Memory safety does not automatically supply correct authorization or protocol logic.
- [ ] **PHP/Ruby and framework languages:** Start with request lifecycle, routing, templates, session handling, ORM/query interfaces, serialization, package management, and tests. Trace a tiny local CRUD route before reviewing unfamiliar production code.
- [ ] **Framework-specific next step:** Read the exact project's build files and tests, identify supported runtime versions, reproduce a normal request, and map framework conventions to the shared concepts above. Add language depth only when it helps explain actual code.

## Engineering capstone and completion rubric

Create a small repository with a local two-role notes application, parameterized database access, server-side ownership checks, and a separate read-only log-summary CLI. Include installation steps, dependency records, synthetic fixtures, configuration examples, meaningful errors, bounded inputs, and tests for both allowed and denied actions. Add a short Bash or PowerShell wrapper only if it simplifies a real setup task.

Use Git to review changes, make focused commits, resolve one harmless merge conflict, and check ignored/generated files. Inspect the diff for credentials, private evidence, debug bypasses, and accidentally committed environment files. Learn CI by running the same local checks in an isolated build environment, with secrets omitted from tests and output.

Evaluate six criteria: **input/data handling**, **authorization**, **failure behavior**, **debugging explanation**, **meaningful tests**, and **clean installation**. Mark each missing, guided, or independent. Require independent authorization and failure tests, plus successful installation from the written instructions. Tests should prove a requirement or prior defect, not merely repeat implementation statements.

For retention, rewrite one small function from its requirements the next day, debug a shuffled failure several days later, and repeat the clean installation after a longer gap. Alternate reading unfamiliar short code with writing your own. Continue to [secure code review and software delivery](13-secure-code-review-and-software-delivery.md) once you can trace data across application layers and justify a fix with evidence.
