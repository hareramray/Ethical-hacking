"""Local-only comparisons with controlled browser and server-side fixtures."""
import html
import io
import json
import mimetypes
import re
import secrets
import warnings
from functools import wraps
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.utils.http import content_disposition_header
from PIL import Image, UnidentifiedImageError

from .fixtures import FIXTURES
from .models import Upload
from .probes import BOOT, CONTEXTS, HASH_BODY, MODES, PAYLOADS, frame_headers
from .traversal import TRAVERSAL_METADATA
from .cross_origin import metadata as cross_origin_metadata
from .sql_lab import SQL_METADATA
from .access_lab import ACCESS_METADATA
from .auth_lab import AUTH_METADATA
from .ssrf_lab import SSRF_METADATA
from .logic_lab import LOGIC_METADATA
from .template_lab import TEMPLATE_METADATA
from .command_lab import COMMAND_METADATA
from .xml_lab import XML_METADATA
from .write_lab import WRITE_METADATA
from .jwt_lab import JWT_METADATA
from .webhook_lab import WEBHOOK_METADATA
from .sanitizer_lab import sanitizer_metadata
from .message_lab import message_metadata
from .archive_lab import ARCHIVE_METADATA
from .clobber_lab import clobber_metadata
from .prototype_lab import prototype_metadata
from .framing_lab import framing_metadata

MAX_UPLOAD = 64 * 1024
MAX_UPLOADS = 20
MAX_PAYLOAD = 2000
APP_POLICY = (
    "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
    f"img-src 'self' data:; font-src 'self'; frame-src 'self' {settings.LAB_PEER_ORIGIN}; "
    "base-uri 'none'; object-src 'none'; form-action 'self'; frame-ancestors 'self'"
)
DOWNLOAD_POLICY = "default-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; sandbox"


def error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def methods(*allowed):
    def decorate(view):
        @wraps(view)
        def checked(request, *args, **kwargs):
            if request.method not in allowed:
                response = error("Method not allowed.", 405)
                response["Allow"] = ", ".join(allowed)
                return response
            return view(request, *args, **kwargs)
        return checked
    return decorate


