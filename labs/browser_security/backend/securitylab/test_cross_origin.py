"""HTTP boundaries for the two-origin lesson; browser tests verify CORS enforcement."""

from urllib.parse import urlencode, urlsplit

from django.test import Client, TestCase, override_settings


MAIN_ORIGIN = "http://127.0.0.1:8766"
PEER_ORIGIN = "http://127.0.0.1:8767"


@override_settings(LAB_ROLE="main", LAB_MAIN_ORIGIN=MAIN_ORIGIN, LAB_PEER_ORIGIN=PEER_ORIGIN)
class CrossOriginHTTPTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True, HTTP_HOST="127.0.0.1:8766")
        bootstrap = self.client.get("/api/bootstrap")
        self.assertEqual(bootstrap.status_code, 200)
        self.csrf = bootstrap.json()["csrfToken"]
        self.prepared = self.prepare()
        self.run_id = self.prepared["runId"]

    def prepare(self):
        response = self.client.post(
            "/api/cross-origin/prepare/",
            data="{}",
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf,
            HTTP_ORIGIN=MAIN_ORIGIN,
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def endpoint(self, name, mode=None, run_id=None):
        path = f"/api/cross-origin/{name}/"
        if mode is not None:
            path += mode + "/"
        return path + "?" + urlencode({"run": run_id or self.run_id})

    def change(self, mode, origin=PEER_ORIGIN, token=None, client=None, run_id=None):
        headers = {}
        if origin is not None:
            headers["HTTP_ORIGIN"] = origin
        if token is not None:
            headers["HTTP_X_CSRFTOKEN"] = token
        return (client or self.client).post(
            self.endpoint("change", mode, run_id),
            data="action=increment",
            content_type="application/x-www-form-urlencoded",
            **headers,
        )

    def counts(self):
        response = self.client.get(self.endpoint("state"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["runId"], self.run_id)
        return response.json()["counts"]

    def test_preparation_requires_csrf_and_identifies_both_origins(self):
        refused = self.client.post(
            "/api/cross-origin/prepare/", data="{}", content_type="application/json"
        )
        self.assertEqual(refused.status_code, 403)
        self.assertEqual(self.prepared["mainOrigin"], MAIN_ORIGIN)
        self.assertEqual(self.prepared["peerOrigin"], PEER_ORIGIN)
        peer_url = urlsplit(self.prepared["peerUrl"])
        self.assertEqual(f"{peer_url.scheme}://{peer_url.netloc}", PEER_ORIGIN)
        self.assertEqual(peer_url.path, "/peer/")
        self.assertFalse(peer_url.query)
        self.assertEqual(self.counts(), {"vulnerable": 0, "fixed": 0})

    def test_fixed_same_origin_requires_a_csrf_token(self):
        response = self.change("fixed", origin=MAIN_ORIGIN)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.counts(), {"vulnerable": 0, "fixed": 0})

    def test_fixed_same_origin_valid_token_is_a_positive_control(self):
        response = self.change("fixed", origin=MAIN_ORIGIN, token=self.csrf)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.counts(), {"vulnerable": 0, "fixed": 1})

    def test_fixed_rejects_peer_origin_even_with_a_valid_token(self):
        for token in (None, self.csrf):
            with self.subTest(token_present=token is not None):
                response = self.change("fixed", token=token)
                self.assertEqual(response.status_code, 403)
                self.assertNotIn("Access-Control-Allow-Origin", response)
        self.assertEqual(self.counts(), {"vulnerable": 0, "fixed": 0})

    def test_vulnerable_peer_post_changes_state_without_exposing_its_response(self):
        response = self.change("vulnerable")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Access-Control-Allow-Origin", response)
        self.assertNotIn("Access-Control-Allow-Credentials", response)
        self.assertEqual(self.counts(), {"vulnerable": 1, "fixed": 0})

    def test_vulnerable_demonstration_accepts_only_the_two_configured_origins(self):
        for origin in (
            None, "null", "http://example.invalid", "http://127.0.0.1:8768",
            "http://127.0.0.1:8767.example.invalid", "https://127.0.0.1:8767",
        ):
            with self.subTest(origin=origin):
                self.assertEqual(self.change("vulnerable", origin=origin).status_code, 403)
        self.assertEqual(self.counts(), {"vulnerable": 0, "fixed": 0})
        self.assertEqual(self.change("vulnerable", origin=MAIN_ORIGIN).status_code, 200)
        self.assertEqual(self.counts()["vulnerable"], 1)

    def test_active_run_cannot_be_used_from_another_session(self):
        other = Client(enforce_csrf_checks=True, HTTP_HOST="127.0.0.1:8766")
        self.assertEqual(other.get("/api/bootstrap").status_code, 200)
        self.assertEqual(other.get(self.endpoint("state")).status_code, 404)
        self.assertEqual(self.change("vulnerable", client=other).status_code, 404)
        for mode in ("vulnerable", "fixed"):
            with self.subTest(mode=mode):
                response = other.get(self.endpoint("data", mode), HTTP_ORIGIN=PEER_ORIGIN)
                self.assertEqual(response.status_code, 404)
                self.assertNotIn(b"CORS_SYNTHETIC_SECRET", response.content)
        self.assertEqual(self.counts(), {"vulnerable": 0, "fixed": 0})

    def test_preparing_a_new_run_invalidates_old_evidence_and_resets_counters(self):
        self.assertEqual(self.change("vulnerable").status_code, 200)
        old_run = self.run_id
        self.run_id = self.prepare()["runId"]
        self.assertNotEqual(self.run_id, old_run)
        self.assertEqual(self.client.get(self.endpoint("state", run_id=old_run)).status_code, 404)
        self.assertEqual(self.change("vulnerable", run_id=old_run).status_code, 404)
        self.assertEqual(self.counts(), {"vulnerable": 0, "fixed": 0})

    def test_synthetic_counter_is_bounded(self):
        for _ in range(10):
            self.assertEqual(self.change("vulnerable").status_code, 200)
        overflow = self.change("vulnerable")
        self.assertLess(overflow.status_code, 500)
        self.assertEqual(self.counts(), {"vulnerable": 10, "fixed": 0})

    def test_only_vulnerable_cors_response_shares_the_synthetic_marker_with_peer(self):
        for mode in ("vulnerable", "fixed"):
            with self.subTest(mode=mode):
                response = self.client.get(self.endpoint("data", mode), HTTP_ORIGIN=PEER_ORIGIN)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {
                    "runId": self.run_id, "marker": "CORS_SYNTHETIC_SECRET", "synthetic": True,
                })
                if mode == "vulnerable":
                    self.assertEqual(response["Access-Control-Allow-Origin"], PEER_ORIGIN)
                    self.assertEqual(response["Access-Control-Allow-Credentials"], "true")
                    self.assertIn("origin", response.get("Vary", "").lower())
                else:
                    self.assertNotEqual(response.get("Access-Control-Allow-Origin"), PEER_ORIGIN)
                    self.assertNotEqual(response.get("Access-Control-Allow-Origin"), "*")
        self.assertEqual(self.counts(), {"vulnerable": 0, "fixed": 0})

    def test_cors_does_not_reflect_unconfigured_origins(self):
        for origin in (
            "null", "http://example.invalid", "http://127.0.0.1:8768",
            "http://127.0.0.1:8767.example.invalid", "https://127.0.0.1:8767",
        ):
            with self.subTest(origin=origin):
                response = self.client.get(self.endpoint("data", "vulnerable"), HTTP_ORIGIN=origin)
                self.assertNotIn("Access-Control-Allow-Origin", response)
                self.assertNotIn("Access-Control-Allow-Credentials", response)

    def test_cors_allowance_does_not_apply_to_other_routes(self):
        for path in ("/api/bootstrap", "/api/health", self.endpoint("state")):
            with self.subTest(path=path):
                response = self.client.get(path, HTTP_ORIGIN=PEER_ORIGIN)
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("Access-Control-Allow-Origin", response)
                self.assertNotIn("Access-Control-Allow-Credentials", response)

    def test_extra_and_duplicate_query_parameters_are_rejected(self):
        for suffix in ("&run=" + self.run_id, "&unexpected=1"):
            for name, mode in (("state", None), ("data", "vulnerable"), ("data", "fixed")):
                with self.subTest(name=name, mode=mode, suffix=suffix):
                    response = self.client.get(self.endpoint(name, mode) + suffix)
                    self.assertEqual(response.status_code, 400)
                    self.assertIn("error", response.json())
            for mode in ("vulnerable", "fixed"):
                with self.subTest(mode=mode, suffix=suffix):
                    response = self.client.post(
                        self.endpoint("change", mode) + suffix,
                        data="action=increment", content_type="application/x-www-form-urlencoded",
                        HTTP_ORIGIN=MAIN_ORIGIN, HTTP_X_CSRFTOKEN=self.csrf,
                    )
                    self.assertEqual(response.status_code, 400)
        self.assertEqual(self.counts(), {"vulnerable": 0, "fixed": 0})

    def test_unknown_runs_do_not_read_or_mutate_current_state(self):
        unknown = ("A" if self.run_id[0] != "A" else "B") + self.run_id[1:]
        self.assertEqual(self.client.get(self.endpoint("state", run_id=unknown)).status_code, 404)
        self.assertEqual(self.change("vulnerable", run_id=unknown).status_code, 404)
        self.assertEqual(
            self.change("fixed", origin=MAIN_ORIGIN, token=self.csrf, run_id=unknown).status_code, 404
        )
        for mode in ("vulnerable", "fixed"):
            with self.subTest(mode=mode):
                response = self.client.get(self.endpoint("data", mode, unknown), HTTP_ORIGIN=PEER_ORIGIN)
                self.assertEqual(response.status_code, 404)
                self.assertNotIn(b"CORS_SYNTHETIC_SECRET", response.content)
        self.assertEqual(self.counts(), {"vulnerable": 0, "fixed": 0})

    def test_peer_pages_allow_both_lessons_without_touching_session_cookies(self):
        with override_settings(LAB_ROLE="peer"):
            for lesson in ("csrf", "cors"):
                with self.subTest(lesson=lesson):
                    response = self.client.get(
                        "/peer/", {"run": self.run_id, "lesson": lesson}, HTTP_HOST="127.0.0.1:8767"
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertFalse(response.cookies)
                    policy = response["Content-Security-Policy"]
                    self.assertIn(f"connect-src {MAIN_ORIGIN}", policy)
                    self.assertIn(f"frame-ancestors {MAIN_ORIGIN}", policy)
                    self.assertNotIn("sandbox", policy)
            script = self.client.get("/peer/boot.js", HTTP_HOST="127.0.0.1:8767")
            self.assertEqual(script.status_code, 200)
            self.assertIn("javascript", script["Content-Type"])
            self.assertFalse(script.cookies)
            health = self.client.get("/api/health", HTTP_HOST="127.0.0.1:8767")
            self.assertEqual(health.status_code, 200)
            self.assertFalse(health.cookies)
        self.assertEqual(self.counts(), {"vulnerable": 0, "fixed": 0})

    def test_peer_role_cannot_serve_dashboard_data_assets_or_existing_labs(self):
        with override_settings(LAB_ROLE="peer"):
            for path in (
                "/", "/api/bootstrap", self.endpoint("state"),
                self.endpoint("data", "vulnerable"), "/api/uploads/", "/api/traversal/",
                "/lab/frame/", "/lab/jsonp.js?callback=labJsonp", "/assets/index.js",
            ):
                with self.subTest(path=path):
                    response = self.client.get(path, HTTP_HOST="127.0.0.1:8767")
                    self.assertEqual(response.status_code, 404)
                    self.assertFalse(response.cookies)
                    self.assertNotIn("Access-Control-Allow-Origin", response)
            response = self.change("vulnerable")
            self.assertEqual(response.status_code, 404)
        self.assertEqual(self.counts(), {"vulnerable": 0, "fixed": 0})
