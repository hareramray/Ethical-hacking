"""Disposable application-cache comparisons using server-owned fictional identities."""
from copy import deepcopy
import json

from django.http import JsonResponse

PRIVATE_ROUTE = "/account/summary/"
PUBLIC_ROUTE = "/catalog/"
ACTORS = {
    "ada": {"id": "user-ada", "tenant": "tenant-blue", "marker": "PRIVATE_ADA_BLUE"},
    "bea": {"id": "user-bea", "tenant": "tenant-blue", "marker": "PRIVATE_BEA_BLUE"},
    "cy": {"id": "user-cy", "tenant": "tenant-amber", "marker": "PRIVATE_CY_AMBER"},
    "anonymous": {"id": "anonymous", "tenant": None, "marker": None},
}
FIXTURES = {
    "private-control": {
        "label": "Control: Ada requests her summary twice",
        "sequence": ["Ada requests her private summary", "Ada requests her private summary again"],
        "steps": [("request", "ada", PRIVATE_ROUTE), ("request", "ada", PRIVATE_ROUTE)],
        "expectation": "Both paths return Ada's marker. The vulnerable path stores it globally; the fixed path reads the origin twice and never stores private content.",
    },
    "cross-user": {
        "label": "Two users, the same private URL",
        "sequence": ["Ada requests her private summary", "Bea requests her own summary at the same URL"],
        "steps": [("request", "ada", PRIVATE_ROUTE), ("request", "bea", PRIVATE_ROUTE)],
        "expectation": "Bea receives Ada's marker from the vulnerable cache. The fixed path returns Bea's own marker and stores neither response.",
    },
    "cross-tenant": {
        "label": "Two tenants, the same private URL",
        "sequence": ["Ada in tenant-blue requests her summary", "Cy in tenant-amber requests their own summary at the same URL"],
        "steps": [("request", "ada", PRIVATE_ROUTE), ("request", "cy", PRIVATE_ROUTE)],
        "expectation": "A path-only cache key crosses the tenant boundary. The fixed path returns Cy's own tenant-amber marker.",
    },
    "revoked": {
        "label": "Permission removed after a private response",
        "sequence": ["Ada requests her private summary", "Remove Ada's summary permission", "Ada requests the summary again"],
        "steps": [("request", "ada", PRIVATE_ROUTE), ("revoke", "ada", None), ("request", "ada", PRIVATE_ROUTE)],
        "expectation": "The vulnerable cache hit bypasses Ada's revoked permission. The fixed handler denies the second request before any cache or origin read.",
    },
    "logout": {
        "label": "Anonymous request after Ada logs out",
        "sequence": ["Ada requests her private summary", "A subsequent request has no authenticated identity"],
        "steps": [("request", "ada", PRIVATE_ROUTE), ("request", "anonymous", PRIVATE_ROUTE)],
        "expectation": "The vulnerable global entry exposes Ada's marker to an anonymous request. The fixed handler denies the anonymous request.",
    },
    "public-control": {
        "label": "Control: shared public catalog stays cacheable",
        "sequence": ["Ada requests the public catalog", "An anonymous visitor requests the same public catalog"],
        "steps": [("request", "ada", PUBLIC_ROUTE), ("request", "anonymous", PUBLIC_ROUTE)],
        "expectation": "Both paths store one public response and serve a real cache HIT on the second request, with only one origin read.",
    },
}
CACHE_METADATA = {
    "fixtures": [{"id": key, **{field: value for field, value in fixture.items() if field != "steps"}}
                 for key, fixture in FIXTURES.items()],
    "privateRoute": PRIVATE_ROUTE,
    "publicRoute": PUBLIC_ROUTE,
    "actors": list(ACTORS.values()),
}


class MemoryCache:
    """An actual cache shared by the fictional requests in one comparison mode."""

    def __init__(self):
        self.entries = {}
        self.lookups = 0
        self.writes = 0
        self.origin_reads = 0
        self.trace = []

    def get(self, key):
        self.lookups += 1
        hit = key in self.entries
        self.trace.append({"operation": "cache-lookup", "key": key, "hit": hit})
        return deepcopy(self.entries[key]) if hit else None

    def put(self, key, response):
        self.entries[key] = deepcopy(response)
        self.writes += 1
        self.trace.append({"operation": "cache-store", "key": key, "marker": response["marker"]})

    def snapshot(self):
        return [{"key": key, **deepcopy(response)} for key, response in self.entries.items()]