def owner(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def upload_record(item):
    prefix = f"/lab/uploads/{item.id}"
    return {
        "id": str(item.id), "name": item.name, "size": item.size,
        "contentType": item.content_type, "submittedContentType": item.submitted_content_type,
        "policy": item.policy, "downloadUrl": prefix + "/download/",
        "previewUrl": prefix + "/preview/?active=0",
        "activePreviewUrl": prefix + "/preview/?active=1",
    }


def owned_upload(request, upload_id):
    key = request.session.session_key
    return Upload.objects.filter(id=upload_id, owner=key).first() if key else None


def upload_path(item):
    # File names are server-generated UUIDs, never client file names.
    root = Path(settings.UPLOAD_DIR).resolve()
    path = (root / (str(item.id) + ".bin")).resolve()
    if path.parent != root:
        raise ValueError("Upload path outside data directory")
    return path


@methods("GET")
def health(request):
    return JsonResponse({"status": "ok", "service": "browser-security-lab"})


@methods("GET")
def bootstrap(request):
    key = owner(request)
    return JsonResponse({
        "csrfToken": get_token(request), "modes": MODES, "contexts": CONTEXTS,
        "payloads": PAYLOADS, "stored": {"payload": request.session.get("lab_payload", "")},
        "traversal": TRAVERSAL_METADATA,
        "crossOrigin": cross_origin_metadata(),
        "sql": SQL_METADATA,
        "access": ACCESS_METADATA,
        "auth": AUTH_METADATA,
        "ssrf": SSRF_METADATA,
        "logic": LOGIC_METADATA,
        "template": TEMPLATE_METADATA,
        "command": COMMAND_METADATA,
        "xml": XML_METADATA,
        "write": WRITE_METADATA,
        "jwt": JWT_METADATA,
        "webhook": WEBHOOK_METADATA,
        "sanitizer": sanitizer_metadata(),
        "message": message_metadata(),
        "archive": ARCHIVE_METADATA,
        "clobber": clobber_metadata(),
        "prototype": prototype_metadata(),
        "framing": framing_metadata(),
        "uploads": [upload_record(item) for item in Upload.objects.filter(owner=key)],
        "fixtures": [{"name": name, "url": "/api/fixtures/" + name, "description": value[1]}
                     for name, value in FIXTURES.items()],
        "limits": {"payloadCharacters": MAX_PAYLOAD, "uploadBytes": MAX_UPLOAD,
                   "uploadsPerSession": MAX_UPLOADS, "imageDimension": 512},
    })


@methods("POST", "DELETE")
def stored(request):
    owner(request)
    if request.method == "DELETE":
        request.session.pop("lab_payload", None)
        return JsonResponse({"stored": {"payload": ""}})
    if request.content_type != "application/json":
        return error("Use an application/json request body.")
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return error("Invalid JSON body.")
    if not isinstance(data, dict) or not isinstance(data.get("payload"), str):
        return error("payload must be a string.")
    if len(data["payload"]) > MAX_PAYLOAD:
        return error("Payload must be at most 2000 characters.")
    request.session["lab_payload"] = data["payload"]
    return JsonResponse({"stored": {"payload": data["payload"]}})


def clean_filename(name):
    name = str(name).replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(char for char in name if ord(char) >= 32 and ord(char) != 127).strip()
    if not name or len(name) > 160:
        raise ValueError("File name must contain 1 to 160 printable characters.")
    return name


def png_bytes(data):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as picture:
                if picture.format != "PNG":
                    raise ValueError("The .png file is not a PNG image.")
                if not (1 <= picture.width <= 512 and 1 <= picture.height <= 512):
                    raise ValueError("PNG dimensions must be at most 512 × 512.")
                picture.verify()
            with Image.open(io.BytesIO(data)) as picture:
                picture.load()
                buffer = io.BytesIO()
                picture.convert("RGBA").save(buffer, format="PNG")
                result = buffer.getvalue()
                if len(result) > MAX_UPLOAD:
                    raise ValueError("Re-encoded PNG exceeds 64 KiB.")
                return result
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombWarning,
            Image.DecompressionBombError) as exc:
        raise ValueError("The .png file must contain a valid, small PNG image.") from exc


def validate_upload(name, data, policy):
    suffix = Path(name).suffix.lower()
    if policy == "strict" and suffix not in {".txt", ".png"}:
        raise ValueError("Strict policy accepts only UTF-8 .txt and valid .png files.")
    if suffix not in {".txt", ".png", ".html", ".svg", ".js", ".json"}:
        raise ValueError("Supported lab extensions: .txt, .png, .html, .svg, .js, .json.")
    if suffix == ".png":
        try:
            return png_bytes(data), "image/png"
        except ValueError:
            if policy == "strict":
                raise
            # The permissive path accepts a textual mismatch but serves it as
            # plain text, never as an automatically sniffed image or HTML.
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Text fixtures must be valid UTF-8.") from exc
    if "\x00" in text:
        raise ValueError("Text fixtures may not contain NUL bytes.")
    types = {".html": "text/html", ".svg": "image/svg+xml"}
    return data, types.get(suffix, "text/plain")


