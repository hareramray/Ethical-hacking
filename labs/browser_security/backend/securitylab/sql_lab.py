"""SQL injection comparisons against a fresh, bounded in-memory fixture database."""
import json
import math
import sqlite3
from contextlib import closing

from django.http import JsonResponse

MAX_INPUT = 256
MAX_ROWS = 20
FIXED_QUERY = "SELECT id, name, marker FROM catalog WHERE public = 1 AND name = ? ORDER BY id"
CATALOG = (
    (1, "Notebook", "PUBLIC_NOTEBOOK", 1),
    (2, "Reader's guide", "PUBLIC_QUOTED_NAME", 1),
    (3, "Private sample", "PRIVATE_SQL_SENTINEL_ONLY_FOR_LAB", 0),
)
SQL_METADATA = {
    "fixtures": [
        {"id": "normal", "label": "Ordinary product name", "input": "Notebook"},
        {"id": "quoted", "label": "Legitimate name with an apostrophe", "input": "Reader's guide"},
        {"id": "tautology", "label": "OR condition reveals the private fixture", "input": "' OR 1=1 -- "},
        {"id": "missing", "label": "No matching product", "input": "Unknown item"},
    ],
    "inputLimit": MAX_INPUT,
    "rowLimit": MAX_ROWS,
    "catalog": [{"id": row[0], "name": row[1], "public": bool(row[3])} for row in CATALOG],
}


def authorize_fixture_query(action, first, second, database, trigger):
    """No disk attachments, schema reads, functions, pragmas, or write operations."""
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if (action == sqlite3.SQLITE_READ and database == "main" and first == "catalog"
            and second in {"id", "name", "marker", "public", ""}):
        return sqlite3.SQLITE_OK
    # SQLite can report a table-only read with no database name for a join.
    if action == sqlite3.SQLITE_READ and first == "catalog" and second == "" and database is None:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def fixture_connection():
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("PRAGMA temp_store = MEMORY")
        connection.execute("CREATE TABLE catalog (id INTEGER PRIMARY KEY, name TEXT, marker TEXT, public INTEGER)")
        connection.executemany("INSERT INTO catalog VALUES (?, ?, ?, ?)", CATALOG)
        connection.commit()
        connection.execute("PRAGMA query_only = ON")
        # Python disables extension loading by default; keep it explicitly disabled
        # on builds exposing the extension-loading API. SQL functions are also denied.
        if hasattr(connection, "enable_load_extension"):
            connection.enable_load_extension(False)
        for category, value in (
            (sqlite3.SQLITE_LIMIT_LENGTH, 4096),
            (sqlite3.SQLITE_LIMIT_SQL_LENGTH, 4096),
            (sqlite3.SQLITE_LIMIT_EXPR_DEPTH, 30),
            (sqlite3.SQLITE_LIMIT_COMPOUND_SELECT, 5),
            (sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, 16),
            (sqlite3.SQLITE_LIMIT_ATTACHED, 0),
        ):
            connection.setlimit(category, value)
        steps = 0

        def budget():
            nonlocal steps
            steps += 1
            return int(steps > 200)

        connection.set_progress_handler(budget, 100)
        connection.set_authorizer(authorize_fixture_query)
        return connection
    except Exception:
        connection.close()
        raise


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def json_cell(value):
    # Custom UNION inputs can produce blobs or infinite floating-point values.
    # Display those as text instead of returning invalid JSON or a server error.
    if isinstance(value, bytes):
        return "hex:" + value.hex()
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def sql_compare(request):
    """Django's normal CSRF middleware protects this POST endpoint."""
    result = {"mode": None, "input": None, "query": None, "parameters": [], "rows": [],
              "outcome": "invalid", "reason": ""}

    def invalid(reason, status=400):
        result["reason"] = reason
        return JsonResponse(result, status=status)

    if request.method != "POST":
        response = invalid("Use POST with an application/json body.", 405)
        response["Allow"] = "POST"
        return response
    if request.GET:
        return invalid("Send mode and input in the JSON body, without query parameters.")
    if request.content_type != "application/json":
        return invalid("Use an application/json request body.")
    try:
        data = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError):
        return invalid("Invalid JSON or duplicate fields.")
    if not isinstance(data, dict) or set(data) != {"mode", "input"}:
        return invalid("Provide exactly mode and input.")
    if not isinstance(data["mode"], str) or data["mode"] not in {"vulnerable", "fixed"}:
        return invalid("mode must be vulnerable or fixed.")
    result["mode"] = data["mode"]
    value = data["input"]
    if not isinstance(value, str) or not 1 <= len(value) <= MAX_INPUT:
        return invalid("input must contain 1 to 256 characters.")
    if any(ord(character) < 32 or 127 <= ord(character) <= 159 for character in value):
        return invalid("Control characters are not supported in this lesson.")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        return invalid("input must contain valid Unicode characters.")
    result["input"] = value
    if result["mode"] == "fixed":
        query, parameters = FIXED_QUERY, (value,)
    else:
        # Intentionally vulnerable: only the separate fixture boundary constrains it.
        query = "SELECT id, name, marker FROM catalog WHERE public = 1 AND name = '" + value + "' ORDER BY id"
        parameters = ()
    result.update(query=query, parameters=list(parameters))
    try:
        with closing(fixture_connection()) as connection:
            # execute(), never executescript(): one user-influenced statement only.
            rows = connection.execute(query, parameters).fetchmany(MAX_ROWS + 1)
            result["rows"] = [dict(zip(("id", "name", "marker"), map(json_cell, row)))
                              for row in rows[:MAX_ROWS]]
            result["outcome"] = "read"
            result["reason"] = (
                "The name was bound as data; the public-only condition remains part of the query."
                if result["mode"] == "fixed" else
                "Input was concatenated into SQL; it can change the public-only query's meaning."
            )
            if len(rows) > MAX_ROWS:
                result["reason"] += " Results are limited to the first 20 rows."
    except sqlite3.Error as exc:
        result["outcome"] = "query_error"
        result["reason"] = "The fixture query failed: " + str(exc)[:240]
    return JsonResponse(result)
