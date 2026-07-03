import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from app.core.security.jwt import decode_jwt, encode_jwt
from app.core.settings import settings
from app.models.entities import RefreshToken, User


class AuthService:
    @staticmethod
    def create_access_token(
        *,
        subject: str,
        extra_claims: Optional[Dict[str, Any]] = None,
        expires_minutes: Optional[int] = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(
            minutes=expires_minutes or settings.access_token_expire_minutes
        )

        payload: Dict[str, Any] = {
            "sub": subject,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }

        if extra_claims:
            payload.update(extra_claims)

        return encode_jwt(payload, settings.jwt_secret_key, settings.jwt_algorithm)

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        return decode_jwt(token, settings.jwt_secret_key, [settings.jwt_algorithm])

    @staticmethod
    def hash_refresh_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    async def create_refresh_token(
        *,
        user: User,
        family_id=None,
        created_by_ip: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[str, RefreshToken]:
        token = secrets.token_urlsafe(48)
        refresh_token = await RefreshToken.create(
            user=user,
            token_hash=AuthService.hash_refresh_token(token),
            family_id=family_id or uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
            created_by_ip=created_by_ip,
            user_agent=user_agent[:255] if user_agent else None,
        )
        return token, refresh_token

    @staticmethod
    async def rotate_refresh_token(
        *,
        token: str,
        created_by_ip: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[User, str, RefreshToken]:
        now = datetime.now(timezone.utc)
        token_hash = AuthService.hash_refresh_token(token)
        refresh_token = await RefreshToken.filter(token_hash=token_hash).select_related("user").first()
        if not refresh_token:
            raise ValueError("Refresh token invalido")

        if refresh_token.revoked_at is not None:
            await RefreshToken.filter(family_id=refresh_token.family_id, revoked_at=None).update(revoked_at=now)
            raise ValueError("Refresh token reutilizado")

        if refresh_token.expires_at <= now:
            raise ValueError("Refresh token invalido o expirado")

        if refresh_token.user.status != "active":
            raise ValueError("Usuario inactivo")

        new_token, new_refresh_token = await AuthService.create_refresh_token(
            user=refresh_token.user,
            family_id=refresh_token.family_id,
            created_by_ip=created_by_ip,
            user_agent=user_agent,
        )
        refresh_token.revoked_at = now
        refresh_token.replaced_by = new_refresh_token
        await refresh_token.save()
        return refresh_token.user, new_token, new_refresh_token

    @staticmethod
    async def revoke_refresh_token(token: str) -> None:
        refresh_token = await RefreshToken.get_or_none(
            token_hash=AuthService.hash_refresh_token(token),
            revoked_at=None,
        )
        if not refresh_token:
            return

        refresh_token.revoked_at = datetime.now(timezone.utc)
        await refresh_token.save()
