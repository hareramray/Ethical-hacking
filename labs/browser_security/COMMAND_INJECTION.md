# Command and argument injection: literal names versus syntax

Open `http://127.0.0.1:8766/` and select **Commands & arguments**. The shared [setup instructions](README.md) start Vue and Django. This lesson uses Python's standard library and your operating system's shell; no extra package is needed.

The intended feature accepts a name and prints it. Compare two ways that a name can acquire unintended meaning: shell separators can start a second command, and program options can change a child program's behavior even when no shell is involved. All examples use synthetic names and marker output.

## Try the comparisons

Select a fixture and click **Compare processes**. Each result shows the actual invocation argument list, child exit code, standard output, and whether the marker action ran.

| Fixture | Vulnerable process | Fixed process |
| --- | --- | --- |
| Ordinary name: `Alice` | Shell prints Alice | Recorder receives one name, Alice |
| Shell separator | Shell prints Alice and a separate `COMMAND_SEPARATOR_MARKER` line | Complete string remains one name; no second command |
| Split option: `Alice --flag` | Whitespace splitting creates two arguments; recorder enables its harmless flag | One literal name, `Alice --flag`; flag remains off |
| Leading option: `--flag` | Recorder treats the name as its flag | `--` ends option parsing; recorder receives the name `--flag` |

The separator fixture is selected for the server's operating system. Windows uses the complete predeclared string `echo Alice & echo COMMAND_SEPARATOR_MARKER`. POSIX uses the complete predeclared string `printf '%s\n' Alice; printf '%s\n' COMMAND_SEPARATOR_MARKER`. These builtins only print the marker; they do not invoke additional executables.

The fixed recorder prints a JSON object containing its received arguments, parsed names, flag state, and marker. Marker text inside a literal name is expected in the fixed separator case. It is evidence that the text survived as data, not evidence of a second command. The effect result checks a separate marker line for the shell and the actual parsed flag for the recorder.

Try the ordinary name again after an injected fixture. Both comparisons should complete, and the previous marker action should disappear.

## What changes in the implementation

The vulnerable shell demonstration explicitly launches `cmd.exe` or `/bin/sh` with a complete constant script. Its dangerous design pattern is placing a name in shell syntax without preserving the data boundary. The endpoint cannot construct a new script: it accepts only an enumerated fixture ID.

The fixed comparison launches an absolute Python executable with an argument list, `shell=False`, and the fixed recorder script. It passes the name as a single argument after `--`. The argument-injection comparison also uses `shell=False` on its vulnerable side, so it demonstrates why avoiding the shell does not by itself validate a target program's options. [Python subprocess security considerations](https://docs.python.org/3/library/subprocess.html#security-considerations)

The recorder's `argparse` configuration recognizes `--flag`. Its `--` delimiter ends option processing, preserving an option-like name as positional data. This convention depends on the actual program: confirm the chosen tool's argument grammar rather than assuming every executable supports it. [Python argparse documentation](https://docs.python.org/3/library/argparse.html#arguments-containing)

On Windows the shell path comes from the operating system's system-directory API, rather than `PATH` or `COMSPEC`. `/d` disables AutoRun commands, and `/v:off` disables delayed expansion. The shell sees only predeclared ASCII strings. [Microsoft cmd documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cmd)

## Fixture boundary and limits

`POST /api/command/compare/` accepts exactly a JSON object with one `fixture` field. Supported IDs are `normal`, `separator`, `argument`, and `leading-option`. Duplicate keys, extra fields, query parameters, unknown fixtures, and bodies over 1,024 bytes are rejected before process creation. Django's normal CSRF middleware remains enabled.

Every child uses an absolute trusted executable, a new disposable working directory, an empty environment, and closed standard input. The recorder runs with Python's `-I -S` options and performs no file, network, or further process operations. On Windows the base Python executable avoids the virtual-environment launcher shim. The shell demonstrations use builtins without child processes. Each direct child has a three-second deadline; Python's process runner kills and waits for it if the deadline expires. At most two comparisons run concurrently, and each runs its two children sequentially. Working directories are removed on success, error, or timeout.

Known fixture strings and the fixed recorder keep output finite; returned stdout and stderr are additionally capped at 2,048 bytes each. A failed or timed-out process reports an unknown effect, rather than claiming that protection succeeded. These restrictions contain the intentionally vulnerable example. They are not a sandbox for running arbitrary commands, and extending the endpoint to accept command text would remove its central boundary.

## Inspect and verify

- [command_lab.py](backend/securitylab/command_lab.py): strict fixture selector, complete shell scripts, child execution, deadlines, and cleanup.
- [command_fixture.py](backend/securitylab/command_fixture.py): the fixed JSON-only argument recorder.
- [CommandLab.vue](frontend/src/CommandLab.vue): fixture selection and text-only result rendering.
- [test_command_lab.py](backend/securitylab/test_command_lab.py): real process behavior, both option cases, HTTP and CSRF boundaries, concurrency, invocation contract, real timeout/reaping, and disposable-directory cleanup.
- [command.spec.js](frontend/tests/command.spec.js): browser comparisons and removal of old marker evidence.

From `labs/browser_security`, run the backend checks:

```powershell
.\.venv\Scripts\python.exe backend/manage.py test securitylab.test_command_lab
```

Build the frontend and stop any running lab before browser checks, because Playwright starts its own two-port server pair. From `labs/browser_security/frontend`:

```powershell
$env:LAB_BROWSER_CHANNEL = 'chrome'
npx playwright test tests/command.spec.js
```

For application code, prefer a library operation where it meets the need. Where a child process is necessary, keep the executable and supported options under application control, preserve argument boundaries, and validate operands according to the program's intended operation. The lesson covers shell syntax and option interpretation; it does not model arbitrary external programs, privilege separation, or operating-system process sandboxes.

Return to the [lab overview](README.md) for the other comparisons.
