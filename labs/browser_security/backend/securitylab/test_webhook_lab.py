"""Real HMAC verification, replay state, transaction rollback, and HTTP boundaries."""
import hashlib
import hmac
import json
import sqlite3
from contextlib import closing
from unittest.mock import patch

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, SimpleTestCase

from . import webhook_lab as lab


class WebhookLabTests(SimpleTestCase):
    secret = b"test-only-key-for-local-signed-fixtures"
    now = 2000000000

    def compare(self, fixture):
        return self.client.post("/api/webhook/compare/", {"fixture": fixture}, content_type="application/json")

    def test_signatures_authenticate_exact_bytes_and_the_timestamp(self):
        raw = lab.event_body()
        delivery = lab.signed_delivery(self.secret, self.now, raw)
        expected = hmac.new(self.secret, b"2000000000." + raw, hashlib.sha256).hexdigest()
        self.assertEqual(delivery["signature"], expected)
        with patch("securitylab.webhook_lab.hmac.compare_digest", wraps=hmac.compare_digest) as compare:
            self.assertTrue(lab.verify_signature(self.secret, delivery))
            compare.assert_called_once_with(expected, expected)
        for changed in ({**delivery, "timestamp": self.now + 1},
                        {**delivery, "rawBody": raw + b" "},
                        {**delivery, "signature": "not-a-signature"},
                        {**delivery, "signature": "\u00e9" * 64},
                        {**delivery, "timestamp": True}):
            self.assertFalse(lab.verify_signature(self.secret, changed))
        self.assertFalse(lab.verify_signature(b"different-secret", delivery))

    def test_normal_and_distinct_event_controls_update_real_ledger(self):
        for fixture, expected in (("normal", 10), ("distinct-events", 20)):
            response = self.compare(fixture)
            self.assertEqual(response.status_code, 200)
            for mode, result in response.json()["results"].items():
                self.assertEqual(result["balanceAfter"], expected)
                self.assertTrue(all(row["signatureValid"] for row in result["deliveries"]))
                self.assertTrue(all(row["sideEffect"] == 10 for row in result["deliveries"]))
                self.assertEqual(len(result["processedEventIds"]), expected // 10 if mode == "fixed" else 0)

    def test_body_tampering_is_rejected_by_both_handlers(self):
        for result in self.compare("body-tampered").json()["results"].values():
            self.assertEqual(result["balanceAfter"], 0)
            receipt = result["deliveries"][0]
            self.assertFalse(receipt["signatureValid"])
            self.assertEqual(receipt["outcome"], "rejected")
            self.assertEqual(receipt["sideEffect"], 0)
            self.assertIsNone(receipt["eventId"])

    def test_signature_verification_precedes_schema_parsing_and_event_claim(self):
        delivery = lab.signed_delivery(self.secret, self.now, lab.event_body())
        delivery["rawBody"] = b"not-json"
        with closing(lab.create_store()) as connection:
            with patch("securitylab.webhook_lab.parse_event") as parse, patch("securitylab.webhook_lab.apply_event") as apply:
                result = lab.receive_delivery(connection, "fixed", delivery, self.secret, self.now)
                self.assertFalse(result["signatureValid"])
                parse.assert_not_called()
                apply.assert_not_called()
            # A rejected delivery cannot poison the ID for the later valid event.
            valid = lab.signed_delivery(self.secret, self.now, lab.event_body())
            self.assertEqual(lab.receive_delivery(connection, "fixed", valid, self.secret, self.now)["outcome"], "applied")

    def test_past_and_future_timestamps_require_freshness_not_just_a_signature(self):
        for fixture in ("stale", "future"):
            results = self.compare(fixture).json()["results"]
            self.assertEqual(results["vulnerable"]["balanceAfter"], 10)
            self.assertEqual(results["fixed"]["balanceAfter"], 0)
            self.assertEqual(results["fixed"]["processedEventIds"], [])
            self.assertTrue(results["fixed"]["deliveries"][0]["signatureValid"])
        for offset in (-lab.WINDOW_SECONDS, lab.WINDOW_SECONDS):
            with closing(lab.create_store()) as connection:
                delivery = lab.signed_delivery(self.secret, self.now + offset, lab.event_body())
                result = lab.receive_delivery(connection, "fixed", delivery, self.secret, self.now)
                self.assertEqual(result["outcome"], "applied")
        with closing(lab.create_store()) as connection:
            stale = lab.signed_delivery(self.secret, self.now - 301, lab.event_body())
            with patch("securitylab.webhook_lab.parse_event") as parse:
                lab.receive_delivery(connection, "fixed", stale, self.secret, self.now)
                parse.assert_not_called()
            valid = lab.signed_delivery(self.secret, self.now, lab.event_body())
            self.assertEqual(lab.receive_delivery(connection, "fixed", valid, self.secret, self.now)["outcome"], "applied")

    def test_exact_replay_and_resigned_retry_are_deduplicated_by_event_id(self):
        for fixture in ("duplicate", "resigned-retry"):
            results = self.compare(fixture).json()["results"]
            self.assertEqual(results["vulnerable"]["balanceAfter"], 20)
            fixed = results["fixed"]
            self.assertEqual(fixed["balanceAfter"], 10)
            self.assertEqual(fixed["processedEventIds"], ["evt_demo_1"])
            first, retry = fixed["deliveries"]
            self.assertEqual([first["outcome"], retry["outcome"]], ["applied", "duplicate"])
            self.assertEqual(retry["balanceBefore"], retry["balanceAfter"])
            self.assertEqual(retry["sideEffect"], 0)
            self.assertTrue(retry["signatureValid"])
            self.assertEqual(first["rawBody"], retry["rawBody"])
            self.assertEqual(first["signature"] == retry["signature"], fixture == "duplicate")

    def test_signed_but_invalid_schema_does_not_reserve_an_event_id(self):
        for result in self.compare("invalid-schema").json()["results"].values():
            self.assertEqual(result["balanceAfter"], 0)
            self.assertTrue(result["deliveries"][0]["signatureValid"])
            self.assertEqual(result["deliveries"][0]["outcome"], "rejected")
        with closing(lab.create_store()) as connection:
            invalid = lab.signed_delivery(self.secret, self.now, lab.event_body(account="OTHER"))
            lab.receive_delivery(connection, "fixed", invalid, self.secret, self.now)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM processed_events").fetchone()[0], 0)
            valid = lab.signed_delivery(self.secret, self.now, lab.event_body())
            self.assertEqual(lab.receive_delivery(connection, "fixed", valid, self.secret, self.now)["outcome"], "applied")
        invalid_bodies = [b'{"id":"evt_demo_1","id":"evt_demo_2"}', b"{}", b"[]", b" "]
        for field, value in (("units", True), ("units", -1), ("units", 101), ("units", 1.5),
                             ("id", "../id"), ("type", "unsupported"), ("extra", "field")):
            event = json.loads(lab.event_body())
            event[field] = value
            invalid_bodies.append(json.dumps(event).encode())
        for raw in invalid_bodies:
            with self.assertRaises(ValueError):
                lab.parse_event(raw)

    def test_event_claim_and_credit_roll_back_together_on_real_database_failure(self):
        with closing(lab.create_store()) as connection:
            connection.execute("CREATE TRIGGER fail_credit BEFORE UPDATE ON ledger BEGIN SELECT RAISE(ABORT, 'fixture failure'); END")
            delivery = lab.signed_delivery(self.secret, self.now, lab.event_body())
            with self.assertRaises(sqlite3.IntegrityError):
                lab.receive_delivery(connection, "fixed", delivery, self.secret, self.now)
            self.assertFalse(connection.in_transaction)
            self.assertEqual(lab.read_balance(connection), 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM processed_events").fetchone()[0], 0)
            connection.execute("DROP TRIGGER fail_credit")
            self.assertEqual(lab.receive_delivery(connection, "fixed", delivery, self.secret, self.now)["outcome"], "applied")
            self.assertEqual(lab.read_balance(connection), 10)

    def test_event_ids_are_scoped_to_trusted_provider_context(self):
        with closing(lab.create_store()) as connection:
            event = lab.parse_event(lab.event_body())
            self.assertEqual(lab.apply_event(connection, event, "fixed", "provider-a"), "applied")
            self.assertEqual(lab.apply_event(connection, event, "fixed", "provider-a"), "duplicate")
            self.assertEqual(lab.apply_event(connection, event, "fixed", "provider-b"), "applied")
            self.assertEqual(lab.read_balance(connection), 20)

    def test_comparisons_have_fresh_secrets_and_independent_state(self):
        with (patch("securitylab.webhook_lab.secrets.token_bytes", side_effect=[b"A" * 32, b"B" * 32]) as secret,
              patch("securitylab.webhook_lab.time.time", return_value=self.now)):
            first = self.compare("duplicate").json()
            second = self.compare("normal").json()
        self.assertEqual(secret.call_count, 2)
        for result in second["results"].values():
            self.assertEqual(result["balanceBefore"], 0)
            self.assertEqual(result["balanceAfter"], 10)
        self.assertNotEqual(first["results"]["fixed"]["deliveries"][0]["signature"], second["results"]["fixed"]["deliveries"][0]["signature"])
        self.assertNotIn("secret", first)

    def test_http_rejects_arbitrary_events_and_invalid_selectors_before_execution(self):
        invalid = ({}, [], {"fixture": None}, {"fixture": []}, {"fixture": "missing"},
                   {"fixture": "normal", "url": "http://example.invalid"}, {"fixture": "normal", "body": "anything"})
        with patch("securitylab.webhook_lab.compare_fixture") as run:
            for body in invalid:
                self.assertEqual(self.client.post("/api/webhook/compare/", body, content_type="application/json").status_code, 400)
            for raw in ("{", '{"fixture":"normal","fixture":"duplicate"}', " " * 2049, "[" * 1000 + "]" * 1000):
                self.assertEqual(self.client.post("/api/webhook/compare/", raw, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/webhook/compare/?fixture=normal", {"fixture": "normal"}, content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/api/webhook/compare/", {"fixture": "normal"}).status_code, 400)
            run.assert_not_called()
        response = self.client.get("/api/webhook/compare/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")

    def test_browser_harness_requires_csrf_and_accepts_same_origin_token(self):
        client = Client(enforce_csrf_checks=True)
        body = json.dumps({"fixture": "normal"})
        self.assertEqual(client.post("/api/webhook/compare/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        response = client.post("/api/webhook/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"]["fixed"]["balanceAfter"], 10)
        self.assertEqual(client.post("/api/webhook/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token,
                                     HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)
