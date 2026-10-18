"""Real PyJWT verification using ephemeral keys and server-owned token fixtures."""
import json
import secrets
from datetime import datetime, timezone

import jwt
from django.http import JsonResponse

ISSUER = "urn:lab:issuer"
AUDIENCE = "urn:lab:reports"
ALLOWED_SUBJECT = "report-reader"
MARKER = "JWT_PROTECTED_REPORT_MARKER"
REQUIRED_CLAIMS = ["exp", "iat", "nbf", "iss", "aud", "sub"]
FIXTURES = {
    "normal": {"label": "Control: valid report reader", "description": "A correctly signed token with the expected issuer, audience, time claims, and permitted subject.", "expectation": "Both handlers authorize the reader and return the synthetic report marker."},
    "tampered": {"label": "Change a signed subject", "description": "Sign a token for visitor, then change its payload subject to report-reader without replacing the signature.", "expectation": "The vulnerable handler trusts the edited subject. The fixed handler rejects the invalid signature."},
    "expired": {"label": "Expired token", "description": "A correctly signed token whose expiration is ten minutes in the past.", "expectation": "The vulnerable handler accepts it. The fixed handler rejects expiration."},
    "wrong-issuer": {"label": "Unexpected issuer", "description": "A correctly signed fixture names urn:lab:other-issuer as its issuer.", "expectation": "The fixed handler rejects the issuer even though the signature is valid."},
    "wrong-audience": {"label": "Token for another audience", "description": "A correctly signed fixture targets urn:lab:other-service instead of reports.", "expectation": "The fixed handler rejects a token intended for another audience."},
    "future": {"label": "Not valid yet", "description": "A correctly signed token has nbf ten minutes in the future.", "expectation": "The fixed handler rejects it before the not-before time."},
    "missing-exp": {"label": "Missing required expiration", "description": "A correctly signed token omits exp entirely.", "expectation": "The fixed handler requires exp; checking expiration only when present would be insufficient."},
    "unsigned": {"label": "Unsigned token (alg: none)", "description": "The fixture has an empty signature and an alg value of none.", "expectation": "The fixed handler's configured HS256 allowlist rejects the unsigned token."},
    "wrong-subject": {"label": "Control: valid token, forbidden subject", "description": "A valid signed token belongs to visitor, who cannot read this report.", "expectation": "Both handlers deny access. Successful token verification is separate from authorization."},
}
POLICY = {"algorithms": ["HS256"], "issuer": ISSUER, "audience": AUDIENCE,
          "requiredClaims": REQUIRED_CLAIMS, "permittedSubject": ALLOWED_SUBJECT,
          "leewaySeconds": 0}
JWT_METADATA = {"library": "PyJWT", "fixtures": [{"id": key, **value} for key, value in FIXTURES.items()],
                "policy": POLICY}


def build_token(fixture_id, key, now):
    """Generate real tokens; the HTTP interface accepts no caller-owned claims."""
    claims = {"iss": ISSUER, "aud": AUDIENCE, "sub": ALLOWED_SUBJECT,
              "iat": now - 60, "nbf": now - 60, "exp": now + 3600}
    if fixture_id in ("tampered", "wrong-subject"):
        claims["sub"] = "visitor"
    elif fixture_id == "expired":
        claims.update(iat=now - 3600, nbf=now - 3600, exp=now - 600)
    elif fixture_id == "wrong-issuer":
        claims["iss"] = "urn:lab:other-issuer"
    elif fixture_id == "wrong-audience":
        claims["aud"] = "urn:lab:other-service"
    elif fixture_id == "future":
        claims["nbf"] = now + 600
    elif fixture_id == "missing-exp":
        del claims["exp"]
    if fixture_id == "unsigned":
        return jwt.encode(claims, key=None, algorithm="none")
    token = jwt.encode(claims, key, algorithm="HS256")
    if fixture_id == "tampered":
        header, payload, signature = token.split(".")
        modified = json.loads(jwt.utils.base64url_decode(payload))
        modified["sub"] = ALLOWED_SUBJECT
        payload = jwt.utils.base64url_encode(json.dumps(modified, separators=(",", ":")).encode()).decode()
        token = ".".join((header, payload, signature))
    return token


