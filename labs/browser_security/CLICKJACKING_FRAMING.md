# Clickjacking and framing: a local counter exercise

This lesson uses actual nested browser frames and response headers. A clearly labelled pretend action covers a harmless practice button. Clicking that area increments only the target document's in-memory counter, up to 20; it does not send an action request, change an account, or persist data.

## Run it

Start the Vue + Django lab using the [lab setup](README.md), open the printed main URL (normally `http://127.0.0.1:8766/`), and choose **Clickjacking & framing**. Both loopback processes must be running.

1. Select **CSP: same-origin ancestors only** and compare the policies.
2. The unrestricted target reports readiness. Click its **Pretend label: preview a card** area. The reported trusted click count becomes 1.
3. Uncheck **Show pretend label** inside that panel. The underlying button says **Practice action: increment local counter**. The visible label and the action receiving the click were different.
4. The fixed target does not report readiness. Inspect the browser console for the actual framing refusal and the target response in the Network panel for its headers.
5. Repeat with **X-Frame-Options: SAMEORIGIN**, then **CSP: explicitly allowed integration**. The last fixture permits both frames and both counter buttons.

The application labels a missing handshake **no readiness**, not **blocked**. A missing script, server failure, or slow load could also produce silence. The automated browser tests verify refusal messages in addition to response headers and compare them against a target that really loads.

## Frame chain and results

The chain is **main dashboard → companion harness → main target**. The two ports are different origins. Both origins are on the same site, so this is not a SameSite-cookie experiment.

| Fixture | Unrestricted target | Fixed target response | Expected browser behavior |
|---|---|---|---|
| CSP same-origin | No framing restriction | `Content-Security-Policy: …; frame-ancestors 'self'` | Companion ancestor is disallowed; fixed target cannot load there. |
| XFO same-origin | No framing restriction | `X-Frame-Options: SAMEORIGIN`; CSP omits `frame-ancestors` | Cross-origin companion is disallowed by XFO. |
| Allowed integration | No framing restriction | `frame-ancestors` lists the exact main and companion origins | Every ancestor is permitted, so both targets run. |

`frame-ancestors` is delivered in the target's HTTP response and checks every ancestor, not just the top page. `frame-src` answers a different question: which child frames the document may load. `default-src 'none'` does not supply a fallback for `frame-ancestors`, and a meta element cannot set it. See [MDN's frame-ancestors reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors).

The XFO fixture deliberately omits `frame-ancestors` to test XFO independently. Modern browsers give an enforced CSP `frame-ancestors` policy precedence over XFO; `ALLOW-FROM` is obsolete. Use CSP for explicit supported integrations. See [MDN's X-Frame-Options reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Frame-Options) and [OWASP's clickjacking defense guidance](https://cheatsheetseries.owasp.org/cheatsheets/Clickjacking_Defense_Cheat_Sheet.html).

An allowed embedder can still overlay its embedded target. The allowlist expresses trust in that integration; it is not an overlay detector. CORS and CSRF tokens do not replace a target framing policy.

## What is measured

- The target runs a fixed external script and reports readiness from its real origin and window.
- The companion accepts only messages from its current target window and exact main origin, with the matching run and bounded schema.
- The dashboard accepts only its current companion windows, exact companion origin, run, mode, fixture, and bounded result fields. Old frames are removed on reruns and navigation.
- Only actual browser input events with `event.isTrusted` increment the practice counter. Playwright clicks the overlay coordinates; no JavaScript click is used to fabricate success. The harness forwards the target's observed count.
- The overlay is intentionally labelled as pretend, has no event handler, and uses `pointer-events: none`. The real target button underneath receives the input.

`isTrusted` is only measurement here, not a general authorization or anti-clickjacking defense.

## Scope and containment

The API accepts only three fixed fixture IDs; there is no custom target URL, HTML, script, or header input. Both document types have restrictive resource policies and a response-level sandbox permitting scripts and real origins, but not top navigation, forms, or popups. Targets never read cookies, browser storage, account data, or application APIs.

The main-origin target shares an origin with the top dashboard even though the intervening companion is cross-origin. The lesson does **not** treat that nesting as an origin boundary. Containment relies on fixed reviewed target scripts, fixed fixture selectors, restrictive resource policy, and sandbox restrictions. The target needs a real origin for this framing-policy demonstration.

This lesson covers embedding and a simple overlay. It does not implement login-sensitive actions, drag-and-drop attacks, cursor manipulation, browser-extension behavior, SameSite-cookie comparisons, or every browser's legacy XFO behavior. Dedicated browser tests currently use the project's Chromium configuration.

## Verification and files

Backend tests check exact response policies, origin roles, selector validation, methods, CSRF, and companion API restrictions. Browser tests verify actual CSP/XFO refusal messages, absence of the blocked target button, allowed integration readiness, real overlay clicks, rejection of synthetic clicks, and fresh counter state on rerun.

- [Django lesson](backend/securitylab/framing_lab.py)
- [HTTP tests](backend/securitylab/test_framing_lab.py)
- [Vue lesson](frontend/src/FramingLab.vue)
- [Browser tests](frontend/tests/framing.spec.js)
- Related: [postMessage security](POSTMESSAGE.md) and [CSRF/CORS](CSRF_CORS.md)
