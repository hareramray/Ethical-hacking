"""Real HTTP SSRF comparisons inside a closed, per-request fixture network."""
import http.client
import json
import re
import socket
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import TCPServer
from urllib.parse import urlsplit

from django.http import JsonResponse

PUBLIC_HOST = "public.fixture.test"
PRIVATE_HOST = "private.fixture.test"
PUBLIC_MARKER = "PUBLIC_SSRF_FIXTURE"
PRIVATE_MARKER = "PRIVATE_SSRF_SENTINEL_ONLY_FOR_LAB"
MAX_TARGET = 256
MAX_REQUESTS = 4
MAX_RESPONSE = 1024
SOCKET_TIMEOUT = 1.0
FIXTURE_SLOTS = threading.BoundedSemaphore(4)
ROUTES = {
    (PUBLIC_HOST, "/info"): (200, PUBLIC_MARKER, None),
    (PRIVATE_HOST, "/marker"): (200, PRIVATE_MARKER, None),
    (PUBLIC_HOST, "/redirect-public"): (302, "", f"http://{PUBLIC_HOST}/info"),
    (PUBLIC_HOST, "/redirect-private"): (302, "", f"http://{PRIVATE_HOST}/marker"),
    (PUBLIC_HOST, "/redirect-external"): (302, "", "http://outside.invalid/info"),
    (PUBLIC_HOST, "/loop"): (302, "", f"http://{PUBLIC_HOST}/loop"),
}
SSRF_METADATA = {
    "fixtures": [
        {"id": "public", "label": "Allowed public information", "target": f"http://{PUBLIC_HOST}/info"},
        {"id": "private", "label": "Direct private fixture", "target": f"http://{PRIVATE_HOST}/marker"},
        {"id": "redirect-private", "label": "Public URL redirects to private fixture", "target": f"http://{PUBLIC_HOST}/redirect-private"},
        {"id": "redirect-public", "label": "Allowed public redirect", "target": f"http://{PUBLIC_HOST}/redirect-public"},
        {"id": "external", "label": "Destination outside the fixture boundary", "target": "http://outside.invalid/info"},
        {"id": "redirect-external", "label": "Redirect outside the fixture boundary", "target": f"http://{PUBLIC_HOST}/redirect-external"},
        {"id": "loop", "label": "Redirect loop reaches the request budget", "target": f"http://{PUBLIC_HOST}/loop"},
    ],
    "targetLimit": MAX_TARGET, "requestLimit": MAX_REQUESTS,
    "publicOrigin": f"http://{PUBLIC_HOST}", "privateOrigin": f"http://{PRIVATE_HOST}",
}


def parse_target(value):
    """Accept one deliberately small canonical URL grammar; never repair a URL."""
    if not isinstance(value, str) or not 1 <= len(value) <= MAX_TARGET:
        raise ValueError("target must contain 1 to 256 characters.")
    if not re.fullmatch(r"http://[a-z0-9.-]+/[A-Za-z0-9/_-]*", value):
        raise ValueError("Use a lowercase http:// host and a plain path; credentials, ports, escapes, queries, fragments, and whitespace are excluded.")
    parsed = urlsplit(value)
    if (parsed.scheme != "http" or parsed.netloc != parsed.hostname
            or parsed.query or parsed.fragment or not parsed.path.startswith("/")):
        raise ValueError("Use a canonical fixture URL.")
    return parsed.hostname, parsed.path


class FixtureHandler(BaseHTTPRequestHandler):
    def setup(self):
        self.request.settimeout(SOCKET_TIMEOUT)
        super().setup()

    def handle(self):
        # An absolute deadline also bounds a partial request from another local
        # process. A socket's inactivity timeout alone can reset after each byte.
        def stop_reading():
            try:
                self.request.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        deadline = threading.Timer(SOCKET_TIMEOUT, stop_reading)
        deadline.name = "ssrf-fixture-deadline"
        deadline.daemon = True
        deadline.start()
        try:
            super().handle()
        except OSError:
            pass
        finally:
            deadline.cancel()
            deadline.join(timeout=SOCKET_TIMEOUT)

    def do_GET(self):
        host = self.headers.get("Host", "")
        status, marker, location = ROUTES.get((host, self.path), (404, "FIXTURE_NOT_FOUND", None))
        body = marker.encode("ascii")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=us-ascii")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        if location:
            self.send_header("Location", location)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


class OwnedConnection(http.client.HTTPConnection):
    """Never pass a submitted host to a resolver, proxy, or socket connector."""
    def connect(self):
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            connection.settimeout(SOCKET_TIMEOUT)
            connection.connect(("127.0.0.1", self.port))
        except BaseException:
            connection.close()
            raise
        self.sock = connection


