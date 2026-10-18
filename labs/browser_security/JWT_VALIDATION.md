# JWT validation: decode, verify, then authorize

This runnable Vue + Django lesson compares trusting decoded JWT claims with verifying them using PyJWT and then checking report permissions. All tokens, identities, issuers, audiences, and report contents are synthetic. It teaches JWT validation, not a complete login, OAuth, or OpenID Connect implementation.

## Run the lesson

From the repository root:

```powershell
python labs/browser_security/run_lab.py --setup
python labs/browser_security/run_lab.py
```

Open the printed local URL, select **JWT validation**, and run a fixture. `--setup` installs the pinned backend dependencies, including PyJWT, and prepares the frontend. See the [lab setup guide](README.md) for prerequisites and separate development commands.

Each comparison creates a random 32-byte HMAC signing key and a token for the selected fixture. The key stays on the server for that comparison and is discarded afterward. Both handlers receive the same token. The fixed handler performs actual PyJWT validation against the current UTC time; the result is not a table of predetermined outcomes.

## Walkthrough

| Fixture | Vulnerable handler | Fixed handler |
| --- | --- | --- |
| Valid report reader | Returns the marker | Verifies and returns the marker |
| Changed signed subject | Trusts the edited subject | Rejects the signature |
| Expired | Returns the marker | Rejects `exp` |
| Unexpected issuer | Returns the marker | Rejects `iss` |
| Other audience | Returns the marker | Rejects `aud` |
| Not valid yet | Returns the marker | Rejects future `nbf` |
| Missing expiration | Returns the marker | Rejects missing required `exp` |
| Unsigned (`alg: none`) | Returns the marker | Rejects the algorithm |
| Valid forbidden subject | Denies report access | Verifies the token, then denies report access |

Start with the valid reader control. Then choose the changed-subject fixture: the server signs a token for `visitor`, changes the encoded payload to `report-reader`, and retains the original signature. The vulnerable path uses the edited claim for authorization. The fixed path detects the mismatch using the library's cryptographic verification.

Next try the claim failures. Those fixtures have correct signatures, demonstrating why a signature alone is insufficient. Finish with the valid forbidden subject: successful verification does not imply permission to read every resource. Both handlers apply the same explicit subject authorization rule.

The evidence panel shows the synthetic compact token and its **unverified** decoded header and claims. Reading that panel does not establish validity. The protected report marker appears in a handler's result only when that handler grants access. Numeric dates are UTC Unix timestamps, with time fixtures ten minutes from the relevant boundary to avoid timing ambiguity.

## Implementation and repair

The vulnerable teaching path calls:

```python
claims = jwt.decode(token, options={"verify_signature": False})
```

The fixed path uses a configured algorithm and trusted validation settings:

```python
claims = jwt.decode(
    token,
    key,
    algorithms=["HS256"],
    issuer="urn:lab:issuer",
    audience="urn:lab:reports",
    options={
        "require": ["exp", "iat", "nbf", "iss", "aud", "sub"],
        "strict_aud": True,
    },
    leeway=0,
)
# Only after successful validation:
allowed = claims["sub"] == "report-reader"
```

Do not derive the accepted algorithm from an untrusted token header. PyJWT's `require` option checks claim presence; enabled validation separately checks their values. Its documented checks include signature, issuer, audience, expiration, and not-before validation. See the [PyJWT API reference](https://pyjwt.readthedocs.io/en/stable/api.html) and [usage examples](https://pyjwt.readthedocs.io/en/stable/usage.html).

The library handles signing and verification; this lesson does not implement custom cryptography. The dependency is pinned to [PyJWT 2.15.1](https://pypi.org/project/PyJWT/2.15.1/), verified against the official package release on 2026-10-18.

## Boundaries and further work

Continue with the separate [OAuth/OIDC and PKCE lesson](OAUTH_OIDC.md) for a local authorization-code flow. It uses OAuthlib and real browser redirects, with an in-process token exchange; the JWT comparison here remains focused on token validation and resource permission.

`POST /api/jwt/compare/` accepts exactly `{"fixture":"normal"}` or another listed fixture ID. Django CSRF protection applies. Requests cannot supply tokens, keys, claims, algorithms, or key-discovery URLs. Fixture selection contains the teaching examples; it does not replace verification in a real application. No remote key lookup or external network request occurs.

This intentionally small report policy is not a production identity system. It does not cover asymmetric keys, JWKS rotation, revocation, refresh tokens, token-type separation, login cookies, or OAuth/OIDC protocol checks. A production design must define trusted issuers and keys, intended token use, replay requirements, and resource permissions. [RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html) describes JWT algorithm verification, issuer and audience validation, and rules that prevent accepting one kind of JWT in place of another.

## Verify the lesson

```powershell
# From labs/browser_security
.venv/Scripts/python.exe backend/manage.py test securitylab.test_jwt_lab

# From labs/browser_security/frontend
$env:LAB_BROWSER_CHANNEL='chrome'
npx playwright test tests/jwt.spec.js
```

Stop the interactive launcher before the browser test command, which starts its own server. Backend tests exercise actual signatures, all required claims, time checks, algorithm allowlisting, independent authorization, fresh keys, and the HTTP/CSRF boundary. Browser tests cover the comparison results and clearing stale evidence when selecting another fixture.

Implementation: [Django handler](backend/securitylab/jwt_lab.py), [Vue lesson](frontend/src/JwtLab.vue), [backend tests](backend/securitylab/test_jwt_lab.py), and [browser tests](frontend/tests/jwt.spec.js).
