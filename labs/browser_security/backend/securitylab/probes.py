"""Fixed, inspectable browser probes adapted from CSP_XSS_HARMLESS_TESTS.md."""
import base64
import hashlib

MODES = [
    {"id": "off", "label": "No script restrictions"},
    {"id": "self", "label": "Same-origin scripts"},
    {"id": "nonce", "label": "Nonce policy"},
    {"id": "hash", "label": "Exact script hashes"},
    {"id": "dynamic", "label": "Nonce + strict-dynamic"},
    {"id": "report", "label": "Report-only nonce policy"},
    {"id": "tt", "label": "Trusted Types + nonce"},
]
PAYLOADS = [
    {"id": "markup", "label": "Inert HTML control", "context": "html", "payload": '<strong data-xss-test="HTML_01">XSS_TEST_HTML_01</strong>'},
    {"id": "script", "label": "Parser-inserted script", "context": "html", "payload": "<script>console.log('XSS_TEST_HTML_SCRIPT_02')</script>"},
    {"id": "image", "label": "Image error handler", "context": "html", "payload": '<img src="data:image/png;base64,AA==" alt="lab image" onerror="console.log(\'XSS_TEST_IMAGE_04\')">'},
    {"id": "svg", "label": "SVG load handler", "context": "html", "payload": '<svg onload="console.log(\'XSS_TEST_SVG_03\')"></svg>'},
    {"id": "button", "label": "Clickable event handler", "context": "html", "payload": '<button type="button" onclick="console.log(\'XSS_TEST_CLICK_05\')">Run harmless marker</button>'},
    {"id": "url", "label": "JavaScript URL", "context": "url", "payload": "javascript:void(console.log('XSS_TEST_URL_16'))"},
    {"id": "attr-double", "label": "Double-quoted attribute", "context": "attribute-double", "payload": '\"><svg onload="console.log(\'XSS_TEST_ATTR_DOUBLE_06\')"></svg><span data-rest="'},
    {"id": "attr-single", "label": "Single-quoted attribute", "context": "attribute-single", "payload": "'><svg onload=\"console.log('XSS_TEST_ATTR_SINGLE_07')\"></svg><span data-rest='"},
    {"id": "attr-unquoted", "label": "Unquoted attribute", "context": "attribute-unquoted", "payload": 'x><svg onload="console.log(\'XSS_TEST_ATTR_UNQUOTED_08\')"></svg><span data-rest=x'},
    {"id": "js-single", "label": "Single-quoted JavaScript string", "context": "js-single", "payload": "';console.log('XSS_TEST_JS_SINGLE_10');//"},
    {"id": "js-double", "label": "Double-quoted JavaScript string", "context": "js-double", "payload": '\";console.log(\'XSS_TEST_JS_DOUBLE_11\');//'},
    {"id": "js-template", "label": "JavaScript template literal", "context": "js-template", "payload": "${console.log('XSS_TEST_JS_TEMPLATE_12')}"},
    {"id": "textarea", "label": "Textarea closing tag", "context": "textarea", "payload": '</textarea><svg onload="console.log(\'XSS_TEST_TEXTAREA_13\')"></svg>'},
    {"id": "title", "label": "Title closing tag", "context": "title", "payload": '</title><svg onload="console.log(\'XSS_TEST_TITLE_14\')"></svg>'},
    {"id": "script-data", "label": "Script closing tag", "context": "script-data", "payload": '</script><svg onload="console.log(\'XSS_TEST_SCRIPT_END_15\')"></svg>'},
    {"id": "handler-string", "label": "Event-handler string", "context": "handler", "payload": "');console.log('XSS_TEST_HANDLER_STRING_09');//"},
    {"id": "srcdoc", "label": "Nested srcdoc (blocked by isolation)", "context": "srcdoc", "payload": "<script>console.log('XSS_TEST_SRCDOC_17')</script>"},
]
CONTEXTS = [{"id": key, "label": label} for key, label in [
    ("html", "HTML body"), ("attribute-double", "Double-quoted attribute"),
    ("attribute-single", "Single-quoted attribute"), ("attribute-unquoted", "Unquoted attribute"),
    ("js-single", "Single-quoted JavaScript string"), ("js-double", "Double-quoted JavaScript string"),
    ("js-template", "JavaScript template literal"), ("textarea", "Textarea"),
    ("title", "Title element"), ("script-data", "Script data"), ("url", "Link URL"),
    ("handler", "Event-handler string (click)"), ("srcdoc", "Nested srcdoc (isolation blocks it)"),
]]

# Defense for both embedded and directly navigated experiment documents. The
# sandbox deliberately has no allow-same-origin, top-navigation, popup, or form.
ISOLATION = (
    "sandbox allow-scripts; base-uri 'none'; object-src 'none'; "
    "frame-ancestors 'self'; form-action 'none'; frame-src 'none'; "
    "img-src 'self' data:; connect-src 'self'"
)
HASH_BODY = "hit('CSP_HASH_EXACT');"