class FixtureServer(HTTPServer):
    def server_bind(self):
        # HTTPServer's default bind also performs a reverse hostname lookup.
        # This fixture needs no DNS, including that otherwise unnecessary lookup.
        TCPServer.server_bind(self)
        self.server_name = "owned-ssrf-fixture"
        self.server_port = self.server_address[1]


@contextmanager
def fixture_server():
    # No caller controls the listening address, port selection, or handler.
    server = FixtureServer(("127.0.0.1", 0), FixtureHandler)
    worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01},
                              name="ssrf-fixture", daemon=True)
    try:
        worker.start()
        yield server.server_port
    finally:
        if worker.is_alive():
            server.shutdown()
        server.server_close()
        if worker.ident is not None:
            worker.join(timeout=SOCKET_TIMEOUT + 1)


def compare_target(target, mode, owned_port):
    result = {"outcome": "invalid", "reason": "", "marker": None, "trace": []}
    current = target
    for _ in range(MAX_REQUESTS):
        try:
            host, path = parse_target(current)
        except ValueError as exc:
            result.update(outcome="invalid", reason=str(exc))
            return result
        # OUTER LAB ISOLATION: applies even to the intentionally vulnerable handler.
        # It never connects to any supplied hostname, IP, port, or unknown route.
        if host not in {PUBLIC_HOST, PRIVATE_HOST} or (host, path) not in ROUTES:
            result.update(outcome="boundary_blocked", reason="The lab boundary stopped this destination before any socket request to it.")
            return result
        # APPLICATION DEFENSE: rechecked before the initial request AND every hop.
        if mode == "fixed" and host != PUBLIC_HOST:
            result.update(outcome="blocked", reason="The application's public-origin allowlist rejected this destination before requesting it.")
            return result
        connection = OwnedConnection("127.0.0.1", owned_port, timeout=SOCKET_TIMEOUT)
        try:
            connection.putrequest("GET", path, skip_host=True, skip_accept_encoding=True)
            connection.putheader("Host", host)
            connection.putheader("Connection", "close")
            connection.endheaders()
            response = connection.getresponse()
            entry = {"url": current, "status": response.status}
            result["trace"].append(entry)
            body = response.read(MAX_RESPONSE + 1)
            if len(body) > MAX_RESPONSE:
                result.update(outcome="response_limit", reason="The response exceeded the 1024-byte lesson limit.")
                return result
            if response.status in {301, 302, 303, 307, 308}:
                current = response.getheader("Location", "")
                entry["location"] = current
                continue
            if response.status != 200:
                result.update(outcome="http_error", reason=f"The fixture returned HTTP {response.status}.")
                return result
            result.update(outcome="read", marker=body.decode("ascii"),
                          reason="Read a synthetic marker through an actual HTTP request to the owned fixture service.")
            return result
        except (OSError, http.client.HTTPException, UnicodeError):
            result.update(outcome="request_error", reason="The bounded fixture request did not complete.")
            return result
        finally:
            connection.close()
    result.update(outcome="request_limit", reason="Stopped after four HTTP requests; redirects cannot run indefinitely.")
    return result


def unique_object(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError("Duplicate JSON field")
        data[key] = value
    return data


def ssrf_compare(request):
    def invalid(reason, status=400):
        return JsonResponse({"target": None, "results": {
            mode: {"outcome": "invalid", "reason": reason, "marker": None, "trace": []}
            for mode in ("vulnerable", "fixed")}}, status=status)

    if request.method != "POST":
        response = invalid("Use POST with an application/json body.", 405)
        response["Allow"] = "POST"
        return response
    if request.GET or request.content_type != "application/json":
        return invalid("Use an application/json body without query parameters.")
    if len(request.body) > 2048:
        return invalid("The request body exceeds the lesson limit.")
    try:
        data = json.loads(request.body, object_pairs_hook=unique_object)
        if not isinstance(data, dict) or set(data) != {"target"}:
            raise ValueError("Provide exactly target.")
        parse_target(data["target"])
    except (ValueError, UnicodeDecodeError, RecursionError) as exc:
        return invalid(str(exc))
    if not FIXTURE_SLOTS.acquire(blocking=False):
        return invalid("Four comparisons are already running. Retry when one finishes.", 503)
    try:
        with fixture_server() as port:
            results = {mode: compare_target(data["target"], mode, port) for mode in ("vulnerable", "fixed")}
        return JsonResponse({"target": data["target"], "results": results})
    finally:
        FIXTURE_SLOTS.release()
