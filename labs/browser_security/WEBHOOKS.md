# Webhook authenticity, freshness, and replay protection

This runnable Vue + Django lesson compares two handlers that receive locally signed, predefined point-credit events. Both use real HMAC-SHA256 verification and real SQLite writes. The vulnerable handler validates signatures and event data but omits freshness and event-ID deduplication. The fixed handler adds both and commits the event claim and point credit together.

Start the [browser security lab](README.md) from the repository root:

```powershell
python labs/browser_security/run_lab.py
```

Open **http://127.0.0.1:8766/**, select **Webhook replay protection**, choose a fixture, and click **Compare deliveries**. Inspect each ledger balance, delivery result, and recorded event ID. Expand **Inspect signed delivery bytes** to compare the exact body and signature.

| Fixture | Signature only | Freshness and event IDs |
| --- | --- | --- |
| One valid event | Credits 10 points | Credits 10 points |
| Body changed after signing | Rejects; zero points | Rejects; zero points |
| Valid signature, old timestamp | Credits 10 points | Rejects; zero points |
| Replay the identical delivery | Credits 20 points | Credits once; 10 points |
| Fresh signature, same event ID | Credits 20 points | Credits once; 10 points |
| Two distinct valid events | Credits 20 points | Credits 20 points |
| Valid signature, future timestamp | Credits 10 points | Rejects; zero points |
| Valid signature, invalid event data | Rejects; zero points | Rejects; zero points |

The normal and distinct-event fixtures are positive controls. A repair that blocks every delivery would fail them. The body-tampering control shows that the intentionally vulnerable implementation still verifies signatures: the weakness here is accepting an authentic delivery more than once, or outside its intended time window.

## What the signature proves

For this lesson, the signed message is the decimal ASCII timestamp, one literal period, and the exact UTF-8 body bytes:

```python
message = str(timestamp).encode("ascii") + b"." + raw_body
signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
valid = hmac.compare_digest(expected_signature, received_signature)
```

