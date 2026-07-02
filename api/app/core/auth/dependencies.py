from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.repositories.user_repository import get_user_by_id, user_has_condominium
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


def require_access_token(require_condominium: bool = False) -> Callable:
    async def _dependency(
        request: Request,
        creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    ) -> None:
        token: Optional[str] = None

        if creds is not None and creds.scheme.lower() == "bearer":
            token = creds.credentials

        if not token:
            token = (
                request.query_params.get("token")
                or request.query_params.get("access_token")
            )

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Falta token Bearer",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload: Dict[str, Any] = AuthService.decode_token(token)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tipo de token no valido",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token incompleto",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await get_user_by_id(str(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no valido",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo",
            )

        condominium_id = (
            request.headers.get("X-Condominium")
            or request.query_params.get("condominium")
            or request.query_params.get("condominium_id")
        )

        if require_condominium and not condominium_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falta header X-Condominium",
            )

        allowed_condominium_ids = {
            str(item.get("id"))
            for item in payload.get("condominiums", [])
            if isinstance(item, dict) and item.get("id")
        }

        if condominium_id:
            if str(condominium_id) not in allowed_condominium_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Condominio no permitido para este usuario",
                )

            if not await user_has_condominium(str(user.id), str(condominium_id)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Usuario no pertenece a este condominio",
                )

        request.state.user_id = str(user.id)
        request.state.user = user
        request.state.company_id = str(user.company_id) if user.company_id else None
        request.state.condominium_id = str(condominium_id) if condominium_id else None
        request.state.condominiums = payload.get("condominiums", [])
        request.state.token_payload = payload

    return _dependency

