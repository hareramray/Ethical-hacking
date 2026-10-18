import ipaddress
from django.conf import settings
from django.core.exceptions import DisallowedHost, RequestDataTooBig, TooManyFieldsSent, TooManyFilesSent
from django.http import JsonResponse


class LocalOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            request.get_host()
            if not ipaddress.ip_address(request.META.get("REMOTE_ADDR", "127.0.0.1")).is_loopback:
                return JsonResponse({"error": "This lab accepts loopback clients only."}, status=403)
        except (ValueError, DisallowedHost):
            return JsonResponse({"error": "Use the printed localhost lab URL."}, status=400)
        if len(request.META.get("QUERY_STRING", "")) > 16000:
            return JsonResponse({"error": "Query is too long."}, status=414)
        try:
            size = int(request.META.get("CONTENT_LENGTH", "0") or "0")
        except ValueError:
            return JsonResponse({"error": "Invalid content length."}, status=400)
        if size > 80 * 1024:
            return JsonResponse({"error": "Request is too large. Files must be at most 64 KiB."}, status=413)
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, (RequestDataTooBig, TooManyFieldsSent, TooManyFilesSent)):
            return JsonResponse({"error": "Request exceeds the lab's size or field limits."}, status=413)


class LabRoleMiddleware:
    """The companion process serves fixed lesson documents, never app APIs."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.LAB_ROLE == "peer" and request.path not in {
            "/peer/", "/peer/boot.js", "/api/health",
            "/peer/message/", "/peer/message/receiver.js",
            "/lab/message/sender/", "/lab/message/sender.js",
            "/peer/framing/", "/peer/framing/boot.js",
            "/peer/redirect/landing/",
            "/peer/preflight/", "/peer/preflight/boot.js",
            "/peer/websocket/", "/peer/websocket/boot.js",
        }:
            response = JsonResponse({"error": "This origin only serves the fixed companion lesson."}, status=404)
            response["Content-Security-Policy"] = "default-src 'none'; sandbox"
            response["X-Content-Type-Options"] = "nosniff"
            response["Cache-Control"] = "no-store"
            return response
        return self.get_response(request)


class ResponseHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Cache-Control"] = "no-store"
        response["Referrer-Policy"] = "no-referrer"
        response["X-Content-Type-Options"] = "nosniff"
        # The frame and preview endpoints supply their experiment-specific policy.
        if "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'self'; sandbox"
        return response
