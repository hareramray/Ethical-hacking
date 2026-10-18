# 03. Understand bytes, processes, and evidence

[Index](README.md) | [Complete source curriculum](curriculum/03-computing-and-study-foundations.md) | [Original roadmap](../roadmaps/03-computing-and-study-foundations.md)

## Prerequisites and outcome

Use a disposable working directory, Python 3, a text editor, and your operating system's process viewer. No security tools are needed. You will compare representations of the same information, trace an ordinary program, repair a configuration mistake, and document a recoverable environment. Use tutorial 02 for the VM and keep personal data outside these exercises.

## 1. Separate a value from its representation

A bit has two states; eight bits form a byte. Decimal 42, binary `00101010`, and hexadecimal `2a` represent the same integer. Each hexadecimal digit describes four bits, so two digits describe a byte. Fixed-width fields retain leading zeroes to preserve width even when they do not change the numerical value.

Eight-bit unsigned integers represent 0 through 255. Eight-bit two's-complement signed integers represent -128 through 127. Python integers grow as needed, whereas other types have bounded ranges; signed overflow in C is not a portable wraparound mechanism. Verify the rules of the actual type before reasoning about a length or size.

```python
print(bin(42), hex(42))
print(0b1010 & 0b1100)  # 8: select bits present in both
print(0b1010 | 0b1100)  # 14: bits present in either
print(0b1010 ^ 0b1100)  # 6: bits that differ
print((~0b1010) & 0b1111)  # 5: complement within four bits
print((255 + 1) & 255)  # 0: explicitly model eight-bit wrapping
```

AND masks select fields; OR combines flags; XOR compares or toggles selected bits. An unbounded integer's NOT operation needs a mask when you intend a fixed-width demonstration. These concepts recur in subnet masks, permissions, and protocol headers.

Endianness describes byte order for a multi-byte value. The integer `0x01020304` becomes bytes `04 03 02 01` in little-endian and `01 02 03 04` in big-endian. It does not mean every arbitrary file should be reversed. A format defines which fields are integers and how they are encoded.

## 2. Inspect text as bytes

ASCII assigns values to a limited character set. Unicode assigns code points across writing systems; UTF-8 and UTF-16 encode those code points into bytes. A visible character can contain multiple code points, and an emoji can require several bytes. Character count, code-point count, and byte length can therefore differ.

Run this saved Python program in a new lab directory:

```python
from pathlib import Path
import base64
import hashlib
import zipfile

root = Path("representation-lab")
root.mkdir(exist_ok=False)
text = "café 🙂\n"
variants = {
    "utf8-lf.txt": text.encode("utf-8"),
    "utf16-lf.txt": text.encode("utf-16"),
    "utf8-crlf.txt": text.replace("\n", "\r\n").encode("utf-8"),
}
for name, data in variants.items():
    (root / name).write_bytes(data)
    print(name, len(data), data.hex(), hashlib.sha256(data).hexdigest())
print("code points:", len(text))
encoded = base64.b64encode(variants["utf8-lf.txt"])
print("base64 round trip:", base64.b64decode(encoded) == variants["utf8-lf.txt"])
with zipfile.ZipFile(root / "copy.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for name in variants:
        archive.write(root / name, arcname=name)
with zipfile.ZipFile(root / "copy.zip") as archive:
    print("archive round trip:", all(archive.read(n) == b for n, b in variants.items()))
```

Expected results include differing byte counts/digests, `code points: 7`, and two `True` round trips. UTF-16 may include a byte-order mark. LF is byte `0a`; CRLF is `0d0a`. Hash changes follow changed bytes, even when editor display looks similar. Base64 and hexadecimal are reversible encodings without a secret. URL percent encoding similarly represents bytes for a particular context; none provides confidentiality.

A file extension is a name convention. The actual content can disagree: renaming a ZIP to `.txt` does not turn it into plain text. File signatures and parsers provide stronger format evidence, though a signature alone does not prove safe content. Metadata includes size, ownership, permissions, timestamps, and attributes. Compression changes representation to save space; an archive groups entries and may preserve selected metadata. Verify which metadata your chosen archive format/tool retains.

## 3. Follow data through the computer

| Component | Function | Useful security connection |
| --- | --- | --- |
| CPU and caches | Execute instructions and keep nearby data | Privilege boundaries and side-channel awareness |
| RAM | Holds active program state | Volatile data differs from saved files |
| Persistent storage | Retains files across power cycles | Encryption, permissions, backups, recovery |
| Network interface | Sends/receives link traffic | Addressing and remote boundaries |
| Firmware / BIOS / UEFI | Initializes hardware and starts boot chain | Boot trust and firmware configuration |
| Peripherals, drivers | Connect software requests to devices | Privileged access and device trust |

At startup, firmware selects boot components, a bootloader prepares the OS, and the kernel manages hardware and starts user-space services. Partitions divide storage; filesystems organize objects and metadata within volumes. Secure Boot authenticates permitted boot components under its configured trust policy. Disk encryption protects stored data when keys are unavailable; it does not automatically prevent an authorized running process from reading unlocked files.

A program is stored code; a process is an executing instance with an identity, address space, handles, and runtime state. Threads execute within a process and share much of that state. The scheduler shares CPU time between runnable threads. User-space code requests privileged operations through system calls; the kernel enforces relevant access rules and manages resources.

