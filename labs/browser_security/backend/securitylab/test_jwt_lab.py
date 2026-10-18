"""Exercise actual JWT cryptography, claims, authorization, and the HTTP boundary."""
import json
import secrets
from datetime import datetime, timezone
from unittest.mock import patch

import jwt
from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, SimpleTestCase, override_settings
from django.urls import path

from .jwt_lab import (ALLOWED_SUBJECT, AUDIENCE, ISSUER, MARKER, REQUIRED_CLAIMS,
                      build_token, compare_tokens, decide_token, jwt_compare)

urlpatterns = [path("api/jwt/compare/", jwt_compare)]


@override_settings(ROOT_URLCONF=__name__)
class JwtLabTests(SimpleTestCase):
    def setUp(self):
        self.key = secrets.token_bytes(32)
        self.now = int(datetime.now(timezone.utc).timestamp())

    def compare(self, fixture):
        return self.client.post("/api/jwt/compare/", {"fixture": fixture}, content_type="application/json")

    def test_valid_token_is_really_signed_and_both_handlers_authorize(self):
        token = build_token("normal", self.key, self.now)
        claims = jwt.decode(token, self.key, algorithms=["HS256"], issuer=ISSUER, audience=AUDIENCE,
                            options={"require": REQUIRED_CLAIMS})
        self.assertEqual(claims["sub"], ALLOWED_SUBJECT)
        for mode in ("vulnerable", "fixed"):
            result = decide_token(token, self.key, mode)
            self.assertEqual(result["outcome"], "accepted")
            self.assertEqual(result["marker"], MARKER)
        self.assertEqual(decide_token(token, self.key, "fixed")["validation"], "verified")

    def test_modified_subject_invalidates_real_signature_but_unverified_decoder_accepts(self):
        token = build_token("tampered", self.key, self.now)
        self.assertEqual(jwt.decode(token, options={"verify_signature": False})["sub"], ALLOWED_SUBJECT)
        with self.assertRaises(jwt.InvalidSignatureError):
            jwt.decode(token, self.key, algorithms=["HS256"], audience=AUDIENCE)
        results = self.compare("tampered").json()["results"]
        self.assertEqual(results["vulnerable"]["marker"], MARKER)
        self.assertEqual(results["fixed"]["outcome"], "rejected")
        self.assertIsNone(results["fixed"]["marker"])
        self.assertIn("Signature", results["fixed"]["reason"])

    def test_correct_signatures_do_not_override_expiration_or_not_before(self):
        for fixture, reason in (("expired", "expired"), ("future", "not valid yet")):
            with self.subTest(fixture=fixture):
                token = build_token(fixture, self.key, self.now)
                # Disable only temporal checks to prove the fixture signature is valid.
                jwt.decode(token, self.key, algorithms=["HS256"], issuer=ISSUER, audience=AUDIENCE,
                           options={"verify_exp": False, "verify_nbf": False})
                self.assertEqual(decide_token(token, self.key, "vulnerable")["marker"], MARKER)
                fixed = decide_token(token, self.key, "fixed")
                self.assertIsNone(fixed["marker"])
                self.assertIn(reason, fixed["reason"])

    def test_issuer_audience_and_required_expiration_are_checked(self):
        for fixture, reason in (("wrong-issuer", "issuer"), ("wrong-audience", "audience"), ("missing-exp", "missing: exp")):
            with self.subTest(fixture=fixture):
                results = self.compare(fixture).json()["results"]
                self.assertEqual(results["vulnerable"]["outcome"], "accepted")
                self.assertEqual(results["fixed"]["outcome"], "rejected")
                self.assertIsNone(results["fixed"]["marker"])
                self.assertIn(reason, results["fixed"]["reason"])

    def test_every_required_claim_is_enforced_and_future_iat_is_rejected(self):
        base = jwt.decode(build_token("normal", self.key, self.now), options={"verify_signature": False})
        for claim in REQUIRED_CLAIMS:
            with self.subTest(claim=claim):
                claims = dict(base)
                del claims[claim]
                result = decide_token(jwt.encode(claims, self.key, algorithm="HS256"), self.key, "fixed")
                self.assertIsNone(result["marker"])
                self.assertIn(f"missing: {claim}", result["reason"])
        base["iat"] = self.now + 600
        self.assertIn("not valid yet", decide_token(jwt.encode(base, self.key, algorithm="HS256"), self.key, "fixed")["reason"])

    def test_unsigned_and_other_signing_algorithm_cannot_change_allowlist(self):
        unsigned = self.compare("unsigned").json()
        self.assertEqual(unsigned["header"]["alg"], "none")
        self.assertTrue(unsigned["token"].endswith("."))
        self.assertEqual(unsigned["results"]["vulnerable"]["marker"], MARKER)
        self.assertIn("allowlist", unsigned["results"]["fixed"]["reason"])
        key = secrets.token_bytes(64)
        other = jwt.encode(unsigned["claims"], key, algorithm="HS384")
        result = decide_token(other, key, "fixed")
        self.assertIn("allowlist", result["reason"])
        self.assertIsNone(result["marker"])

    def test_authorization_still_denies_valid_token_for_another_subject(self):
        results = self.compare("wrong-subject").json()["results"]
        self.assertEqual(results["fixed"]["validation"], "verified")
        for result in results.values():
            self.assertEqual(result["outcome"], "rejected")
            self.assertIsNone(result["marker"])
            self.assertIn("not authorized", result["reason"])

    def test_comparisons_use_fresh_keys_without_serializing_them(self):
        keys = [secrets.token_bytes(32), secrets.token_bytes(32)]
        with patch("securitylab.jwt_lab.secrets.token_bytes", side_effect=keys) as random_key:
            first, second = compare_tokens("normal"), compare_tokens("normal")
        self.assertEqual(random_key.call_args_list[0].args, (32,))
        self.assertEqual(random_key.call_count, 2)
        self.assertNotEqual(first["token"], second["token"])
        self.assertEqual(decide_token(first["token"], keys[0], "fixed")["outcome"], "accepted")
        self.assertEqual(decide_token(first["token"], keys[1], "fixed")["outcome"], "rejected")
        for result in (first, second):
            self.assertNotIn("key", result)
            self.assertNotIn("secret", result)
            self.assertLess(len(json.dumps(result)), 6000)

    def test_invalid_or_custom_input_never_generates_a_token(self):
        with patch("securitylab.jwt_lab.compare_tokens") as compare:
            for body in ({}, [], {"fixture": "unknown"}, {"fixture": None}, {"fixture": []},
                         {"fixture": "normal", "token": "custom"}, {"fixture": "normal", "key": "custom"}):
                self.assertEqual(self.client.post("/api/jwt/compare/", body, content_type="application/json").status_code, 400)
            for raw in ('{', '{"fixture":"normal","fixture":"unsigned"}', ' ' * 2049, '[' * 1000 + ']' * 1000):
                self.assertEqual(self.client.post("/api/jwt/compare/", raw, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/jwt/compare/?fixture=normal", {"fixture": "normal"}, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/jwt/compare/", {"fixture": "normal"}).status_code, 400)
            compare.assert_not_called()
        response = self.client.get("/api/jwt/compare/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")

    def test_csrf_token_and_origin_are_enforced(self):
        client = Client(enforce_csrf_checks=True)
        body = json.dumps({"fixture": "normal"})
        self.assertEqual(client.post("/api/jwt/compare/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        response = client.post("/api/jwt/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"]["fixed"]["marker"], MARKER)
        self.assertEqual(client.post("/api/jwt/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token,
                                     HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)