@methods("GET", "POST")
def uploads(request):
    key = owner(request)
    if request.method == "GET":
        return JsonResponse({"uploads": [upload_record(item) for item in Upload.objects.filter(owner=key)]})
    policy = request.POST.get("policy", "strict")
    if policy not in {"strict", "lab"}:
        return error("Unknown upload policy.")
    files = request.FILES.getlist("file")
    if len(files) != 1 or len(request.FILES) != 1:
        return error("Upload exactly one file using the file field.")
    if Upload.objects.filter(owner=key).count() >= MAX_UPLOADS:
        return error("Session limit is 20 uploads. Delete a fixture before adding another.")
    source = files[0]
    if source.size > MAX_UPLOAD:
        return error("Files must be at most 64 KiB.", 413)
    data = source.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        return error("Files must be at most 64 KiB.", 413)
    if not data:
        return error("Empty fixtures are not accepted.")
    try:
        name = clean_filename(source.name)
        processed, content_type = validate_upload(name, data, policy)
    except ValueError as exc:
        return error(str(exc))
    item = Upload(owner=key, name=name, size=len(processed), content_type=content_type,
                  submitted_content_type=(source.content_type or "")[:120], policy=policy)
    path = upload_path(item)
    try:
        path.write_bytes(processed)
        item.save()
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return JsonResponse({"upload": upload_record(item),
                         "uploads": [upload_record(row) for row in Upload.objects.filter(owner=key)]}, status=201)


@methods("DELETE")
def delete_upload(request, upload_id):
    item = owned_upload(request, upload_id)
    if item is None:
        return error("Upload not found in this session.", 404)
    upload_path(item).unlink(missing_ok=True)
    item.delete()
    return JsonResponse({"deleted": str(upload_id)})


def attachment(data, name):
    response = HttpResponse(data, content_type="application/octet-stream")
    response["Content-Disposition"] = content_disposition_header(True, name)
    response["Content-Security-Policy"] = DOWNLOAD_POLICY
    return response


@methods("GET")
def fixture(request, name):
    value = FIXTURES.get(name)
    return attachment(value[0], name) if value else error("Unknown fixture.", 404)


@methods("GET")
def download(request, upload_id):
    item = owned_upload(request, upload_id)
    if item is None or not upload_path(item).is_file():
        return error("Upload not found in this session.", 404)
    return attachment(upload_path(item).read_bytes(), item.name)


def preview_boot(request):
    config = json.dumps({"runId": request.GET.get("run_id", "")[:128],
                         "parentOrigin": request.scheme + "://" + request.get_host()})
    # JSON strings can contain </script> when run_id is supplied by a caller.
    config = config.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return r"""(() => {
      const config = CONFIG;
      const original = console.log.bind(console);
      window.__labEvents = [];
      function emit(kind, message, details) {
        const event = {channel:'browser-security-lab',runId:config.runId,kind,
          message:String(message).slice(0,1000)};
        if (details) event.details=details;
        if (window.__labEvents.length>=250) return;
        window.__labEvents.push(event);
        if (parent!==window) parent.postMessage(event,config.parentOrigin);
      }
      console.log=(...values)=>{original(...values);emit('marker',values.join(' '));};
      window.hit=id=>console.log(id);
      document.addEventListener('securitypolicyviolation',event=>emit('violation',
        event.effectiveDirective,{directive:event.effectiveDirective,
          disposition:event.disposition,blocked:event.blockedURI}));
      window.addEventListener('error',event=>emit('error',event.message));
      console.log('UPLOAD_PREVIEW_BOOT_OK');
      document.addEventListener('DOMContentLoaded',()=>{window.__labReady=true;});
    })();""".replace("CONFIG", config)


