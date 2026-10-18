"""Execute fixed GraphQL documents against disposable, fictional tenant records."""
from copy import deepcopy
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from graphql import GraphQLError, build_schema, execute_sync, parse, specified_rules, validate
from graphql.validation import ValidationRule


FIELD_BUDGET = 12
ACTOR = {"id": "ada", "tenant": "blue", "role": "member"}
DOCUMENTS = {
    "blue-note": {"id": "blue-note", "tenant": "blue", "owner": "ada", "title": "Blue notebook",
                  "marker": "FICTIONAL_BLUE_MARKER", "adminNote": "FICTIONAL_BLUE_ADMIN_NOTE", "related": "amber-note"},
    "amber-note": {"id": "amber-note", "tenant": "amber", "owner": "cy", "title": "Amber notebook",
                   "marker": "FICTIONAL_AMBER_MARKER", "adminNote": "FICTIONAL_AMBER_ADMIN_NOTE", "related": "blue-note"},
}
FIXTURES = {
    "allowed": {
        "label": "Control: read an allowed tenant document",
        "query": "query Read($id: ID!) { document(id: $id) { id title marker } }",
        "variables": {"id": "blue-note"},
        "expectation": "Both executors return the fictional blue marker with no GraphQL errors.",
    },
    "nested-tenant": {
        "label": "Nested relation crosses a tenant boundary",
        "query": "query Nested { document(id: \"blue-note\") { id relatedDocument { id marker } } }",
        "variables": {},
        "expectation": "The fixed nested resolver refuses the amber document. The allowed blue parent remains in data, with a GraphQL error at document.relatedDocument.",
    },
    "protected-field": {
        "label": "Allowed object contains an administrator-only field",
        "query": "query Field { document(id: \"blue-note\") { id title adminNote } }",
        "variables": {},
        "expectation": "The fixed executor returns the allowed title but nulls adminNote and records a field-permission error for this member.",
    },
    "own-mutation": {
        "label": "Control: rename your own document",
        "query": "mutation Rename($id: ID!, $title: String!) { renameDocument(id: $id, title: $title) { id title } }",
        "variables": {"id": "blue-note", "title": "HARMLESS_RENAMED_NOTE"},
        "expectation": "Both paths rename Ada's own blue note exactly once. A new comparison resets both stores.",
    },
    "forbidden-mutation": {
        "label": "Attempt to rename another tenant's document",
        "query": "mutation Rename($id: ID!, $title: String!) { renameDocument(id: $id, title: $title) { id title } }",
        "variables": {"id": "amber-note", "title": "HARMLESS_RENAMED_NOTE"},
        "expectation": "The vulnerable resolver changes the amber title. The fixed resolver checks ownership and tenant before writing; before and after remain equal.",
    },
    "aliases": {
        "label": "Two aliases require two authorization decisions",
        "query": "query Aliases { own: document(id: \"blue-note\") { id marker } other: document(id: \"amber-note\") { id marker } }",
        "variables": {},
        "expectation": "The fixed executor returns own and refuses other. Aliases do not grant shared authorization to sibling fields.",
    },
    "query-budget": {
        "label": "Bounded alias fan-out exceeds a field budget",
        "query": "query Budget { " + " ".join(f'n{i}: document(id: "blue-note") {{ id title }}' for i in range(1, 9)) + " }",
        "variables": {},
        "expectation": "The fixed validation rule rejects 24 selected field nodes against a budget of 12 before any resolver executes. The vulnerable executor resolves all eight harmless aliases.",
    },
}


def graphql_metadata():
    return {"fixtures": [{"id": key, **deepcopy(value)} for key, value in FIXTURES.items()],
            "actor": deepcopy(ACTOR), "fieldBudget": FIELD_BUDGET, "engine": "graphql-core"}


SCHEMA = build_schema("""
    type Query { document(id: ID!): Document }
    type Mutation { renameDocument(id: ID!, title: String!): Document }
    type Document {
        id: ID!
        title: String!
        marker: String!
        adminNote: String
        relatedDocument: Document
    }
""")


def permission(info, document, action):
    context = info.context
    same_tenant = document["tenant"] == context["actor"]["tenant"]
    allowed = same_tenant
    if action == "admin-field":
        allowed = same_tenant and context["actor"]["role"] == "admin"
    elif action == "rename":
        allowed = same_tenant and document["owner"] == context["actor"]["id"]
    context["checks"].append({"path": info.path.as_list(), "action": action,
                              "document": document["id"], "allowed": allowed,
                              "enforced": context["mode"] == "fixed"})
    if context["mode"] == "fixed" and not allowed:
        raise GraphQLError("This fictional identity may not access this object or field.",
                           extensions={"code": "FORBIDDEN"})


