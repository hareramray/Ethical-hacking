"""Current authorization across a disposable, synchronously drained export queue."""
from contextlib import closing
import json
import sqlite3

from django.http import JsonResponse

ACTOR = {"id": "user-ada", "tenantId": "tenant-blue"}
PEER = {"id": "user-bea", "tenantId": "tenant-blue"}
OTHER_TENANT = {"id": "user-ada", "tenantId": "tenant-amber"}
MARKER = "FICTIONAL-ADA-BLUE-EXPORT"
FIXTURES = {
    "normal": {"label": "Control: permission remains valid", "expectation": "Both paths enqueue, create one fictional export, and deliver its marker to Ada."},
    "revoke-before-worker": {"label": "Revoke after enqueue, before processing", "expectation": "The vulnerable worker trusts its old grant and creates an export. The fixed worker rereads permission and creates no artifact."},
    "revoke-before-download": {"label": "Revoke after processing, before download", "expectation": "Both workers create an artifact while authorized. Only the vulnerable path delivers it after permission is revoked."},
    "peer-download": {"label": "Another owner requests the completed export", "expectation": "Bea has export permission in the same tenant, but does not own Ada's artifact. The fixed download denies the owner mismatch."},
    "cross-tenant-download": {"label": "Same user ID in another tenant requests export", "expectation": "The requester ID matches, but the current tenant does not. The fixed download denies this independent tenant mismatch."},
    "initially-denied": {"label": "Control: no permission at submission", "expectation": "Both paths deny submission. No queued job, artifact, or delivered marker exists."},
}
QUEUE_METADATA = {
    "actor": ACTOR,
    "policy": "Current export permission is required at submission, worker execution, and download; resource/artifact owner and tenant must also match.",
    "fixtures": [{"id": key, **value} for key, value in FIXTURES.items()],
}


def create_store():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript("""
        CREATE TABLE memberships (principal TEXT, tenant TEXT, can_export INTEGER NOT NULL, PRIMARY KEY (principal, tenant));
        CREATE TABLE resources (id INTEGER PRIMARY KEY, owner TEXT NOT NULL, tenant TEXT NOT NULL, marker TEXT NOT NULL);
        CREATE TABLE jobs (id INTEGER PRIMARY KEY, principal TEXT NOT NULL, tenant TEXT NOT NULL, resource_id INTEGER NOT NULL REFERENCES resources(id), granted_at_enqueue INTEGER NOT NULL, state TEXT NOT NULL);
        CREATE TABLE artifacts (job_id INTEGER PRIMARY KEY REFERENCES jobs(id), owner TEXT NOT NULL, tenant TEXT NOT NULL, marker TEXT NOT NULL);
        CREATE TABLE events (sequence INTEGER PRIMARY KEY, stage TEXT NOT NULL, decision TEXT NOT NULL, actor TEXT NOT NULL, tenant TEXT NOT NULL, reason TEXT NOT NULL);
    """)
    connection.executemany("INSERT INTO memberships VALUES (?, ?, ?)", [
        (ACTOR["id"], ACTOR["tenantId"], 1), (PEER["id"], PEER["tenantId"], 1),
        (OTHER_TENANT["id"], OTHER_TENANT["tenantId"], 1),
    ])
    connection.execute("INSERT INTO resources VALUES (1, ?, ?, ?)", (ACTOR["id"], ACTOR["tenantId"], MARKER))
    connection.commit()
    return connection


def check_mode(mode):
    if mode not in ("vulnerable", "fixed"):
        raise ValueError("Unknown handler")


def permitted(connection, actor):
    row = connection.execute("SELECT can_export FROM memberships WHERE principal = ? AND tenant = ?", (actor["id"], actor["tenantId"])).fetchone()
    return bool(row and row["can_export"] == 1)


def owns(row, actor):
    return row is not None and row["owner"] == actor["id"] and row["tenant"] == actor["tenantId"]


def event(connection, stage, decision, actor, reason):
    connection.execute("INSERT INTO events (stage, decision, actor, tenant, reason) VALUES (?, ?, ?, ?, ?)",
                       (stage, decision, actor["id"], actor["tenantId"], reason))


def revoke(connection):
    with connection:
        connection.execute("UPDATE memberships SET can_export = 0 WHERE principal = ? AND tenant = ?", (ACTOR["id"], ACTOR["tenantId"]))
        event(connection, "role change", "revoked", ACTOR, "The stored export permission is now false; any earlier grant is stale.")


