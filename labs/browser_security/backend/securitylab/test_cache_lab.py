"""Actual cache evidence, private reuse boundaries, and fixture endpoint restrictions."""
import json
from unittest.mock import patch

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, SimpleTestCase, override_settings
from django.urls import path

from . import cache_lab

urlpatterns = [path("api/cache/compare/", cache_lab.cache_compare)]


@override_settings(ROOT_URLCONF=__name__)
class CacheLabTests(SimpleTestCase):
    def compare(self, fixture="private-control"):
        return self.client.post("/api/cache/compare/", {"fixture": fixture}, content_type="application/json")

    def test_ordinary_private_response_works_without_shared_storage(self):
        results = self.compare().json()["results"]
        for result in results.values():
            self.assertEqual([step["returnedMarker"] for step in result["requests"]], ["PRIVATE_ADA_BLUE"] * 2)
            self.assertEqual(result["outcome"], "no disclosure")
        self.assertEqual([step["cacheStatus"] for step in results["vulnerable"]["requests"]], ["MISS", "HIT"])
        self.assertEqual(results["vulnerable"]["writes"], 1)
        self.assertEqual(results["vulnerable"]["originReads"], 1)
        self.assertEqual(results["vulnerable"]["entries"][0]["marker"], "PRIVATE_ADA_BLUE")
        self.assertEqual([step["cacheStatus"] for step in results["fixed"]["requests"]], ["BYPASS"] * 2)
        self.assertEqual(results["fixed"]["lookups"], 0)
        self.assertEqual(results["fixed"]["writes"], 0)
        self.assertEqual(results["fixed"]["originReads"], 2)
        self.assertEqual(results["fixed"]["entries"], [])

    def test_other_user_and_other_tenant_receive_only_their_own_fixed_response(self):
        for fixture, expected in (("cross-user", "PRIVATE_BEA_BLUE"), ("cross-tenant", "PRIVATE_CY_AMBER")):
            with self.subTest(fixture=fixture):
                results = self.compare(fixture).json()["results"]
                vulnerable, fixed = results["vulnerable"], results["fixed"]
                self.assertEqual(vulnerable["outcome"], "exposed")
                self.assertEqual(vulnerable["requests"][1]["returnedMarker"], "PRIVATE_ADA_BLUE")
                self.assertEqual(vulnerable["requests"][1]["cacheStatus"], "HIT")
                self.assertEqual(vulnerable["requests"][1]["authorization"], "skipped on cache hit")
                self.assertFalse(vulnerable["requests"][1]["originRead"])
                self.assertEqual(vulnerable["lookups"], 2)
                self.assertEqual(vulnerable["writes"], 1)
                self.assertEqual(fixed["requests"][1]["returnedMarker"], expected)
                self.assertEqual(fixed["outcome"], "no disclosure")
                self.assertEqual(fixed["entries"], [])

    def test_permission_removal_and_anonymous_requests_are_denied_before_reading(self):
        for fixture in ("revoked", "logout"):
            with self.subTest(fixture=fixture):
                results = self.compare(fixture).json()["results"]
                vulnerable, fixed = results["vulnerable"], results["fixed"]
                self.assertEqual(vulnerable["outcome"], "exposed")
                self.assertFalse(vulnerable["requests"][1]["permissionNow"])
                self.assertEqual(vulnerable["requests"][1]["returnedMarker"], "PRIVATE_ADA_BLUE")
                denied = fixed["requests"][1]
                self.assertEqual(denied["status"], 403)
                self.assertEqual(denied["cacheStatus"], "NOT_CHECKED")
                self.assertEqual(denied["authorization"], "denied")
                self.assertIsNone(denied["returnedMarker"])
                self.assertFalse(denied["originRead"])
                self.assertEqual(fixed["originReads"], 1)
                self.assertEqual(fixed["lookups"], 0)
                self.assertEqual(fixed["trace"][-1]["operation"], "authorize")
                self.assertFalse(fixed["trace"][-1]["allowed"])

    def test_public_positive_control_reuses_a_stored_value_for_anonymous_visitor(self):
        results = self.compare("public-control").json()["results"]
        for result in results.values():
            self.assertEqual(result["outcome"], "no disclosure")
            self.assertEqual([step["cacheStatus"] for step in result["requests"]], ["MISS", "HIT"])
            self.assertEqual([step["returnedMarker"] for step in result["requests"]], ["PUBLIC_CATALOG"] * 2)
            self.assertEqual(result["originReads"], 1)
            self.assertEqual(result["lookups"], 2)
            self.assertEqual(result["writes"], 1)
            self.assertEqual(result["entries"][0]["visibility"], "public")
        fixed = results["fixed"]
        self.assertEqual(fixed["entries"][0]["key"], "lab:v1:public:/catalog/")
        self.assertEqual([item["operation"] for item in fixed["trace"]],
                         ["authorize", "cache-lookup", "origin-read", "cache-store", "authorize", "cache-lookup"])

    def test_existing_private_entry_cannot_bypass_fixed_authorization_or_private_policy(self):
        cache = cache_lab.MemoryCache()
        cache.put(cache_lab.PRIVATE_ROUTE, {"marker": "OLD_PRIVATE_ADA", "owner": "user-ada", "visibility": "private"})
        initial_trace = len(cache.trace)
        denied = cache_lab.serve_request(cache, "fixed", "ada", cache_lab.PRIVATE_ROUTE, set())
        self.assertEqual(denied["status"], 403)
        self.assertIsNone(denied["returnedMarker"])
        self.assertEqual(cache.lookups, 0)
        self.assertEqual(cache.origin_reads, 0)
        self.assertEqual([item["operation"] for item in cache.trace[initial_trace:]], ["authorize"])
        allowed = cache_lab.serve_request(cache, "fixed", "bea", cache_lab.PRIVATE_ROUTE, {"bea"})
        self.assertEqual(allowed["returnedMarker"], "PRIVATE_BEA_BLUE")
        self.assertEqual(allowed["cacheStatus"], "BYPASS")
        self.assertEqual(cache.lookups, 0)
        self.assertEqual(cache.origin_reads, 1)
        # Bypass is not a purge: a deployment needs an explicit old-entry purge.
        self.assertEqual(cache.snapshot()[0]["marker"], "OLD_PRIVATE_ADA")

    def test_cache_hit_returns_the_actual_stored_entry_without_an_origin_read(self):
        cache = cache_lab.MemoryCache()
        cache.put(cache_lab.PRIVATE_ROUTE, {"marker": "STORED_TEST_MARKER", "owner": "user-ada", "visibility": "private"})
        result = cache_lab.serve_request(cache, "vulnerable", "bea", cache_lab.PRIVATE_ROUTE, {"bea"})
        self.assertEqual(result["returnedMarker"], "STORED_TEST_MARKER")
        self.assertTrue(result["disclosed"])
        self.assertEqual(cache.origin_reads, 0)
        self.assertEqual(cache.lookups, 1)

    def test_miss_does_not_create_or_cache_a_denied_response(self):
        for mode in ("vulnerable", "fixed"):
            cache = cache_lab.MemoryCache()
            result = cache_lab.serve_request(cache, mode, "anonymous", cache_lab.PRIVATE_ROUTE, set())
            self.assertEqual(result["status"], 403)
            self.assertEqual(cache.snapshot(), [])
            self.assertEqual(cache.origin_reads, 0)
            self.assertEqual(cache.writes, 0)

    def test_comparisons_are_disposable_and_do_not_reuse_state_between_modes_or_requests(self):
        expected = self.compare("cross-user").json()
        self.compare("revoked")
        self.compare("public-control")
        self.assertEqual(self.compare("cross-user").json(), expected)
        for fixture in cache_lab.FIXTURES:
            results = self.compare(fixture).json()["results"]
            self.assertTrue(results["vulnerable"]["requests"][0]["originRead"])
            self.assertTrue(results["fixed"]["requests"][0]["originRead"])

    def test_invalid_input_cannot_choose_an_actor_route_or_cache_entry(self):
        with patch("securitylab.cache_lab.compare_fixture") as compare:
            for body in ({}, [], {"fixture": []}, {"fixture": None}, {"fixture": 3}, {"fixture": "unknown"},
                         {"fixture": "cross-user", "actor": "admin"}, {"fixture": "cross-user", "route": "/secret"},
                         {"fixture": "public-control", "key": "shared"}, {"fixture": "logout", "mode": "fixed"}):
                self.assertEqual(self.client.post("/api/cache/compare/", body, content_type="application/json").status_code, 400)
            for raw in ("{", '{"fixture":"cross-user","fixture":"logout"}', " " * 2049,
                        "[" * 1000 + "]" * 1000, b'\xff'):
                self.assertEqual(self.client.post("/api/cache/compare/", raw, content_type="application/json").status_code, 400)
            compare.assert_not_called()

    def test_methods_queries_and_content_type_are_restricted(self):
        response = self.client.get("/api/cache/compare/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")
        self.assertEqual(self.client.post("/api/cache/compare/", {"fixture": "logout"}).status_code, 400)
        self.assertEqual(self.client.post("/api/cache/compare/?actor=admin", {"fixture": "logout"}, content_type="application/json").status_code, 400)

    def test_csrf_and_origin_validation_apply_and_http_transport_remains_no_store(self):
        client = Client(enforce_csrf_checks=True)
        body = json.dumps({"fixture": "public-control"})
        self.assertEqual(client.post("/api/cache/compare/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        response = client.post("/api/cache/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(client.post("/api/cache/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token,
                                     HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)
