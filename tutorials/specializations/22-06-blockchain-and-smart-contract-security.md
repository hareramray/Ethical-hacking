# Tutorial: Blockchain and smart-contract security

[Index](../README.md) | [Full source curriculum](../curriculum/specializations/22-06-blockchain-and-smart-contract-security.md) | [Original roadmap](../../roadmaps/specializations/22-06-blockchain-and-smart-contract-security.md)

## Model an escrow before choosing tools

Use only valueless local fixtures in this lesson. Begin with a Python state machine, then implement the same specification on a local development chain if you are learning Solidity. The objective is to define assets, roles, transitions, and invariants, demonstrate a controlled failure, and verify a repair. No wallet containing real funds, mainnet contract, live market, or third-party account is needed.

A blockchain maintains replicated state under a consensus system. A signed transaction requests an exact transition; an application's friendly description is not the authoritative set of parameters. In an Ethereum-style system, externally controlled accounts and contract accounts participate differently in execution. Nonces help order account transactions. Gas bounds and prices execution resources. Persistent storage survives transactions, while temporary execution data has a different lifetime.

A read-only query observes state. A simulated transaction predicts a result under a particular state snapshot. A committed transaction changes the chain's accepted state. Those are different forms of evidence. Application confirmation policies also depend on finality assumptions and possible reorganizations. A transaction receipt is not proof that every associated off-chain workflow completed correctly.

## 1. Specify assets, roles, and state

Define an invented escrow with buyer `Mira`, seller `Dev`, and administrator `Admin`. It holds 100 training units. States are `EMPTY`, `FUNDED`, `RELEASED`, and `CANCELLED`. Only the buyer may fund or cancel under the agreed pre-release policy. Only the buyer may approve release. The administrator may pause new operations but cannot silently redirect the escrow's beneficiary.

Write the intended transitions before implementation:

| Starting state | Action and actor | Next state | Accounting effect |
|---|---|---|---|
| EMPTY | Buyer deposits positive units | FUNDED | Assets and liability increase equally |
| FUNDED | Buyer approves release | RELEASED | Seller receives units; liability becomes zero |
| FUNDED | Buyer cancels when policy permits | CANCELLED | Buyer receives refund; liability becomes zero |
| RELEASED | Any repeat release | Unchanged, denied | No second payment |
| Any state | Unpermitted administrator action | Unchanged, denied | No asset change |

State invariants precisely. Outstanding liabilities must not exceed available assets. Completed escrows cannot be released twice. A denied operation must preserve relevant state. Changing a privileged parameter requires the designated role. A withdrawal must not increase the withdrawing actor's entitlement. Decide which operations remain available while paused instead of assuming pause means every function stops.

On-chain data is generally observable even when a language marks a field `private`; visibility restricts programming access, not public ledger inspection. Event logs support observation, but contract state and transaction semantics determine the application's actual state. Handle repeated submissions and partial off-chain failures explicitly: a UI timeout may occur after a transaction was accepted.

## 2. Demonstrate and repair a controlled authorization flaw

Use this local model to make the policy failure visible without interacting with a chain:

```python
class Escrow:
    def __init__(self):
        self.buyer, self.seller = "Mira", "Dev"
        self.state = "EMPTY"
        self.assets = 0
        self.liability = 0
        self.paid = 0

    def deposit(self, actor, amount):
        if actor != self.buyer or self.state != "EMPTY" or amount <= 0:
            raise ValueError("deposit denied")
        self.assets = self.liability = amount
        self.state = "FUNDED"

    def release_training_bug(self, actor):
        if self.state != "FUNDED":
            raise ValueError("release denied")
        # Deliberate defect: actor authorization is missing.
        self.paid += self.assets
        self.assets = self.liability = 0
        self.state = "RELEASED"

e = Escrow()
e.deposit("Mira", 100)
e.release_training_bug("Observer")
print(e.state, e.paid)
```

The observed `RELEASED 100` violates the defined authorization policy even though the accounting totals happen to balance. This shows why one invariant is insufficient. The minimal sequence is buyer deposit followed by an unauthorized release request.

Repair the first condition to require both `actor == self.buyer` and `state == "FUNDED"`. Repeat the unauthorized request and verify the exception leaves `FUNDED`, 100 assets, and 100 liability. Then release as Mira, expect `RELEASED`, zero liability, and 100 paid. Repeat release and confirm denial without a second payment. Add a cancellation transition with its own actor and state checks, then test release after cancellation.

This model does not implement transaction rollback, cryptographic signatures, tokens, gas, or chain consensus. When porting it to a local contract, tests must verify the actual execution semantics rather than assuming Python behavior is equivalent.

## 3. Learn the contract execution model

In Solidity, distinguish persistent `storage`, temporary `memory`, and input `calldata`. Learn mappings, arrays, structs, visibility, modifiers, inheritance, errors, fallback handling, and external calls. A modifier is a reusable code mechanism; it is only effective if it checks the correct policy and is applied to every relevant entry point.

Write units beside every number. Token decimals, fixed-point scales, time values, percentages, and quantities cannot be mixed casually. With integer arithmetic, `5 * 2 // 3` gives 3 while `(5 // 3) * 2` gives 2; operation order changes rounding. Define who receives a remainder. Compiler-checked arithmetic, unchecked blocks, explicit conversions, and dependency code can have different assumptions. Record compiler version and optimizer settings, then consult warnings and known-bug information for that exact build.

