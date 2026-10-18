"""Lifecycle evidence, handler invariants, and the comparison API boundary."""
import json
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, SimpleTestCase, override_settings

from .auth_lab import FIXTURE_PASSWORD, MARKER, NEW_PASSWORD, RESET_TTL, FixtureAuth, run_scenario


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AuthLabTests(SimpleTestCase):
    # Fast hashing applies only to these tests. The app retains Django's hasher.
    def compare(self, scenario):
        return self.client.post("/api/auth/compare/", {"scenario": scenario}, content_type="application/json")

    def test_rotation_replays_saved_token_and_preserves_legitimate_login(self):
        results = self.compare("rotation").json()["results"]
        self.assertEqual(results["vulnerable"]["outcome"], "exposed")
        self.assertEqual(results["fixed"]["outcome"], "protected")
        self.assertEqual([item["passed"] for item in results["vulnerable"]["checks"]], [True, False, False])
        self.assertTrue(all(item["passed"] for item in results["fixed"]["checks"]))
        self.assertEqual(results["vulnerable"]["steps"][-1]["result"], MARKER)
        self.assertNotIn(MARKER, results["fixed"]["steps"][-1]["result"])

    def test_logout_replay_checks_server_revocation_after_discarding_client_token(self):
        results = self.compare("logout").json()["results"]
        self.assertEqual([item["passed"] for item in results["vulnerable"]["checks"]], [True, True, False])
        self.assertTrue(all(item["passed"] for item in results["fixed"]["checks"]))
        self.assertEqual(results["vulnerable"]["steps"][-1]["result"], MARKER)
        self.assertIn("Access denied", results["fixed"]["steps"][-1]["result"])

    def test_expiry_boundary_is_checked_with_actual_password_state(self):
        results = self.compare("reset-expiry").json()["results"]
        self.assertEqual(results["vulnerable"]["steps"][2]["result"], "accepted")
        self.assertEqual(results["fixed"]["steps"][2]["result"], "expired")
        self.assertEqual(results["fixed"]["steps"][2]["time"], 100 + RESET_TTL)
        self.assertEqual([item["result"] for item in results["fixed"]["steps"][-2:]], ["Accepted", "Rejected"])
        self.assertEqual([item["result"] for item in results["vulnerable"]["steps"][-2:]], ["Rejected", "Accepted"])

    def test_reset_reuse_cannot_replace_the_legitimate_password_in_fixed_mode(self):
        results = self.compare("reset-reuse").json()["results"]
        self.assertEqual(results["fixed"]["steps"][2]["result"], "accepted")
        self.assertEqual(results["fixed"]["steps"][3]["result"], "already_used")
        self.assertEqual(results["vulnerable"]["steps"][3]["result"], "accepted")
        self.assertEqual([item["result"] for item in results["fixed"]["steps"][-2:]], ["Accepted", "Rejected"])
        self.assertTrue(all(item["passed"] for item in results["fixed"]["checks"]))

    def test_negative_and_legitimate_controls_pass_for_both_handlers(self):
        for scenario in ("invalid-password", "legitimate-reset"):
            with self.subTest(scenario=scenario):
                results = self.compare(scenario).json()["results"]
                for result in results.values():
                    self.assertEqual(result["outcome"], "control_passed")
                    self.assertTrue(all(item["passed"] for item in result["checks"]))

    def test_unknown_reset_and_anonymous_tokens_never_authenticate(self):
        for mode in ("vulnerable", "fixed"):
            store = FixtureAuth(mode, make_password(FIXTURE_PASSWORD))
            try:
                self.assertIsNone(store.read("unknown"))
                self.assertIsNone(store.read(store.anonymous()))
                self.assertEqual(store.reset("unknown", NEW_PASSWORD), "unknown_token")
                self.assertIsNotNone(store.login(store.anonymous(), FIXTURE_PASSWORD))
                self.assertIsNone(store.login(store.anonymous(), NEW_PASSWORD))
            finally:
                store.close()

    def test_fixed_valid_reset_revokes_preexisting_sessions(self):
        store = FixtureAuth("fixed", make_password(FIXTURE_PASSWORD))
        try:
            session = store.login(store.anonymous(), FIXTURE_PASSWORD)
            self.assertEqual(store.read(session), MARKER)
            self.assertEqual(store.reset(store.issue_reset(), NEW_PASSWORD), "accepted")
            self.assertIsNone(store.read(session))
            self.assertIsNotNone(store.login(store.anonymous(), NEW_PASSWORD))
        finally:
            store.close()

    def test_separate_stores_cannot_reuse_each_others_tokens(self):
        first = FixtureAuth("fixed", make_password(FIXTURE_PASSWORD))
        second = FixtureAuth("fixed", make_password(FIXTURE_PASSWORD))
        try:
            token = first.login(first.anonymous(), FIXTURE_PASSWORD)
            reset = first.issue_reset()
            self.assertEqual(first.read(token), MARKER)
            self.assertIsNone(second.read(token))
            self.assertEqual(second.reset(reset, NEW_PASSWORD), "unknown_token")
        finally:
            first.close()
            second.close()

    def test_request_stores_are_cleared_after_success_and_failure(self):
        stores = []
        constructor = FixtureAuth

        def track(mode, password_hash):
            instance = constructor(mode, password_hash)
            stores.append(instance)
            return instance

        with patch("securitylab.auth_lab.FixtureAuth", side_effect=track):
            self.compare("reset-reuse")
            self.compare("rotation")
            with patch.object(constructor, "reset", side_effect=RuntimeError("fixture failure")):
                with self.assertRaisesRegex(RuntimeError, "fixture failure"):
                    run_scenario("legitimate-reset", "fixed", make_password(FIXTURE_PASSWORD))
        self.assertEqual(len(stores), 5)
        for store in stores:
            self.assertTrue(store.closed)
            self.assertEqual(store.sessions, {})
            self.assertEqual(store.resets, {})
            self.assertEqual(store.password_hash, "")

    def test_invalid_inputs_are_rejected_before_hashing_or_store_creation(self):
        with patch("securitylab.auth_lab.make_password") as hash_password:
            for body in ({}, [], {"scenario": None}, {"scenario": []}, {"scenario": 1},
                         {"scenario": "unknown"}, {"scenario": "rotation", "token": "external"}):
                with self.subTest(body=body):
                    response = self.client.post("/api/auth/compare/", body, content_type="application/json")
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(response.json()["results"], {})
            for body in ("{", '{"scenario":"rotation","scenario":"logout"}', b'\xff'):
                self.assertEqual(self.client.post("/api/auth/compare/", body, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/auth/compare/", ' ' * 1025, content_type="application/json").status_code, 413)
            self.assertEqual(self.client.post("/api/auth/compare/?extra=1", {"scenario": "rotation"}, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/auth/compare/", {"scenario": "rotation"}).status_code, 400)
            response = self.client.get("/api/auth/compare/")
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "POST")
            hash_password.assert_not_called()

    def test_concurrency_budget_rejects_immediately_and_releases_after_error(self):
        with patch("securitylab.auth_lab.COMPARISON_SLOTS") as slots:
            slots.acquire.return_value = False
            with patch("securitylab.auth_lab.make_password") as hash_password:
                response = self.compare("rotation")
                self.assertEqual(response.status_code, 429)
                self.assertEqual(response["Retry-After"], "2")
                hash_password.assert_not_called()
            slots.acquire.assert_called_once_with(blocking=False)
            slots.release.assert_not_called()
        with patch("securitylab.auth_lab.COMPARISON_SLOTS") as slots:
            slots.acquire.return_value = True
            with patch("securitylab.auth_lab.run_scenario", side_effect=RuntimeError("fixture failure")):
                with self.assertRaisesRegex(RuntimeError, "fixture failure"):
                    self.compare("rotation")
            slots.release.assert_called_once()

    def test_csrf_is_required_and_comparison_does_not_replace_controller_cookie(self):
        client = Client(enforce_csrf_checks=True)
        body = json.dumps({"scenario": "invalid-password"})
        self.assertEqual(client.post("/api/auth/compare/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        client.cookies[settings.SESSION_COOKIE_NAME] = "unrelated-controller-session"
        response = client.post("/api/auth/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(settings.SESSION_COOKIE_NAME, response.cookies)
        self.assertNotIn(settings.CSRF_COOKIE_NAME, response.cookies)
        self.assertEqual(client.cookies[settings.SESSION_COOKIE_NAME].value, "unrelated-controller-session")
        self.assertEqual(client.post("/api/auth/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token,
                                     HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)

    @override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
    def test_real_django_password_hasher_executes_the_login_comparison(self):
        hashes = []
        real_make_password = make_password

        def tracked_hash(password):
            result = real_make_password(password)
            hashes.append(result)
            return result

        with patch("securitylab.auth_lab.make_password", side_effect=tracked_hash):
            response = self.compare("rotation")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"]["fixed"]["outcome"], "protected")
        self.assertEqual(len(hashes), 1)
        self.assertTrue(hashes[0].startswith("pbkdf2_sha256$"))
