# Business logic: a single-use coupon under overlap

This runnable Vue + Django lesson compares a stale check with an atomic conditional update. Each run creates two disposable SQLite databases containing one `DEMO_ONCE` coupon and an empty credit ledger. A successful redemption awards **10 synthetic points**. There are no purchases, real balances, or externally supplied database paths.

Start the application using the [lab README](README.md), open `http://127.0.0.1:8766/`, and select **Business logic & races**. No additional service or dependency is required by this lesson.

## Exercise

1. Select **One legitimate redemption** and compare. Both handlers should commit one credit worth 10 points.
2. Select **Replay after the first attempt finishes**. Both handlers should reject the second attempt and keep the total at 10 points. Passing this test does not establish safety under overlap.
3. Select **Two overlapping attempts**. The vulnerable handler should commit two credits worth 20 points; the fixed handler should commit one credit worth 10 points. Either fixed attempt can win.
4. Inspect the coupon's `used` flag. It is `true` in both stores. The independently queried ledger, with one row for each successful attempt, exposes the duplicate credit that this boolean alone would hide.
5. Run the legitimate case again. Every comparison starts fresh; prior points never carry over.

| Scenario | Vulnerable committed credits | Fixed committed credits |
| --- | --- | --- |
| One attempt | 1 / 10 points | 1 / 10 points |
| Two sequential attempts | 1 / 10 points | 1 / 10 points |
| Two overlapping attempts | 2 / 20 points | 1 / 10 points |

The overlapping scenario uses **two actual Python workers with separate SQLite connections**. A scheduling barrier deliberately makes both vulnerable attempts finish their availability check before either writes. Fixed workers rendezvous before opening their transactions. This instrumentation makes the lesson reproducible; it does not measure whether a particular network request timing would produce a race in another application. A race occurs when concurrent operations can violate an expected rule because coordination is insufficient. [MITRE CWE-362](https://cwe.mitre.org/data/definitions/362.html)

## What changes between the handlers

The vulnerable path reads `used` outside its write transaction:

```python
available = connection.execute(
    "SELECT used FROM coupons WHERE id = ?", ("DEMO_ONCE",)
).fetchone()[0] == 0
# Both overlapping attempts can now have available == True.
if available:
    connection.execute("BEGIN IMMEDIATE")
    connection.execute("UPDATE coupons SET used = 1 WHERE id = ?", ("DEMO_ONCE",))
    connection.execute("INSERT INTO credits VALUES (?, ?)", (attempt_id, 10))
    connection.commit()
```

Even serialized writes can follow the same stale decision. The fixed path puts the eligibility condition into the mutation and checks the affected-row count:

```python
connection.execute("BEGIN IMMEDIATE")
changed = connection.execute(
    "UPDATE coupons SET used = 1 WHERE id = ? AND used = 0", ("DEMO_ONCE",)
).rowcount
if changed == 1:
    connection.execute("INSERT INTO credits VALUES (?, ?)", (attempt_id, 10))
    connection.commit()
else:
    connection.rollback()
```

The implementation also rolls back when the credit insertion fails, keeping coupon consumption and its reward in one transaction. SQLite permits one write transaction at a time; `BEGIN IMMEDIATE` acquires write access before these statements and may report busy when another writer holds it. Connections in this fixture have a half-second lock wait. [SQLite transaction documentation](https://www.sqlite.org/lang_transaction.html)

This is a single-use invariant, not a general idempotency implementation. The lesson does not model order/payment workflows, arbitrary reward values, user-supplied worker counts, multi-service transactions, or retry keys scoped to authenticated accounts. Those require separate exercises and tests.

## Request and resource boundaries

`POST /api/logic/compare/` accepts exactly one JSON field:

```json
{"scenario":"concurrent"}
```

Accepted scenarios are `single`, `sequential`, and `concurrent`. Django's normal CSRF protection applies. Extra fields, duplicate JSON keys, query parameters, other content types, and oversized bodies are rejected before opening a fixture database. The server returns both handlers' committed ledger totals and per-attempt outcomes.

Each concurrent handler uses exactly two workers. Barriers, joins, and SQLite lock waits have timeouts. A per-process limit permits four active comparisons. Failures return an unavailable result instead of presenting a partial comparison as evidence. Connections close and temporary stores are removed after completed or failed runs; no application session or upload database is involved. Operating-system disk stalls are outside the fixture's timing guarantees.

## Verification

From the lab directory:

```powershell
.\.venv\Scripts\python.exe backend\manage.py test securitylab.test_logic_lab
```

The backend tests verify legitimate behavior, sequential replay, the actual two-connection race, independent ledger totals, rollback if credit insertion fails, isolated fresh stores, worker-failure cleanup, lock-wait bounds, concurrency limits, and request/CSRF validation.

For the browser tests, stop any manually running lab pair first so the test launcher can own both ports. From `frontend`:

```powershell
$env:LAB_BROWSER_CHANNEL = 'chrome'
npx playwright test tests/logic.spec.js
```

The three browser cases exercise the legitimate control, sequential replay, forced overlap, and replacement of prior results when changing scenarios. The [README](README.md) explains browser setup and the complete regression suite.
