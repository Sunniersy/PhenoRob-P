import uuid
from datetime import datetime, timedelta, timezone

import jwt
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password_hash: str, plain_password: str) -> bool:
    return check_password_hash(password_hash, plain_password)


def encode_token(payload: dict, secret: str, expires_minutes: int = 30) -> str:
    claims = dict(payload)
    claims["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    claims["iat"] = datetime.now(timezone.utc)
    claims["jti"] = str(uuid.uuid4())
    claims.setdefault("type", "access")
    return jwt.encode(claims, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> dict:
    return jwt.decode(token, secret, algorithms=["HS256"])


def create_refresh_token(payload: dict, secret: str, expires_days: int = 7) -> str:
    """Create a long-lived refresh token."""
    claims = dict(payload)
    claims["exp"] = datetime.now(timezone.utc) + timedelta(days=expires_days)
    claims["iat"] = datetime.now(timezone.utc)
    claims["type"] = "refresh"
    claims["jti"] = str(uuid.uuid4())
    return jwt.encode(claims, secret, algorithm="HS256")


def verify_refresh_token(token: str, secret: str) -> dict:
    """Verify a refresh token and ensure it is a refresh-type token."""
    claims = jwt.decode(token, secret, algorithms=["HS256"])
    if claims.get("type") != "refresh":
        raise jwt.InvalidTokenError("token is not a refresh token")
    return claims

