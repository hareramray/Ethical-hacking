# SQL injection: compare concatenation and parameters

This Vue + Django lesson searches a real SQLite database containing three synthetic products. The intended feature returns public products only. Compare a vulnerable query that concatenates input with a fixed query that binds input as data, then verify that ordinary searches still work.

## Start the lesson

From the repository root:

```powershell
python labs/browser_security/run_lab.py --setup
python labs/browser_security/run_lab.py
```

For an existing installation, rebuild with `python labs/browser_security/run_lab.py --build` and restart the server. Open **http://127.0.0.1:8766/** and select **SQL injection**. See the [lab guide](README.md) for prerequisites.

1. Choose **Ordinary product name** and compare. Both handlers return `Notebook` with `PUBLIC_NOTEBOOK`.
2. Choose **OR condition reveals the private fixture**. The input is `' OR 1=1 -- `, including a trailing space. The concatenated query returns all three synthetic records, including `PRIVATE_SQL_SENTINEL_ONLY_FOR_LAB`. The parameterized query returns no rows.
3. Inspect **Executed SQL** and **Bound parameters**. In fixed mode, the statement retains `name = ?`; the entire supplied string appears in the separate parameters list.
4. Choose **Legitimate name with an apostrophe**. `Reader's guide` causes a syntax error in the vulnerable query, but the fixed query returns `PUBLIC_QUOTED_NAME`.
5. Choose **No matching product**. Both handlers return no rows. A successful request with no result is distinct from a failed query.

| Input | Vulnerable result | Fixed result |
| --- | --- | --- |
| `Notebook` | One public record | Same public record |
| `Reader's guide` | Query error | Public record with an apostrophe |
| `' OR 1=1 -- ` | All three fixture records | No matching record |
| `Private sample` | No matching public record | No matching public record |
| `Unknown item` | No matching record | No matching record |

All query text, parameters, and rows render as text in the dashboard. This is a server-side SQL lesson; changing a browser CSP mode does not repair the database query.

## Inspect the repair

The [handler](backend/securitylab/sql_lab.py) constructs this intentionally vulnerable statement:

```python
query = "SELECT id, name, marker FROM catalog WHERE public = 1 AND name = '" + value + "' ORDER BY id"
rows = connection.execute(query).fetchall()
```

The fixture closes the quoted value, introduces an always-true `OR` condition, and comments out the remaining text. The input changes the query's logic, so its intended public-only restriction no longer holds.

The repair keeps the SQL and value separate:

```python
query = "SELECT id, name, marker FROM catalog WHERE public = 1 AND name = ? ORDER BY id"
rows = connection.execute(query, (value,)).fetchall()
```

Python's SQLite API supports placeholders for bound values and recommends them instead of formatting input into statements. Parameters represent values; they do not supply table names, column names, or arbitrary SQL syntax. See [Python's placeholder guidance](https://docs.python.org/3/library/sqlite3.html#how-to-use-placeholders-to-bind-values-in-sql-queries). The actual handler fetches at most 21 rows and returns at most 20, instead of the unbounded `fetchall()` used in these short excerpts.

Parameters preserve query structure. They do not supply a missing authorization condition: the fixed query still explicitly includes `public = 1`. This direct `sqlite3` example is also distinct from Django's ORM and Django cursor placeholder conventions.

## API and exercise boundaries

The UI sends `POST /api/sql/` with JSON containing exactly `mode` (`vulnerable` or `fixed`) and `input` (1–256 characters). Django's CSRF protection remains enabled; the UI obtains its token from the existing bootstrap endpoint and sends `X-CSRFToken`.

Responses show the mode, input, executed query, separate parameters, returned rows, outcome, and reason. Normal results and query errors use HTTP 200 because the comparison itself completed; inspect `outcome`, which is `read` or `query_error`. Invalid inputs use HTTP 400 with `outcome: invalid`. Missing CSRF protection produces HTTP 403; unsupported methods produce HTTP 405. Control characters, duplicate JSON fields, extra body fields, and URL query parameters are rejected.

Each request creates a fresh `:memory:` database and closes it afterward. The application's Django database is never queried by this lesson. A separate SQLite authorizer permits only SELECT operations and reads from the synthetic catalog. Attachments, schema reads, pragmas, mutations, and SQL functions are denied after fixture setup; extension loading remains disabled. The query uses one `execute()` call, a progress budget, SQL limits, memory-only temporary storage, and bounded output. These are exercise boundaries, independent of the parameterization repair. The private sentinel is deliberately readable through the vulnerable SELECT.

This lesson covers a predicate bypass and a legitimate quoted name. It does not demonstrate real-account login bypass, filesystem reads, extensions, time delays, destructive writes, or every SQL dialect. SQLite syntax and driver behavior differ from other databases. The [SQLite connection API](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.set_authorizer) documents the authorizer and other callbacks used to constrain this example.

## Verify the behavior

The [backend tests](backend/securitylab/test_sql_lab.py) exercise real queries, bound values, CSRF, invalid inputs, connection cleanup, denied operations, and the progress budget. The [browser tests](frontend/tests/sql.spec.js) compare both handlers and confirm inert text rendering. Stop the lab on ports 8766 and 8767, then run:

```powershell
$env:LAB_BROWSER_CHANNEL = 'chrome'
python labs/browser_security/run_lab.py --test
Remove-Item Env:LAB_BROWSER_CHANNEL
```

Record the input, both query forms, both result sets, the missing separation between data and syntax, and the successful apostrophe search after the repair. No fixture reset is needed because requests never share this temporary database.
