# 03. Computing and study foundations

[All topic roadmaps](README.md) | [Original master roadmap](../ETHICAL_HACKING_ROADMAP.md#03-computing-and-study-foundations)

<!-- TOPIC-TOC:START -->

## Contents

- [Computer architecture and data](#computer-architecture-and-data)
- [Operating systems and application execution](#operating-systems-and-application-execution)
- [Learning workflow and technical communication](#learning-workflow-and-technical-communication)
- [Safe practice and exit criteria](#safe-practice-and-exit-criteria)
- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1 — Represent information accurately](#stage-1--represent-information-accurately)
  - [Stage 2 — Follow data through a computer](#stage-2--follow-data-through-a-computer)
  - [Stage 3 — Manage files and execution environments](#stage-3--manage-files-and-execution-environments)
  - [Stage 4 — Turn observations into explanations](#stage-4--turn-observations-into-explanations)
- [Guided labs with evidence](#guided-labs-with-evidence)
  - [Lab A — One text file, several representations](#lab-a--one-text-file-several-representations)
  - [Lab B — Application, process, and resource boundary](#lab-b--application-process-and-resource-boundary)
  - [Lab C — Restore and explain a failure](#lab-c--restore-and-explain-a-failure)
- [Capstone and completion rubric](#capstone-and-completion-rubric)
- [Retention and next steps](#retention-and-next-steps)

<!-- TOPIC-TOC:END -->



**Prerequisites:** None. **Priority:** Core. Understand the systems you will later assess before installing security tools.

## Computer architecture and data

- [ ] Identify CPU, RAM, persistent storage, network interfaces, motherboard firmware, and peripherals; distinguish volatile from persistent information.
- [ ] Understand bits, bytes, binary, hexadecimal, signed integers, overflow, Boolean operations, endianness, and the difference between a value and its representation.
- [ ] Recognize ASCII, Unicode, UTF-8, newline conventions, URL encoding, hexadecimal encoding, and Base64. Encoding does not provide secrecy.
- [ ] Understand files, directories, extensions, actual file formats, metadata, compression, archives, checksums, file signatures, and why an extension can misrepresent content.
- [ ] Understand BIOS/UEFI, bootloaders, operating-system startup, Secure Boot concepts, disk partitions, filesystems, and disk encryption at an introductory level.

## Operating systems and application execution

- [ ] Explain kernel space versus user space, processes versus threads, executable files versus running programs, and the role of system calls.
- [ ] Learn scheduling, virtual memory, address spaces, stack and heap, file handles/descriptors, shared libraries, interprocess communication, and signals/events conceptually.
- [ ] Distinguish administrator privileges, application permissions, hardware access, and network access. Installing a program does not automatically give it every permission.
- [ ] Understand clients, servers, services, databases, caches, queues, APIs, and the difference between local and remote execution.
- [ ] Compare virtual machines, containers, and compatibility layers. Learn host/guest boundaries, virtual disks, snapshots, resource limits, and shared-folder risks.
- [ ] Learn availability basics: CPU load, memory pressure, disk space, latency, backups, restoration, and why snapshots alone are not a complete backup plan.
- [ ] **Advanced:** Study interrupts, direct memory access, kernel modules/drivers, memory mapping, executable loaders, and hardware-assisted virtualization when specializing in systems security.

## Learning workflow and technical communication

- [ ] Use a text editor, terminal, browser developer tools, Markdown, a password manager, and a structured note directory.
- [ ] Read a manual page or official reference; identify supported versions, defaults, prerequisites, limitations, and whether an example is safe in your environment.
- [ ] Practice hypothesis-driven troubleshooting: observation → possible cause → smallest discriminating test → result → revised explanation.
- [ ] Keep notes containing date, objective, environment/version, actions, evidence, interpretation, remediation, and retest. Separate confirmed observations from assumptions.
- [ ] Learn basic probability, percentages, orders of magnitude, and rates; distinguish correlation from causation and statistical confidence from certainty.
- [ ] Explain a technical issue twice: once to another engineer and once to a nontechnical stakeholder. Record what could not be tested.
- [ ] Use active recall, spaced review, and reconstruction from memory; measure successful independent tasks rather than videos watched.

## Safe practice and exit criteria

**Labs:** Inventory your own computer; create a disposable VM; install an ordinary application; inspect its process and files; take a snapshot; make a harmless configuration change; restore it. Compare a text file's displayed content, encoding, bytes, metadata, and checksum. Break and repair a local application's configuration while recording evidence.

**Exit gate:** Rebuild the VM from written instructions, explain how a program reaches memory and accesses a file, distinguish encoding from encryption, and troubleshoot one failure without blindly reinstalling everything.

**Common gaps:** Memorizing commands without understanding output; confusing a terminal with an operating system; using screenshots without written reproduction steps; treating a successful restore as proof that every backup works.

## Detailed learning sequence

Use the original checklist above as the coverage list and this sequence as your practice plan. **Practical depth** means performing the task, explaining the result, and repeating it without a copied walkthrough. **Awareness depth** means drawing the mechanism, recognizing its security relevance, and knowing which reference to consult; it does not require writing a driver or operating system.

### Stage 1 — Represent information accurately

- [ ] Convert a short number between decimal, binary, and hexadecimal by hand, then verify it with a calculator. Explain why two hexadecimal digits represent one byte and why leading zeroes can matter in a fixed-width field.
- [ ] Compare an unsigned eight-bit range with a signed two's-complement eight-bit range. Distinguish wraparound in a fixed-width representation from a language that grows integers automatically; never assume every language handles overflow alike.
- [ ] Use AND, OR, XOR, and NOT on small bit patterns. Apply a mask to select a field and explain why this later helps with subnet masks, permission bits, and protocol flags.
- [ ] Encode the same short sentence in UTF-8 and UTF-16. Include an accented character and an emoji. Compare character count, code points, and byte length; recognize that a visible character can comprise multiple code points.
- [ ] Observe a newline in a hexadecimal viewer. Compare LF and CRLF and the presence or absence of a final newline. Record why a text editor can display two files identically while their hashes differ.
- [ ] Separate a file's raw bytes from its interpretation: a byte sequence might be text, an integer, compressed content, or part of an executable depending on the format. Explain endianness using a four-byte integer, without reversing every byte of an arbitrary file.
- [ ] Learn rounding and unit mistakes: bits per second versus bytes per second, decimal storage units versus binary units, duration versus clock time, and percentage versus percentage-point change.

**Checkpoint:** Given a small byte dump, describe what you can establish directly and what requires knowing the encoding or file format. Decode a Base64 string and explain why no secret key was involved.

### Stage 2 — Follow data through a computer

- [ ] Draw the path from storage to RAM to CPU execution. Mark caches, the operating system, and an application's files. Explain that deleting a file, closing a process, and powering down are different events.
- [ ] Distinguish an address from the data stored there. At awareness depth, describe virtual addresses, pages, page faults, and why a process cannot ordinarily read every other process's memory.
- [ ] Follow a program launch: executable selection, loader and libraries, process creation, permissions inherited from its execution context, arguments, environment, and termination status.
- [ ] Explain the stack as storage associated with function calls and the heap as dynamically managed storage. Learn that the precise layout and ownership rules depend on the language and runtime.
- [ ] Inspect a parent process and two child processes. Compare process identifiers, command lines, users, and working directories. Notice that a long-running service need not have a visible window.
- [ ] Model a file operation as application request, operating-system permission check, filesystem operation, and result. Describe what an open handle or descriptor refers to and why a pathname is not the same thing as an already-open resource.
- [ ] At awareness depth, connect interrupts, device drivers, DMA, and firmware to privileged hardware access. Record these as later systems-security prerequisites rather than prerequisites for every web assessment.

### Stage 3 — Manage files and execution environments

- [ ] Create a small directory convention: `notes`, `lab-config`, `synthetic-data`, `evidence`, and `reports`. Put lab identifiers and dates in records; keep personal credentials and unrelated documents outside the lab.
- [ ] Compare absolute paths, relative paths, current directories, file extensions, and actual file signatures. Practice names with spaces and non-ASCII characters before writing automation that handles files.
- [ ] Compare a copy, a compressed archive, and a snapshot. State what each includes and excludes: permissions, open application state, external volumes, recovery keys, and host dependencies may require separate treatment.
- [ ] Learn the VM boundary: virtual CPU/RAM, guest disk, network mode, console, clipboard integration, shared folders, and device passthrough. Enable integrations only when a lab needs them and document them.
- [ ] Learn the container boundary at awareness depth: a container typically shares a kernel with its environment while a VM runs a guest kernel. Map host mounts, process isolation, and resource limits before treating a container as disposable.
- [ ] Record available host memory and free storage before allocating a VM. Observe ordinary resource use first; do not manufacture a disk-full or memory-exhaustion incident on your daily-use computer.

### Stage 4 — Turn observations into explanations

- [ ] Write each problem as an observable symptom, such as “the local application exits after reading its configuration.” Avoid beginning with a diagnosis such as “the OS is broken.”
- [ ] List at least two plausible causes and a test that distinguishes them. Change one variable, record the before/after result, and restore the baseline before trying the next explanation.
- [ ] Learn evidence strength: an error message is an observation, a configuration file shows intended settings, and a successful runtime test shows behavior for that exact case. None alone proves all possible behavior.
- [ ] Keep UTC or an explicit local offset with timestamps. Record tool versions and whether a command ran on the host or guest; these details make later evidence correlation possible.
- [ ] Build a glossary in your own words. For each new term, add an example, a related term it is often confused with, and one question you can answer from memory.
- [ ] Practice reading documentation by locating its applicability, required privileges, defaults, input syntax, side effects, and rollback instructions before using an example.

## Guided labs with evidence

### Lab A — One text file, several representations

**Setup:** Create a new folder containing a short synthetic sentence. Use a text editor that displays its encoding and newline settings, plus an operating-system hashing utility.

**Actions:** Save UTF-8 and UTF-16 copies. Make another UTF-8 copy with the alternate newline convention. Inspect file sizes and bytes, calculate a SHA-256 digest for each, and archive the folder. Extract the archive into a different directory and compare the extracted bytes with the originals.

**Expected observation:** Different encodings or newlines change bytes and therefore usually the digest, even when text looks similar. A faithful archive round trip preserves the file bytes. A digest comparison checks byte equality against a reference; it does not establish who created that reference.

**Evidence:** A table containing filename, encoding, byte count, newline convention, digest, and explanation. Include a small byte excerpt and extraction verification.

**Troubleshooting:** If values change unexpectedly, inspect the editor's automatic newline conversion, byte-order mark, final newline, or archive extraction destination. Correct the specific conversion and repeat the comparison.

### Lab B — Application, process, and resource boundary

**Setup:** In a disposable VM, install an ordinary text editor or a small local application. Record installation source and create a clean snapshot after shutdown or an application-consistent checkpoint where supported.

**Actions:** Open a synthetic file, locate the process, record its identity, working directory where observable, CPU/memory use, and file location. Close the application and verify that its process exits while the saved file remains. Change one harmless application setting, restart it, and find where that setting persists.

**Expected observation:** Runtime state and saved configuration have different lifetimes. The application's identity and permissions affect file access. Memory use can fluctuate without indicating a defect.

**Evidence:** A diagram connecting executable, process, account, configuration, and data; before/after notes; and a screenshot only where it adds evidence beyond text.

**Troubleshooting:** If several processes appear, examine their parent/child relationship. If a setting persists after reinstalling, investigate the user profile rather than assuming the installer controls all application state.

### Lab C — Restore and explain a failure

**Setup:** Back up the local application's synthetic data and configuration to a separate lab location. Write a short rebuild procedure before making changes.

**Actions:** Introduce one harmless invalid configuration value, capture the exact failure, and restore the known-good value. Recreate the VM or application environment from your notes and restore the backup. Verify both content and expected access permissions.

**Expected observation:** Correcting the cause restores behavior; a complete rebuild tests whether the documentation and backup contain what you actually need.

**Evidence:** Symptom, two hypotheses, discriminating test, correction, successful retest, and any undocumented dependency discovered during rebuilding.

**Troubleshooting:** Distinguish missing files, wrong paths, incompatible configuration, and permission failures. If recovery depends on a key, document where its separate test copy is stored without placing the key in the report.

## Capstone and completion rubric

Build a “computer-to-application” dossier for one disposable VM. Include a resource inventory, boot-to-process diagram, file-format comparison, installation record, backup/recovery procedure, and a repaired configuration failure. Another learner should be able to follow it without relying on your memory.

Score each criterion **0 = missing, 1 = works with help, 2 = independently repeatable**: information representation; process and privilege explanation; environment inventory; troubleshooting evidence; restoration; and communication. Repeat every criterion scored below 2. Passing requires a successful restore and an explanation of the observed behavior, rather than a particular aggregate score.

## Retention and next steps

After the first lab, reconstruct its diagram the next day. A few days later, repeat it with a different filename and encoding. The following week, troubleshoot a different configuration failure without opening the old solution first. Revisit weak items after longer gaps; shorten the gap when recall fails. Keep a dated record of what you could perform independently.

Move to [networking](04-networking-and-internet-protocols.md) once you can separate an application, process, operating system, and network interface. Return to low-level architecture when [programming](07-programming-and-automation.md) or a systems specialization makes the extra depth useful.