# Keep this string constant: the hash mode hashes precisely these bytes.
BOOT = r"""
(() => {
  'use strict';
  const config = JSON.parse(document.body.dataset.lab || '{}');
  const originalLog = console.log.bind(console);
  const events = window.__labEvents = [];
  function emit(kind, message, details) {
    const item = {channel: 'browser-security-lab', runId: config.runId || '', kind,
      message: String(message).slice(0, 1000)};
    if (details) item.details = details;
    if (events.length >= 250) return;
    events.push(item);
    const results = document.getElementById('results');
    if (results) {
      const line = document.createElement('div');
      line.textContent = kind + ': ' + item.message;
      results.appendChild(line);
    }
    if (window.parent !== window && config.parentOrigin) {
      window.parent.postMessage(item, config.parentOrigin);
    }
  }
  console.log = (...values) => {
    originalLog(...values);
    emit('marker', values.map(value => {
      try { return typeof value === 'string' ? value : JSON.stringify(value); }
      catch (_) { return '[unserializable]'; }
    }).join(' '));
  };
  window.hit = id => console.log(id);
  window.labJsonp = data => {
    if (!data || data.marker !== 'JSONP_TEST_22' || typeof data.text !== 'string') return;
    hit(data.marker);
    hit(data.text);
  };
  document.addEventListener('securitypolicyviolation', event => {
    const details = {directive: event.effectiveDirective, disposition: event.disposition,
      blocked: event.blockedURI, line: event.lineNumber};
    emit('violation', details.directive + ' (' + details.disposition + ')', details);
  });
  window.addEventListener('error', event => emit('error', event.message || 'Resource load failed'));
  window.addEventListener('unhandledrejection', event => emit('error', String(event.reason)));
  function attempt(label, operation) {
    try { operation(); }
    catch (error) { emit('error', label + ': ' + error.name + ': ' + error.message); }
  }
  const actions = {
    inline() {
      const script = document.createElement('script');
      script.text = "hit('CSP_DYNAMIC_INLINE');";
      document.body.appendChild(script);
    },
    external() {
      const script = document.createElement('script');
      script.src = '/lab/probe.js';
      script.onerror = () => emit('error', 'CSP_EXTERNAL_LOAD_ERROR');
      document.body.appendChild(script);
    },
    jsonp() {
      const script = document.createElement('script');
      script.src = '/lab/jsonp.js?callback=labJsonp';
      script.onerror = () => emit('error', 'JSONP_LOAD_ERROR');
      document.body.appendChild(script);
    },
    eval() { eval("hit('CSP_EVAL');"); },
    function() { new Function("hit('CSP_FUNCTION');")(); },
    timer() { setTimeout("hit('CSP_STRING_TIMER');", 0); },
    callback() { setTimeout(() => hit('CSP_CALLBACK_TIMER'), 0); },
    connect() {
      // The sandbox's opaque origin cannot read this response. no-cors permits
      // a credential-free request without enabling CORS on the Django API.
      fetch('/lab/ping', {credentials: 'omit', mode: 'no-cors'})
        .then(() => hit('CSP_CONNECT_OK'))
        .catch(() => hit('CSP_CONNECT_FAILED'));
    },
    handler() { document.getElementById('handler-probe').click(); },
    url() { document.getElementById('url-probe').click(); }
  };
  hit('CSP_BOOT_OK');
  document.addEventListener('DOMContentLoaded', () => {
    if (config.source === 'dom') {
      attempt('DOM rendering', () => {
        const payload = location.hash.length > 1
          ? decodeURIComponent(location.hash.slice(1)).slice(0, 2000)
          : config.payload;
        hit(location.hash.length > 1 ? 'DOM_SOURCE_FRAGMENT' : 'DOM_SOURCE_QUERY');
        const sink = document.getElementById('sink');
        if (config.render === 'text') {
          sink.textContent = payload;
          hit('SAFE_TEXT_RENDERED');
        } else {
          sink.innerHTML = payload;
        }
      });
    } else if ((config.source === 'reflected' || config.source === 'stored') && config.render === 'text') {
      hit('SAFE_TEXT_RENDERED');
    }
    if (config.source === 'csp' && actions[config.probe]) {
      attempt(config.probe, actions[config.probe]);
    }
    if (config.source === 'jsonp' && config.probe === 'jsonp') {
      attempt('jsonp', actions.jsonp);
    }
    setTimeout(() => { window.__labReady = true; hit('LAB_FRAME_READY'); }, 50);
  });
})();
"""


def digest(source):
    return base64.b64encode(hashlib.sha256(source.encode("utf-8")).digest()).decode("ascii")


def experiment_policy(mode, nonce):
    scripts = {
        "self": "'self'",
        "nonce": f"'nonce-{nonce}'",
        "hash": f"'sha256-{digest(BOOT)}' 'sha256-{digest(HASH_BODY)}'",
        "dynamic": f"'nonce-{nonce}' 'strict-dynamic'",
        "report": f"'nonce-{nonce}'",
        "tt": f"'nonce-{nonce}'",
    }
    value = (
        "default-src 'none'; base-uri 'none'; object-src 'none'; frame-src 'none'; "
        "form-action 'none'; img-src data:; connect-src 'none'; script-src-attr 'none'; "
        "script-src " + scripts[mode] + ";"
    )
    if mode == "tt":
        value += " require-trusted-types-for 'script'; trusted-types 'none';"
    return value


def frame_headers(mode, nonce):
    if mode == "off":
        return {"Content-Security-Policy": ISOLATION}
    if mode == "report":
        return {"Content-Security-Policy": ISOLATION,
                "Content-Security-Policy-Report-Only": experiment_policy(mode, nonce)}
    # A comma separates policies so overlapping directives intersect instead of
    # becoming duplicate directives (which browsers would ignore after first).
    return {"Content-Security-Policy": ISOLATION + ", " + experiment_policy(mode, nonce)}
