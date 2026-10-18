"""Resolver authorization, actual writes, pre-execution validation and HTTP boundaries."""
import json
from unittest.mock import patch

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, SimpleTestCase, override_settings
from django.urls import path

from . import graphql_lab

urlpatterns = [path("api/graphql/compare/", graphql_lab.graphql_compare)]


@override_settings(ROOT_URLCONF=__name__)
class GraphqlLabTests(SimpleTestCase):
    def compare(self, fixture="allowed"):
        return self.client.post("/api/graphql/compare/", {"fixture": fixture}, content_type="application/json")

    def test_positive_read_returns_real_data_through_both_executors(self):
        for result in self.compare().json()["results"].values():
            self.assertEqual(result["data"], {"document": {"id": "blue-note", "title": "Blue notebook", "marker": "FICTIONAL_BLUE_MARKER"}})
            self.assertEqual(result["errors"], [])
            self.assertTrue(result["validationPassed"])
            self.assertEqual(result["resolverCalls"], 4)
            self.assertEqual(result["writes"], 0)

    def test_nested_relation_enforces_tenant_boundary_and_preserves_parent(self):
        results = self.compare("nested-tenant").json()["results"]
        self.assertEqual(results["vulnerable"]["data"]["document"]["relatedDocument"]["marker"], "FICTIONAL_AMBER_MARKER")
        fixed = results["fixed"]
        self.assertEqual(fixed["data"], {"document": {"id": "blue-note", "relatedDocument": None}})
        self.assertEqual(fixed["errors"][0]["path"], ["document", "relatedDocument"])
        self.assertEqual(fixed["errors"][0]["extensions"]["code"], "FORBIDDEN")
        self.assertEqual([check["allowed"] for check in fixed["checks"]], [True, False])
        self.assertEqual(fixed["resolverCalls"], 3)
        self.assertNotIn("FICTIONAL_AMBER_MARKER", json.dumps(fixed["data"]))

    def test_field_permission_returns_partial_data_for_member(self):
        results = self.compare("protected-field").json()["results"]
        self.assertEqual(results["vulnerable"]["data"]["document"]["adminNote"], "FICTIONAL_BLUE_ADMIN_NOTE")
        self.assertEqual(results["fixed"]["data"]["document"], {"id": "blue-note", "title": "Blue notebook", "adminNote": None})
        self.assertEqual(results["fixed"]["errors"][0]["path"], ["document", "adminNote"])

    def test_same_tenant_admin_is_allowed_to_read_protected_field(self):
        with patch.dict(graphql_lab.ACTOR, {"role": "admin"}):
            result = graphql_lab.execute_fixture("protected-field", "fixed")
        self.assertEqual(result["data"]["document"]["adminNote"], "FICTIONAL_BLUE_ADMIN_NOTE")
        self.assertEqual(result["errors"], [])

    def test_own_mutation_positive_control_performs_one_real_write(self):
        for result in self.compare("own-mutation").json()["results"].values():
            self.assertEqual(result["data"], {"renameDocument": {"id": "blue-note", "title": "HARMLESS_RENAMED_NOTE"}})
            self.assertEqual(result["before"]["blue-note"], "Blue notebook")
            self.assertEqual(result["after"]["blue-note"], "HARMLESS_RENAMED_NOTE")
            self.assertEqual(result["before"]["amber-note"], result["after"]["amber-note"])
            self.assertEqual(result["writes"], 1)
            self.assertEqual(result["errors"], [])

    def test_forbidden_mutation_checks_before_changing_store(self):
        results = self.compare("forbidden-mutation").json()["results"]
        vulnerable, fixed = results["vulnerable"], results["fixed"]
        self.assertEqual(vulnerable["after"]["amber-note"], "HARMLESS_RENAMED_NOTE")
        self.assertEqual(vulnerable["writes"], 1)
        self.assertEqual(fixed["data"], {"renameDocument": None})
        self.assertEqual(fixed["before"], fixed["after"])
        self.assertEqual(fixed["writes"], 0)
        self.assertEqual(fixed["resolverCalls"], 1)
        self.assertEqual(fixed["errors"][0]["path"], ["renameDocument"])

    def test_ownership_is_required_even_for_same_tenant_mutation(self):
        with patch.dict(graphql_lab.ACTOR, {"id": "another-blue-member"}):
            result = graphql_lab.execute_fixture("own-mutation", "fixed")
        self.assertEqual(result["writes"], 0)
        self.assertEqual(result["before"], result["after"])
        self.assertEqual(result["errors"][0]["extensions"]["code"], "FORBIDDEN")

    def test_aliases_make_independent_decisions_and_errors_use_response_alias(self):
        results = self.compare("aliases").json()["results"]
        self.assertEqual(results["vulnerable"]["data"]["other"]["marker"], "FICTIONAL_AMBER_MARKER")
        fixed = results["fixed"]
        self.assertEqual(fixed["data"], {"own": {"id": "blue-note", "marker": "FICTIONAL_BLUE_MARKER"}, "other": None})
        self.assertEqual(fixed["errors"][0]["path"], ["other"])
        self.assertEqual([check["path"] for check in fixed["checks"]], [["own"], ["other"]])
        self.assertEqual(fixed["resolverCalls"], 4)

    def test_actual_validation_budget_rejects_before_any_resolver_or_write(self):
        results = self.compare("query-budget").json()["results"]
        vulnerable, fixed = results["vulnerable"], results["fixed"]
        self.assertEqual(len(vulnerable["data"]), 8)
        self.assertEqual(vulnerable["resolverCalls"], 24)
        self.assertEqual(vulnerable["errors"], [])
        self.assertFalse(fixed["validationPassed"])
        self.assertEqual(fixed["selectedFields"], 24)
        self.assertEqual(fixed["fieldBudget"], 12)
        self.assertIsNone(fixed["data"])
        self.assertEqual(fixed["resolverCalls"], 0)
        self.assertEqual(fixed["checks"], [])
        self.assertEqual(fixed["writes"], 0)
        self.assertEqual(fixed["errors"][0]["extensions"]["code"], "FIELD_BUDGET_EXCEEDED")
        self.assertNotIn("path", fixed["errors"][0])

    def test_each_mode_and_rerun_uses_an_independent_store(self):
        expected = self.compare("forbidden-mutation").json()
        self.compare("own-mutation")
        self.assertEqual(self.compare("forbidden-mutation").json(), expected)
        self.assertEqual(graphql_lab.DOCUMENTS["amber-note"]["title"], "Amber notebook")
        self.assertEqual(graphql_lab.DOCUMENTS["blue-note"]["title"], "Blue notebook")
        for fixture in graphql_lab.FIXTURES:
            results = self.compare(fixture).json()["results"]
            self.assertEqual(results["vulnerable"]["before"], results["fixed"]["before"])

    def test_unknown_queries_variables_and_identities_are_rejected_before_execution(self):
        with patch("securitylab.graphql_lab.compare_fixture") as execute:
            for body in ({}, [], {"fixture": []}, {"fixture": None}, {"fixture": "unknown"},
                         {"fixture": "allowed", "query": "{ document(id: \"blue-note\") { id } }"},
                         {"fixture": "allowed", "actor": "admin"}, {"fixture": "allowed", "variables": {}},
                         {"fixture": "allowed", "mode": "fixed"}):
                self.assertEqual(self.client.post("/api/graphql/compare/", body, content_type="application/json").status_code, 400)
            for body in ("{", '{"fixture":"allowed","fixture":"aliases"}', " " * 2049,
                         "[" * 1000 + "]" * 1000, b"\xff"):
                self.assertEqual(self.client.post("/api/graphql/compare/", body, content_type="application/json").status_code, 400)
            execute.assert_not_called()

    def test_http_methods_query_parameters_and_content_type_are_bounded(self):
        response = self.client.get("/api/graphql/compare/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")
        self.assertEqual(self.client.post("/api/graphql/compare/", {"fixture": "allowed"}).status_code, 400)
        self.assertEqual(self.client.post("/api/graphql/compare/?query=x", {"fixture": "allowed"}, content_type="application/json").status_code, 400)

    def test_csrf_origin_checks_and_no_store_apply(self):
        client = Client(enforce_csrf_checks=True)
        body = json.dumps({"fixture": "allowed"})
        self.assertEqual(client.post("/api/graphql/compare/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        response = client.post("/api/graphql/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(client.post("/api/graphql/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token,
                                     HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)
