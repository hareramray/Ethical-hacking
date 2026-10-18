# Open redirects and return URLs: local navigation markers

This lesson sends real HTTP redirects and observes the browser arriving at a marker page. The vulnerable handler trusts the selected return URL; the fixed handler permits one exact relative path. Every destination is owned by the lab: no credentials, account actions, external websites, or arbitrary URL parameters are involved.

## Run it

Start both Vue + Django lab processes using the [lab setup](README.md), open the printed main URL (normally `http://127.0.0.1:8766/`), and select **Open redirects**.

1. Choose **Allowed relative return path**, then compare. Both frames display `MAIN_RETURN_MARKER`.
2. Choose **Absolute URL to the companion**. The unchecked handler sends the browser to the companion's `COMPANION_RETURN_MARKER`; the fixed handler returns `RETURN_URL_REJECTED`.
3. Repeat with **Scheme-relative URL to the companion**. A leading `//` introduces an authority; it does not mean an ordinary same-origin relative path.
4. Choose **Dot segments in a relative path**. The unchecked handler sends an alternate spelling; the browser normalizes it to the main landing path. The fixed handler rejects that spelling under its exact-path rule.
5. In DevTools Network, inspect `/lab/redirect/go/`: accepted navigation has status **302** and a **Location** header. Fixed rejection has status **400**, a visible refusal document, and no Location header. Inspect the subsequent landing request and the final URL displayed in the panel.

The iframe's `src` attribute remains the initial handler URL after a redirect. Use the displayed destination observation, the actual frame URL, and Network evidence to determine where navigation ended.

## Fixtures and expected results

The examples below omit server-generated run, fixture, and mode query fields.

| Fixture | Candidate return URL | Unchecked result | Fixed result |
|---|---|---|---|
| Allowed | `/lab/redirect/landing/` | 302, main marker | 302, main marker |
| Absolute companion | `http://127.0.0.1:8767/peer/redirect/landing/` on default ports | 302, companion marker | 400, refused |
| Scheme-relative companion | `//127.0.0.1:8767/peer/redirect/landing/` on default ports | 302, companion marker | 400, refused |
| Dot segments | `/lab/redirect/discard/../landing/` | 302; browser normalizes to main marker | 400, refused |

The dot-segment fixture is a benign alternate spelling, not itself an exploit or a demonstration of access-control bypass. It shows why a destination policy should explicitly decide which spellings it permits. The companion is a local stand-in for a destination outside the application's return-URL policy, even though both servers belong to this lab.

## The repair

The fixed function rejects controls, whitespace, backslashes, and percent-encoded spelling before parsing. It rejects schemes, authorities, query strings, and fragments, then checks exact membership in a small set of allowed relative paths. It adds its own correlation fields only after that check. No decoding or normalization loop attempts to turn rejected input into accepted input.

This deliberately narrow rule suits an application with a single return destination. It is not a general-purpose URL sanitizer. Applications with multiple legitimate destinations can map short destination identifiers to server-owned URLs and authorize the destination action separately. OWASP recommends avoiding untrusted redirect destinations and, where they are required, using explicit permitted destinations; see [Unvalidated Redirects and Forwards](https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html).

There are two distinct boundaries here:

- **Exercise containment:** both modes accept only a named fixture, which the server maps to an owned local candidate. The lab never exposes an arbitrary open-redirect endpoint.
- **Demonstrated repair:** only the fixed handler applies `permitted_return_path()` to that candidate. The unchecked handler passes the fixture's candidate directly into its 302 Location.

Redirect validation is separate from login, authorization, CSRF defenses, and the [SSRF lesson](SSRF.md). Here the browser follows the redirect; the server does not fetch a supplied URL. A permitted destination must still enforce its own authorization in a real application.

## Measurement and containment

Each destination displays a fixed marker and reports its actual `location.href`. The Vue panel checks the current source window, opaque message origin, run, mode, fixture, exact evidence schema, marker, and expected destination. The displayed marker alone does not prove HTTP status or headers; the browser tests additionally observe the actual 302/400 responses and final frame URLs.

Frames and response CSP use `sandbox allow-scripts` without `allow-same-origin`, forms, popups, or top navigation. Marker scripts use a fresh nonce. Their resource policy disallows connections, nested frames, and objects. They do not read cookies or storage. The opaque message origin is therefore `null`; URL ownership is checked separately. The companion serves only its fixed marker document for this lesson and does not expose application APIs.

Run identifiers correlate observations; they are not authorization tokens, and the marker routes are intentionally stateless. All document parameters have exact bounded selectors. Rerunning or leaving the lesson removes the old frames and ignores late preparation responses.

This lesson does not implement OAuth redirect URI handling, authentication callbacks, arbitrary encoded URL variants, IDN/Unicode host comparisons, every browser parser difference, or a general allowlist for external sites. Unit checks include malformed candidates rejected by the narrow rule; only the four listed fixtures are runnable navigation comparisons. Browser tests use the project's Chromium configuration.

## Verification and files

For registered OAuth callback destinations and authorization-code binding, use the separate [OAuth/OIDC and PKCE lesson](OAUTH_OIDC.md). An ordinary return-URL allowlist is not a complete OAuth callback policy.

- [Django lesson](backend/securitylab/redirect_lab.py): bounded selectors, actual redirects, fixed validator, and marker documents.
- [Backend tests](backend/securitylab/test_redirect_lab.py): Location/status contracts, valid control, strict selectors, parser edge cases, CSRF, host/scheme/role boundaries, and companion API restrictions.
- [Vue lesson](frontend/src/RedirectLab.vue): comparison controls and destination observations.
- [Browser tests](frontend/tests/redirect.spec.js): actual response headers, final frame URLs and markers, cross-origin destinations, normalized paths, stale state, and leaving during preparation.
- Related: [postMessage validation](POSTMESSAGE.md), [CSRF/CORS](CSRF_CORS.md), and [SSRF](SSRF.md).