def resolve_document(_source, info, id):
    document = info.context["store"].get(id)
    if document is not None:
        permission(info, document, "read")
    return document


def resolve_related(source, info):
    document = info.context["store"].get(source["related"])
    if document is not None:
        permission(info, document, "nested-read")
    return document


def resolve_admin_note(source, info):
    permission(info, source, "admin-field")
    return source["adminNote"]


def resolve_rename(_source, info, id, title):
    document = info.context["store"].get(id)
    if document is None:
        return None
    permission(info, document, "rename")
    document["title"] = title
    info.context["writes"] += 1
    return document


SCHEMA.query_type.fields["document"].resolve = resolve_document
SCHEMA.mutation_type.fields["renameDocument"].resolve = resolve_rename
SCHEMA.get_type("Document").fields["relatedDocument"].resolve = resolve_related
SCHEMA.get_type("Document").fields["adminNote"].resolve = resolve_admin_note


class FieldBudgetRule(ValidationRule):
    """A real pre-execution AST rule, scoped to these fragment-free fixtures."""
    def __init__(self, context):
        super().__init__(context)
        self.count = 0

    def enter_field(self, _node, *_args):
        self.count += 1

    def leave_document(self, node, *_args):
        if self.count > FIELD_BUDGET:
            self.report_error(GraphQLError(
                f"Selected field nodes {self.count} exceed the lesson budget of {FIELD_BUDGET}.",
                nodes=node, extensions={"code": "FIELD_BUDGET_EXCEEDED"}))


def count_fields(node):
    """Count selection nodes in server-owned documents (no fragment definitions)."""
    if node.kind == "document":
        return sum(count_fields(definition) for definition in node.definitions)
    selection = getattr(node, "selection_set", None)
    return (1 if node.kind == "field" else 0) + (sum(count_fields(item) for item in selection.selections) if selection else 0)


def count_resolver(next_resolver, source, info, **kwargs):
    info.context["resolverCalls"] += 1
    return next_resolver(source, info, **kwargs)


def execute_fixture(fixture_id, mode):
    if fixture_id not in FIXTURES or mode not in ("vulnerable", "fixed"):
        raise ValueError("Choose a server-owned fixture and comparison mode.")
    fixture = FIXTURES[fixture_id]
    context = {"actor": deepcopy(ACTOR), "mode": mode, "store": deepcopy(DOCUMENTS),
               "checks": [], "resolverCalls": 0, "writes": 0}
    before = {key: item["title"] for key, item in context["store"].items()}
    document = parse(fixture["query"])
    rules = (*specified_rules, FieldBudgetRule) if mode == "fixed" else specified_rules
    validation_errors = validate(SCHEMA, document, rules=rules)
    data, errors = None, validation_errors
    if not validation_errors:
        result = execute_sync(SCHEMA, document, context_value=context,
                              variable_values=deepcopy(fixture["variables"]), middleware=[count_resolver])
        data, errors = result.data, result.errors or []
    return {
        "data": data, "errors": [error.formatted for error in errors],
        "validationPassed": not validation_errors, "selectedFields": count_fields(document),
        "fieldBudget": FIELD_BUDGET if mode == "fixed" else None,
        "resolverCalls": context["resolverCalls"], "writes": context["writes"],
        "before": before, "after": {key: item["title"] for key, item in context["store"].items()},
        "checks": context["checks"],
    }


def compare_fixture(fixture_id):
    return {"fixture": fixture_id, "results": {mode: execute_fixture(fixture_id, mode)
                                               for mode in ("vulnerable", "fixed")}}


def respond(data, status=200, allow=None):
    response = JsonResponse(data, status=status)
    response["Cache-Control"] = "no-store"
    if allow:
        response["Allow"] = allow
    return response


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


@csrf_protect
def graphql_compare(request):
    if request.method != "POST":
        return respond({"error": "Use POST for a disposable comparison."}, 405, "POST")
    if request.GET or request.content_type != "application/json" or len(request.body) > 2048:
        return respond({"error": "Send a small JSON object with only fixture; no query parameters."}, 400)
    try:
        body = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return respond({"error": "Send valid JSON with unique fields."}, 400)
    if (not isinstance(body, dict) or set(body) != {"fixture"}
            or not isinstance(body["fixture"], str) or body["fixture"] not in FIXTURES):
        return respond({"error": "Choose a listed fixture. Queries, variables and identities are server-owned."}, 400)
    return respond(compare_fixture(body["fixture"]))