@methods("GET")
def preview(request, upload_id):
    item = owned_upload(request, upload_id)
    if item is None or not upload_path(item).is_file():
        return error("Upload not found in this session.", 404)
    active = request.GET.get("active", "0")
    if active not in {"0", "1"}:
        return error("active must be 0 or 1.")
    data = upload_path(item).read_bytes()
    nonce = secrets.token_urlsafe(24)
    script_policy = "'unsafe-inline'" if active == "1" else f"'nonce-{nonce}'"
    policy = (
        "sandbox allow-scripts; default-src 'none'; base-uri 'none'; form-action 'none'; "
        "frame-ancestors 'self'; object-src 'none'; frame-src 'none'; connect-src 'none'; "
        "img-src data:; style-src 'unsafe-inline'; script-src " + script_policy
    )
    if item.content_type == "text/html":
        script_markup = f'<script nonce="{nonce}">{preview_boot(request)}</script>'
        # Instrumentation is first, so early uploaded scripts and violations are
        # visible. The original body remains deliberately unsanitized in lab mode.
        text = data.decode("utf-8")
        text = re.sub(r"^\s*<!doctype[^>]*>", "", text, count=1, flags=re.IGNORECASE)
        data = ("<!doctype html><meta charset=\"utf-8\">" + script_markup + text).encode()
    elif item.content_type == "image/svg+xml":
        text = data.decode("utf-8")
        match = re.search(r"<svg\b[^>]*>", text, re.IGNORECASE)
        if match:
            script_markup = f'<script nonce="{nonce}"><![CDATA[{preview_boot(request)}]]></script>'
            data = (text[:match.end()] + script_markup + text[match.end():]).encode()
    response = HttpResponse(data, content_type=item.content_type + ("; charset=utf-8" if item.content_type != "image/png" else ""))
    response["Content-Security-Policy"] = policy
    response["Content-Disposition"] = content_disposition_header(False, item.name)
    return response


def context_fixture(context, payload, nonce):
    """Intentionally unsafe surrounding contexts; only used in sandbox frames."""
    templates = {
        "html": payload,
        "attribute-double": '<input aria-label="Attribute control" value="' + payload + '">',
        "attribute-single": "<input aria-label='Attribute control' value='" + payload + "'>",
        "attribute-unquoted": '<input aria-label="Attribute control" value=' + payload + ">",
        "js-single": f'<script nonce="{nonce}">window.labValue = \'{payload}\';</script>',
        "js-double": f'<script nonce="{nonce}">window.labValue = "{payload}";</script>',
        "js-template": f'<script nonce="{nonce}">window.labValue = `{payload}`;</script>',
        "textarea": '<textarea aria-label="Textarea control">' + payload + "</textarea>",
        "title": "<title>" + payload + "</title>",
        "script-data": '<script type="application/json">{"value":"' + payload + '"}</script>',
        "url": '<a id="context-action" href="' + payload + '">Run URL marker (click)</a>',
        "handler": '<button id="context-action" onclick="console.log(\'' + payload + '\')">Run handler marker (click)</button>',
        # Attribute escaping defines this context without escaping its inner
        # document. The isolation policy independently blocks nested frames.
        "srcdoc": '<iframe title="Nested srcdoc control" srcdoc="' + html.escape(payload, quote=True) + '"></iframe>',
    }
    return templates[context]


@methods("GET")
def frame(request):
    args = request.GET
    mode, source = args.get("mode", "nonce"), args.get("source", "reflected")
    render, probe = args.get("render", "text"), args.get("probe", "callback")
    context = args.get("context", "html")
    if mode not in {item["id"] for item in MODES}:
        return error("Unknown CSP mode.")
    if source not in {"reflected", "dom", "stored", "jsonp", "csp"}:
        return error("Unknown payload source.")
    if render not in {"text", "html"} or context not in {item["id"] for item in CONTEXTS}:
        return error("Unknown rendering mode or context.")
    if probe not in {"inline", "external", "eval", "function", "timer", "callback", "connect", "handler", "url", "jsonp"}:
        return error("Unknown probe.")
    if source == "jsonp" and probe not in {"jsonp", "external"}:
        return error("JSONP probes use jsonp (dynamic) or external (parser-inserted).")
    payload = request.session.get("lab_payload", "") if source == "stored" else args.get("payload", "")
    if len(payload) > MAX_PAYLOAD or len(args.get("run_id", "")) > 128:
        return error("Payload or run ID exceeds its limit.")
    nonce = secrets.token_urlsafe(24)
    config = {"source": source, "render": render, "probe": probe, "payload": payload,
              "runId": args.get("run_id", ""), "parentOrigin": request.scheme + "://" + request.get_host()}
    if mode in {"off", "self", "report"}:
        boot = f'<script nonce="{nonce}" src="/lab/boot.js"></script>'
    else:
        boot = f'<script nonce="{nonce}">{BOOT}</script>'
    sink = ""
    if source in {"reflected", "stored"}:
        sink = html.escape(payload) if render == "text" else context_fixture(context, payload, nonce)
    parser_jsonp = '<script src="/lab/jsonp.js?callback=labJsonp"></script>' if source == "jsonp" and probe == "external" else ""
    body = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Isolated browser experiment</title></head>
