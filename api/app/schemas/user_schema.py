from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserMembershipInput(BaseModel):
    condominium_id: UUID
    role_code: str = Field(..., max_length=60)
    unit_id: Optional[UUID] = None
    status: str = Field(default="active", max_length=30)
    receives_notifications: bool = True


class UserMembershipOut(BaseModel):
    id: UUID
    condominium_id: UUID
    condominium_name: Optional[str] = None
    role_id: UUID
    role_code: str
    role_name: Optional[str] = None
    unit_id: Optional[UUID] = None
    unit_identifier: Optional[str] = None
    status: str
    receives_notifications: bool


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=40)
    company_id: Optional[UUID] = None
    global_role: Optional[str] = Field(default=None, max_length=60)
    status: str = Field(default="active", max_length=30)
    condominium_id: Optional[UUID] = None
    role_code: Optional[str] = Field(default=None, max_length=60)
    memberships: Optional[list[UserMembershipInput]] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=40)
    company_id: Optional[UUID] = None
    global_role: Optional[str] = Field(default=None, max_length=60)
    status: Optional[str] = Field(default=None, max_length=30)
    condominium_id: Optional[UUID] = None
    role_code: Optional[str] = Field(default=None, max_length=60)
    memberships: Optional[list[UserMembershipInput]] = None


class UserOut(BaseModel):
    id: UUID
    company_id: Optional[UUID] = None
    email: str
    full_name: str
    phone: Optional[str] = None
    status: str
    global_role: Optional[str] = None
    condominium_id: Optional[UUID] = None
    role_code: Optional[str] = None
    memberships: list[UserMembershipOut] = Field(default_factory=list)


class UserCreatedOut(UserOut):
    condominium_id: Optional[UUID] = None
    role_code: Optional[str] = None


class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int


class UserPage(BaseModel):
    items: list[UserOut]
    meta: PageMeta
