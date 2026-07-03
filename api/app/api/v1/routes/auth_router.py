from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.auth.dependencies import require_access_token, user_is_komite_employee
from app.core.security.passwords import verify_password
from app.models.entities import Company, Condominium
from app.repositories.user_repository import get_user_by_email, get_user_memberships
from app.schemas.auth.auth_schema import (
    CompanyLoginResponse,
    CondominiumLoginResponse,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserLoginResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


def _company_payload(company: Company | None) -> CompanyLoginResponse | None:
    if not company:
        return None
    return CompanyLoginResponse(id=str(company.id), name=company.name)


def _client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


async def _build_token_response(user, refresh_token: str | None = None) -> TokenResponse:
    memberships = await get_user_memberships(str(user.id))
    condominiums: list[CondominiumLoginResponse] = []
    seen_condominiums: set[tuple[str, str, str | None]] = set()

    async def add_condominium_payload(condominium, membership) -> None:
        key = (
            str(condominium.id),
            membership.role.code,
            str(membership.unit.id) if membership.unit else None,
        )
        if key in seen_condominiums:
            return
        seen_condominiums.add(key)
        condominiums.append(
            CondominiumLoginResponse(
                id=str(condominium.id),
                name=condominium.name,
                role=membership.role.code,
                role_name=membership.role.name,
                unit_id=str(membership.unit.id) if membership.unit else None,
                unit_identifier=membership.unit.identifier if membership.unit else None,
            )
        )

    for membership in memberships:
        if membership.condominium:
            await add_condominium_payload(membership.condominium, membership)
            continue

        if not membership.company_id:
            continue

        company_condominiums = await Condominium.filter(
            company_id=membership.company_id,
            status="active",
        ).order_by("name")
        for condominium in company_condominiums:
            await add_condominium_payload(condominium, membership)

    company = await Company.get_or_none(id=user.company_id) if user.company_id else None

    user_payload = UserLoginResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        company_profile=user.company_profile,
    )

    company_payload = _company_payload(company)

    token_condominiums = [item.model_dump() for item in condominiums]
    access_token = AuthService.create_access_token(
        subject=str(user.id),
        extra_claims={
            "email": user.email,
            "full_name": user.full_name,
            "company_profile": user.company_profile,
            "company": company_payload.model_dump() if company_payload else None,
            "condominiums": token_condominiums,
        },
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_payload,
        company=company_payload,
        condominiums=condominiums,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request) -> TokenResponse:
    invalid_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = await get_user_by_email(payload.email)
    if not user:
        raise invalid_exc

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    if not verify_password(payload.password, user.password_hash):
        raise invalid_exc

    refresh_token, _ = await AuthService.create_refresh_token(
        user=user,
        created_by_ip=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return await _build_token_response(user, refresh_token)


@router.post("/backoffice-login", response_model=TokenResponse)
async def backoffice_login(payload: LoginRequest, request: Request) -> TokenResponse:
    invalid_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = await get_user_by_email(payload.email)
    if not user:
        raise invalid_exc

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    if not verify_password(payload.password, user.password_hash):
        raise invalid_exc

    if not await user_is_komite_employee(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a empleados de Komite",
        )

    refresh_token, _ = await AuthService.create_refresh_token(
        user=user,
        created_by_ip=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return await _build_token_response(user, refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshTokenRequest, request: Request) -> TokenResponse:
    try:
        user, new_refresh_token, _ = await AuthService.rotate_refresh_token(
            token=payload.refresh_token,
            created_by_ip=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await _build_token_response(user, new_refresh_token)


@router.post("/logout")
async def logout(payload: LogoutRequest) -> dict[str, bool]:
    await AuthService.revoke_refresh_token(payload.refresh_token)
    return {"success": True}


@router.get("/me", response_model=MeResponse, dependencies=[Depends(require_access_token())])
async def me(request: Request) -> MeResponse:
    return await _build_token_response(request.state.user)
