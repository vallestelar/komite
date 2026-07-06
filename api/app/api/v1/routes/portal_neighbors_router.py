from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr, Field
from tortoise.exceptions import IntegrityError
from tortoise.expressions import Q

from app.core.auth.dependencies import require_access_token
from app.models.entities import Unit, UnitContact, User
from app.schemas.user_schema import PageMeta


router = APIRouter(
    prefix="/api/v1/portal/neighbors",
    tags=["Portal neighbors"],
    dependencies=[Depends(require_access_token(require_condominium=True))],
)

RELATIONSHIP_TYPES = {"copropietario", "residente", "arrendatario", "contacto", "otro"}


class NeighborCreate(BaseModel):
    unit_id: UUID
    relationship_type: str = Field(default="residente", max_length=40)
    full_name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    document_type: str | None = Field(default="rut", max_length=30)
    document_number: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=255)
    is_primary_contact: bool = False
    receives_notifications: bool = True
    start_date: date | None = None
    end_date: date | None = None
    status: str = Field(default="active", max_length=30)
    metadata: dict = Field(default_factory=dict)


class NeighborUpdate(BaseModel):
    unit_id: UUID | None = None
    relationship_type: str | None = Field(default=None, max_length=40)
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    document_type: str | None = Field(default=None, max_length=30)
    document_number: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=255)
    is_primary_contact: bool | None = None
    receives_notifications: bool | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = Field(default=None, max_length=30)
    metadata: dict | None = None


class NeighborOut(BaseModel):
    id: UUID
    company_id: UUID | None = None
    condominium_id: UUID
    unit_id: UUID
    unit_identifier: str
    user_id: UUID | None = None
    relationship_type: str
    full_name: str
    email: str | None = None
    phone: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    address: str | None = None
    is_primary_contact: bool
    receives_notifications: bool
    start_date: date | None = None
    end_date: date | None = None
    status: str
    metadata: dict = Field(default_factory=dict)


class NeighborPage(BaseModel):
    items: list[NeighborOut]
    meta: PageMeta


def _clean_text(value: str | None) -> str | None:
    return value.strip() if value and value.strip() else None


def _clean_email(value: str | None) -> str | None:
    return value.strip().lower() if value and value.strip() else None


def _validate_relationship(value: str) -> str:
    relationship = value.strip().lower()
    if relationship not in RELATIONSHIP_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tipo de relacion no permitido",
        )
    return relationship


async def _unit_or_404(unit_id: UUID, request: Request) -> Unit:
    unit = await Unit.get_or_none(id=unit_id, condominium_id=request.state.condominium_id)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidad no encontrada en el condominio activo",
        )
    return unit


async def _sync_user(
    *,
    request: Request,
    email: str | None,
    full_name: str,
    phone: str | None,
    document_type: str | None,
    document_number: str | None,
    address: str | None,
) -> User | None:
    if not email:
        return None

    user = await User.get_or_none(email=email)
    if not user:
        return await User.create(
            company_id=request.state.company_id,
            email=email,
            full_name=full_name,
            phone=phone,
            document_type=document_type,
            document_number=document_number,
            address=address,
            status="active",
        )
    if str(user.company_id) != str(request.state.company_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email en otra empresa",
        )

    user.full_name = full_name
    user.phone = phone
    user.document_type = document_type
    user.document_number = document_number
    user.address = address
    await user.save()
    return user


async def _neighbor_out(contact: UnitContact) -> NeighborOut:
    return NeighborOut(
        id=contact.id,
        company_id=contact.company_id,
        condominium_id=contact.condominium_id,
        unit_id=contact.unit_id,
        unit_identifier=contact.unit.identifier,
        user_id=contact.user_id,
        relationship_type=contact.relationship_type,
        full_name=contact.full_name,
        email=contact.email,
        phone=contact.phone,
        document_type=contact.document_type,
        document_number=contact.document_number,
        address=contact.address,
        is_primary_contact=contact.is_primary_contact,
        receives_notifications=contact.receives_notifications,
        start_date=contact.start_date,
        end_date=contact.end_date,
        status=contact.status,
        metadata=contact.metadata,
    )


def _base_query(request: Request):
    return UnitContact.filter(
        condominium_id=request.state.condominium_id,
        company_id=request.state.company_id,
    ).select_related("unit", "user")


async def _ensure_not_duplicate(contact: UnitContact | None, request: Request, unit: Unit, payload: dict) -> None:
    query = UnitContact.filter(
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
        unit=unit,
        relationship_type=payload["relationship_type"],
    )
    if contact:
        query = query.exclude(id=contact.id)

    email = payload.get("email")
    document_number = payload.get("document_number")
    if email:
        query = query.filter(email=email)
    elif document_number:
        query = query.filter(document_number=document_number)
    else:
        query = query.filter(full_name=payload["full_name"])

    if await query.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe ese contacto para la unidad y tipo de relacion",
        )


async def _clear_other_primary(request: Request, unit: Unit, contact_id: UUID | None = None) -> None:
    query = UnitContact.filter(
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
        unit=unit,
        is_primary_contact=True,
    )
    if contact_id:
        query = query.exclude(id=contact_id)
    await query.update(is_primary_contact=False)