def is_allowed(actor_id, route, permissions):
    return route == PUBLIC_ROUTE or (actor_id != "anonymous" and actor_id in permissions)


def serve_request(cache, mode, actor_id, route, permissions):
    if mode not in ("vulnerable", "fixed") or actor_id not in ACTORS or route not in (PRIVATE_ROUTE, PUBLIC_ROUTE):
        raise ValueError("Only server-owned cache fixtures are supported")
    actor = ACTORS[actor_id]
    private = route == PRIVATE_ROUTE
    expected_allowed = is_allowed(actor_id, route, permissions)
    evidence = {
        "actor": actor["id"], "tenant": actor["tenant"], "route": route,
        "permissionNow": expected_allowed, "status": 200, "cacheStatus": "NOT_CHECKED",
        "lookupKey": None, "storedKey": None, "originRead": False,
        "authorization": "not checked", "returnedMarker": None, "disclosed": False,
    }

    def authorize():
        allowed = is_allowed(actor_id, route, permissions)
        evidence["authorization"] = "allowed" if allowed else "denied"
        cache.trace.append({"operation": "authorize", "actor": actor["id"], "allowed": allowed})
        if not allowed:
            evidence["status"] = 403
            evidence["reason"] = "The current fictional identity has no permission; no content was returned."
        return allowed

    # This check is deliberately before any cached data can be returned.
    if mode == "fixed" and not authorize():
        return evidence

    if mode == "fixed" and private:
        evidence["cacheStatus"] = "BYPASS"
        cache.trace.append({"operation": "private-cache-bypass", "route": route})
        key = None
        response = None
    else:
        key = route if mode == "vulnerable" else "lab:v1:public:" + route
        evidence["lookupKey"] = key
        response = cache.get(key)
        evidence["cacheStatus"] = "HIT" if response is not None else "MISS"

    if response is None:
        if mode == "vulnerable" and not authorize():
            return evidence
        cache.origin_reads += 1
        evidence["originRead"] = True
        response = {"marker": actor["marker"] if private else "PUBLIC_CATALOG",
                    "visibility": "private" if private else "public",
                    "owner": actor["id"] if private else None}
        cache.trace.append({"operation": "origin-read", "route": route, "marker": response["marker"]})
        if key is not None:
            cache.put(key, response)
            evidence["storedKey"] = key
    elif mode == "vulnerable":
        evidence["authorization"] = "skipped on cache hit"

    evidence["returnedMarker"] = response["marker"]
    evidence["disclosed"] = private and (not expected_allowed or response["owner"] != actor["id"])
    if evidence["disclosed"]:
        evidence["reason"] = "A global cache hit returned a private marker that this request may not receive."
    elif private and mode == "fixed":
        evidence["reason"] = "Current permission passed. This private response bypassed shared storage and came from the origin."
    elif not private:
        evidence["reason"] = "This public response is identical for every visitor and may be shared."
    else:
        evidence["reason"] = "Ada receives her own marker in this control, but the global entry remains available to later identities."
    return evidence


def compare_fixture(fixture_id):
    results = {}
    for mode in ("vulnerable", "fixed"):
        cache = MemoryCache()
        permissions = {"ada", "bea", "cy"}
        requests = []
        for action, actor, route in FIXTURES[fixture_id]["steps"]:
            if action == "revoke":
                permissions.discard(actor)
                cache.trace.append({"operation": "permission-revoked", "actor": ACTORS[actor]["id"]})
            else:
                requests.append(serve_request(cache, mode, actor, route, permissions))
        results[mode] = {
            "outcome": "exposed" if any(request["disclosed"] for request in requests) else "no disclosure",
            "requests": requests,
            "lookups": cache.lookups, "writes": cache.writes, "originReads": cache.origin_reads,
            "entries": cache.snapshot(), "trace": cache.trace,
        }
    return {"fixture": fixture_id, "results": results}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def cache_compare(request):
    """The request selects a fixture; it cannot supply identities, URLs or content."""
    def invalid(message, status=400):
        return JsonResponse({"error": message}, status=status)

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
        return invalid("Provide exactly fixture; identities, cache keys and routes are server-owned.")
    if not isinstance(body["fixture"], str) or body["fixture"] not in FIXTURES:
        return invalid("Choose a listed cache fixture.")
    return JsonResponse(compare_fixture(body["fixture"]))
