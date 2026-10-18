# Local OAuth / OIDC authorization-code lab

This lesson runs real browser redirects and OAuthlib 4.0.0 authorization-code processing, including PKCE S256, single-use codes, and signed OpenID Connect ID tokens. It uses only the predetermined identity `fictional-reader`, owned callback URLs, and disposable transaction state. There is no password input, external identity provider, consent screen, or actual account login.

Start the lab using [README.md](README.md), open the printed main URL, and choose **OAuth / OIDC & PKCE**. Select a fixture and run the comparison. Every comparison creates separate vulnerable and fixed client/provider transactions.

## Follow the actual flow

1. The Vue page sends a CSRF-protected `POST /api/oauth/prepare/` with one predefined fixture ID.
2. Each frame navigates to `/lab/oauth/start/`. A real HTTP 302 sends the browser to `/lab/oauth/provider/authorize/` with `response_type=code`, `scope=openid`, state, nonce, and an S256 PKCE challenge.
3. OAuthlib validates the authorization request and issues a random authorization code. A second real HTTP 302 sends the browser to the registered callback, or the invalid-redirect fixture is refused by the provider before a code is issued.
4. The callback checks the saved transaction. The confidential server-side client serializes a token request containing the code, callback, client secret, and verifier. It calls OAuthlib's token endpoint **in-process**, which returns a protocol status and JSON token response.
5. OAuthlib validates the code/client/callback/PKCE binding and issues a signed ID token. PyJWT verifies the signature, configured HS256 algorithm, issuer, audience, required time claims, and subject. The client additionally checks the access-token hash and, in fixed mode, the saved nonce. Only a harmless identity marker is rendered.

Browser Network shows the start, provider, and callback navigations. The displayed token exchange statuses are **not network HTTP requests**: they are the status values returned by the in-process protocol endpoint. This avoids an outbound HTTP service and keeps the local experiment deterministic. The token endpoint URI is internal; there is no public `/token/` route.

## Fixtures and responsible checks

| Fixture | Vulnerable observation | Fixed observation | Responsibility |
|---|---|---|---|
| Valid control | One exchange returns 200; fictional identity accepted | Same successful flow | Both parties preserve legitimate login |
| Wrong verifier | Provider storage loses the PKCE binding; wrong verifier is accepted | Token exchange returns 400 `invalid_grant` | Provider stores the challenge with the code and enforces S256 |
| State mismatch | Client ignores unexpected callback state and accepts identity | Refused before any token exchange | Client correlates callback state with its saved transaction |
| Nonce mismatch | Client accepts a signed ID token containing the wrong nonce | Exchange returns 200, but client refuses the ID token | Client binds the ID token to the originating request |
| Reused code | Two exchanges of the same actual code both return 200 | First returns 200; second returns 400 `invalid_grant` | Provider consumes the code atomically after first use |
| Invalid redirect | Real code reaches an alternate owned callback; it is never redeemed | Provider refuses before code issuance or redirection | Provider exactly matches registered redirect URIs |

For state and nonce fixtures, the lab deliberately changes the value sent on the authorization request while keeping the original value in the client's saved transaction. The provider correctly reflects the received value; it cannot determine the client's original expectation. These fixtures isolate the client's correlation check. They do not demonstrate a complete login-CSRF or token-injection attack against another user; PKCE and the other still-active checks can also affect exploitability.

The invalid-redirect fixture deliberately registers an extra owned callback in vulnerable mode. The fixed registry contains only the intended callback. This is a bounded illustration of overly permissive provider registration, not an arbitrary redirect service. Both callbacks contain generated run/mode query fields and are matched exactly for each disposable transaction. There is no claim of production dynamic-client registration.

The replay fixture reports `FIRST_LOGIN_OK_REPLAY_REFUSED` in fixed mode: the second redemption was denied **after the first succeeded**. A rejected nonce likewise happens **after token issuance**, so token issuance by itself does not prove client acceptance.

## Inspect and repair

- In DevTools Network, inspect both 302 `Location` values. The provider response carries a code and state to the callback; tokens and the verifier stay server-side.
- Compare `LocalValidator.get_code_challenge()` and `is_pkce_required()`: the vulnerable adapter discards the challenge binding. OAuthlib performs the actual S256 verification when the binding is present.
- Compare `invalidate_authorization_code()`: the fixed adapter removes the code under the same lock as redemption. Codes are also bound to the client and exact callback and expire after 60 seconds.
- Compare the callback's state check and `verify_identity()` nonce check. They are separate from signature, issuer, audience and expiration checks; both modes retain those baseline ID-token checks.
- Retain the valid control after every repair. The expected result is successful authorized identity processing with refusals at the correct boundaries.

Implementation: [oauth_lab.py](backend/securitylab/oauth_lab.py), [OAuthLab.vue](frontend/src/OAuthLab.vue). Tests: [test_oauth_lab.py](backend/securitylab/test_oauth_lab.py), [oauth.spec.js](frontend/tests/oauth.spec.js).

## Local boundaries and limits

The provider and client use separate URL namespaces **on the same loopback HTTP origin**. This is not a cross-origin provider or a production TLS deployment. Both use a disposable per-transaction confidential-client secret; the provider signs HS256 ID tokens with that secret. No real access-token resource API, refresh token, discovery, UserInfo endpoint, JWKS rotation, logout, revocation service, MFA, session login, or account recovery is implemented. This complements [JWT validation](JWT_VALIDATION.md) and [authentication/session exercises](AUTH_SESSIONS.md); it does not replace them.

Only predefined fixtures and exact prepared authorization parameters are accepted. Runs belong to the Django session, expire after five minutes, and are bounded to eight per owner and 128 total in the single-process in-memory store. A lock protects checks and code consumption. Finished runs discard codes; process restart discards all transactions. A production deployment would require a shared transactional store and policies for issued-token revocation on code reuse. This lab has no usable resource tokens, so it does not model that revocation behavior.

The callback's final result document has a nonce CSP, disables networking/forms/frames, and uses an opaque sandbox origin. Vue accepts messages only from the current frame window, opaque origin, run, fixture, mode, and bounded exact schema. No code, token, verifier, client secret, state, or nonce appears in result telemetry. Local callback URLs contain short-lived codes as the protocol requires; `no-store` and `no-referrer` are supplied, and the lab disables development access logging of query strings.

## References

- [OAuthlib OpenID Connect provider integration](https://oauthlib.readthedocs.io/en/latest/oauth2/oidc/validator.html)
- [OAuthlib request validator responsibilities](https://oauthlib.readthedocs.io/en/latest/oauth2/validator.html)
- [OAuthlib 4.0.0 package](https://pypi.org/project/oauthlib/4.0.0/)
- [RFC 7636: PKCE](https://www.rfc-editor.org/rfc/rfc7636)
- [OpenID Connect Core: ID token validation](https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation)
- [RFC 9700: OAuth 2.0 security best current practice](https://www.rfc-editor.org/rfc/rfc9700)