The [implementation](backend/securitylab/webhook_lab.py) creates a fresh 32-byte secret for every comparison and uses the same secret and deliveries for both handlers. The secret is not returned to the browser. Changing the body, including JSON whitespace, or changing the timestamp invalidates its existing signature. Verification happens before JSON parsing or consulting event IDs. Python provides [`hmac.compare_digest`](https://docs.python.org/3/library/hmac.html#hmac.compare_digest) for digest comparison without content-dependent early exit.

This is a **local teaching contract**, not an implementation of every provider's protocol. Real integrations must follow the provider's header parsing, key management, signing, and timestamp rules. For example, [Stripe's webhook documentation](https://docs.stripe.com/webhooks#preventing-replay-attacks) explains its signed timestamps and notes that retry deliveries receive new timestamps and signatures. The lesson does not implement Stripe's complete header format, key rotation, or SDK.

## Freshness and event identity solve different problems

The fixed handler accepts a signed timestamp only when `abs(now - timestamp) <= 300`. The comparison captures one server clock value and evaluates both handlers against it. The old and future fixtures sit one second outside the allowed window; tests also cover both inclusive boundaries. A real service needs an accurate clock and a tolerance suited to its provider and delivery contract.

An identical replay inside that window still has a valid signature. A legitimate retry can also be freshly signed while carrying the same event ID. Therefore the fixed handler records `(provider, event_id)` after signature verification, freshness checking, and schema validation. The provider comes from trusted handler configuration, not a field chosen by the event body.

The allowed event has exactly `id`, `type`, `account`, and `units`: a bounded `evt_...` identifier, the `points.credit` type, the fictional `DEMO_ACCOUNT`, and an integer from 1 to 100. Booleans, extra or duplicate fields, unsupported accounts, and unsupported event types fail validation. Both handlers apply this schema so the comparison isolates the missing replay defenses. A signed but invalid event never reserves its ID.

[Stripe's duplicate-event guidance](https://docs.stripe.com/events/manage-webhook-endpoints#handle-duplicate-events) describes tracking processed event IDs. It also discusses cases where distinct event objects can refer to the same underlying operation. This lesson models one credit per unique event ID; it does not establish a universal business idempotency key for real payment or fulfillment systems.

## Commit the claim and side effect together

Each handler gets its own fresh in-memory SQLite database. The fixed path executes these operations in one transaction:

```sql
BEGIN IMMEDIATE;
INSERT INTO processed_events (provider, event_id) VALUES (?, ?)
    ON CONFLICT (provider, event_id) DO NOTHING;
-- If no row was inserted, roll back and report a duplicate.
UPDATE ledger SET balance = balance + ? WHERE id = 1;
COMMIT;
```

The composite primary key enforces uniqueness. The implementation rolls back both operations if the credit fails. Recording the event before an unrelated transaction could lose a legitimate retry; applying the credit before separately recording the event could repeat it after a crash. Explicit transaction handling keeps the local claim and ledger effect together; see [Python's SQLite transaction control](https://docs.python.org/3/library/sqlite3.html#transaction-control).

The displayed point balances are read from SQLite, not inferred from the expected fixture outcome. A duplicate reports no balance change. It represents an already handled event that a receiver can acknowledge successfully without repeating the business effect; this dashboard does not perform an external HTTP delivery or return provider acknowledgments.

Deliveries in the lesson are sequential. A backend test forces a real SQLite failure with a trigger, verifies rollback of both the claim and credit, removes the trigger, and successfully retries the event. The tests do not demonstrate concurrent webhook workers, distributed transactions, or exactly-once network delivery. Real databases must retain deduplication state across requests and restarts. Queued work and external effects need their own durable idempotency and recovery design.

## API and exercise boundaries

The browser sends `POST /api/webhook/compare/` with exactly one JSON selector, for example:

```json
{"fixture":"resigned-retry"}
```

The other identifiers are `normal`, `body-tampered`, `stale`, `duplicate`, `distinct-events`, `future`, and `invalid-schema`. Success returns HTTP 200 with `fixture`, `expectation`, `clock`, `windowSeconds`, `signingFormat`, and `results.vulnerable` / `results.fixed`. Each result contains the before/after balance, recorded event IDs, explanatory text, and one or two delivery receipts. Receipts show signature validity, the validated event ID when reached, exact body text, timestamp, signature, decision, and balance change.

Unknown selectors, arbitrary event bodies, URLs, secrets, query parameters, extra or duplicate JSON fields, malformed JSON, and request bodies over 2,048 bytes are rejected. Unsupported methods return HTTP 405. A ledger failure returns HTTP 503 without a partial comparison. Each comparison closes its disposable databases; no state persists between clicks. Body and signature evidence are rendered as inert Vue text.

This endpoint is a **browser-operated lesson harness**, so ordinary Django CSRF protection remains enabled. It is not a provider-facing webhook endpoint. An actual provider receiver authenticates provider deliveries according to that provider's protocol; browser CSRF tokens are not provider credentials. Scope any framework CSRF exception to the actual receiver, retaining CSRF protection on browser actions. [Provider endpoint guidance](https://docs.stripe.com/events/manage-webhook-endpoints#exempt-webhook-route-from-csrf-protection) explains that distinction.

All events and signatures are created locally, all points are fictional, and no network requests leave the comparison. The fixture selector bounds the exercise. It does not accept arbitrary signatures, event payloads, secrets, or delivery destinations.

## Verification

The [backend tests](backend/securitylab/test_webhook_lab.py) exercise real HMAC calculation, exact-byte and timestamp tampering, constant-time comparison use, positive controls, past/future freshness boundaries, exact replay, fresh re-signing, schema validation, provider-scoped uniqueness, transaction rollback, request isolation, selector rejection, and CSRF. The [browser tests](frontend/tests/webhook.spec.js) check the visible balances and decisions, inspect inert body evidence, compare retry signatures, and confirm that switching fixtures clears previous results.

Run the focused backend tests from `labs/browser_security`:

```powershell
.venv/Scripts/python.exe backend/manage.py test securitylab.test_webhook_lab
```

To run the full browser/backend suite, stop the lab servers on ports 8766 and 8767, then run from the repository root:

```powershell
$env:LAB_BROWSER_CHANNEL = 'chrome'
python labs/browser_security/run_lab.py --test
Remove-Item Env:LAB_BROWSER_CHANNEL
```

For a useful observation record, compare the event IDs, timestamps, signatures, and resulting ledger balances for **identical replay**, **freshly signed retry**, and **distinct valid events**. The first two must credit only once in the fixed handler; the last must still credit twice.
