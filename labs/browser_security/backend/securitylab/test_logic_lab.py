"""Real concurrent SQLite comparisons, transaction boundaries, and HTTP controls."""
import json
import sqlite3
import tempfile
import threading
import time
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, SimpleTestCase, override_settings
from django.urls import path

from . import logic_lab

urlpatterns = [path("api/logic/compare/", logic_lab.logic_compare)]


@override_settings(ROOT_URLCONF=__name__)
class LogicLabTests(SimpleTestCase):
    def compare(self, scenario="single"):
        return self.client.post("/api/logic/compare/", {"scenario": scenario}, content_type="application/json")

    def test_legitimate_redemption_works_in_both_handlers(self):
        response = self.compare()
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertFalse(result["schedulingFixture"])
        for mode in ("vulnerable", "fixed"):
            self.assertEqual(result["results"][mode], {
                "mode": mode, "attempts": [{"attemptId": 1, "outcome": "redeemed", "rewardUnits": 10}],
                "redemptions": 1, "rewardUnits": 10, "couponUsed": True,
            })

    def test_sequential_replay_is_rejected_by_both_handlers(self):
        response = self.compare("sequential")
        self.assertEqual(response.status_code, 200)
        for result in response.json()["results"].values():
            self.assertEqual(result["redemptions"], 1)
            self.assertEqual(result["rewardUnits"], 10)
            self.assertEqual([attempt["outcome"] for attempt in result["attempts"]], ["redeemed", "already_used"])

    def test_real_overlapping_connections_duplicate_only_vulnerable_credit(self):
        response = self.compare("concurrent")
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertTrue(response.json()["schedulingFixture"])
        self.assertEqual(results["vulnerable"]["redemptions"], 2)
        self.assertEqual(results["vulnerable"]["rewardUnits"], 20)
        self.assertEqual([attempt["outcome"] for attempt in results["vulnerable"]["attempts"]], ["redeemed", "redeemed"])
        self.assertEqual(results["fixed"]["redemptions"], 1)
        self.assertEqual(results["fixed"]["rewardUnits"], 10)
        self.assertCountEqual([attempt["outcome"] for attempt in results["fixed"]["attempts"]], ["redeemed", "already_used"])
        self.assertTrue(results["fixed"]["couponUsed"])
        self.assertTrue(results["vulnerable"]["couponUsed"])

    def test_each_comparison_uses_fresh_stores_and_removes_temporary_files(self):
        factory = tempfile.TemporaryDirectory
        directories = []

        def tracked_directory(*args, **kwargs):
            directory = factory(*args, **kwargs)
            directories.append(Path(directory.name))
            return directory

        with patch("securitylab.logic_lab.tempfile.TemporaryDirectory", side_effect=tracked_directory):
            concurrent = self.compare("concurrent")
            single = self.compare("single")
        self.assertEqual(concurrent.status_code, 200)
        self.assertEqual(single.status_code, 200)
        self.assertEqual(len(set(directories)), 4)
        self.assertTrue(all(not directory.exists() for directory in directories))
        self.assertEqual(single.json()["results"]["vulnerable"]["redemptions"], 1)
        self.assertFalse(any(thread.name.startswith("coupon-fixture-") for thread in threading.enumerate()))

    def test_fixed_credit_failure_rolls_back_coupon_consumption(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.sqlite3"
            logic_lab.create_store(path)
            with closing(logic_lab.connection_to(path)) as connection:
                connection.execute("CREATE TRIGGER reject_credit BEFORE INSERT ON credits BEGIN SELECT RAISE(ABORT, 'fixture credit failure'); END")
            with self.assertRaises(sqlite3.IntegrityError):
                logic_lab.redeem(path, "fixed", 1)
            with closing(logic_lab.connection_to(path)) as connection:
                self.assertEqual(connection.execute("SELECT used FROM coupons").fetchone(), (0,))
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM credits").fetchone(), (0,))
                connection.execute("DROP TRIGGER reject_credit")
            self.assertEqual(logic_lab.redeem(path, "fixed", 1)["outcome"], "redeemed")

    def test_failed_worker_releases_peer_and_cleans_fixture(self):
        real_redeem = logic_lab.redeem
        factory = tempfile.TemporaryDirectory
        directories = []

        def tracked_directory(*args, **kwargs):
            directory = factory(*args, **kwargs)
            directories.append(Path(directory.name))
            return directory

        def fail_one(path, mode, attempt_id, gate=None, stop=None):
            if attempt_id == 1:
                raise sqlite3.OperationalError("synthetic worker failure")
            return real_redeem(path, mode, attempt_id, gate, stop)

        started = time.monotonic()
        with patch("securitylab.logic_lab.redeem", side_effect=fail_one), \
                patch("securitylab.logic_lab.tempfile.TemporaryDirectory", side_effect=tracked_directory):
            response = self.compare("concurrent")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["results"], {})
        self.assertEqual(response.json()["outcome"], "unavailable")
        self.assertLess(time.monotonic() - started, logic_lab.WORKER_TIMEOUT)
        self.assertTrue(all(not directory.exists() for directory in directories))
        self.assertFalse(any(thread.name.startswith("coupon-fixture-") for thread in threading.enumerate()))
        self.assertEqual(self.compare().status_code, 200)

    def test_busy_database_has_a_bounded_lock_wait(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.sqlite3"
            logic_lab.create_store(path)
            with closing(logic_lab.connection_to(path)) as locker:
                locker.execute("BEGIN IMMEDIATE")
                started = time.monotonic()
                with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                    logic_lab.redeem(path, "fixed", 1)
                self.assertLess(time.monotonic() - started, logic_lab.WORKER_TIMEOUT)
                locker.rollback()
            self.assertEqual(logic_lab.redeem(path, "fixed", 1)["outcome"], "redeemed")

    def test_comparison_limit_rejects_work_without_creating_a_store(self):
        with patch("securitylab.logic_lab.ACTIVE_COMPARISONS") as semaphore, \
                patch("securitylab.logic_lab.run_fixture") as fixture:
            semaphore.acquire.return_value = False
            response = self.compare("concurrent")
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()["results"], {})
            fixture.assert_not_called()
            semaphore.release.assert_not_called()

    def test_input_validation_precedes_fixture_creation(self):
        with patch("securitylab.logic_lab.run_fixture") as fixture:
            for body in ({}, [], {"scenario": []}, {"scenario": None}, {"scenario": "unknown"},
                         {"scenario": "single", "rewardUnits": 1000}, {"scenario": "concurrent", "workers": 100}):
                with self.subTest(body=body):
                    response = self.client.post("/api/logic/compare/", body, content_type="application/json")
                    self.assertEqual(response.status_code, 400)
            for raw in ('{', '{"scenario":"single","scenario":"concurrent"}', '"' + 'x' * 1025 + '"'):
                self.assertEqual(self.client.post("/api/logic/compare/", raw, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/logic/compare/", {"scenario": "single"}).status_code, 400)
            self.assertEqual(self.client.post("/api/logic/compare/?mode=fixed", {"scenario": "single"}, content_type="application/json").status_code, 400)
            response = self.client.get("/api/logic/compare/")
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "POST")
            fixture.assert_not_called()

    def test_post_requires_csrf_and_legitimate_token_succeeds(self):
        client = Client(enforce_csrf_checks=True)
        body = json.dumps({"scenario": "single"})
        self.assertEqual(client.post("/api/logic/compare/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        self.assertEqual(client.post("/api/logic/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(client.post("/api/logic/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token,
                                     HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)
