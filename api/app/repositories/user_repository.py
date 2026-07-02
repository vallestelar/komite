from typing import Optional
from uuid import UUID

from app.models.entities import User, UserCondominium


async def get_user_by_email(email: str) -> Optional[User]:
    return await User.get_or_none(email=email)


async def get_user_by_id(user_id: str) -> Optional[User]:
    try:
        return await User.get_or_none(id=UUID(user_id))
    except Exception:
        return await User.get_or_none(id=user_id)


async def get_user_memberships(user_id: str) -> list[UserCondominium]:
    return await UserCondominium.filter(
        user_id=user_id,
        status="active",
    ).select_related("condominium", "role", "unit")


async def user_has_condominium(user_id: str, condominium_id: str) -> bool:
    return await UserCondominium.filter(
        user_id=user_id,
        condominium_id=condominium_id,
        status="active",
    ).exists()

