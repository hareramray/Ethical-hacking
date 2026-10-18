# 22.5 Browser, kernel, and virtualization research

[All topic roadmaps](../README.md) | [Specialization overview](../22-advanced-specialization-map.md)

<!-- TOPIC-TOC:START -->

## Contents

- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1: Demonstrate prerequisite debugging competence](#stage-1-demonstrate-prerequisite-debugging-competence)
  - [Stage 2: Choose one boundary and understand its design](#stage-2-choose-one-boundary-and-understand-its-design)
  - [Stage 3: Develop a precise bug model](#stage-3-develop-a-precise-bug-model)
  - [Stage 4: Engineer a bounded experiment](#stage-4-engineer-a-bounded-experiment)
  - [Stage 5: Learn patch review and responsible reporting](#stage-5-learn-patch-review-and-responsible-reporting)
- [Worked lab: a toy asynchronous parser service](#worked-lab-a-toy-asynchronous-parser-service)
- [Blind spots and advancement criteria](#blind-spots-and-advancement-criteria)

<!-- TOPIC-TOC:END -->



**Prerequisites:** Advanced operating systems, C/C++, assembly, debugging, fuzzing, and mitigation knowledge.

- [ ] Study browser process models, sandboxing, JavaScript engines, JIT compilation, extension permissions, IPC, and origin isolation.
- [ ] Study kernel interfaces, drivers, memory ownership, synchronization, device interfaces, hypervisors, virtual devices, and guest/host boundaries.
- [ ] Learn harness engineering, reproducibility, root-cause analysis, patch verification, coordinated disclosure, and careful management of untrusted inputs.

**Project:** Fuzz a small open-source parser or toy interface in a disposable local environment. **Pass:** Deliver a minimized bug report, patch or mitigation analysis, and regression evidence. Advance to complex targets only after demonstrating reliable isolation and debugging.

## Detailed learning sequence

### Stage 1: Demonstrate prerequisite debugging competence

Before selecting a complex target, build and debug a small native application with symbols. Explain allocation, ownership, object lifetime, pointers, references, stack unwinding, threading, and synchronization. Reproduce an ordinary crash, minimize its input, and repair it. Learn the build system and test conventions of the project you intend to study.

- [ ] Read a stack trace with inlining and optimized frames.
- [ ] Distinguish source revision, build configuration, runtime configuration, and input corpus.
- [ ] Explain virtual memory, privilege levels, system calls, exceptions, and process isolation.
- [ ] Understand locks, atomics, reference counts, cancellation, and asynchronous callbacks.
- [ ] Preserve a minimal reproduction environment and a known-good baseline.
- [ ] Establish resource limits, disposable test environments, and a documented recovery process.

### Stage 2: Choose one boundary and understand its design

For browsers, study renderer processes, the browser process, utility services, site/origin concepts, sandbox policies, and interprocess messaging. Learn the difference between JavaScript language behavior, engine implementation, document security policy, and operating-system privilege. Review extension permissions and the trust relationship between content scripts, extension pages, and privileged APIs.

For kernels, map a single interface from user input to validation, allocation, locking, operation, and cleanup. Study drivers, system calls, filesystem interfaces, networking code, and device-control interfaces as separate research areas. Understand the context in which code executes and which resources may sleep, block, or be accessed concurrently.

For virtualization, distinguish the guest kernel, guest userspace, virtual device model, hypervisor, host process, and host kernel. Map shared-memory regions, device queues, configuration registers, and lifecycle transitions. A fault in a guest application is different from a fault in a host-side device process; evidence must establish which boundary was reached.

### Stage 3: Develop a precise bug model

Write the invariant you are studying. Examples include an object's lifetime outlasting every callback, a length remaining within its allocated buffer, or a request being authorized for the caller that supplied it. Trace every operation that can change the relevant state.

Study memory safety, integer conversions, type confusion, reference-count errors, stale handles, races, double-fetch assumptions, and input validation. For engines, learn parsing, bytecode, optimization, deoptimization, garbage collection, and the assumptions an optimization relies on. For concurrency, construct a state-transition model before attempting to interpret intermittent failures.

Separate exploitability from defect discovery. Record input influence, reachable privileges, failure type, required configuration, and known mitigations. Do not promote an assertion failure or renderer crash into a claim about host compromise without evidence. Minimal root-cause reports and fixes are useful research outcomes.

### Stage 4: Engineer a bounded experiment

Choose a small component that can be exercised independently. Use the project's supported test or fuzzing harness where possible. Set memory and time limits, preserve diagnostic output, and disable unnecessary external services. Build with appropriate sanitizers and debugging options for the target.

- [ ] Seed the corpus with valid boundary cases and small malformed variants.
- [ ] Confirm the harness reaches the intended component rather than only an outer parser.
- [ ] Record coverage limitations and environmental prerequisites.
- [ ] Minimize failures while checking that the same underlying defect remains.
- [ ] Reproduce on a clean build and distinguish harness defects from target defects.
- [ ] Compare behavior before and after a candidate patch.
- [ ] Add a focused regression test plus valid neighboring cases.
- [ ] Document nondeterminism instead of silently discarding inconsistent runs.

### Stage 5: Learn patch review and responsible reporting

Read a small upstream bug fix and explain the invariant it restores. Trace nearby call sites and alternate paths to understand why the fix belongs at that layer. Study backport considerations, configuration dependence, and compatibility effects. Avoid assuming a changed line is the full root cause.

Prepare a report containing affected component, exact revision, build instructions, minimal input, observed result, expected result, diagnostic trace, and proposed reasoning. Follow the project's security-reporting process for newly discovered security-sensitive issues. Public portfolio work can use your own toy defects, already-public fixed issues, or reports cleared through the relevant process.

## Worked lab: a toy asynchronous parser service

**Setup:** Build a small local service that accepts invented records and processes them asynchronously. Include a deliberately incorrect ownership transition in a training branch. Run it in a disposable VM with no sensitive files and no external exposure. Preserve the correct reference implementation separately.

**Actions:** Exercise normal input, cancellation, repeated requests, and shutdown during pending work. Use a sanitizer and debugger to identify a lifetime error. Minimize the sequence that triggers the same failure. Draw the object lifetime and callback sequence, then implement a clear ownership fix.

**Expected behavior:** The defective branch yields a reproducible diagnostic under a defined sequence; the corrected branch preserves object lifetime, handles cancellation, and completes normal requests. The report describes the demonstrated property without claiming a browser, kernel, or hypervisor exploit.

**Evidence:** Save source revisions, build settings, input sequence, timing assumptions, stack traces, allocation/release history, patch, and regression results. Explain how the toy pattern relates conceptually to a more complex codebase.

**Correction:** Repair ownership or synchronization at the correct boundary, rather than suppressing the diagnostic. Verify successful operation, cancellation, shutdown, and repeated execution. If the reproducer is nondeterministic, report repetition counts and observed outcomes.

## Blind spots and advancement criteria

Sanitizers alter timing and memory layout. Debuggers can hide races. An optimized build may omit assertions that made a failure obvious. A test VM does not automatically contain flaws in its hypervisor. A project configured without normal protections may demonstrate a bug while misrepresenting real exposure.

Advance to larger components only when you can independently reproduce, minimize, explain, repair, and retest smaller defects. Use [Chromium's process architecture](https://www.chromium.org/developers/design-documents/multi-process-architecture/) for browser boundaries, [Linux KASAN documentation](https://www.kernel.org/doc/html/latest/dev-tools/kasan.html) for kernel memory-error instrumentation, and [QEMU developer documentation](https://www.qemu.org/docs/master/devel/index.html) for virtualization internals. Consult the documentation matching the revision under test.

