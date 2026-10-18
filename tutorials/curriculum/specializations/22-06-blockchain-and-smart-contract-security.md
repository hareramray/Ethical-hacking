# 22.6 Blockchain and smart-contract security

[All topic roadmaps](../README.md) | [Specialization overview](../22-advanced-specialization-map.md)

<!-- TOPIC-TOC:START -->

## Contents

- [Detailed learning sequence](#detailed-learning-sequence)
  - [Stage 1: Understand state and transaction execution](#stage-1-understand-state-and-transaction-execution)
  - [Stage 2: Learn the language and execution model](#stage-2-learn-the-language-and-execution-model)
  - [Stage 3: Define invariants before finding vulnerabilities](#stage-3-define-invariants-before-finding-vulnerabilities)
  - [Stage 4: Review dependencies, oracles, and governance](#stage-4-review-dependencies-oracles-and-governance)
  - [Stage 5: Build layered testing and review](#stage-5-build-layered-testing-and-review)
- [Worked lab: a local training escrow](#worked-lab-a-local-training-escrow)
- [Debugging blind spots and completion gates](#debugging-blind-spots-and-completion-gates)

<!-- TOPIC-TOC:END -->



**Prerequisites:** Programming, cryptography concepts, distributed systems, and transaction semantics.

- [ ] Learn accounts, keys, signatures, transactions, gas, contract execution, events, storage, oracles, and upgrade/proxy models.
- [ ] Study access control, reentrancy, arithmetic/rounding, signature replay, initialization, oracle assumptions, front-running concepts, economic invariants, and privileged administration.
- [ ] Learn unit, property, invariant, and fuzz testing; distinguish code correctness from protocol-economic assumptions.

**Project:** Audit a toy contract on a local development chain or designated testnet with valueless assets. **Pass:** State invariants, reproduce a controlled failure, repair it, and verify the invariant. Consult [Solidity security considerations](https://docs.solidity.org/en/latest/security-considerations.html); do not use mainnet funds as learning material.

## Detailed learning sequence

### Stage 1: Understand state and transaction execution

Use a local development chain with valueless test accounts. Learn externally controlled accounts, contract accounts, signatures, nonces, transaction ordering, gas, execution, reversion, events, and persistent storage. Distinguish application intent from a signed transaction's exact parameters. Record the chain identifier, compiler version, optimizer settings, and deployed bytecode for every experiment.

- [ ] Trace a transaction from an authorized signer through contract execution to resulting state.
- [ ] Explain the difference between a read-only query, a simulated transaction, and a committed state transition.
- [ ] Understand public visibility of on-chain data, including values declared private at the language level.
- [ ] Explain why event logs support observation but are not always the authoritative application state.
- [ ] Model failed transactions, partial off-chain workflows, and repeated submissions.
- [ ] Distinguish finality assumptions, reorganizations, and application-level confirmation policy.

### Stage 2: Learn the language and execution model

Study storage, memory, calldata, mappings, arrays, structs, visibility, modifiers, inheritance, errors, fallback handling, and external calls. Learn units explicitly: token decimals, fixed-point scaling, timestamps, quantities, and rounding direction. Compare compiler-checked arithmetic with explicit unchecked operations and conversions.

Trace caller identity and execution context through ordinary calls, delegated execution, and proxy patterns. Review initialization and constructor assumptions. Understand that a contract designed for direct deployment may behave differently behind a proxy. Read the compiler's warnings, relevant known-bug information, and dependency release documentation for the exact build.

### Stage 3: Define invariants before finding vulnerabilities

Write properties such as: total recorded balances never exceed available assets; only the designated role can change a parameter; withdrawing cannot increase the caller's entitlement; a signature cannot be reused outside its intended domain; paused state blocks only the operations defined by policy.

Study access control, reentrancy, checks and state updates around external calls, error handling, precision loss, rounding, denial-of-service conditions, and unbounded loops. Consider multi-step sequences and interactions across contracts. A function that looks correct in isolation can violate a system invariant when called after another operation.

For signatures, record signer, message structure, chain and contract context, nonce, deadline, and permitted action. Study replay protection and domain separation. For tokens, review return-value behavior, fee mechanisms, rebasing, callbacks, and decimal assumptions when those behaviors are in scope.

### Stage 4: Review dependencies, oracles, and governance

List every external assumption: price source, update frequency, liquidity, trusted operator, bridge message, sequencer behavior, token implementation, administrative key, and upgrade authority. Distinguish code bugs from economic assumptions and governance decisions. Record how stale or missing information is handled.

Model privileged operations, role transfer, emergency pause, timelocks, upgrade authorization, initializer access, storage-layout compatibility, and incident procedures. Review whether monitoring can observe meaningful state changes and whether the team can act within the design's constraints. Governance controls do not remove the need for correct contract authorization.

Study front-running and transaction-order dependence conceptually using local deterministic fixtures. Avoid copying a public-market strategy into a learning exercise. A local simulation can test whether an invariant depends on ordering without moving real assets or interacting with live users.

### Stage 5: Build layered testing and review

Start with unit tests for individual functions and expected reverts. Add property tests for input ranges and invariant tests for sequences of actions. Create handlers that model legitimate actors and track reference state independently of the contract implementation. Include boundary quantities, zero values, repeated calls, expired approvals, and role changes.

Use static analysis as a source of hypotheses, then confirm each finding against the code and execution path. Examine external calls and state changes manually. Compare source code, compilation settings, artifacts, and deployed bytecode in your own environment. Record unreachable or unsupported scenarios rather than forcing a false positive into the report.

## Worked lab: a local training escrow

**Setup:** Implement a small escrow with fictional users, a test token, a release condition, cancellation rules, and a designated administrator. Use a local chain and freshly generated training keys. Write the intended state machine and balance invariants before coding tests.

**Actions:** Exercise deposit, release, cancellation, unauthorized administration, duplicate requests, and zero or boundary amounts. Add a deliberately flawed training branch with an incorrect authorization or accounting check. Build a sequence test that demonstrates the invariant failure, then reduce it to the smallest meaningful action sequence.

**Expected behavior:** Only permitted actors perform each transition; recorded liabilities match the intended accounting model; completed escrows cannot be released twice; failed actions leave the relevant state consistent; the corrected branch passes both normal and adversarial local fixtures.

**Evidence:** Keep source and compiler settings, deployment script, local chain configuration, transaction receipts, pre/post state, invariant definitions, failing sequence, patch, and test results. Explain why the demonstrated sequence is possible within the toy contract's rules.

**Correction:** Fix the relevant authorization, state transition, or arithmetic assumption. Retest neighboring states and legitimate workflows. If using a library, verify the correct integration and version assumptions instead of assuming the dependency automatically enforces the application's policy.

## Debugging blind spots and completion gates

A test can pass because it never generated a meaningful state. A handler may silently discard reverted calls and hide a coverage gap. An oracle mock may be too convenient. A local fork's state can become stale, and public test networks can have different operational conditions from a local chain. Gas measurements depend on compiler settings and state.

- [ ] Explain the system's state machine, assets, roles, and external assumptions.
- [ ] Produce unit, property, and sequence-based invariant tests.
- [ ] Demonstrate one controlled failure and its verified repair using valueless assets.
- [ ] Review initialization, privileged administration, upgrades, and emergency behavior.
- [ ] Deliver findings with exact code references, preconditions, impact reasoning, and minimal local evidence.
- [ ] State what was not assessed, including protocol economics and external dependency trust.

**Primary resources:** Study [Solidity security considerations](https://docs.soliditylang.org/en/latest/security-considerations.html) and [OpenZeppelin Contracts documentation](https://docs.openzeppelin.com/contracts/). Treat these as reference material for specific mechanisms and integration patterns, and use your chosen development framework's official testing documentation for reproducible local experiments.