def enqueue(connection, mode, actor):
    check_mode(mode)
    with connection:
        resource = connection.execute("SELECT * FROM resources WHERE id = 1").fetchone()
        if not permitted(connection, actor) or not owns(resource, actor):
            event(connection, "enqueue", "denied", actor, "Current export permission and ownership in this tenant are required before inserting any job.")
            return None
        job_id = connection.execute("INSERT INTO jobs (principal, tenant, resource_id, granted_at_enqueue, state) VALUES (?, ?, 1, 1, 'queued')",
                                    (actor["id"], actor["tenantId"])).lastrowid
        event(connection, "enqueue", "queued", actor, "Current permission and resource ownership passed. A job with the submitting principal and tenant was stored.")
        return job_id


def process_job(connection, mode, job_id):
    check_mode(mode)
    with connection:
        job = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if job is None:
            event(connection, "worker", "skipped", ACTOR, "There is no queued job to process.")
            return False
        subject = {"id": job["principal"], "tenantId": job["tenant"]}
        if job["state"] != "queued":
            event(connection, "worker", "skipped", subject, "This job is no longer queued; it cannot create a second artifact.")
            return False
        resource = connection.execute("SELECT * FROM resources WHERE id = ?", (job["resource_id"],)).fetchone()
        authorized = bool(job["granted_at_enqueue"]) if mode == "vulnerable" else permitted(connection, subject) and owns(resource, subject)
        if not authorized or resource is None:
            connection.execute("UPDATE jobs SET state = 'denied' WHERE id = ?", (job_id,))
            event(connection, "worker", "denied", subject, "The worker reread the current permission and resource owner/tenant; authorization failed before artifact creation.")
            return False
        connection.execute("INSERT INTO artifacts VALUES (?, ?, ?, ?)", (job_id, resource["owner"], resource["tenant"], resource["marker"]))
        connection.execute("UPDATE jobs SET state = 'completed' WHERE id = ?", (job_id,))
        event(connection, "worker", "created", subject,
              "An old enqueue grant was trusted without rereading current authorization." if mode == "vulnerable" else
              "The current permission and resource owner/tenant passed. The worker stored one artifact.")
        return True


def download(connection, mode, actor, job_id):
    check_mode(mode)
    with connection:
        artifact = connection.execute("SELECT * FROM artifacts WHERE job_id = ?", (job_id,)).fetchone()
        if artifact is None:
            event(connection, "download", "unavailable", actor, "No stored artifact exists, so no marker can be delivered.")
            return None
        if mode == "fixed" and (not permitted(connection, actor) or not owns(artifact, actor)):
            event(connection, "download", "denied", actor, "Current export permission and the artifact's stored owner and tenant must all match at delivery.")
            return None
        event(connection, "download", "delivered", actor,
              "The artifact was fetched by job ID alone, without current permission or ownership checks." if mode == "vulnerable" else
              "Current permission, artifact owner, and tenant passed at delivery.")
        return artifact["marker"]


def compare_fixture(fixture_id):
    results = {}
    downloader = PEER if fixture_id == "peer-download" else OTHER_TENANT if fixture_id == "cross-tenant-download" else ACTOR
    for mode in ("vulnerable", "fixed"):
        with closing(create_store()) as connection:
            if fixture_id == "initially-denied":
                revoke(connection)
            job_id = enqueue(connection, mode, ACTOR)
            if fixture_id == "revoke-before-worker":
                revoke(connection)
            process_job(connection, mode, job_id)
            if fixture_id == "revoke-before-download":
                revoke(connection)
            marker = download(connection, mode, downloader, job_id)
            jobs = [dict(row) for row in connection.execute("SELECT * FROM jobs ORDER BY id")]
            # Artifact metadata proves creation without presenting an undelivered
            # marker as if the protected download had succeeded.
            artifacts = [dict(row) for row in connection.execute("SELECT job_id, owner, tenant FROM artifacts ORDER BY job_id")]
            results[mode] = {
                "outcome": "delivered" if marker is not None else "denied",
                "jobCount": len(jobs), "artifactCount": len(artifacts),
                "jobState": jobs[0]["state"] if jobs else "absent",
                "submitterPermissionNow": permitted(connection, ACTOR),
                "downloaderPermissionNow": permitted(connection, downloader),
                "deliveredMarker": marker, "jobs": jobs, "artifacts": artifacts,
                "events": [dict(row) for row in connection.execute("SELECT * FROM events ORDER BY sequence")],
            }
    return {"fixture": fixture_id, "actor": ACTOR, "downloader": downloader, "results": results}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def queue_compare(request):
    """The request selects a bounded scenario; identities and state are server-owned."""
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
        return invalid("Provide exactly fixture; identities, permissions, and jobs are server-owned.")
    if not isinstance(body["fixture"], str) or body["fixture"] not in FIXTURES:
        return invalid("Choose a listed queued authorization fixture.")
    return JsonResponse(compare_fixture(body["fixture"]))
