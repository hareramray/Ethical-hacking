"""HTTP behavior, destination isolation, and lifecycle checks for the SSRF lab."""
import json
import socket
import threading
import time
from unittest.mock import patch

from django.conf import settings
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, SimpleTestCase

from . import ssrf_lab as lab


class SSRFLabTests(SimpleTestCase):
    def compare(self, target):
        return self.client.post("/api/ssrf/compare/", {"target": target}, content_type="application/json")

    def test_public_information_and_public_redirect_succeed_in_both_handlers(self):
        for path, count in (("/info", 1), ("/redirect-public", 2)):
            with self.subTest(path=path):
                response = self.compare(f"http://{lab.PUBLIC_HOST}{path}")
                self.assertEqual(response.status_code, 200)
                for result in response.json()["results"].values():
                    self.assertEqual(result["outcome"], "read")
                    self.assertEqual(result["marker"], lab.PUBLIC_MARKER)
                    self.assertEqual(len(result["trace"]), count)
                    self.assertEqual(result["trace"][-1]["status"], 200)

    def test_direct_private_destination_is_requested_only_by_vulnerable_handler(self):
        results = self.compare(f"http://{lab.PRIVATE_HOST}/marker").json()["results"]
        self.assertEqual(results["vulnerable"]["marker"], lab.PRIVATE_MARKER)
        self.assertEqual(len(results["vulnerable"]["trace"]), 1)
        self.assertEqual(results["fixed"]["outcome"], "blocked")
        self.assertIsNone(results["fixed"]["marker"])
        self.assertEqual(results["fixed"]["trace"], [])

    def test_public_redirect_revalidates_private_destination_before_connection(self):
        results = self.compare(f"http://{lab.PUBLIC_HOST}/redirect-private").json()["results"]
        self.assertEqual(results["vulnerable"]["marker"], lab.PRIVATE_MARKER)
        self.assertEqual([entry["status"] for entry in results["vulnerable"]["trace"]], [302, 200])
        self.assertEqual(results["fixed"]["outcome"], "blocked")
        self.assertEqual(len(results["fixed"]["trace"]), 1)
        self.assertEqual(results["fixed"]["trace"][0]["location"], f"http://{lab.PRIVATE_HOST}/marker")
        self.assertIsNone(results["fixed"]["marker"])

    def test_external_hosts_local_services_and_unknown_paths_never_connect(self):
        targets = ("http://outside.invalid/info", "http://127.0.0.1/info",
                   "http://169.254.169.254/info", "http://localhost/info",
                   f"http://{lab.PUBLIC_HOST}.evil.invalid/info", f"http://{lab.PUBLIC_HOST}/unknown")
        with patch.object(lab.OwnedConnection, "connect") as connect:
            for target in targets:
                with self.subTest(target=target):
                    response = self.compare(target)
                    self.assertEqual(response.status_code, 200)
                    for result in response.json()["results"].values():
                        self.assertEqual(result["outcome"], "boundary_blocked")
                        self.assertEqual(result["trace"], [])
                        self.assertIsNone(result["marker"])
            connect.assert_not_called()

    def test_external_redirect_and_loop_are_bounded(self):
        external = self.compare(f"http://{lab.PUBLIC_HOST}/redirect-external").json()["results"]
        loop = self.compare(f"http://{lab.PUBLIC_HOST}/loop").json()["results"]
        for result in external.values():
            self.assertEqual(result["outcome"], "boundary_blocked")
            self.assertEqual(len(result["trace"]), 1)
            self.assertNotIn("outside.invalid", result["trace"][0]["url"])
        for result in loop.values():
            self.assertEqual(result["outcome"], "request_limit")
            self.assertEqual(len(result["trace"]), 4)
            self.assertIsNone(result["marker"])

    def test_no_dns_or_environment_proxy_and_connections_use_owned_server_port(self):
        original_connect = lab.OwnedConnection.connect
        original_server = lab.FixtureServer
        server_ports, destinations = [], []

        def tracked_server(*args, **kwargs):
            server = original_server(*args, **kwargs)
            server_ports.append(server.server_port)
            return server

        def tracked_connect(connection):
            destinations.append((connection.host, connection.port))
            self.assertEqual(connection.host, "127.0.0.1")
            self.assertIn(connection.port, server_ports)
            return original_connect(connection)

        with (patch.object(lab, "FixtureServer", side_effect=tracked_server),
              patch.object(lab.OwnedConnection, "connect", tracked_connect),
              patch("socket.getaddrinfo", side_effect=AssertionError("DNS is forbidden")),
              patch("socket.getfqdn", side_effect=AssertionError("Reverse DNS is forbidden")),
              patch.dict("os.environ", {"HTTP_PROXY": "http://outside.invalid:9999", "http_proxy": "http://outside.invalid:9999"})):
            response = self.compare(f"http://{lab.PUBLIC_HOST}/redirect-private")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(destinations), 3)
        self.assertEqual(response.json()["results"]["vulnerable"]["marker"], lab.PRIVATE_MARKER)
        self.assertFalse(any(worker.name == "ssrf-fixture" for worker in threading.enumerate()))
        for port in server_ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.settimeout(0.2)
                self.assertNotEqual(probe.connect_ex(("127.0.0.1", port)), 0)

    def test_ambiguous_and_invalid_input_is_rejected_before_starting_fixture(self):
        targets = ("", "x" * 257, 1, None, [], "file:///fixture", "https://public.fixture.test/info",
                   "http://public.fixture.test:80/info", "http://user@public.fixture.test/info",
                   "http://PUBLIC.fixture.test/info", "http://public.fixture.test/info?",
                   "http://public.fixture.test/info#", "http://public%2efixture.test/info",
                   "http://public.fixture.test/%69nfo", "http://public.fixture.test\\@private.fixture.test/info",
                   " http://public.fixture.test/info", "http://public.fixture.test/in\nfo", "\ud800")
        with patch.object(lab, "fixture_server") as server:
            for target in targets:
                with self.subTest(target=target):
                    response = self.compare(target)
                    self.assertEqual(response.status_code, 400)
                    self.assertTrue(all(result["outcome"] == "invalid" for result in response.json()["results"].values()))
            for body in ({}, [], {"target": f"http://{lab.PUBLIC_HOST}/info", "extra": 1}):
                self.assertEqual(self.client.post("/api/ssrf/compare/", body, content_type="application/json").status_code, 400)
            for body in ("{", '{"target":"x","target":"y"}'):
                self.assertEqual(self.client.post("/api/ssrf/compare/", body, content_type="application/json").status_code, 400)
            server.assert_not_called()
        self.assertEqual(self.client.post("/api/ssrf/compare/?extra=1", {"target": "x"}, content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/api/ssrf/compare/", {"target": "x"}).status_code, 400)
        response = self.client.get("/api/ssrf/compare/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")

    def test_response_limit_connection_failure_and_fixture_cleanup(self):
        with patch.dict(lab.ROUTES, {(lab.PUBLIC_HOST, "/info"): (200, "A" * (lab.MAX_RESPONSE + 1), None)}):
            response = self.compare(f"http://{lab.PUBLIC_HOST}/info")
        for result in response.json()["results"].values():
            self.assertEqual(result["outcome"], "response_limit")
            self.assertIsNone(result["marker"])
        with patch.object(lab.OwnedConnection, "connect", side_effect=TimeoutError):
            response = self.compare(f"http://{lab.PUBLIC_HOST}/info")
        self.assertTrue(all(result["outcome"] == "request_error" for result in response.json()["results"].values()))
        self.assertFalse(any(worker.name == "ssrf-fixture" for worker in threading.enumerate()))

    def test_partial_local_request_cannot_prevent_fixture_shutdown(self):
        entered = threading.Event()
        original_handle = lab.FixtureHandler.handle

        def observed_handle(handler):
            entered.set()
            original_handle(handler)

        started = time.monotonic()
        with patch.object(lab.FixtureHandler, "handle", observed_handle):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.settimeout(2)
                with lab.fixture_server() as port:
                    client.connect(("127.0.0.1", port))
                    client.sendall(b"GET /info HTTP/1.1\r\nHost: public.fixture.test\r\n")
                    self.assertTrue(entered.wait(timeout=1))
                self.assertLess(time.monotonic() - started, 3)
        self.assertFalse(any(worker.name.startswith("ssrf-fixture") for worker in threading.enumerate()))

    def test_comparison_requires_csrf_and_accepts_legitimate_token(self):
        client = Client(enforce_csrf_checks=True)
        body = json.dumps({"target": f"http://{lab.PUBLIC_HOST}/info"})
        self.assertEqual(client.post("/api/ssrf/compare/", body, content_type="application/json").status_code, 403)
        request = RequestFactory().get("/")
        token = get_token(request)
        client.cookies[settings.CSRF_COOKIE_NAME] = request.META["CSRF_COOKIE"]
        response = client.post("/api/ssrf/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.post("/api/ssrf/compare/", body, content_type="application/json", HTTP_X_CSRFTOKEN=token,
                                     HTTP_ORIGIN="http://untrusted.invalid").status_code, 403)