External calls transfer control to another component. Reentrancy is a concern when another call can observe or alter state before an earlier operation has finished establishing its invariant. Study checks, state updates, interactions, and appropriate guards using local fixtures. Also inspect return values, failed calls, callback-capable tokens, fee-on-transfer behavior, rebasing, and decimal assumptions. A “standard token” label does not prove every dependency behaves identically. Solidity's security discussion covers reentrancy, public information, gas-related limitations, and other execution pitfalls. [Solidity security considerations](https://docs.soliditylang.org/en/latest/security-considerations.html)

Ordinary calls and delegated execution use different execution contexts. Proxies depend on implementation code while preserving particular storage and caller behavior. Constructor assumptions do not automatically initialize proxy storage. Review initializer access, repeat initialization, implementation changes, and storage-layout compatibility. A correct implementation integrated incorrectly can still violate application policy.

## 4. Make signatures and dependencies explicit

For a signed authorization fixture, record signer, message fields, intended action, chain context, contract context, nonce, and deadline. A valid signature proves a relationship to signed bytes under an algorithm; it does not by itself establish that the authorization belongs to this chain, contract, or current request. Domain separation and consumed nonces help prevent reuse outside the intended context. Test duplicate, expired, wrong-domain, and changed-argument fixtures locally.

Create a dependency table containing price oracle, update frequency, stale-data policy, token implementation, bridge messages where applicable, sequencer assumptions, administrative keys, and upgrade authority. For the escrow, choose a simple human-approved release condition rather than introducing unnecessary prices. If adding an oracle later, model missing, delayed, and implausible values; do not give every test a convenient perfect price.

Transaction-order dependence is another assumption. Run two deterministic local sequences: cancellation before release, and release before cancellation. Exactly one terminal transition should succeed under the chosen state machine. That teaches ordering without reproducing a strategy against live users. Protocol economics, liquidity, incentives, and external trust are separate from code correctness and need their own models.

Front-running describes acting on knowledge of a pending transaction to obtain an advantageous ordering. For this curriculum, study the concept only through those local sequence permutations. Ask which guarantees should hold regardless of order, which outcomes legitimately depend on the first accepted action, and how the interface communicates that uncertainty. Also bound iteration over stored arrays: an operation that must process an ever-growing list may eventually exceed available execution resources and undermine availability.

Governance operations deserve ordinary authorization tests. Review role grants, revocations, two-step ownership transfer where selected, emergency pause, timelocks, upgrade permission, and incident decision authority. Libraries provide mechanisms, while the application still defines who should hold a role and why. [OpenZeppelin access-control documentation](https://docs.openzeppelin.com/contracts/5.x/api/access)

## 5. Layer the test strategy

Start with unit tests for each transition and expected denial. Test zero, one, a typical amount, a boundary amount, repeated calls, expired approvals, and role changes. Capture pre-state and post-state around every failed action. On a local chain, save receipts and explicitly query relevant storage rather than relying only on emitted events.

Property tests examine many values against a general rule. For example, for every positive deposit in a bounded training range, depositing increases assets and liabilities equally. Invariant tests examine action sequences. Build a handler that chooses legitimate fictional actors and tracks an independent reference ledger. Do not copy the contract's calculation into the reference model; the same bug could then appear in both and pass.

Record how often handlers reach meaningful states and how often calls revert. A suite that silently discards every rejected deposit may never test a funded escrow. Include successful release and cancellation coverage as well as denials. Fuzzing expands input and sequence exploration; it does not prove a property beyond the modeled state and tested conditions.

Use static analysis to generate hypotheses, then confirm reachability, actor permissions, and actual state effects. Manually review external calls and privileged transitions. Compare source, compilation settings, deployment artifacts, and local deployed bytecode. Gas measurements depend on build settings and state, so report their conditions rather than treating one reading as universal.

## 6. Assemble an audit and retest record

For the deliberately flawed release, report the exact function, missing buyer check, funded precondition, unauthorized actor, minimal two-step sequence, observed state change, and repair. Distinguish the violated authorization policy from the accounting invariant that still held. Rerun normal funding, valid release, duplicate release, cancellation, release after cancellation, and unauthorized administration.

Save source revisions, local chain identifier, compiler and optimizer settings, test-token behavior, deployment script, receipts, pre/post state, invariant definitions, patch, and results. Record unsupported scenarios. A stale local fork, a public testnet, and a fresh local chain have different assumptions; this exercise requires only the local environment.

## Questions with answer guidance

1. **Why did balanced accounting fail to catch the bug?** The unauthorized release preserved totals while violating actor policy. Security needs multiple independent invariants.
2. **Can a successful simulation prove a later transaction succeeds?** No. State and ordering may change before commitment.
3. **Why is a proxy initialization review separate from constructor review?** Their execution and storage contexts differ; direct-deployment assumptions may not hold.
4. **What remains outside a passing escrow test suite?** Unmodeled token behavior, governance trust, protocol economics, consensus assumptions, and other dependencies.

Completion means one controlled failure reproduced and repaired with valueless assets, successful ordinary workflows, meaningful unit/property/sequence tests, and an honest inventory of unassessed assumptions. It does not mean a short toy audit establishes safety for a real financial protocol.
