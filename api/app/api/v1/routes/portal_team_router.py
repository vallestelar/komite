from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.auth.dependencies import require_access_token
from app.models.entities import Condominium, CondominiumOperationalStaff


router = APIRouter(
    prefix="/api/v1/portal/team",
    tags=["Portal team"],
    dependencies=[Depends(require_access_token(require_condominium=True))],
)


class PortalTeamMemberOut(BaseModel):
    id: UUID
    user_id: UUID
    full_name: str
    email: str | None = None
    phone: str | None = None
    portal_profile: str
    company_profile: str | None = None
    organization_position: str | None = None
    responsibility: str | None = None
    is_primary: bool
    status: str


class PortalTeamResponse(BaseModel):
    items: list[PortalTeamMemberOut]
    mode: str
    condominium_id: UUID
    condominium_name: str


@router.get("/", response_model=PortalTeamResponse)
async def list_company_team(request: Request) -> PortalTeamResponse:
    if not request.state.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no tiene empresa asociada",
        )

    condominium = await Condominium.get_or_none(
        id=request.state.condominium_id,
        company_id=request.state.company_id,
    )
    if not condominium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condominio no encontrado para la empresa del usuario",
        )

    custom_rows = await (
        CondominiumOperationalStaff.filter(
            company_id=request.state.company_id,
            condominium_id=request.state.condominium_id,
        )
        .select_related("user")
        .order_by("-is_primary", "portal_profile")
    )
    metadata = condominium.metadata or {}
    mode = metadata.get("operational_staff_mode") or ("custom" if custom_rows else "company")
    if mode == "custom":
        rows = custom_rows
    else:
        rows = await (
            CondominiumOperationalStaff.filter(
                company_id=request.state.company_id,
                condominium_id__isnull=True,
            )
            .select_related("user")
            .order_by("-is_primary", "portal_profile")
        )

    rows = sorted(rows, key=lambda item: (item.status != "active", not item.is_primary, item.user.full_name.casefold()))
    return PortalTeamResponse(
        items=[
            PortalTeamMemberOut(
                id=row.id,
                user_id=row.user_id,
                full_name=row.user.full_name,
                email=row.user.email,
                phone=row.user.phone,
                portal_profile=row.portal_profile,
                company_profile=row.user.company_profile,
                organization_position=row.user.organization_position,
                responsibility=row.responsibility or row.user.organization_position,
                is_primary=row.is_primary,
                status=row.status,
            )
            for row in rows
        ],
        mode=mode,
        condominium_id=condominium.id,
        condominium_name=condominium.name,
    )