@router.get("/", response_model=NeighborPage)
async def list_neighbors(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    q: str | None = Query(None),
) -> NeighborPage:
    query = _base_query(request)
    if q:
        query = query.filter(
            Q(email__icontains=q)
            | Q(full_name__icontains=q)
            | Q(phone__icontains=q)
            | Q(document_number__icontains=q)
            | Q(unit__identifier__icontains=q)
            | Q(relationship_type__icontains=q)
        )

    total = await query.count()
    items = await query.order_by("unit__identifier", "relationship_type", "full_name").offset((page - 1) * page_size).limit(page_size)
    pages = max(1, (total + page_size - 1) // page_size)
    return NeighborPage(
        items=[await _neighbor_out(item) for item in items],
        meta=PageMeta(total=total, page=page, page_size=page_size, pages=pages),
    )


@router.get("/{contact_id}", response_model=NeighborOut)
async def get_neighbor(contact_id: UUID, request: Request) -> NeighborOut:
    contact = await _base_query(request).filter(id=contact_id).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contacto no encontrado")
    return await _neighbor_out(contact)


@router.post("/", response_model=NeighborOut, status_code=status.HTTP_201_CREATED)
async def create_neighbor(payload: NeighborCreate, request: Request) -> NeighborOut:
    unit = await _unit_or_404(payload.unit_id, request)
    data = payload.model_dump()
    data["relationship_type"] = _validate_relationship(data["relationship_type"])
    data["full_name"] = data["full_name"].strip()
    data["email"] = _clean_email(str(data["email"])) if data.get("email") else None
    data["phone"] = _clean_text(data.get("phone"))
    data["document_type"] = _clean_text(data.get("document_type")) or "rut"
    data["document_number"] = _clean_text(data.get("document_number"))
    data["address"] = _clean_text(data.get("address"))

    await _ensure_not_duplicate(None, request, unit, data)
    try:
        user = await _sync_user(
            request=request,
            email=data["email"],
            full_name=data["full_name"],
            phone=data["phone"],
            document_type=data["document_type"],
            document_number=data["document_number"],
            address=data["address"],
        )
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un usuario con ese email")
    if data["is_primary_contact"]:
        await _clear_other_primary(request, unit)

    contact = await UnitContact.create(
        company_id=request.state.company_id,
        condominium_id=request.state.condominium_id,
        unit=unit,
        user=user,
        relationship_type=data["relationship_type"],
        full_name=data["full_name"],
        email=data["email"],
        phone=data["phone"],
        document_type=data["document_type"],
        document_number=data["document_number"],
        address=data["address"],
        is_primary_contact=data["is_primary_contact"],
        receives_notifications=data["receives_notifications"],
        start_date=data["start_date"],
        end_date=data["end_date"],
        status=data["status"],
        metadata=data["metadata"],
    )
    contact = await UnitContact.get(id=contact.id).select_related("unit", "user")
    return await _neighbor_out(contact)


@router.patch("/{contact_id}", response_model=NeighborOut)
async def update_neighbor(contact_id: UUID, payload: NeighborUpdate, request: Request) -> NeighborOut:
    contact = await _base_query(request).filter(id=contact_id).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contacto no encontrado")

    data = payload.model_dump(exclude_unset=True)
    unit = await _unit_or_404(data.pop("unit_id"), request) if "unit_id" in data else contact.unit
    relationship_type = _validate_relationship(data.pop("relationship_type")) if "relationship_type" in data and data["relationship_type"] else contact.relationship_type
    full_name = data.pop("full_name").strip() if "full_name" in data and data["full_name"] else contact.full_name
    email = _clean_email(str(data.pop("email"))) if "email" in data and data["email"] else (None if "email" in data else contact.email)
    phone = _clean_text(data.pop("phone")) if "phone" in data else contact.phone
    document_type = _clean_text(data.pop("document_type")) if "document_type" in data else contact.document_type
    document_number = _clean_text(data.pop("document_number")) if "document_number" in data else contact.document_number
    address = _clean_text(data.pop("address")) if "address" in data else contact.address

    next_payload = {
        "relationship_type": relationship_type,
        "full_name": full_name,
        "email": email,
        "document_number": document_number,
    }
    await _ensure_not_duplicate(contact, request, unit, next_payload)

    try:
        user = await _sync_user(
            request=request,
            email=email,
            full_name=full_name,
            phone=phone,
            document_type=document_type,
            document_number=document_number,
            address=address,
        )
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un usuario con ese email")

    contact.unit = unit
    contact.user = user
    contact.relationship_type = relationship_type
    contact.full_name = full_name
    contact.email = email
    contact.phone = phone
    contact.document_type = document_type
    contact.document_number = document_number
    contact.address = address
    if "is_primary_contact" in data:
        contact.is_primary_contact = data["is_primary_contact"]
    if "receives_notifications" in data:
        contact.receives_notifications = data["receives_notifications"]
    if "start_date" in data:
        contact.start_date = data["start_date"]
    if "end_date" in data:
        contact.end_date = data["end_date"]
    if "status" in data and data["status"]:
        contact.status = data["status"]
    if "metadata" in data and data["metadata"] is not None:
        contact.metadata = data["metadata"]

    if contact.is_primary_contact:
        await _clear_other_primary(request, unit, contact.id)
    await contact.save()

    contact = await UnitContact.get(id=contact.id).select_related("unit", "user")
    return await _neighbor_out(contact)


@router.delete("/{contact_id}")
async def delete_neighbor(contact_id: UUID, request: Request) -> dict[str, int]:
    contact = await _base_query(request).filter(id=contact_id).first()
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contacto no encontrado")
    deleted = await UnitContact.filter(id=contact_id).delete()
    return {"deleted": deleted}
