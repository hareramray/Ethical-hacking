# 22.1 AI, LLM, RAG, and agent security

[All topic roadmaps](../README.md) | [Specialization overview](../22-advanced-specialization-map.md)

<!-- TOPIC-TOC:START -->

## Contents

- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1: Build the system before testing its security](#stage-1-build-the-system-before-testing-its-security)
  - [Stage 2: Model trust and permissions explicitly](#stage-2-model-trust-and-permissions-explicitly)
  - [Stage 3: Study retrieval and tenant isolation](#stage-3-study-retrieval-and-tenant-isolation)
  - [Stage 4: Evaluate untrusted content and output handling](#stage-4-evaluate-untrusted-content-and-output-handling)
  - [Stage 5: Build evaluations that detect regressions](#stage-5-build-evaluations-that-detect-regressions)
- [Worked lab: a two-tenant research assistant](#worked-lab-a-two-tenant-research-assistant)
- [Blind spots and research gates](#blind-spots-and-research-gates)

<!-- TOPIC-TOC:END -->



**Prerequisites:** Web/API security, Python, identity, data pipelines, and basic machine learning.

- [ ] Learn model training versus inference, tokens, context windows, embeddings, vector stores, retrieval-augmented generation, tools, agents, memory, and evaluation datasets.
- [ ] Trace trust boundaries across user input, documents, retrieved content, tool responses, system instructions, identities, and external actions.
- [ ] Study direct/indirect prompt injection, sensitive-data exposure, excessive permissions, unsafe output handling, poisoned retrieval data, supply-chain risks, resource exhaustion, and incorrect claims.
- [ ] Test tenant isolation, retrieval authorization, document provenance, connector scopes, secret handling, tool argument validation, action approvals, memory retention, and auditability.
- [ ] Understand model limitations and non-determinism; maintain repeatable evaluation cases and measure both security failures and legitimate-task success.

**Project:** Build a local assistant over synthetic documents with mock tools. Evaluate whether untrusted document content can cause unauthorized actions, then enforce boundaries outside the model and retest. **Pass:** Demonstrate tenant separation, limited tool permissions, traceable actions, and a regression suite. Use the [OWASP GenAI Security Project](https://genai.owasp.org/) for its evolving application and agent guidance.

## Detailed learning sequence

### Stage 1: Build the system before testing its security

Implement a small document-search application before adding an assistant. Learn ingestion, parsing, chunking, metadata, embeddings, indexing, retrieval, ranking, and context assembly as separate stages. Record which identity performs each operation and where authorization is evaluated. Then add a model response and a mock tool that changes a local synthetic record.

- [ ] Explain why training data, inference context, retrieved documents, conversation history, and tool results have different provenance.
- [ ] Distinguish model output quality from the application's authorization guarantees.
- [ ] Trace a user request through authentication, retrieval, context assembly, generation, output rendering, and optional tool execution.
- [ ] Identify caches, background jobs, conversation stores, and observability systems that receive copies of the data.
- [ ] Learn token budgeting, sampling, context truncation, structured outputs, and failure handling without assuming reproducibility from one setting alone.

### Stage 2: Model trust and permissions explicitly

Draw boundaries between user intent, external content, model suggestions, application policy, and executed actions. Retrieved text and tool results can contain instructions, but their presence does not grant authority. Write an action policy outside the model that checks the authenticated principal, resource ownership, operation, arguments, and required user approval where applicable.

Treat tool descriptions and schemas as interfaces, not access-control mechanisms. Validate argument types, allowed values, destination paths, resource identifiers, and request size. Give mock tools narrow functions with explicit outcomes. Separate reading a document from changing it, and creating a draft from sending it. Bind any confirmation to the actual operation and arguments so a later change cannot silently reuse an earlier decision.

### Stage 3: Study retrieval and tenant isolation

Create two fictional tenants with overlapping document titles but different access lists. Preserve tenant and document identifiers through chunking and indexing. Test authorization before retrieval and again when returning or acting on a resource where appropriate. Consider metadata filtering, stale indexes, deleted documents, shared caches, hybrid search, reranking, and citation resolution.

Ask whether an unauthorized document can influence an answer even if its text is not quoted. Consider summaries, titles, embeddings, and search counts as potential disclosure paths. Review ingestion privileges separately from reading privileges. Document who can replace source content and how versioning, provenance, and deletion propagate to derived data.

### Stage 4: Evaluate untrusted content and output handling

Create harmless fixture documents containing conflicting instructions to attempt a mock action that the current user is not allowed to perform. Measure whether the application blocks the action at the policy boundary, whether the model attempted it, and whether the final response accurately describes the outcome. Avoid relying solely on a model refusing the request.

Treat generated HTML, markdown links, SQL, shell suggestions, and file paths as untrusted output. Evaluate their consumers using ordinary application-security principles. Study destination allowlists, output encoding, schema validation, and constrained APIs. Plan bounded resource use for tool loops, document ingestion, long conversations, repeated retries, and expensive searches.

Review memory and conversation reuse. Define which facts may be saved, who can retrieve them, how users remove them, and how account switching affects state. Test synthetic secrets in prompts, retrieval results, logs, error messages, and trace exports.

### Stage 5: Build evaluations that detect regressions

Create a case schema containing scenario identifier, principal, tenant, source documents, allowed actions, prohibited actions, expected evidence, and scoring notes. Include ordinary successful tasks, ambiguity, malformed inputs, permission failures, and conflicting document instructions. Record model identifier, configuration, prompt revision, retrieval version, policy version, and date for every run.

Run cases repeatedly when the system is nondeterministic. Report counts and failure categories rather than claiming safety from a single success. Separate retrieval failures, reasoning mistakes, policy violations, incorrect tool arguments, and misleading final responses. Track legitimate-task success alongside security blocks so a system that refuses everything does not appear effective.

## Worked lab: a two-tenant research assistant

**Setup:** Create ten invented documents for each of two tenants, including similar titles, one deleted document, and one document that contains an instruction-like sentence. Build a local retrieval service and mock tools named by business function, such as reading a project and updating a synthetic task. Tools write only to a disposable local database.

**Actions:** Run a permitted document question, a cross-tenant question, a request involving the deleted document, and a request whose retrieved content suggests an unauthorized task update. Repeat after switching accounts, refreshing the index, and restarting the application. Add one permitted update to confirm the policy still allows normal work.

**Expected behavior:** Retrieval respects the active identity; deleted content is handled according to the documented deletion policy; untrusted content cannot authorize an action; allowed actions produce clear auditable records; denial is reflected truthfully in the answer.

**Evidence:** Save sanitized input/output traces, retrieved document identifiers, authorization decisions, proposed and executed tool arguments, final database state, and aggregate evaluation results. Keep synthetic marker values so accidental cross-tenant influence is easy to recognize.

**Correction:** Fix the actual boundary: identity propagation, filtering, cache partitioning, argument validation, or action authorization. Re-run the entire case suite and compare normal task completion. Prompt wording may improve behavior, but it does not replace an authorization check.

## Blind spots and research gates

A convincing answer can cite an irrelevant document. A blocked final tool call can conceal earlier disclosure in context. A clean index can coexist with stale caches. A passing evaluation may contain familiar examples the implementation was tuned to recognize. Test variations and reserve cases for later evaluation.

- [ ] Demonstrate tenant separation across retrieval, memory, caching, and mock actions.
- [ ] Explain the authority of every input channel and enforce action policy outside generation.
- [ ] Provide repeated-run results with both security outcomes and legitimate-task success.
- [ ] Show document removal propagating through the components you operate.
- [ ] Produce a regression case for every confirmed defect and a traceable corrected result.

**Primary resources:** Use [OWASP's LLM risk catalog](https://genai.owasp.org/llm-top-10/) as a coverage cross-check and [MITRE ATLAS](https://atlas.mitre.org/) to study documented AI-related behaviors. Supplement these with the documentation for your selected model provider, retrieval engine, identity service, and tool framework; record the versions you actually tested.

