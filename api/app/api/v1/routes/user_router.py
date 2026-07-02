from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from tortoise.exceptions import IntegrityError
from tortoise.expressions import Q

from app.core.auth.dependencies import require_access_token
from app.core.security.passwords import hash_password
from app.models.entities import Company, Condominium, Role, Unit, User, UserCondominium
from app.schemas.user_schema import (
    PageMeta,
    UserCreate,
    UserCreatedOut,
    UserMembershipInput,
    UserMembershipOut,
    UserOut,
    UserPage,
    UserUpdate,
)

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
    dependencies=[Depends(require_access_token())],
)


async def _membership_out(membership: UserCondominium) -> UserMembershipOut:
    return UserMembershipOut(
        id=membership.id,
        condominium_id=membership.condominium_id,
        condominium_name=membership.condominium.name if membership.condominium else None,
        role_id=membership.role_id,
        role_code=membership.role.code,
        role_name=membership.role.name,
        unit_id=membership.unit_id,
        unit_identifier=membership.unit.identifier if membership.unit else None,
        status=membership.status,
        receives_notifications=membership.receives_notifications,
    )


async def _user_memberships(user: User) -> list[UserCondominium]:
    return await UserCondominium.filter(user=user).select_related(
        "condominium",
        "role",
        "unit",
    )


async def _user_out(user: User) -> UserOut:
    memberships = await _user_memberships(user)
    first_membership = memberships[0] if memberships else None

    return UserOut(
        id=user.id,
        company_id=user.company_id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        status=user.status,
        global_role=user.global_role,
        condominium_id=first_membership.condominium_id if first_membership else None,
        role_code=first_membership.role.code if first_membership else None,
        memberships=[await _membership_out(membership) for membership in memberships],
    )


def _legacy_membership(
    condominium_id: UUID | None,
    role_code: str | None,
) -> list[UserMembershipInput] | None:
    if condominium_id is None:
        return None

    return [
        UserMembershipInput(
            condominium_id=condominium_id,
            role_code=role_code or "vecino",
        )
    ]


async def _replace_memberships(
    user: User,
    memberships: list[UserMembershipInput],
) -> None:
    await UserCondominium.filter(user=user).delete()
    seen_memberships: set[tuple[str, str, str | None]] = set()

    for item in memberships:
        membership_key = (
            str(item.condominium_id),
            item.role_code,
            str(item.unit_id) if item.unit_id else None,
        )
        if membership_key in seen_memberships:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Hay accesos duplicados para el mismo condominio, rol y unidad",
            )
        seen_memberships.add(membership_key)

        condominium = await Condominium.get_or_none(id=item.condominium_id)
        if not condominium:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Condominio no encontrado: {item.condominium_id}",
            )

        role = await Role.get_or_none(code=item.role_code)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rol no encontrado: {item.role_code}",
            )

        unit = None
        if item.unit_id:
            unit = await Unit.get_or_none(id=item.unit_id, condominium=condominium)
            if not unit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Unidad no encontrada en el condominio: {item.unit_id}",
                )

        await UserCondominium.create(
            user=user,
            condominium=condominium,
            role=role,
            unit=unit,
            status=item.status,
            receives_notifications=item.receives_notifications,
        )


@router.post("/", response_model=UserCreatedOut, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, request: Request) -> UserCreatedOut:
    company_id = payload.company_id or request.state.company_id
    company = None

    if company_id:
        company = await Company.get_or_none(id=company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada",
            )

    memberships = payload.memberships
    if memberships is None:
        memberships = _legacy_membership(payload.condominium_id, payload.role_code) or []

    try:
        user = await User.create(
            company=company,
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            phone=payload.phone,
            status=payload.status,
            global_role=payload.global_role,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email",
        )

    if memberships:
        await _replace_memberships(user, memberships)

    return UserCreatedOut(**(await _user_out(user)).model_dump())


@router.get("/", response_model=UserPage)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    q: str | None = Query(None),
    order_by: list[str] | None = Query(None),
) -> UserPage:
    query = User.all()
    if q:
        query = query.filter(
            Q(email__icontains=q)
            | Q(full_name__icontains=q)
            | Q(global_role__icontains=q)
        )

    if order_by:
        query = query.order_by(*order_by)

    total = await query.count()
    items = await query.offset((page - 1) * page_size).limit(page_size)
    pages = (total + page_size - 1) // page_size

    return UserPage(
        items=[await _user_out(user) for user in items],
        meta=PageMeta(total=total, page=page, page_size=page_size, pages=pages),
    )


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: UUID) -> UserOut:
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return await _user_out(user)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: UUID, payload: UserUpdate) -> UserOut:
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    data = payload.model_dump(exclude_unset=True)
    password = data.pop("password", None)
    memberships = data.pop("memberships", None)
    condominium_id = data.pop("condominium_id", None)
    role_code = data.pop("role_code", None)
    memberships_touched = (
        "memberships" in payload.model_fields_set
        or "condominium_id" in payload.model_fields_set
        or "role_code" in payload.model_fields_set
    )

    if "company_id" in data and data["company_id"] is not None:
        company = await Company.get_or_none(id=data["company_id"])
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada",
            )

    for key, value in data.items():
        setattr(user, key, value)

    if password:
        user.password_hash = hash_password(password)

    try:
        await user.save()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email",
        )

    if memberships_touched:
        if memberships is None:
            memberships = _legacy_membership(condominium_id, role_code) or []
        await _replace_memberships(
            user,
            [UserMembershipInput(**item) for item in memberships],
        )

    return await _user_out(user)


@router.delete("/{user_id}")
async def delete_user(user_id: UUID):
    deleted = await User.filter(id=user_id).delete()
    if deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return {"deleted": deleted}
