import os
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status
import hmac
import hashlib
import json
import base64

JWT_SECRET = os.getenv("JWT_SECRET", "default_secret_for_dev")

def verify_jwt_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Validates Bearer JWT token against the shared JWT_SECRET from the Node.js backend.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = authorization.split(" ")[1]
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed JWT token structure"
        )

    header_b64, payload_b64, signature_b64 = parts

    def base64url_decode(s: str) -> bytes:
        rem = len(s) % 4
        if rem > 0:
            s += "=" * (4 - rem)
        return base64.urlsafe_b64decode(s)

    try:
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(
            JWT_SECRET.encode("utf-8"),
            signing_input,
            hashlib.sha256
        ).digest()
        provided_sig = base64url_decode(signature_b64)

        if not hmac.compare_digest(expected_sig, provided_sig):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWT signature"
            )

        payload_bytes = base64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
        return payload

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification error: {str(e)}"
        )
