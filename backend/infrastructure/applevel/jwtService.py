from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Mapping, Optional, Protocol

import jwt

from nomac import settings


class HasUserFields(Protocol):
    id: Any  # UUID or str
    sub: Optional[str]
    email: str
    name: str


@dataclass(frozen=True)
class JwtConfig:
    alg: str = getattr(settings, "JWT_ALGORITHM", "RS256")
    access_ttl_min: int = getattr(settings, "JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 60)
    refresh_ttl_days: int = getattr(settings, "JWT_REFRESH_TOKEN_LIFETIME_DAYS", 7)
    issuer: str = getattr(settings, "JWT_ISSUER", "nomac-api")
    audience: str = getattr(settings, "JWT_AUDIENCE", "nomac-clients")
    # Keys: prefer asymmetric (RS256/ES256)
    private_key: str = getattr(
        settings,
        "JWT_PRIVATE_KEY",
        getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY),
    )
    public_key: str = getattr(
        settings,
        "JWT_PUBLIC_KEY",
        getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY),
    )
    leeway_seconds: int = getattr(settings, "JWT_LEEWAY_SECONDS", 30)
    kid: Optional[str] = getattr(settings, "JWT_KID", None)


def _get(field_source: Any, key: str) -> Optional[Any]:
    if isinstance(field_source, Mapping):
        return field_source.get(key)
    return getattr(field_source, key, None)


def _norm_email(email: Optional[str]) -> Optional[str]:
    return email.strip().lower() if isinstance(email, str) else None


class JwtService:
    def __init__(self, cfg: JwtConfig | None = None) -> None:
        self.cfg = cfg or JwtConfig()

    # ---- Public API ---------------------------------------------------------
    def generate_access_token(
        self,
        user: HasUserFields | Dict[str, Any],
        extra_claims: Dict[str, Any] | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        email = _norm_email(_get(user, "email"))
        if not email:
            raise ValueError("Cannot generate access token: email missing")
        payload = {
            "email": email,
            "token_type": "access",
            "iss": self.cfg.issuer,
            "aud": self.cfg.audience,
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self.cfg.access_ttl_min)).timestamp()),
            "jti": uuid.uuid4().hex,
            **(extra_claims or {}),
        }
        headers = {"kid": self.cfg.kid} if self.cfg.kid else None
        return jwt.encode(
            payload, self.cfg.private_key, algorithm=self.cfg.alg, headers=headers
        )

    def generate_refresh_token(
        self, user: HasUserFields | Dict[str, Any], family_id: str | None = None
    ) -> str:
        now = datetime.now(timezone.utc)
        email = _norm_email(_get(user, "email"))
        if not email:
            raise ValueError("Cannot generate access token: email missing")
        payload = {
            "email": email,
            "token_type": "refresh",
            "iss": self.cfg.issuer,
            "aud": self.cfg.audience,
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(days=self.cfg.refresh_ttl_days)).timestamp()),
            "jti": uuid.uuid4().hex,
            "tff": family_id or uuid.uuid4().hex,
        }
        headers = {"kid": self.cfg.kid} if self.cfg.kid else None
        return jwt.encode(
            payload, self.cfg.private_key, algorithm=self.cfg.alg, headers=headers
        )

    def decode_and_verify(
        self, token: str, expected_type: str | None = None
    ) -> Dict[str, Any]:
        options = {"require": ["exp", "iat", "nbf", "iss", "aud", "email"]}
        payload = jwt.decode(
            token,
            self.cfg.public_key,
            algorithms=[self.cfg.alg],
            audience=self.cfg.audience,
            issuer=self.cfg.issuer,
            leeway=self.cfg.leeway_seconds,
            options=options,
        )
        if expected_type and payload.get("token_type") != expected_type:
            raise jwt.InvalidTokenError("Unexpected token_type")
        # Optional: check jti in a denylist to support logout/rotation
        return payload