Virtual addresses refer to a process's memory view, not unrestricted physical RAM. Pages map portions of that view to memory or backing storage; a page fault triggers handling when an access needs mapping or violates a rule. Stack storage commonly supports function calls and local state; heap storage supports dynamically managed objects. Exact organization depends on language/runtime, so diagrams are conceptual rather than universal layouts.

Launching a program involves selecting an executable, loading code and libraries, setting arguments/environment/working directory, establishing execution credentials, and eventually producing an exit status. A handle or file descriptor refers to an open resource; a pathname is a way of locating an object. Renaming a file does not necessarily invalidate an already-open handle.

## 4. Observe an ordinary process

Start the loopback web service from tutorial 02. On Linux use `ps -ef`, `ss -ltnp`, and the service terminal; on Windows use Task Manager and these read-only PowerShell commands:

```powershell
Get-Process | Select-Object -First 10 Id,ProcessName,CPU,WorkingSet64
Get-CimInstance Win32_Process |
    Where-Object { $_.Name -match '^python' } |
    Select-Object ProcessId,ParentProcessId,ExecutablePath,CommandLine
```

Record process ID, parent, account, executable, arguments, and memory observations where permissions allow. Stop the server and confirm the process exits while the saved page remains. This distinguishes runtime lifetime from persistent data. A background service can run without a visible window; several child processes can belong to one application.

Do not equate administrator membership, current process privilege, application permissions, hardware access, and network reachability. A process can read one directory but not another, and can connect to a local service while a firewall blocks another route. Signals on Unix-like systems and events/control mechanisms on Windows communicate termination or other actions; graceful shutdown lets the program release resources before forced termination is considered.

## 5. Recognize common application components

A client initiates a request; a server handles it. A service is usually a long-running background workload. A database persists structured state, a cache speeds selected reads, a queue decouples work in time, and an API defines an interaction contract. A local browser can call a remote server; displaying a result locally does not mean processing occurred locally. Trace where each operation runs and which identity it uses.

VMs run guest kernels on virtualized resources. Containers typically share their environment's kernel with isolation mechanisms. Compatibility environments provide another execution interface and may expose host files. Map guest disks, host mounts, clipboard, device passthrough, and network interfaces; the label “virtual” is not a complete security model.

At systems-specialist depth, interrupts notify the CPU of events, drivers mediate device access, DMA permits devices to transfer memory under platform controls, and kernel modules extend privileged code. Memory mapping exposes file/device regions in an address space; loaders prepare executables and libraries; hardware-assisted virtualization supports guest execution. These are later investigation paths, not requirements to write a driver before studying HTTP.

## 6. Repair a small configuration failure

Create `settings.json` containing `{"port": 8000}`. Save this program beside it:

```python
import json
from pathlib import Path

config_path = Path(__file__).with_name("settings.json")
settings = json.loads(config_path.read_text(encoding="utf-8"))
port = settings["port"]
if type(port) is not int or not 1024 <= port <= 65535:
    raise ValueError("port must be an integer from 1024 to 65535")
print("configuration accepted:", port)
```

Predict the valid result, then change the value to `"eight thousand"`. Preserve the exact exception. Two hypotheses might be “wrong file loaded” and “wrong value type.” Printing the resolved configuration path and inspecting the parsed type distinguish them. Restore integer 8000 and rerun. Also test malformed JSON and a missing key; they fail at different stages. Do not hide every exception under one generic message.

Keep date/offset, objective, environment/version, action, evidence, interpretation, remediation, and retest. Tell an engineer the type and validation failure; tell a nontechnical owner that a bad setting prevented startup and that validation now identifies it clearly. State which behaviors were not tested.

## 7. Measure and learn accurately

Bandwidth in bits per second differs from bytes per second; divide by eight before accounting for overhead. Decimal GB and binary GiB differ. A change from 10% to 15% is five percentage points and a 50% relative increase. An order of magnitude is roughly a factor of ten. A small number of successes supports a limited observation, not certainty about every input. Correlation between a change and failure suggests a hypothesis; controlled variation strengthens a causal explanation.

Observe normal CPU, memory, disk space, latency, and process behavior before diagnosing a fault. Memory pressure, full storage, and overloaded dependencies can harm availability. Do not intentionally exhaust a daily machine. A backup must be restorable and include keys and dependencies; snapshots alone are not a full recovery plan.

Use a terminal, editor, Markdown, browser developer tools, password manager, and structured directories as instruments for reasoning. Read documentation for version, privileges, defaults, and side effects. Reconstruct diagrams tomorrow, repeat a variation after several days, and measure independent tasks rather than video hours.

## Capstone and answer guidance

Deliver a resource inventory, boot-to-process diagram, representation table, installation record, restored configuration failure, and backup/rebuild instructions. Another learner should reproduce the environment without your memory.

If two files look identical but hashes differ, inspect encoding, line endings, byte-order mark, and final newline. If reinstalling an application preserves its setting, investigate per-user configuration. If a restored file is inaccessible, verify identity and permissions as well as bytes. If CPU use fluctuates, compare workload and sampling interval before calling it a defect. Pass when you explain and independently repeat each core observation, then continue to networking.
