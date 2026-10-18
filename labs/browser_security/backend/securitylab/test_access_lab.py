"""Check identity, object, tenant and action boundaries over harmless records."""
import json

from django.test import Client, TestCase

from .access_lab import RECORDS


class AccessLabTests(TestCase):
    def choose(self, actor_id, client=None):
        client = client or self.client
        return client.post("/api/access/identity/", {"actorId": actor_id}, content_type="application/json")

    def read(self, record="alice-a", mode="fixed", action="read", client=None):
        return (client or self.client).get("/api/access/record/", {"mode": mode, "record": record, "action": action})

    def assert_no_record(self, response, status, outcome):
        self.assertEqual(response.status_code, status)
        self.assertEqual(response.json()["outcome"], outcome)
        self.assertIsNone(response.json()["record"])
        for record in RECORDS.values():
            self.assertNotIn(record["marker"], response.content.decode())

    def test_owner_can_read_in_both_modes_but_cannot_review_in_fixed(self):
        for actor, record in (("alice", "alice-a"), ("bob", "bob-a"), ("carol", "carol-b")):
            self.choose(actor)
            for mode in ("vulnerable", "fixed"):
                with self.subTest(actor=actor, mode=mode):
                    response = self.read(record, mode)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json()["record"]["marker"], RECORDS[record]["marker"])
            self.assert_no_record(self.read(record, action="review"), 403, "denied")

    def test_peer_idor_and_cross_tenant_reads_are_denied_only_by_fixed_handler(self):
        self.choose("alice")
        for record in ("bob-a", "carol-b"):
            for action in ("read", "review"):
                with self.subTest(record=record, action=action):
                    vulnerable = self.read(record, "vulnerable", action)
                    self.assertEqual(vulnerable.status_code, 200)
                    self.assertEqual(vulnerable.json()["record"]["marker"], RECORDS[record]["marker"])
                    self.assert_no_record(self.read(record, action=action), 403, "denied")

    def test_admin_can_read_and_review_own_tenant_but_not_another_tenant(self):
        self.choose("admin-a")
        for action in ("read", "review"):
            for record in ("alice-a", "bob-a"):
                self.assertEqual(self.read(record, action=action).status_code, 200)
            self.assert_no_record(self.read("carol-b", action=action), 403, "denied")
            self.assertEqual(self.read("carol-b", "vulnerable", action).status_code, 200)

    def test_anonymous_and_invalid_session_identity_fail_closed_in_both_handlers(self):
        for actor in (None, "anonymous", "not-a-persona", {"role": "admin"}):
            session = self.client.session
            if actor is None:
                session.pop("lab_actor", None)
            else:
                session["lab_actor"] = actor
            session.save()
            for mode in ("vulnerable", "fixed"):
                for action in ("read", "review"):
                    self.assert_no_record(self.read(mode=mode, action=action), 401, "unauthenticated")

    def test_state_exposes_only_synthetic_metadata_and_identity_is_session_local(self):
        other = Client()
        self.assertEqual(self.client.get("/api/access/state/").json()["actorId"], "anonymous")
        self.choose("alice")
        self.choose("admin-a", other)
        for client, actor in ((self.client, "alice"), (other, "admin-a")):
            response = client.get("/api/access/state/")
            self.assertEqual(response.json()["actorId"], actor)
            self.assertIn("no-store", response["Cache-Control"])
            for record in RECORDS.values():
                self.assertNotIn(record["marker"], response.content.decode())
        self.assert_no_record(self.read("bob-a"), 403, "denied")
        self.assertEqual(self.read("bob-a", client=other).status_code, 200)

    def test_identity_change_requires_csrf_and_validates_the_real_token(self):
        client = Client(enforce_csrf_checks=True)
        token = client.get("/api/bootstrap").json()["csrfToken"]
        missing = client.post("/api/access/identity/", {"actorId": "alice"}, content_type="application/json")
        self.assertEqual(missing.status_code, 403)
        self.assertEqual(client.get("/api/access/state/").json()["actorId"], "anonymous")
        valid = client.post("/api/access/identity/", {"actorId": "alice"}, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(valid.status_code, 200)
        self.assertEqual(client.get("/api/access/state/").json()["actorId"], "alice")

    def test_identity_rejects_forged_role_tenant_unknown_and_duplicate_fields(self):
        self.choose("alice")
        cases = [
            '{"actorId":"alice","role":"admin"}',
            '{"actorId":"alice","tenant":"team-b"}',
            '{"actorId":"alice","actorId":"admin-a"}',
            '{"actorId":"nobody"}', '{"actorId":[]}', '[]', 'null', '{}', 'not-json',
        ]
        for raw in cases:
            with self.subTest(raw=raw):
                response = self.client.post("/api/access/identity/", raw, content_type="application/json")
                self.assertEqual(response.status_code, 400)
                self.assertEqual(self.client.get("/api/access/state/").json()["actorId"], "alice")
        self.assertEqual(self.client.post("/api/access/identity/?role=admin", json.dumps({"actorId": "admin-a"}), content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/api/access/identity/", {"actorId": "admin-a"}).status_code, 400)

    def test_record_query_rejects_duplicates_forged_roles_and_invalid_inputs(self):
        self.choose("alice")
        queries = (
            "mode=fixed&role=admin", "mode=fixed&tenant=team-b", "actorId=admin-a",
            "record=alice-a&record=bob-a", "mode=fixed&mode=vulnerable",
            "action=read&action=review", "mode=unknown", "action=delete", "record=", "record=" + "x" * 65,
        )
        for query in queries:
            with self.subTest(query=query):
                self.assert_no_record(self.client.get("/api/access/record/?" + query), 400, "invalid")
        # Even bogus role/tenant session data cannot override the server fixture map.
        session = self.client.session
        session["role"] = "admin"
        session["tenant"] = "team-b"
        session.save()
        self.assert_no_record(self.read("bob-a", action="review"), 403, "denied")

    def test_missing_records_methods_and_response_cache_policy(self):
        self.choose("alice")
        for mode in ("vulnerable", "fixed"):
            self.assert_no_record(self.read("does-not-exist", mode), 404, "not_found")
            response = self.read(mode=mode)
            self.assertIn("no-store", response["Cache-Control"])
            self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        for path, allowed in (("state", "GET"), ("record", "GET")):
            response = self.client.post(f"/api/access/{path}/")
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], allowed)
        response = self.client.get("/api/access/identity/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")
        self.assertEqual(self.client.get("/api/access/state/?role=admin").status_code, 400)

    def test_review_does_not_mutate_records_or_other_session_state(self):
        self.choose("admin-a")
        before = json.dumps(RECORDS, sort_keys=True)
        session_before = dict(self.client.session)
        for mode in ("vulnerable", "fixed"):
            self.assertEqual(self.read("bob-a", mode, "review").status_code, 200)
        self.assertEqual(json.dumps(RECORDS, sort_keys=True), before)
        self.assertEqual(dict(self.client.session), session_before)
