"""HTTP/session and ASGI authorization contracts; browser tests exercise upgrades."""
import asyncio
import json
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit

from asgiref.sync import async_to_sync, sync_to_async
from asgiref.testing import ApplicationCommunicator
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.test import Client, TransactionTestCase, override_settings
from django.urls import path

from . import websocket_lab as lesson

MAIN = "http://127.0.0.1:8766"
PEER = "http://127.0.0.1:8767"


def bootstrap(request):
    return JsonResponse({"csrfToken": get_token(request)})


urlpatterns = [
    path("api/bootstrap", bootstrap),
    path("api/websocket/prepare/", lesson.websocket_prepare),
    path("api/websocket/state/", lesson.websocket_state),
    path("api/websocket/revoke/", lesson.websocket_revoke),
    path("lab/websocket/frame/", lesson.websocket_frame),
    path("lab/websocket/boot.js", lesson.websocket_script),
    path("peer/websocket/", lesson.websocket_peer),
    path("peer/websocket/boot.js", lesson.websocket_peer_script),
]


@override_settings(ROOT_URLCONF=__name__, LAB_ROLE="main", LAB_MAIN_ORIGIN=MAIN, LAB_PEER_ORIGIN=PEER)
class WebSocketTests(TransactionTestCase):
    def setUp(self):
        with lesson._lock:
            lesson._runs.clear()
        self.client = Client(enforce_csrf_checks=True, HTTP_HOST="127.0.0.1:8766")
        self.csrf = self.client.get("/api/bootstrap").json()["csrfToken"]

    def prepare(self, fixture="allowed"):
        response = self.client.post("/api/websocket/prepare/", json.dumps({"fixture": fixture}), content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf, HTTP_ORIGIN=MAIN)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        data["query"] = parse_qs(urlsplit(data["harness"]).query)
        return data

    def scope(self, prepared, mode="fixed", origin=MAIN):
        return {"type": "websocket", "asgi": {"version": "3.0"}, "scheme": "ws", "path": "/ws/security/" + mode + "/", "client": ("127.0.0.1", 32100),
                "query_string": urlencode({"run": prepared["runId"], "cap": prepared["query"]["f" if mode == "fixed" else "v"][0]}).encode(),
                "headers": [(b"host", b"127.0.0.1:8766"), (b"origin", origin.encode()), (b"cookie", ("browser_lab_session=" + self.client.cookies["browser_lab_session"].value).encode())]}

    async def connect(self, scope, accepted=True):
        connection = ApplicationCommunicator(lesson.websocket_application, scope)
        await connection.send_input({"type": "websocket.connect"})
        output = await connection.receive_output()
        self.assertEqual(output["type"], "websocket.accept" if accepted else "websocket.close")
        if not accepted:
            self.assertEqual(output["code"], 1008)
            await connection.wait()
        return connection

    async def message(self, connection, action="subscribe", tenant="alpha"):
        await connection.send_input({"type": "websocket.receive", "text": json.dumps({"action": action, "tenant": tenant})})
        response = await connection.receive_output()
        self.assertEqual(response["type"], "websocket.send")
        return json.loads(response["text"])

    async def disconnect(self, connection):
        await connection.send_input({"type": "websocket.disconnect", "code": 1000})
        await connection.wait()

    def test_prepare_csrf_fixed_json_and_host_and_state_ownership(self):
        self.assertEqual(self.client.post("/api/websocket/prepare/", '{}', content_type="application/json").status_code, 403)
        for raw in ('[]', '{}', '{"fixture":[]}', '{"fixture":"custom"}', '{"fixture":"allowed","fixture":"wrong-origin"}', '{"fixture":"allowed","url":"http://example.invalid"}', '[' * 300):
            response = self.client.post("/api/websocket/prepare/", raw, content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf)
            self.assertEqual(response.status_code, 400)
        data = self.prepare()
        state = self.client.get("/api/websocket/state/", {"run": data["runId"]})
        self.assertEqual(state.status_code, 200)
        self.assertNotIn("capability", state.content.decode())
        stranger = Client(HTTP_HOST="127.0.0.1:8766")
        self.assertEqual(stranger.get("/api/websocket/state/", {"run": data["runId"]}).status_code, 404)
        with override_settings(LAB_MAIN_ORIGIN="http://localhost:8766"):
            self.assertEqual(self.client.get("/api/websocket/state/", {"run": data["runId"]}).status_code, 404)

    def test_allowed_upgrade_and_fictional_event_both_modes(self):
        prepared = self.prepare()
        async def check():
            for mode in lesson.MODES:
                connection = await self.connect(self.scope(prepared, mode))
                self.assertEqual(await self.message(connection), {"kind": "event", "marker": "HARMLESS_ALPHA_EVENT"})
                await self.disconnect(connection)
        async_to_sync(check)()
        state = self.client.get("/api/websocket/state/", {"run": prepared["runId"]}).json()["modes"]
        for value in state.values():
            self.assertEqual((value["handshake"], value["messages"], value["deliveries"], value["closed"]), ("accepted", 1, 1, True))

    def test_companion_origin_is_accepted_only_in_deliberately_broad_mode(self):
        prepared = self.prepare("wrong-origin")
        async def check():
            connection = await self.connect(self.scope(prepared, "vulnerable", PEER))
            self.assertEqual((await self.message(connection))["marker"], "HARMLESS_ALPHA_EVENT")
            await self.disconnect(connection)
            await self.connect(self.scope(prepared, "fixed", PEER), accepted=False)
        async_to_sync(check)()
        self.assertEqual(lesson._runs[prepared["runId"]]["modes"]["fixed"]["handshake"], "origin refused")

    def test_message_tenant_and_action_authorization_are_independent_of_upgrade(self):
        for fixture, action, tenant, vulnerable, fixed in (("foreign-tenant", "subscribe", "beta", "HARMLESS_BETA_EVENT", "WS_TENANT_DENIED"), ("forbidden-action", "publish", "alpha", "FICTIONAL_PUBLISH_ACCEPTED", "WS_ACTION_DENIED")):
            prepared = self.prepare(fixture)
            async def check():
                for mode, marker in (("vulnerable", vulnerable), ("fixed", fixed)):
                    connection = await self.connect(self.scope(prepared, mode))
                    self.assertEqual((await self.message(connection, action, tenant))["marker"], marker)
                    await self.disconnect(connection)
            async_to_sync(check)()

    def test_live_permission_revocation_rechecks_delivery_without_reconnecting(self):
        prepared = self.prepare("permission-revoked")
        def revoke():
            return self.client.post("/api/websocket/revoke/", json.dumps({"run": prepared["runId"]}), content_type="application/json", HTTP_X_CSRFTOKEN=self.csrf).status_code
        self.assertEqual(revoke(), 409)
        async def check():
            connections = {mode: await self.connect(self.scope(prepared, mode)) for mode in lesson.MODES}
            for connection in connections.values():
                self.assertEqual((await self.message(connection))["marker"], "HARMLESS_ALPHA_EVENT")
            self.assertEqual(await sync_to_async(revoke)(), 200)
            self.assertEqual(await sync_to_async(revoke)(), 409)
            for mode, connection in connections.items():
                self.assertEqual((await self.message(connection, "deliver"))["marker"], "HARMLESS_ALPHA_EVENT" if mode == "vulnerable" else "WS_PERMISSION_DENIED")
                await self.disconnect(connection)
        async_to_sync(check)()
        state = lesson._runs[prepared["runId"]]
        self.assertEqual(state["modes"]["vulnerable"]["deliveries"], 2)
        self.assertEqual(state["modes"]["fixed"]["deliveries"], 1)

    def test_transport_guards_reject_nonloopback_wrong_host_duplicate_headers_and_peer_role(self):
        prepared = self.prepare()
        changes = [
            {"client": ("192.0.2.1", 32000)}, {"scheme": "wss"}, {"path": "/ws/arbitrary/"},
            {"headers": [(b"host", b"localhost:8766"), (b"origin", MAIN.encode())]},
            {"headers": self.scope(prepared)["headers"] + [(b"host", b"127.0.0.1:8766")]},
            {"headers": self.scope(prepared)["headers"] + [(b"origin", MAIN.encode())]},
            {"headers": [(b"host", b"127.0.0.1:8766"), (b"origin", b"https://example.invalid")]},
            {"query_string": self.scope(prepared)["query_string"] + b"&run=extra"},
        ]
        async def check():
            for changeset in changes:
                with self.subTest(changes=changeset):
                    await self.connect({**self.scope(prepared), **changeset}, accepted=False)
            with override_settings(LAB_ROLE="peer"):
                await self.connect(self.scope(prepared), accepted=False)
            connection = await self.connect(self.scope(prepared))
            await self.disconnect(connection)
        async_to_sync(check)()

    def test_handshake_requires_matching_session_capability_freshness_and_single_use(self):
        prepared = self.prepare()
        async def check():
            bad_cookie = self.scope(prepared)
            bad_cookie["headers"][-1] = (b"cookie", b"browser_lab_session=" + b"a" * 32)
            await self.connect(bad_cookie, accepted=False)
            bad_cap = self.scope(prepared)
            bad_cap["query_string"] = urlencode({"run": prepared["runId"], "cap": "f" * 48}).encode()
            await self.connect(bad_cap, accepted=False)
            connection = await self.connect(self.scope(prepared))
            await self.disconnect(connection)
            await self.connect(self.scope(prepared), accepted=False)
        async_to_sync(check)()
        prepared = self.prepare()
        lesson._runs[prepared["runId"]]["created"] -= lesson.RUN_TTL + 1
        async_to_sync(self.connect)(self.scope(prepared), accepted=False)

    def test_deleted_django_session_cannot_continue_sending_even_in_vulnerable_mode(self):
        prepared = self.prepare()
        session = self.client.session
        async def check():
            connection = await self.connect(self.scope(prepared, "vulnerable"))
            await self.message(connection)
            await sync_to_async(session.delete)()
            await connection.send_input({"type": "websocket.receive", "text": '{"action":"subscribe","tenant":"alpha"}'})
            self.assertEqual(await connection.receive_output(), {"type": "websocket.close", "code": 1008})
            await connection.wait()
        async_to_sync(check)()

    def test_binary_oversized_duplicate_and_invalid_messages_close_without_echo(self):
        for event in ({"bytes": b"binary"}, {"text": "x" * 513}, {"text": '{"action":"subscribe","action":"publish","tenant":"alpha"}'}, {"text": '{"action":[],"tenant":"alpha"}'}, {"text": '{"action":"execute","tenant":"alpha"}'}, {"text": '{"action":"deliver","tenant":"alpha"}'}):
            prepared = self.prepare()
            async def check():
                connection = await self.connect(self.scope(prepared))
                await connection.send_input({"type": "websocket.receive", **event})
                self.assertEqual(await connection.receive_output(), {"type": "websocket.close", "code": 1008})
                await connection.wait()
            async_to_sync(check)()

    def test_message_count_lifetime_and_per_owner_store_are_bounded(self):
        prepared = self.prepare()
        async def count_check():
            connection = await self.connect(self.scope(prepared))
            for _ in range(lesson.MAX_MESSAGES):
                await self.message(connection)
            self.assertEqual(await connection.receive_output(), {"type": "websocket.close", "code": 1008})
            await connection.wait()
        async_to_sync(count_check)()
        prepared = self.prepare()
        async def timeout_check():
            connection = await self.connect(self.scope(prepared))
            self.assertEqual(await connection.receive_output(), {"type": "websocket.close", "code": 1000})
            await connection.wait()
        with patch.object(lesson, "SOCKET_TTL", 0.02):
            async_to_sync(timeout_check)()
        for _ in range(6):
            self.prepare()
        self.assertEqual(len(lesson._runs), 4)

    def test_harness_and_script_are_fixed_owned_and_role_scoped(self):
        data = self.prepare()
        url = urlsplit(data["harness"])
        response = self.client.get(url.path + "?" + url.query)
        self.assertEqual(response.status_code, 200)
        self.assertIn("connect-src ws://127.0.0.1:8766", response["Content-Security-Policy"])
        self.assertEqual(Client(HTTP_HOST="127.0.0.1:8766").get(url.path + "?" + url.query).status_code, 404)
        self.assertEqual(self.client.get("/lab/websocket/boot.js").status_code, 200)
        data = self.prepare("wrong-origin")
        url = urlsplit(data["harness"])
        with override_settings(LAB_ROLE="peer"):
            peer = Client(HTTP_HOST="127.0.0.1:8767")
            self.assertEqual(peer.get(url.path + "?" + url.query).status_code, 200)
            self.assertEqual(peer.get("/peer/websocket/boot.js").status_code, 200)
            self.assertEqual(peer.get("/api/websocket/state/", {"run": data["runId"]}).status_code, 404)
