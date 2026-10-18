"""Stored queue transitions, separate execution/delivery decisions, and HTTP limits."""
from contextlib import closing
import json
from unittest.mock import patch

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, SimpleTestCase, override_settings
from django.urls import path

from . import queue_lab as lab

urlpatterns = [path("api/queue/compare/", lab.queue_compare)]


@override_settings(ROOT_URLCONF=__name__)
class QueueLabTests(SimpleTestCase):
    def compare(self, fixture="normal"):
        response = self.client.post("/api/queue/compare/", {"fixture": fixture}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_allowed_control_stores_a_job_artifact_and_delivers_its_actual_marker(self):
        for result in self.compare()["results"].values():
            self.assertEqual(result["outcome"], "delivered")
            self.assertEqual(result["jobCount"], 1)
            self.assertEqual(result["artifactCount"], 1)
            self.assertEqual(result["jobState"], "completed")
            self.assertEqual(result["deliveredMarker"], lab.MARKER)
            self.assertEqual([item["decision"] for item in result["events"]], ["queued", "created", "delivered"])

    def test_revocation_before_worker_prevents_fixed_artifact_creation(self):
        results = self.compare("revoke-before-worker")["results"]
        self.assertEqual(results["vulnerable"]["deliveredMarker"], lab.MARKER)
        self.assertEqual(results["vulnerable"]["artifactCount"], 1)
        fixed = results["fixed"]
        self.assertFalse(fixed["submitterPermissionNow"])
        self.assertEqual(fixed["jobs"][0]["granted_at_enqueue"], 1)
        self.assertEqual(fixed["jobCount"], 1)
        self.assertEqual(fixed["jobState"], "denied")
        self.assertEqual(fixed["artifacts"], [])
        self.assertIsNone(fixed["deliveredMarker"])
        self.assertEqual([item["decision"] for item in fixed["events"]], ["queued", "revoked", "denied", "unavailable"])

    def test_revocation_after_worker_keeps_artifact_but_denies_delivery(self):
        results = self.compare("revoke-before-download")["results"]
        for result in results.values():
            self.assertEqual(result["jobState"], "completed")
            self.assertEqual(result["artifactCount"], 1)
            self.assertFalse(result["downloaderPermissionNow"])
        self.assertEqual(results["vulnerable"]["deliveredMarker"], lab.MARKER)
        self.assertIsNone(results["fixed"]["deliveredMarker"])
        self.assertEqual([item["decision"] for item in results["fixed"]["events"]], ["queued", "created", "revoked", "denied"])
        self.assertNotIn("marker", results["fixed"]["artifacts"][0])

    def test_owner_and_tenant_checks_are_independent_of_current_export_permission(self):
        for fixture in ("peer-download", "cross-tenant-download"):
            with self.subTest(fixture=fixture):
                body = self.compare(fixture)
                fixed = body["results"]["fixed"]
                self.assertTrue(fixed["downloaderPermissionNow"])
                self.assertEqual(fixed["artifactCount"], 1)
                self.assertIsNone(fixed["deliveredMarker"])
                self.assertEqual(body["results"]["vulnerable"]["deliveredMarker"], lab.MARKER)
                artifact = fixed["artifacts"][0]
                self.assertEqual(artifact["owner"] == body["downloader"]["id"], fixture == "cross-tenant-download")
                self.assertEqual(artifact["tenant"] == body["downloader"]["tenantId"], fixture == "peer-download")

    def test_initial_denial_does_not_enqueue_any_job_or_create_an_artifact(self):
        for result in self.compare("initially-denied")["results"].values():
            self.assertEqual(result["jobs"], [])
            self.assertEqual(result["artifacts"], [])
            self.assertIsNone(result["deliveredMarker"])
            self.assertEqual([item["decision"] for item in result["events"]], ["revoked", "denied", "skipped", "unavailable"])

    def test_worker_rereads_resource_owner_and_tenant_not_just_membership(self):
        for column, value in (("owner", "user-bea"), ("tenant", "tenant-amber")):
            for mode in ("vulnerable", "fixed"):
                with self.subTest(column=column, mode=mode), closing(lab.create_store()) as connection:
                    job_id = lab.enqueue(connection, mode, lab.ACTOR)
                    # The column comes from this fixed test tuple, never input.
                    with connection:
                        connection.execute(f"UPDATE resources SET {column} = ? WHERE id = 1", (value,))
                    self.assertTrue(lab.permitted(connection, lab.ACTOR))
                    self.assertEqual(lab.process_job(connection, mode, job_id), mode == "vulnerable")
                    self.assertEqual(connection.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0], int(mode == "vulnerable"))

    def test_missing_membership_denies_execution_and_delivery(self):
        for stage in ("worker", "download"):
            with self.subTest(stage=stage), closing(lab.create_store()) as connection:
                job_id = lab.enqueue(connection, "fixed", lab.ACTOR)
                if stage == "download":
                    self.assertTrue(lab.process_job(connection, "fixed", job_id))
                with connection:
                    connection.execute("DELETE FROM memberships WHERE principal = ? AND tenant = ?", (lab.ACTOR["id"], lab.ACTOR["tenantId"]))
                if stage == "worker":
                    self.assertFalse(lab.process_job(connection, "fixed", job_id))
                self.assertIsNone(lab.download(connection, "fixed", lab.ACTOR, job_id))

    def test_queue_really_stores_state_and_download_reads_the_stored_payload(self):
        with closing(lab.create_store()) as connection:
            job_id = lab.enqueue(connection, "fixed", lab.ACTOR)
            self.assertEqual(connection.execute("SELECT state FROM jobs WHERE id = ?", (job_id,)).fetchone()[0], "queued")
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0], 0)
            with connection:
                connection.execute("UPDATE resources SET marker = ? WHERE id = 1", ("CHANGED-FICTIONAL-MARKER",))
            self.assertTrue(lab.process_job(connection, "fixed", job_id))
            self.assertFalse(lab.process_job(connection, "fixed", job_id))
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0], 1)
            with connection:
                connection.execute("UPDATE resources SET marker = ? WHERE id = 1", ("LATER-RESOURCE-MARKER",))
            self.assertEqual(lab.download(connection, "fixed", lab.ACTOR, job_id), "CHANGED-FICTIONAL-MARKER")

    def test_fixtures_and_modes_have_fresh_isolated_state(self):
        first = self.compare()
        for fixture in lab.FIXTURES:
            self.compare(fixture)
        self.assertEqual(first, self.compare())

    def test_selector_rejects_authority_and_malformed_input_before_creating_store(self):
        with patch("securitylab.queue_lab.create_store") as create:
            for body in ({}, [], {"fixture": None}, {"fixture": []}, {"fixture": "unknown"},
                         {"fixture": "normal", "actor": "admin"}, {"fixture": "normal", "permission": True},
                         {"fixture": "normal", "jobId": 1}, {"fixture": "normal", "mode": "fixed"}):
                self.assertEqual(self.client.post("/api/queue/compare/", body, content_type="application/json").status_code, 400)
            for raw in ("{", '{"fixture":"normal","fixture":"initially-denied"}', " " * 2049, "[" * 1000 + "]" * 1000, b"\xff"):
                self.assertEqual(self.client.post("/api/queue/compare/", raw, content_type="application/json").status_code, 400)
            create.assert_not_called()

    def test_http_method_content_type_and_query_boundaries(self):
        response = self.client.get("/api/queue/compare/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")
        self.assertEqual(self.client.post("/api/queue/compare/", {"fixture": "normal"}).status_code, 400)
        self.assertEqual(self.client.post("/api/queue/compare/?actor=admin", {"fixture": "normal"}, content_type="application/json").status_code, 400)

    def test_csrf_protection_remains_enabled(self):
        client = Client(enforce_csrf_checks=True)
        body = json.dumps({"fixture": "normal"})
        self.assertEqual(client.post("/api/queue/compare/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        self.assertEqual(client.post("/api/queue/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(client.post("/api/queue/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token,
                                     HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)
