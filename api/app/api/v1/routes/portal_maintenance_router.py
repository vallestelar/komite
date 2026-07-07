from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.auth.dependencies import require_access_token
from app.models.entities import CondominiumInspectionItem, CondominiumInspectionTemplate


router = APIRouter(
    prefix="/api/v1/portal/maintenance",
    tags=["Portal maintenance"],
    dependencies=[Depends(require_access_token(require_condominium=True))],
)


class PortalMaintenanceTemplateOut(BaseModel):
    id: UUID
    name: str
    template_type: str
    version: int
    status: str
    effective_from: str | None = None
    effective_to: str | None = None


class PortalMaintenanceItemOut(BaseModel):
    id: UUID
    condominium_template_id: UUID
    section_name: str | None = None
    asset_name: str | None = None
    task_name: str
    instructions: str | None = None
    periodicity: str | None = None
    planned_months: list = Field(default_factory=list)
    responsible_user_id: UUID | None = None
    responsible_profile: str | None = None
    estimated_duration_minutes: int | None = None
    priority: str
    status: str


class PortalMaintenanceResponse(BaseModel):
    templates: list[PortalMaintenanceTemplateOut]
    selected_template: PortalMaintenanceTemplateOut | None = None
    items: list[PortalMaintenanceItemOut]


class PortalMaintenanceItemUpdate(BaseModel):
    section_name: str | None = Field(default=None, max_length=150)
    asset_name: str | None = Field(default=None, max_length=180)
    task_name: str | None = Field(default=None, max_length=255)
    instructions: str | None = None
    periodicity: str | None = Field(default=None, max_length=80)
    planned_months: list | None = None
    responsible_profile: str | None = Field(default=None, max_length=60)
    responsible_user_id: UUID | None = None
    estimated_duration_minutes: int | None = None
    priority: str | None = Field(default=None, max_length=30)
    status: str | None = Field(default=None, max_length=30)


class PortalMaintenanceItemCreate(BaseModel):
    condominium_template_id: UUID
    section_name: str | None = Field(default=None, max_length=150)
    asset_name: str | None = Field(default=None, max_length=180)
    task_name: str = Field(..., max_length=255)
    instructions: str | None = None
    periodicity: str | None = Field(default=None, max_length=80)
    planned_months: list = Field(default_factory=list)
    responsible_profile: str | None = Field(default=None, max_length=60)
    responsible_user_id: UUID | None = None
    estimated_duration_minutes: int | None = None
    priority: str = Field(default="medium", max_length=30)
    status: str = Field(default="active", max_length=30)


def _template_out(template: CondominiumInspectionTemplate) -> PortalMaintenanceTemplateOut:
    return PortalMaintenanceTemplateOut(
        id=template.id,
        name=template.name,
        template_type=template.template_type,
        version=template.version,
        status=template.status,
        effective_from=template.effective_from.isoformat() if template.effective_from else None,
        effective_to=template.effective_to.isoformat() if template.effective_to else None,
    )


def _item_out(item: CondominiumInspectionItem) -> PortalMaintenanceItemOut:
    return PortalMaintenanceItemOut(
        id=item.id,
        condominium_template_id=item.condominium_template_id,
        section_name=item.section_name,
        asset_name=item.asset_name,
        task_name=item.task_name,
        instructions=item.instructions,
        periodicity=item.periodicity,
        planned_months=item.planned_months or [],
        responsible_user_id=item.responsible_user_id,
        responsible_profile=item.responsible_profile,
        estimated_duration_minutes=item.estimated_duration_minutes,
        priority=item.priority,
        status=item.status,
    )


async def _get_template_or_404(
    template_id: UUID,
    request: Request,
) -> CondominiumInspectionTemplate:
    template = await CondominiumInspectionTemplate.get_or_none(
        id=template_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
        template_type__in=("maintenance", "mixed"),
    )
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plantilla del condominio no encontrada")
    return template


@router.get("/", response_model=PortalMaintenanceResponse)
async def list_maintenance_plan(
    request: Request,
    template_id: UUID | None = None,
) -> PortalMaintenanceResponse:
    templates = await (
        CondominiumInspectionTemplate.filter(
            company_id=request.state.company_id,
            condominium_id=request.state.condominium_id,
            template_type__in=("maintenance", "mixed"),
        )
        .order_by("-version", "name")
    )

    selected_template = None
    if template_id:
        selected_template = next((item for item in templates if str(item.id) == str(template_id)), None)
        if not selected_template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plantilla del condominio no encontrada")
    elif templates:
        selected_template = templates[0]

    items: list[CondominiumInspectionItem] = []
    if selected_template:
        items = await (
            CondominiumInspectionItem.filter(
                company_id=request.state.company_id,
                condominium_id=request.state.condominium_id,
                condominium_template_id=selected_template.id,
            )
            .order_by("section_name", "task_name")
        )

    return PortalMaintenanceResponse(
        templates=[_template_out(template) for template in templates],
        selected_template=_template_out(selected_template) if selected_template else None,
        items=[_item_out(item) for item in items],
    )


@router.post("/items", response_model=PortalMaintenanceItemOut, status_code=status.HTTP_201_CREATED)
async def create_maintenance_item(
    payload: PortalMaintenanceItemCreate,
    request: Request,
) -> PortalMaintenanceItemOut:
    await _get_template_or_404(payload.condominium_template_id, request)
    actor = getattr(request.state.user, "email", None) or str(request.state.user_id)
    item = await CondominiumInspectionItem.create(
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
        condominium_template_id=payload.condominium_template_id,
        section_name=payload.section_name,
        asset_name=payload.asset_name,
        task_name=payload.task_name,
        instructions=payload.instructions,
        periodicity=payload.periodicity,
        planned_months=payload.planned_months,
        responsible_profile=payload.responsible_profile,
        responsible_user_id=payload.responsible_user_id,
        estimated_duration_minutes=payload.estimated_duration_minutes,
        priority=payload.priority,
        status=payload.status,
        metadata={"created_from_portal": True},
        created_by=actor,
        updated_by=actor,
    )
    return _item_out(item)


@router.patch("/items/{item_id}", response_model=PortalMaintenanceItemOut)
async def update_maintenance_item(
    item_id: UUID,
    payload: PortalMaintenanceItemUpdate,
    request: Request,
) -> PortalMaintenanceItemOut:
    item = await CondominiumInspectionItem.get_or_none(
        id=item_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de mantención no encontrado")

    data = payload.model_dump(exclude_unset=True)
    for field_name, value in data.items():
        setattr(item, field_name, value)
    item.updated_by = getattr(request.state.user, "email", None) or str(request.state.user_id)
    await item.save()
    return _item_out(item)


@router.post("/items/{item_id}/deactivate", response_model=PortalMaintenanceItemOut)
async def deactivate_maintenance_item(
    item_id: UUID,
    request: Request,
) -> PortalMaintenanceItemOut:
    item = await CondominiumInspectionItem.get_or_none(
        id=item_id,
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
    ).select_related("condominium_template")
    if not item or item.condominium_template.template_type not in ("maintenance", "mixed"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de mantención no encontrado")

    item.status = "inactive"
    item.updated_by = getattr(request.state.user, "email", None) or str(request.state.user_id)
    await item.save()
    return _item_out(item)
