# Tutorial: Browser, kernel, and virtualization research

[Index](../README.md) | [Full source curriculum](../curriculum/specializations/22-05-browser-kernel-and-virtualization-research.md) | [Original roadmap](../../roadmaps/specializations/22-05-browser-kernel-and-virtualization-research.md)

## Practice research on a small boundary first

Complex systems research begins with reproducibility and ownership reasoning. In this lesson you will build an asynchronous parser model, produce a minimal lifetime failure, repair the invariant, and verify neighboring cases. The exercise is entirely local and does not develop a browser exploit, kernel privilege escalation, or virtual-machine escape.

Before advancing, be comfortable building a native program with symbols, following a stack trace, and explaining pointers, allocation, references, object lifetime, stack unwinding, threads, and synchronization. Record source revision, compiler, build options, runtime configuration, and input corpus separately. A bug report saying only “latest version crashes” is difficult to reproduce because each of those variables can change behavior.

Virtual memory gives processes an address-space abstraction. Privilege levels and system calls control transitions into kernel services. Exceptions interrupt normal execution for conditions such as invalid accesses. Process isolation, sandboxes, and virtualization introduce different boundaries; none should be assumed to be absolute merely because a test runs inside a VM.

## 1. Choose and describe one boundary

For a browser, distinguish the browser process, renderer processes, utility services, sandbox policy, and interprocess messaging. JavaScript language rules, engine implementation, document-origin policy, and operating-system privilege are separate layers. Chromium's architecture describes process separation and communication; its exact allocation strategies depend on version and configuration. [Chromium multi-process architecture](https://www.chromium.org/developers/design-documents/multi-process-architecture/)

An origin normally combines scheme, host, and port; a site is a different grouping concept. Do not assume one tab, origin, site, and process are interchangeable. Content scripts, extension pages, and privileged extension APIs also have distinct capabilities. Review extension permissions and message authorization before reasoning about their effects.

For a kernel interface, trace a request from userspace through copying or validation, allocation, locking, operation, and cleanup. Drivers, system calls, networking, filesystems, and device-control interfaces have different execution contexts. Determine whether a context may sleep or block, which locks are held, and which data can change concurrently.

For virtualization, label guest userspace, guest kernel, virtual-device queues, host-side device process, hypervisor, and host kernel. Shared memory, configuration registers, queue descriptors, reset, and hot-unplug create input and lifecycle boundaries. A guest application crash demonstrates a different property from a fault in a host-side device process. Use the project's developer documentation to locate the responsible component before making an impact claim. [QEMU developer documentation](https://www.qemu.org/docs/master/devel/index.html)

Select only one of those boundaries for later research. For this tutorial, the analogous boundary is a request queue transferring a record to a parser callback.

## 2. Write the invariant before the experiment

An invariant is a statement that should remain true across all permitted transitions. Our invariant is: every callback that needs a record holds a valid record until it finishes, or detects cancellation before using it.

Other useful invariants include a length remaining within the allocated buffer, a handle still referring to the expected object generation, or the caller remaining authorized for an operation. Explicit invariants turn vague crashes into specific questions.

Study bug classes by connecting them to state:

| Bug class | Broken assumption | Safe review question |
|---|---|---|
| Integer conversion | A length has the same range in two types | What happens at zero, maximum, and signed boundaries? |
| Type confusion | An object has the expected runtime shape | Where is the tag validated before use? |
| Reference-count error | Every owner retains and releases exactly once | Which path drops the final reference? |
| Stale handle | An identifier still names the original object | Can a recycled identifier change meaning? |
| Race | Shared state stays stable across operations | Which interleaving invalidates the check? |
| Double fetch | Input is unchanged between two reads | Can input mutate after validation? |

Locks coordinate critical sections; atomics provide specific operations and ordering properties; reference counts manage lifetime but do not automatically protect object contents. Cancellation and shutdown require explicit ownership decisions. In JavaScript engines, parsing, bytecode, optimization, deoptimization, and garbage collection each maintain assumptions about values and lifetimes. An optimization must remain valid when those assumptions change.

Just-in-time, or JIT, compilation produces executable code while a program runs. Review the assumptions connecting observed types, optimized code, and fallback or deoptimization paths. In native debugging, use assembly to relate an instruction's access to the calling convention, register values, and source expression. Reading that relationship is a prerequisite skill; generating an exploit is not required to explain a faulty bounds or lifetime check.

## 3. Reproduce a lifetime error without native memory corruption

Save this Python model as `lifetime_model.py`. It deliberately represents freed storage with a missing dictionary entry, making the same ownership mistake observable as a deterministic assertion rather than a harmful memory access:

```python
class ParserService:
    def __init__(self):
        self.records = {}
        self.callbacks = []
        self.results = []

    def submit(self, key, text):
        self.records[key] = text
        def callback():
            assert key in self.records, "record expired before callback"
            self.results.append(self.records[key].split(":"))
        self.callbacks.append(callback)

    def cancel_buggy(self, key):
        self.records.pop(key, None)

    def run(self):
        for callback in self.callbacks:
            callback()
        self.callbacks.clear()

service = ParserService()
service.submit("R1", "temperature:25")
service.cancel_buggy("R1")
service.run()
```

