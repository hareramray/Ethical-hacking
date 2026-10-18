"""Actual writes to disposable SQLite profiles, with object and field checks."""
from contextlib import closing
import json
import sqlite3

from django.http import JsonResponse

ACTOR = {"id": "user-ada", "tenantId": "tenant-blue"}
MAX_NAME_LENGTH = 40
COLUMNS = {"displayName": "display_name", "ownerId": "owner_id", "tenantId": "tenant_id", "role": "role"}
FIXTURES = {
    "own": {"label": "Control: edit your display name", "targetId": 101, "patch": {"displayName": "Ada Lovelace"}, "expectation": "Both handlers update Ada's display name. Protected properties remain unchanged."},
    "peer": {"label": "Edit a peer in the same tenant", "targetId": 102, "patch": {"displayName": "Changed by Ada"}, "expectation": "The vulnerable handler edits Bea's profile. The fixed handler denies the object write because Ada is not its owner."},
    "cross-tenant": {"label": "Edit a profile in another tenant", "targetId": 201, "patch": {"displayName": "Changed by Ada"}, "expectation": "The fixed handler denies a different tenant even though this fixture deliberately has a matching owner identifier."},
    "owner": {"label": "Mass assign ownership", "targetId": 101, "patch": {"ownerId": "user-bea"}, "expectation": "Blind assignment transfers the fictional profile. The fixed handler rejects ownerId as a protected property."},
    "tenant": {"label": "Mass assign tenant membership", "targetId": 101, "patch": {"tenantId": "tenant-amber"}, "expectation": "Blind assignment moves the fictional profile. The fixed handler rejects tenantId as a protected property."},
    "role": {"label": "Mass assign a privileged role", "targetId": 101, "patch": {"role": "administrator"}, "expectation": "Blind assignment persists the administrator label. The fixed handler rejects role; this label grants no real lab permissions."},
    "mixed": {"label": "Mix an allowed edit with a protected role", "targetId": 101, "patch": {"displayName": "Name must not partially change", "role": "administrator"}, "expectation": "The fixed handler rejects the entire patch before writing: both the display name and role stay unchanged."},
    "invalid-type": {"label": "Schema: a numeric display name", "targetId": 101, "patch": {"displayName": 17}, "expectation": "The vulnerable handler stores a number. The fixed handler requires a string and leaves the profile unchanged."},
    "too-long": {"label": "Schema: a display name beyond 40 characters", "targetId": 101, "patch": {"displayName": "N" * 41}, "expectation": "The vulnerable handler stores 41 characters. The fixed handler rejects the value before writing."},
}
WRITE_METADATA = {"actor": ACTOR, "editableFields": ["displayName"], "maxNameLength": MAX_NAME_LENGTH,
                  "fixtures": [{"id": key, **value} for key, value in FIXTURES.items()]}


def create_store():
    connection = sqlite3.connect(":memory:", isolation_level=None)
    connection.row_factory = sqlite3.Row
    # display_name intentionally has no affinity, so the invalid-type fixture
    # exposes the stored integer instead of relying on SQLite's text coercion.
    connection.execute("CREATE TABLE profiles (id INTEGER PRIMARY KEY, display_name NOT NULL, owner_id TEXT NOT NULL, tenant_id TEXT NOT NULL, role TEXT NOT NULL)")
    connection.executemany("INSERT INTO profiles VALUES (?, ?, ?, ?, ?)", [
        (101, "Ada", "user-ada", "tenant-blue", "member"),
        (102, "Bea", "user-bea", "tenant-blue", "member"),
        (201, "Ada at Amber", "user-ada", "tenant-amber", "member"),
    ])
    return connection


def read_profile(connection, target_id):
    row = connection.execute("SELECT * FROM profiles WHERE id = ?", (target_id,)).fetchone()
    if row is None:
        return None
    return {"id": row["id"], **{field: row[column] for field, column in COLUMNS.items()}}


def apply_update(connection, mode, actor, target_id, patch):
    """Authorize persisted state and validate the complete patch before writing."""
    if mode not in ("vulnerable", "fixed"):
        raise ValueError("Unknown handler")
    connection.execute("BEGIN IMMEDIATE")
    before = read_profile(connection, target_id)
    outcome, reason, changed = "updated", "", 0
    try:
        if before is None:
            outcome, reason = "denied", "The selected profile is unavailable."
        elif mode == "fixed" and (before["ownerId"] != actor["id"] or before["tenantId"] != actor["tenantId"]):
            outcome, reason = "denied", "The persisted owner and tenant must both match the server-established actor before any write."
        elif mode == "fixed" and (not isinstance(patch, dict) or not patch or set(patch) - {"displayName"}):
            outcome, reason = "rejected", "Only displayName is editable. The entire patch was rejected; no allowed field was partially applied."
        elif mode == "fixed" and (type(patch["displayName"]) is not str or not 1 <= len(patch["displayName"]) <= MAX_NAME_LENGTH or not patch["displayName"].strip()):
            outcome, reason = "rejected", "displayName must be a nonblank string of 1 to 40 characters. No fields were written."
        if outcome != "updated":
            connection.rollback()
        else:
            # Column names come only from this fixed mapping. Values always use
            # SQL parameters; this exercise concerns authorization, not SQLi.
            assignments = ", ".join(f"{COLUMNS[field]} = ?" for field in patch)
            values = list(patch.values()) + [target_id]
            where = "id = ?"
            if mode == "fixed":
                where += " AND owner_id = ? AND tenant_id = ?"
                values += [actor["id"], actor["tenantId"]]
            changed = connection.execute(f"UPDATE profiles SET {assignments} WHERE {where}", values).rowcount
            connection.commit()
            reason = ("The fixture actor is present, so the vulnerable handler blindly binds every supplied property and writes by object ID alone."
                      if mode == "vulnerable" else
                      "The persisted owner and tenant matched. The complete patch passed the field allowlist and value schema before the scoped update committed.")
    except Exception:
        connection.rollback()
        raise
    after = read_profile(connection, target_id)
    return {"outcome": outcome, "before": before, "after": after, "rowsChanged": changed,
            "changedFields": [field for field in COLUMNS if before is not None and before[field] != after[field]], "reason": reason}


def compare_fixture(fixture_id):
    fixture = FIXTURES[fixture_id]
    results = {}
    for mode in ("vulnerable", "fixed"):
        with closing(create_store()) as connection:
            results[mode] = apply_update(connection, mode, ACTOR, fixture["targetId"], fixture["patch"])
    return {"fixture": fixture_id, "actor": ACTOR, "targetId": fixture["targetId"], "patch": fixture["patch"], "results": results}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def write_compare(request):
    """Normal CSRF applies. The HTTP body selects a fixture, never an actor/patch."""
    def invalid(reason, status=400):
        return JsonResponse({"error": reason}, status=status)

    if request.method != "POST":
        response = invalid("Use POST with a JSON fixture identifier.", 405)
        response["Allow"] = "POST"
        return response
    if request.GET or request.content_type != "application/json":
        return invalid("Use application/json without query parameters.")
    if len(request.body) > 2048:
        return invalid("The fixture request is too large.")
    try:
        body = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return invalid("Invalid JSON or duplicate fields.")
    if not isinstance(body, dict) or set(body) != {"fixture"}:
        return invalid("Provide exactly fixture; actors, target IDs, and patches are server-owned.")
    if not isinstance(body["fixture"], str) or body["fixture"] not in FIXTURES:
        return invalid("Choose a listed API write fixture.")
    return JsonResponse(compare_fixture(body["fixture"]))
