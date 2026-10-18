"""Read-only authorization examples over synthetic records and practice personas."""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect


ACTORS = {
    "alice": {"id": "alice", "name": "Alice", "tenant": "team-a", "role": "member"},
    "bob": {"id": "bob", "name": "Bob", "tenant": "team-a", "role": "member"},
    "carol": {"id": "carol", "name": "Carol", "tenant": "team-b", "role": "member"},
    "admin-a": {"id": "admin-a", "name": "Admin A", "tenant": "team-a", "role": "admin"},
}
RECORDS = {
    "alice-a": {"id": "alice-a", "ownerId": "alice", "tenant": "team-a", "marker": "ALICE_PRIVATE_LAB_RECORD"},
    "bob-a": {"id": "bob-a", "ownerId": "bob", "tenant": "team-a", "marker": "BOB_PRIVATE_LAB_RECORD"},
    "carol-b": {"id": "carol-b", "ownerId": "carol", "tenant": "team-b", "marker": "CAROL_PRIVATE_LAB_RECORD"},
}
ACCESS_METADATA = {
    "actors": [*ACTORS.values(), {"id": "anonymous", "name": "Anonymous", "tenant": None, "role": None}],
    "records": [{key: value for key, value in record.items() if key != "marker"} for record in RECORDS.values()],
}


def respond(data, status=200, allow=None):
    response = JsonResponse(data, status=status)
    response["Cache-Control"] = "no-store"
    if allow:
        response["Allow"] = allow
    return response


def current_actor_id(request):
    actor_id = request.session.get("lab_actor", "anonymous")
    return actor_id if isinstance(actor_id, str) and actor_id in ACTORS else "anonymous"


def access_state(request):
    if request.method != "GET":
        return respond({"error": "Use GET for practice identity state."}, 405, "GET")
    if request.GET:
        return respond({"error": "State does not accept query parameters."}, 400)
    return respond({"actorId": current_actor_id(request), **ACCESS_METADATA})


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


@csrf_protect
def access_identity(request):
    """A deliberately exposed teaching control, never a real login endpoint."""
    if request.method != "POST":
        return respond({"error": "Use POST to choose a practice identity."}, 405, "POST")
    if request.GET or request.content_type != "application/json" or len(request.body) > 1024:
        return respond({"error": "Send a small JSON object with only actorId; no query parameters."}, 400)
    try:
        data = json.loads(request.body, object_pairs_hook=unique_json_object)
    except (ValueError, UnicodeDecodeError):
        return respond({"error": "Send valid JSON with unique fields."}, 400)
    if not isinstance(data, dict) or set(data) != {"actorId"}:
        return respond({"error": "Only the actorId field is accepted."}, 400)
    actor_id = data["actorId"]
    if not isinstance(actor_id, str) or actor_id not in {*ACTORS, "anonymous"}:
        return respond({"error": "Choose a known practice identity."}, 400)
    request.session["lab_actor"] = actor_id
    return respond({"actorId": actor_id, **ACCESS_METADATA})


def access_record(request):
    mode = request.GET.get("mode", "fixed")
    record_id = request.GET.get("record", "alice-a")
    action = request.GET.get("action", "read")
    actor = ACTORS.get(current_actor_id(request))
    result = {"mode": mode, "actor": actor, "recordId": record_id, "action": action,
              "outcome": "invalid", "reason": "", "record": None}

    def finish(outcome, reason, status, record=None, allow=None):
        result.update(outcome=outcome, reason=reason, record=record)
        return respond(result, status, allow)

    if request.method != "GET":
        return finish("invalid", "Use GET; both actions are read-only.", 405, allow="GET")
    if any(key not in {"mode", "record", "action"} or len(request.GET.getlist(key)) != 1 for key in request.GET):
        return finish("invalid", "Use one mode, record and action. Roles and tenants come from the server.", 400)
    if mode not in {"vulnerable", "fixed"} or action not in {"read", "review"} or not 1 <= len(record_id) <= 64:
        return finish("invalid", "Choose vulnerable or fixed, a record ID, and read or review.", 400)
    if actor is None:
        return finish("unauthenticated", "Choose a signed-in practice persona. Both handlers require an identity.", 401)
    record = RECORDS.get(record_id)
    if record is None:
        return finish("not_found", "No synthetic record has that ID.", 404)
    if mode == "vulnerable":
        return finish("allowed", "Only identity was checked; ownership, tenant and role were ignored.", 200, record)

    same_tenant = actor["tenant"] == record["tenant"]
    tenant_admin = same_tenant and actor["role"] == "admin"
    owner = same_tenant and actor["id"] == record["ownerId"]
    if action == "review" and not tenant_admin:
        return finish("denied", "Review requires an administrator in this record's tenant.", 403)
    if action == "read" and not (owner or tenant_admin):
        return finish("denied", "Read requires ownership or an administrator in this record's tenant.", 403)
    return finish("allowed", "The server verified the identity, tenant and required permission before returning the record.", 200, record)
