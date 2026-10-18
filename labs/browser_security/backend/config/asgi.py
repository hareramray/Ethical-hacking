"""HTTP remains Django; one bounded lesson receives real WebSocket scopes."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django_application = get_asgi_application()

from securitylab.websocket_lab import websocket_application  # noqa: E402


async def application(scope, receive, send):
    if scope["type"] == "websocket":
        await websocket_application(scope, receive, send)
    elif scope["type"] == "http":
        await django_application(scope, receive, send)
    else:
        raise ValueError("Only HTTP and WebSocket scopes are enabled.")
