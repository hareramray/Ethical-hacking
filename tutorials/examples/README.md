# Portable practice pack

[Tutorial index](../README.md)

These original teaching examples need Python 3.9 or newer, use only the standard library, and contain synthetic data. Run commands from the repository root in PowerShell or a terminal. `python --version` identifies your interpreter; use `python3` if that is its name on your OS. They do not install packages, modify system settings, or scan other hosts.

## 1. Authorization before and after repair

Run `python tutorials/examples/access_lab.py`. With the owner check disabled in the in-memory comparison, Bob receives status 200 for Alice's note. Enabling it produces 403; Alice still receives 200 and an unknown identity receives 401. Authentication establishes identity; authorization decides which object that identity can use.

For HTTP observation, run `python tutorials/examples/access_lab.py --serve` in one terminal. The server binds only to `127.0.0.1:8765` and always enforces ownership. In another PowerShell terminal:

```powershell
curl.exe -i -H 'Authorization: Bearer alice-lab' http://127.0.0.1:8765/notes/n1
curl.exe -i -H 'Authorization: Bearer bob-lab' http://127.0.0.1:8765/notes/n1
curl.exe -i http://127.0.0.1:8765/notes/n1
```

In Linux/macOS, use `curl` instead of `curl.exe`. Expect 200 with synthetic text, 403 without the note, and 401 respectively. In a browser, use developer tools to inspect the request and response; the address bar alone sends no training token. Ctrl+C stops the server. Port already in use means another local process occupies 8765; identify it and choose another port in your own copy rather than stopping an unknown service.

Fixed tokens are public lab fixtures. This is not a deployable authentication system, and it lacks TLS, token lifecycle, rate limiting, and production HTTP hardening. The defective behavior is available only through the local function comparison, not an exposed vulnerable server.

## 2. A synthetic incident timeline

Run `python tutorials/examples/analyze_events.py`. It prints E1–E6 ordered by event time and `Review pairs: [('E3', 'E5')]`. E2 arrives late. E4 belongs to `u20`, while E3/E5 belong to `u2`; similar display names do not establish the same identity. The review pair is a denial followed by an allowed read of the same document in the same session within 120 seconds. It raises a question, not a verdict. Decide whether a legitimate policy change explains it.

Change an event in a separate working copy, retaining the original. Predict whether changing its stable identity, session, document, or time changes the match. A missing match may mean absent evidence or a narrower rule, not safe activity. The detector sorts a finite offline dataset; it does not implement production streaming, deduplication, or late-arrival watermarks.

## 3. Parser failure and repair

Run `python tutorials/examples/parser_lab.py`. The record `03 61 62 63` means length 3 followed by ASCII `abc`. Both parsers accept it. The record `05 61 62 63` declares five bytes but supplies three. The naive parser raises `IndexError`; the corrected parser rejects it with a deliberate `ValueError`. This illustrates validation ordering safely in Python; it is not evidence of memory corruption or code execution.

Read `parse_checked`: a record must include a length byte, declare at most 32 bytes, and contain exactly the declared payload. Consider empty input, zero-length payload, 32 and 33 bytes, truncation, and extra trailing data. A parser for a stream of multiple records would need a different contract.

## Verify and retain evidence

Run `python tutorials/examples/check_examples.py`. Four test methods check the permission matrix, actual loopback HTTP statuses and body confidentiality, correlation negatives and time boundaries, and a deterministic 207-input parser corpus. It briefly starts and shuts down a loopback server on an OS-assigned port. No persistent listener remains. Tests print `OK` on success.

Use [the learning-note template](../templates/learning-note.md) to record interpreter version, prediction, observed output, explanation, repair, and limitation. The API and events illustrate distinct fixtures; do not claim the event file was captured from this HTTP server. Only sanitized synthetic artifacts belong in a public portfolio.
