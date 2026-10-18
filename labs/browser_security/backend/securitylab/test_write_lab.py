"""Persisted write evidence, full-patch rejection, and fixture HTTP boundaries."""
from contextlib import closing
import json
from unittest.mock import patch

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, SimpleTestCase, override_settings
from django.urls import path

from . import write_lab

urlpatterns = [path("api/write/compare/", write_lab.write_compare)]


@override_settings(ROOT_URLCONF=__name__)
class WriteLabTests(SimpleTestCase):
    def compare(self, fixture="own", **extra):
        return self.client.post("/api/write/compare/", {"fixture": fixture, **extra}, content_type="application/json")

    def test_legitimate_own_name_update_commits_and_preserves_protected_fields(self):
        response = self.compare()
        self.assertEqual(response.status_code, 200)
        for result in response.json()["results"].values():
            self.assertEqual(result["outcome"], "updated")
            self.assertEqual(result["before"]["displayName"], "Ada")
            self.assertEqual(result["after"]["displayName"], "Ada Lovelace")
            self.assertEqual(result["changedFields"], ["displayName"])
            self.assertEqual(result["rowsChanged"], 1)

    def test_peer_and_cross_tenant_are_independent_object_boundaries(self):
        for fixture in ("peer", "cross-tenant"):
            with self.subTest(fixture=fixture):
                results = self.compare(fixture).json()["results"]
                self.assertEqual(results["vulnerable"]["rowsChanged"], 1)
                self.assertEqual(results["vulnerable"]["after"]["displayName"], "Changed by Ada")
                self.assertEqual(results["fixed"]["outcome"], "denied")
                self.assertEqual(results["fixed"]["before"], results["fixed"]["after"])
                self.assertEqual(results["fixed"]["rowsChanged"], 0)
        cross = self.compare("cross-tenant").json()
        self.assertEqual(cross["actor"]["id"], cross["results"]["fixed"]["before"]["ownerId"])
        self.assertNotEqual(cross["actor"]["tenantId"], cross["results"]["fixed"]["before"]["tenantId"])

    def test_protected_owner_tenant_and_role_never_change_in_fixed_handler(self):
        for fixture, field in (("owner", "ownerId"), ("tenant", "tenantId"), ("role", "role")):
            with self.subTest(fixture=fixture):
                body = self.compare(fixture).json()
                vulnerable, fixed = body["results"]["vulnerable"], body["results"]["fixed"]
                self.assertEqual(vulnerable["changedFields"], [field])
                self.assertEqual(vulnerable["after"][field], body["patch"][field])
                self.assertEqual(fixed["outcome"], "rejected")
                self.assertEqual(fixed["after"], fixed["before"])
                self.assertEqual(fixed["rowsChanged"], 0)

    def test_mixed_patch_is_rejected_without_a_partial_allowed_write(self):
        with closing(write_lab.create_store()) as connection:
            trace = []
            connection.set_trace_callback(trace.append)
            result = write_lab.apply_update(connection, "fixed", write_lab.ACTOR, 101, write_lab.FIXTURES["mixed"]["patch"])
            self.assertEqual(result["outcome"], "rejected")
            self.assertEqual(result["changedFields"], [])
            self.assertEqual(write_lab.read_profile(connection, 101), result["before"])
            self.assertFalse(any(statement.startswith("UPDATE") for statement in trace))
            self.assertIn("ROLLBACK", trace)
            self.assertFalse(connection.in_transaction)
        vulnerable = self.compare("mixed").json()["results"]["vulnerable"]
        self.assertEqual(vulnerable["changedFields"], ["displayName", "role"])

    def test_value_schema_rejects_types_lengths_and_blank_names(self):
        for value in (None, 17, True, [], {}, "", "   ", "x" * 41):
            with self.subTest(value=value), closing(write_lab.create_store()) as connection:
                result = write_lab.apply_update(connection, "fixed", write_lab.ACTOR, 101, {"displayName": value})
                self.assertEqual(result["outcome"], "rejected")
                self.assertEqual(result["after"], result["before"])
        for fixture in ("invalid-type", "too-long"):
            body = self.compare(fixture).json()
            self.assertEqual(body["results"]["vulnerable"]["after"]["displayName"], body["patch"]["displayName"])
            self.assertEqual(body["results"]["fixed"]["outcome"], "rejected")
        with closing(write_lab.create_store()) as connection:
            self.assertEqual(write_lab.apply_update(connection, "fixed", write_lab.ACTOR, 101, {"displayName": "x" * 40})["outcome"], "updated")

    def test_real_sql_transaction_changes_only_the_target_and_rereads_committed_state(self):
        with closing(write_lab.create_store()) as connection:
            peers = [write_lab.read_profile(connection, target) for target in (102, 201)]
            trace = []
            connection.set_trace_callback(trace.append)
            result = write_lab.apply_update(connection, "fixed", write_lab.ACTOR, 101, {"displayName": "O'Neil <marker>"})
            self.assertEqual(result["after"], write_lab.read_profile(connection, 101))
            self.assertEqual(result["after"]["displayName"], "O'Neil <marker>")
            self.assertEqual(peers, [write_lab.read_profile(connection, target) for target in (102, 201)])
            self.assertEqual(sum(statement.startswith("UPDATE") for statement in trace), 1)
            self.assertIn("BEGIN IMMEDIATE", trace)
            self.assertIn("COMMIT", trace)
            self.assertFalse(connection.in_transaction)

    def test_every_comparison_and_mode_starts_from_fresh_fixture_state(self):
        first = self.compare("own").json()
        self.compare("role")
        self.compare("tenant")
        second = self.compare("own").json()
        self.assertEqual(first, second)
        for fixture in write_lab.FIXTURES:
            results = self.compare(fixture).json()["results"]
            self.assertEqual(results["vulnerable"]["before"], results["fixed"]["before"])

    def test_invalid_http_inputs_do_not_create_a_store_or_supply_authority(self):
        with patch("securitylab.write_lab.create_store") as store:
            for body in ({}, [], {"fixture": []}, {"fixture": None}, {"fixture": "unknown"},
                         {"fixture": "own", "actor": {"id": "admin"}}, {"fixture": "own", "patch": {"role": "administrator"}},
                         {"fixture": "own", "targetId": 201}, {"fixture": "own", "mode": "fixed"}):
                self.assertEqual(self.client.post("/api/write/compare/", body, content_type="application/json").status_code, 400)
            for raw in ("{", '{"fixture":"own","fixture":"role"}', " " * 2049, "[" * 1000 + "]" * 1000):
                self.assertEqual(self.client.post("/api/write/compare/", raw, content_type="application/json").status_code, 400)
            store.assert_not_called()

    def test_methods_content_type_and_query_are_restricted(self):
        response = self.client.get("/api/write/compare/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")
        self.assertEqual(self.client.post("/api/write/compare/", {"fixture": "own"}).status_code, 400)
        self.assertEqual(self.client.post("/api/write/compare/?actor=admin", {"fixture": "own"}, content_type="application/json").status_code, 400)

    def test_normal_csrf_validation_applies_to_the_fixture_endpoint(self):
        client = Client(enforce_csrf_checks=True)
        body = json.dumps({"fixture": "own"})
        self.assertEqual(client.post("/api/write/compare/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        self.assertEqual(client.post("/api/write/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(client.post("/api/write/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token,
                                     HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)