def decide_token(token, key, mode):
    """Both paths perform the same authorization after their decoding step."""
    if mode not in ("vulnerable", "fixed"):
        raise ValueError("Unknown JWT handler")
    result = {"mode": mode, "outcome": "rejected", "validation": "skipped" if mode == "vulnerable" else "rejected",
              "reason": "", "marker": None}
    try:
        if mode == "vulnerable":
            claims = jwt.decode(token, options={"verify_signature": False})
        else:
            claims = jwt.decode(token, key, algorithms=["HS256"], issuer=ISSUER, audience=AUDIENCE,
                                options={"require": REQUIRED_CLAIMS, "strict_aud": True}, leeway=0)
            result["validation"] = "verified"
    except jwt.InvalidSignatureError:
        result["reason"] = "Signature verification failed: the payload and signature do not match."
    except jwt.ExpiredSignatureError:
        result["reason"] = "The token has expired (exp)."
    except jwt.ImmatureSignatureError:
        result["reason"] = "The token is not valid yet (nbf or iat)."
    except jwt.InvalidIssuerError:
        result["reason"] = "The issuer does not match the configured issuer (iss)."
    except jwt.InvalidAudienceError:
        result["reason"] = "The audience does not match the reports service (aud)."
    except jwt.MissingRequiredClaimError as failure:
        result["reason"] = f"A required claim is missing: {failure.claim}."
    except jwt.InvalidAlgorithmError:
        result["reason"] = "The token algorithm is outside the configured HS256 allowlist."
    except jwt.InvalidTokenError:
        result["reason"] = "The token could not be validated."
    else:
        if claims.get("sub") != ALLOWED_SUBJECT:
            result["reason"] = "The subject is not authorized to read this report. A valid token does not grant every permission."
        else:
            result.update(outcome="accepted", marker=MARKER, reason=(
                "Unverified claims were used for authorization; signature, issuer, audience and time checks were skipped."
                if mode == "vulnerable" else
                "PyJWT verified the signature and required claims against the configured policy; the subject is authorized."
            ))
    return result


def compare_tokens(fixture_id):
    now = int(datetime.now(timezone.utc).timestamp())
    key = secrets.token_bytes(32)
    token = build_token(fixture_id, key, now)
    return {"fixture": fixture_id, "token": token, "header": jwt.get_unverified_header(token),
            "claims": jwt.decode(token, options={"verify_signature": False}), "checkedAt": now,
            "policy": POLICY, "results": {mode: decide_token(token, key, mode) for mode in ("vulnerable", "fixed")}}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def jwt_compare(request):
    """Ordinary Django CSRF protection applies; only bounded fixture IDs enter."""
    def invalid(reason, status=400):
        return JsonResponse({"error": reason}, status=status)

    if request.method != "POST":
        response = invalid("Use POST with a JSON fixture identifier.", 405)
        response["Allow"] = "POST"
        return response
    if request.GET or request.content_type != "application/json":
        return invalid("Use application/json without query parameters.")
    if len(request.body) > 2048:
        return invalid("The fixture request is too large.")
    try:
        body = json.loads(request.body, object_pairs_hook=unique_object)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return invalid("Invalid JSON or duplicate fields.")
    if not isinstance(body, dict) or set(body) != {"fixture"}:
        return invalid("Provide exactly fixture; custom tokens, claims and keys are not accepted.")
    if not isinstance(body["fixture"], str) or body["fixture"] not in FIXTURES:
        return invalid("Choose a listed JWT fixture.")
    return JsonResponse(compare_tokens(body["fixture"]))