Expected behavior in the deliberately defective model is an `AssertionError` identifying the expired record. The minimal causal sequence is `submit`, `cancel`, `run`. A thousand random strings are unnecessary because the defect is lifecycle-related, not dependent on the spelling of the record. Reduce the string to `a:b` and confirm the same assertion remains. Removing `cancel` should allow normal parsing.

Draw the timeline: submit creates a record, submit queues a callback referencing its identifier, cancel removes the record, callback later tries to use it. The callback's existence does not keep the record alive in this model. In native code, an analogous ownership defect can manifest as a use-after-free, but this Python assertion proves only the modeled lifetime failure.

## 4. Repair ownership and cancellation semantics

Choose a documented policy: canceled requests produce no result, while their pending callbacks complete harmlessly. One repair captures an immutable record and gives the callback a cancellation check. Use a fresh monotonically increasing request identifier so a reused name cannot accidentally refer to a new request.

```python
class FixedParserService:
    def __init__(self):
        self.next_id = 0
        self.cancelled = set()
        self.callbacks = []
        self.results = []

    def submit(self, text):
        request_id = self.next_id
        self.next_id += 1
        def callback(record=text, rid=request_id):
            if rid not in self.cancelled:
                self.results.append(record.split(":"))
            self.cancelled.discard(rid)
        self.callbacks.append(callback)
        return request_id

    def cancel(self, request_id):
        self.cancelled.add(request_id)

    def run(self):
        pending, self.callbacks = self.callbacks, []
        for callback in pending:
            callback()
```

Run three cases. A normal request produces one parsed result. A canceled request produces no result. Two requests with identical text remain distinct when only one is canceled. Define shutdown as either draining accepted work or canceling and draining it; test that policy explicitly. This single-threaded model does not prove a concurrent implementation safe. If multiple threads share cancellation state, the synchronization design needs separate analysis.

The repair preserves ownership at the actual boundary. Removing the assertion, catching and ignoring every exception, or disabling diagnostics would conceal the defect without restoring the invariant. Inspect alternate paths such as failed submission, repeated cancellation, and shutdown during queued work.

## 5. Engineer a bounded harness

A harness turns an input into a controlled target invocation and observable result. For the model, inputs are short sequences of `submit`, `cancel`, `run`, and `shutdown`. Start with valid cases, then small malformed or boundary variations. Limit sequence length, runtime, and memory. Preserve the seed and sequence for every failure. Verify that instrumentation reaches the intended parser and cancellation logic rather than only rejecting input in an outer wrapper.

For a small native training implementation, build with symbols and suitable instrumentation. AddressSanitizer can diagnose several memory-access and lifetime errors; compiler and runtime configuration matter. Its official guide documents building, linking, symbolization, and limitations. [Clang AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html) Kernel AddressSanitizer is a distinct kernel instrumentation facility with configuration-specific capabilities. [Linux KASAN](https://www.kernel.org/doc/html/latest/dev-tools/kasan.html)

Read a diagnostic in three parts: failing access, allocation history, and release history where available. Inline and optimized frames can complicate stack interpretation. Compare source revision and symbols before assuming a line number is accurate. Reproduce on a clean build to separate harness mistakes from target defects.

Minimize while preserving the same root cause. A smaller input that crashes at a different layer is not necessarily a minimized version of the original bug. Keep valid neighboring cases in the regression suite so the patch cannot pass by rejecting all inputs. For nondeterministic failures, record attempts, failures, scheduling assumptions, and instrumentation; do not discard inconsistent results.

## 6. Review a patch and write a precise report

Explain the invariant restored by the patch, why it belongs at this ownership boundary, and which alternate paths now satisfy it. Review nearby call sites, compatibility, configuration dependence, and backport implications. A one-line diff may depend on a much larger design assumption.

Use this report structure for the toy defect: component and revision; exact build or interpreter environment; minimal sequence; expected and observed results; assertion or diagnostic; lifetime timeline; patch rationale; regression results; limitations. State that the demonstrated impact is a canceled request reaching invalid modeled state. Do not transform that observation into a claim of browser, kernel, or host compromise.

For newly discovered security-sensitive issues in real projects, follow their reporting process and coordinated disclosure expectations. Public portfolio material can use your own toy defect, already-public fixed issues, or appropriately cleared reports. Manage untrusted corpora carefully, keep sensitive host files outside the test environment, and avoid unnecessary external services.

## Questions with answer guidance

1. **Why might a sanitizer change reproduction frequency?** Instrumentation changes memory layout, timing, and resource use; observed rates are environment-dependent.
2. **Does a renderer crash demonstrate a sandbox escape?** No. Establish the failing process and crossed boundary separately.
3. **Why can reference counting still leave a race?** Lifetime and concurrent access to contents are distinct properties.
4. **What demonstrates readiness for a larger target?** Independent ability to reproduce, minimize, explain, repair, and retest a smaller defect with honest limitations.

Complete this lesson by preserving both models, their minimal sequences, expected outputs, the ownership diagram, and a regression table covering normal work, cancellation, repeated requests, and shutdown. Advanced research starts when those results are reproducible, not when the target name becomes more impressive.