<body data-lab="{html.escape(json.dumps(config), quote=True)}">
<h2>Isolated experiment</h2><p>Policy: {mode}. Source: {source}. Rendering: {render}. Context: {context}.</p>
<div id="results" role="log" aria-label="Experiment evidence"></div>
{boot}
<script nonce="{nonce}">hit('CSP_NONCE_MATCH');</script>
<script nonce="incorrect-lab-nonce">hit('CSP_NONCE_WRONG');</script>
<script>{HASH_BODY}</script><script>{HASH_BODY} </script>
<script src="/lab/parser.js"></script>
<h3>Output</h3><div id="sink">{sink}</div>{parser_jsonp}
<button id="handler-probe" type="button" onclick="hit('CSP_HANDLER')">Inline handler control</button>
<a id="url-probe" href="javascript:void(hit('CSP_JS_URL'))">JavaScript URL control</a>
</body></html>'''
    response = HttpResponse(body, content_type="text/html; charset=utf-8")
    for name, value in frame_headers(mode, nonce).items():
        response[name] = value
    return response


@methods("GET")
def script(request, name):
    sources = {"boot": BOOT, "probe": "hit('CSP_DYNAMIC_EXTERNAL');", "parser": "hit('CSP_PARSER_EXTERNAL');"}
    return HttpResponse(sources[name], content_type="text/javascript; charset=utf-8")


@methods("GET")
def jsonp(request):
    if dict(request.GET.lists()) != {"callback": ["labJsonp"]}:
        return error("Only the exact callback labJsonp is supported.")
    data = {"marker": "JSONP_TEST_22", "text": "<strong>JSONP_TEXT_ONLY</strong>"}
    return HttpResponse("labJsonp(" + json.dumps(data) + ");", content_type="text/javascript; charset=utf-8")


@methods("GET")
def ping(request):
    return HttpResponse("LOCAL_LAB_PING", content_type="text/plain; charset=utf-8")


@methods("GET")
def index(request):
    target = settings.FRONTEND_DIR / "index.html"
    if target.is_file():
        response = FileResponse(target.open("rb"), content_type="text/html; charset=utf-8")
    else:
        response = HttpResponse(
            "<!doctype html><html lang=en><meta charset=utf-8><title>Browser lab setup</title>"
            "<h1>Build the Vue interface</h1><p>From labs/browser_security run "
            "<code>python run_lab.py --setup</code>, then start the lab with "
            "<code>python run_lab.py --serve</code>.</p></html>",
            content_type="text/html; charset=utf-8",
        )
    response["Content-Security-Policy"] = APP_POLICY
    return response


@methods("GET")
def asset(request, asset):
    root = (settings.FRONTEND_DIR / "assets").resolve()
    target = (root / asset).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        return error("Asset not found.", 404)
    content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    if target.suffix == ".js":
        content_type = "text/javascript"
    response = FileResponse(target.open("rb"), content_type=content_type)
    response["Content-Security-Policy"] = APP_POLICY
    return response


def csrf_failure(request, reason=""):
    return error("CSRF check failed. Reload the lab and try again.", 403)


def bad_request(request, exception=None):
    return error("Invalid request.", 400)


def forbidden(request, exception=None):
    return error("Forbidden.", 403)


def not_found(request, exception=None):
    return error("Route not found.", 404)


def server_error(request):
    return error("The local lab encountered an error. Check the server terminal.", 500)
