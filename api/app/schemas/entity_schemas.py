from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AuditOut(BaseModel):
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int


class CompanyCreate(BaseModel):
    name: str = Field(..., max_length=150)
    rut: Optional[str] = Field(default=None, max_length=30)
    legal_name: Optional[str] = Field(default=None, max_length=180)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=40)
    status: str = Field(default="active", max_length=30)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=150)
    rut: Optional[str] = Field(default=None, max_length=30)
    legal_name: Optional[str] = Field(default=None, max_length=180)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=40)
    status: Optional[str] = Field(default=None, max_length=30)
    metadata: Optional[dict[str, Any]] = None


class CompanyOut(AuditOut):
    id: UUID
    name: str
    rut: Optional[str] = None
    legal_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompanyPage(BaseModel):
    items: list[CompanyOut]
    meta: PageMeta


class BankCreate(BaseModel):
    name: str = Field(..., max_length=120)
    code: Optional[str] = Field(default=None, max_length=40)
    country: str = Field(default="Chile", max_length=80)
    website: Optional[str] = Field(default=None, max_length=255)
    status: str = Field(default="active", max_length=30)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BankUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    code: Optional[str] = Field(default=None, max_length=40)
    country: Optional[str] = Field(default=None, max_length=80)
    website: Optional[str] = Field(default=None, max_length=255)
    status: Optional[str] = Field(default=None, max_length=30)
    metadata: Optional[dict[str, Any]] = None


class BankOut(AuditOut):
    id: UUID
    name: str
    code: Optional[str] = None
    country: str
    website: Optional[str] = None
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class BankPage(BaseModel):
    items: list[BankOut]
    meta: PageMeta


class CondominiumCreate(BaseModel):
    company_id: UUID
    name: str = Field(..., max_length=150)
    address: Optional[str] = Field(default=None, max_length=255)
    commune: Optional[str] = Field(default=None, max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    towers_count: int = 0
    units_count: int = 0
    status: str = Field(default="active", max_length=30)
    communication_rules: dict[str, Any] = Field(default_factory=dict)
    incident_categories: list[Any] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CondominiumUpdate(BaseModel):
    company_id: Optional[UUID] = None
    name: Optional[str] = Field(default=None, max_length=150)
    address: Optional[str] = Field(default=None, max_length=255)
    commune: Optional[str] = Field(default=None, max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    towers_count: Optional[int] = None
    units_count: Optional[int] = None
    status: Optional[str] = Field(default=None, max_length=30)
    communication_rules: Optional[dict[str, Any]] = None
    incident_categories: Optional[list[Any]] = None
    metadata: Optional[dict[str, Any]] = None


class CondominiumOut(AuditOut):
    id: UUID
    company_id: UUID
    name: str
    address: Optional[str] = None
    commune: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    towers_count: int
    units_count: int
    status: str
    communication_rules: dict[str, Any] = Field(default_factory=dict)
    incident_categories: list[Any] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CondominiumPage(BaseModel):
    items: list[CondominiumOut]
    meta: PageMeta


class CondominiumOperationalStaffCreate(BaseModel):
    company_id: UUID
    condominium_id: Optional[UUID] = None
    user_id: UUID
    portal_profile: str = Field(..., max_length=60)
    responsibility: Optional[str] = Field(default=None, max_length=120)
    is_primary: bool = False
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = Field(default="active", max_length=30)
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CondominiumOperationalStaffUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    portal_profile: Optional[str] = Field(default=None, max_length=60)
    responsibility: Optional[str] = Field(default=None, max_length=120)
    is_primary: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(default=None, max_length=30)
    notes: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class CondominiumOperationalStaffOut(AuditOut):
    id: UUID
    company_id: UUID
    condominium_id: Optional[UUID] = None
    user_id: UUID
    portal_profile: str
    responsibility: Optional[str] = None
    is_primary: bool
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CondominiumOperationalStaffPage(BaseModel):
    items: list[CondominiumOperationalStaffOut]
    meta: PageMeta


class BuildingCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: UUID
    name: str = Field(..., max_length=100)
    floors_count: int = 0
    units_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class BuildingUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    name: Optional[str] = Field(default=None, max_length=100)
    floors_count: Optional[int] = None
    units_count: Optional[int] = None
    metadata: Optional[dict[str, Any]] = None


class BuildingOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: UUID
    name: str
    floors_count: int
    units_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class BuildingPage(BaseModel):
    items: list[BuildingOut]
    meta: PageMeta


class CommonAreaCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: UUID
    name: str = Field(..., max_length=120)
    area_type: str = Field(default="other", max_length=40)
    location: Optional[str] = Field(default=None, max_length=160)
    capacity: Optional[int] = None
    requires_reservation: bool = False
    status: str = Field(default="active", max_length=30)
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommonAreaUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    name: Optional[str] = Field(default=None, max_length=120)
    area_type: Optional[str] = Field(default=None, max_length=40)
    location: Optional[str] = Field(default=None, max_length=160)
    capacity: Optional[int] = None
    requires_reservation: Optional[bool] = None
    status: Optional[str] = Field(default=None, max_length=30)
    notes: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class CommonAreaOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: UUID
    name: str
    area_type: str
    location: Optional[str] = None
    capacity: Optional[int] = None
    requires_reservation: bool
    status: str
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommonAreaPage(BaseModel):
    items: list[CommonAreaOut]
    meta: PageMeta


class CondominiumAssetCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: UUID
    name: str = Field(..., max_length=140)
    asset_type: str = Field(default="other", max_length=50)
    location: Optional[str] = Field(default=None, max_length=160)
    brand: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=100)
    serial_number: Optional[str] = Field(default=None, max_length=100)
    provider: Optional[str] = Field(default=None, max_length=160)
    installation_date: Optional[date] = None
    requires_maintenance: bool = True
    maintenance_frequency: Optional[str] = Field(default=None, max_length=80)
    status: str = Field(default="active", max_length=30)
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CondominiumAssetUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    name: Optional[str] = Field(default=None, max_length=140)
    asset_type: Optional[str] = Field(default=None, max_length=50)
    location: Optional[str] = Field(default=None, max_length=160)
    brand: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=100)
    serial_number: Optional[str] = Field(default=None, max_length=100)
    provider: Optional[str] = Field(default=None, max_length=160)
    installation_date: Optional[date] = None
    requires_maintenance: Optional[bool] = None
    maintenance_frequency: Optional[str] = Field(default=None, max_length=80)
    status: Optional[str] = Field(default=None, max_length=30)
    notes: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class CondominiumAssetOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: UUID
    name: str
    asset_type: str
    location: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    provider: Optional[str] = None
    installation_date: Optional[date] = None
    requires_maintenance: bool
    maintenance_frequency: Optional[str] = None
    status: str
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CondominiumAssetPage(BaseModel):
    items: list[CondominiumAssetOut]
    meta: PageMeta


class UnitCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: UUID
    building_id: Optional[UUID] = None
    identifier: str
    floor: Optional[str] = Field(default=None, max_length=20)
    unit_type: str = Field(default="apartment", max_length=30)
    external_code: Optional[str] = None
    allocation_number: Optional[int] = None
    allocation_identifier: Optional[str] = None
    proration_total: Optional[Decimal] = None
    proration: Optional[Decimal] = None
    assignment_date: Optional[date] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UnitUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    building_id: Optional[UUID] = None
    identifier: Optional[str] = None
    floor: Optional[str] = Field(default=None, max_length=20)
    unit_type: Optional[str] = Field(default=None, max_length=30)
    external_code: Optional[str] = None
    allocation_number: Optional[int] = None
    allocation_identifier: Optional[str] = None
    proration_total: Optional[Decimal] = None
    proration: Optional[Decimal] = None
    assignment_date: Optional[date] = None
    metadata: Optional[dict[str, Any]] = None


class UnitOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: UUID
    building_id: Optional[UUID] = None
    identifier: str
    floor: Optional[str] = None
    unit_type: str
    external_code: Optional[str] = None
    allocation_number: Optional[int] = None
    allocation_identifier: Optional[str] = None
    proration_total: Optional[Decimal] = None
    proration: Optional[Decimal] = None
    assignment_date: Optional[date] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UnitPage(BaseModel):
    items: list[UnitOut]
    meta: PageMeta


class UnitAnnexCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: UUID
    unit_id: UUID
    annex_type: str = Field(default="parking", max_length=40)
    identifier: str = Field(..., max_length=80)
    description: Optional[str] = Field(default=None, max_length=255)
    status: str = Field(default="active", max_length=30)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UnitAnnexUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    annex_type: Optional[str] = Field(default=None, max_length=40)
    identifier: Optional[str] = Field(default=None, max_length=80)
    description: Optional[str] = Field(default=None, max_length=255)
    status: Optional[str] = Field(default=None, max_length=30)
    metadata: Optional[dict[str, Any]] = None


class UnitAnnexOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: UUID
    unit_id: UUID
    annex_type: str
    identifier: str
    description: Optional[str] = None
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class UnitAnnexPage(BaseModel):
    items: list[UnitAnnexOut]
    meta: PageMeta


class UnitPetCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: UUID
    unit_id: UUID
    name: str = Field(..., max_length=120)
    species: str = Field(default="dog", max_length=40)
    breed: Optional[str] = Field(default=None, max_length=120)
    color: Optional[str] = Field(default=None, max_length=80)
    chip_number: Optional[str] = Field(default=None, max_length=80)
    status: str = Field(default="active", max_length=30)
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UnitPetUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    name: Optional[str] = Field(default=None, max_length=120)
    species: Optional[str] = Field(default=None, max_length=40)
    breed: Optional[str] = Field(default=None, max_length=120)
    color: Optional[str] = Field(default=None, max_length=80)
    chip_number: Optional[str] = Field(default=None, max_length=80)
    status: Optional[str] = Field(default=None, max_length=30)
    notes: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class UnitPetOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: UUID
    unit_id: UUID
    name: str
    species: str
    breed: Optional[str] = None
    color: Optional[str] = None
    chip_number: Optional[str] = None
    status: str
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UnitPetPage(BaseModel):
    items: list[UnitPetOut]
    meta: PageMeta


class UnitContactCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: UUID
    unit_id: UUID
    user_id: Optional[UUID] = None
    relationship_type: str = Field(default="residente", max_length=40)
    full_name: str = Field(..., max_length=150)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=40)
    document_type: Optional[str] = Field(default=None, max_length=30)
    document_number: Optional[str] = Field(default=None, max_length=40)
    address: Optional[str] = Field(default=None, max_length=255)
    is_primary_contact: bool = False
    receives_notifications: bool = True
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = Field(default="active", max_length=30)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UnitContactUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    relationship_type: Optional[str] = Field(default=None, max_length=40)
    full_name: Optional[str] = Field(default=None, max_length=150)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=40)
    document_type: Optional[str] = Field(default=None, max_length=30)
    document_number: Optional[str] = Field(default=None, max_length=40)
    address: Optional[str] = Field(default=None, max_length=255)
    is_primary_contact: Optional[bool] = None
    receives_notifications: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(default=None, max_length=30)
    metadata: Optional[dict[str, Any]] = None


class UnitContactOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: UUID
    unit_id: UUID
    user_id: Optional[UUID] = None
    relationship_type: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    address: Optional[str] = None
    is_primary_contact: bool
    receives_notifications: bool
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class UnitContactPage(BaseModel):
    items: list[UnitContactOut]
    meta: PageMeta


class CommitteeMemberCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: UUID
    user_id: Optional[UUID] = None
    unit_contact_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    position: str = Field(..., max_length=80)
    full_name: str = Field(..., max_length=150)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=40)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = Field(default="active", max_length=30)
    receives_notifications: bool = True
    display_order: int = 0
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommitteeMemberUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    unit_contact_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    position: Optional[str] = Field(default=None, max_length=80)
    full_name: Optional[str] = Field(default=None, max_length=150)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=40)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(default=None, max_length=30)
    receives_notifications: Optional[bool] = None
    display_order: Optional[int] = None
    notes: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class CommitteeMemberOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: UUID
    user_id: Optional[UUID] = None
    unit_contact_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    position: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    receives_notifications: bool
    display_order: int
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommitteeMemberPage(BaseModel):
    items: list[CommitteeMemberOut]
    meta: PageMeta


class RoleCreate(BaseModel):
    code: str = Field(..., max_length=60)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    permissions: dict[str, Any] = Field(default_factory=dict)
    is_system: bool = True


class RoleUpdate(BaseModel):
    code: Optional[str] = Field(default=None, max_length=60)
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    permissions: Optional[dict[str, Any]] = None
    is_system: Optional[bool] = None


class RoleOut(AuditOut):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    permissions: dict[str, Any] = Field(default_factory=dict)
    is_system: bool


class RolePage(BaseModel):
    items: list[RoleOut]
    meta: PageMeta


class UserCondominiumCreate(BaseModel):
    company_id: Optional[UUID] = None
    user_id: UUID
    condominium_id: Optional[UUID] = None
    role_id: UUID
    unit_id: Optional[UUID] = None
    status: str = Field(default="active", max_length=30)
    receives_notifications: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserCondominiumUpdate(BaseModel):
    company_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    status: Optional[str] = Field(default=None, max_length=30)
    receives_notifications: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None


class UserCondominiumOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    user_id: UUID
    condominium_id: Optional[UUID] = None
    role_id: UUID
    unit_id: Optional[UUID] = None
    status: str
    receives_notifications: bool
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserCondominiumPage(BaseModel):
    items: list[UserCondominiumOut]
    meta: PageMeta


class IncidentCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: UUID
    reported_by_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    category: str = Field(..., max_length=80)
    priority: str = Field(default="medium", max_length=30)
    status: str = Field(default="new", max_length=40)
    original_description: str
    ai_description: Optional[str] = None
    confidence_score: Optional[float] = None
    due_date: Optional[date] = None
    closed_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IncidentUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    reported_by_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    category: Optional[str] = Field(default=None, max_length=80)
    priority: Optional[str] = Field(default=None, max_length=30)
    status: Optional[str] = Field(default=None, max_length=40)
    original_description: Optional[str] = None
    ai_description: Optional[str] = None
    confidence_score: Optional[float] = None
    due_date: Optional[date] = None
    closed_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class IncidentOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: UUID
    reported_by_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    category: str
    priority: str
    status: str
    original_description: str
    ai_description: Optional[str] = None
    confidence_score: Optional[float] = None
    due_date: Optional[date] = None
    closed_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IncidentPage(BaseModel):
    items: list[IncidentOut]
    meta: PageMeta


class IncidentEventCreate(BaseModel):
    company_id: Optional[UUID] = None
    incident_id: UUID
    user_id: Optional[UUID] = None
    event_type: str = Field(..., max_length=60)
    previous_status: Optional[str] = Field(default=None, max_length=40)
    new_status: Optional[str] = Field(default=None, max_length=40)
    comment: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IncidentEventUpdate(BaseModel):
    company_id: Optional[UUID] = None
    incident_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    event_type: Optional[str] = Field(default=None, max_length=60)
    previous_status: Optional[str] = Field(default=None, max_length=40)
    new_status: Optional[str] = Field(default=None, max_length=40)
    comment: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class IncidentEventOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    incident_id: UUID
    user_id: Optional[UUID] = None
    event_type: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    comment: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IncidentEventPage(BaseModel):
    items: list[IncidentEventOut]
    meta: PageMeta


class TaskCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: UUID
    incident_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    title: str = Field(..., max_length=180)
    description: Optional[str] = None
    status: str = Field(default="pending", max_length=40)
    priority: str = Field(default="medium", max_length=30)
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    incident_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    title: Optional[str] = Field(default=None, max_length=180)
    description: Optional[str] = None
    status: Optional[str] = Field(default=None, max_length=40)
    priority: Optional[str] = Field(default=None, max_length=30)
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class TaskOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: UUID
    incident_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskPage(BaseModel):
    items: list[TaskOut]
    meta: PageMeta


class SupportTicketCreate(BaseModel):
    company_id: UUID
    condominium_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    requester_name: Optional[str] = Field(default=None, max_length=150)
    requester_email: Optional[str] = Field(default=None, max_length=255)
    subject: str = Field(..., max_length=180)
    description: Optional[str] = None
    category: str = Field(default="general", max_length=80)
    priority: str = Field(default="medium", max_length=30)
    status: str = Field(default="open", max_length=40)
    due_date: Optional[date] = None
    resolved_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SupportTicketUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    requester_name: Optional[str] = Field(default=None, max_length=150)
    requester_email: Optional[str] = Field(default=None, max_length=255)
    subject: Optional[str] = Field(default=None, max_length=180)
    description: Optional[str] = None
    category: Optional[str] = Field(default=None, max_length=80)
    priority: Optional[str] = Field(default=None, max_length=30)
    status: Optional[str] = Field(default=None, max_length=40)
    due_date: Optional[date] = None
    resolved_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class SupportTicketOut(AuditOut):
    id: UUID
    company_id: UUID
    condominium_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None
    subject: str
    description: Optional[str] = None
    category: str
    priority: str
    status: str
    due_date: Optional[date] = None
    resolved_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SupportTicketPage(BaseModel):
    items: list[SupportTicketOut]
    meta: PageMeta


class TaskChecklistCreate(BaseModel):
    company_id: Optional[UUID] = None
    task_id: UUID
    label: str = Field(..., max_length=180)
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    completed_by_id: Optional[UUID] = None
    position: int = 0


class TaskChecklistUpdate(BaseModel):
    company_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    label: Optional[str] = Field(default=None, max_length=180)
    is_completed: Optional[bool] = None
    completed_at: Optional[datetime] = None
    completed_by_id: Optional[UUID] = None
    position: Optional[int] = None


class TaskChecklistOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    task_id: UUID
    label: str
    is_completed: bool
    completed_at: Optional[datetime] = None
    completed_by_id: Optional[UUID] = None
    position: int


class TaskChecklistPage(BaseModel):
    items: list[TaskChecklistOut]
    meta: PageMeta


class InspectionTemplateCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    name: str = Field(..., max_length=150)
    description: Optional[str] = None
    template_type: str = Field(default="inspection", max_length=80)
    inspection_type: str = Field(..., max_length=80)
    version: int = 1
    status: str = Field(default="active", max_length=30)
    source_file_name: Optional[str] = Field(default=None, max_length=255)
    checklist_schema: list[Any] = Field(default_factory=list)
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class InspectionTemplateUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    name: Optional[str] = Field(default=None, max_length=150)
    description: Optional[str] = None
    template_type: Optional[str] = Field(default=None, max_length=80)
    inspection_type: Optional[str] = Field(default=None, max_length=80)
    version: Optional[int] = None
    status: Optional[str] = Field(default=None, max_length=30)
    source_file_name: Optional[str] = Field(default=None, max_length=255)
    checklist_schema: Optional[list[Any]] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None


class InspectionTemplateOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    template_type: str
    inspection_type: str
    version: int
    status: str
    source_file_name: Optional[str] = None
    checklist_schema: list[Any] = Field(default_factory=list)
    is_active: bool
    metadata: dict[str, Any] = Field(default_factory=dict)


class InspectionTemplatePage(BaseModel):
    items: list[InspectionTemplateOut]
    meta: PageMeta


class InspectionTemplateSectionCreate(BaseModel):
    company_id: Optional[UUID] = None
    template_id: UUID
    name: str = Field(..., max_length=150)
    description: Optional[str] = None
    display_order: int = 0
    status: str = Field(default="active", max_length=30)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InspectionTemplateSectionUpdate(BaseModel):
    company_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    name: Optional[str] = Field(default=None, max_length=150)
    description: Optional[str] = None
    display_order: Optional[int] = None
    status: Optional[str] = Field(default=None, max_length=30)
    metadata: Optional[dict[str, Any]] = None


class InspectionTemplateSectionOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    template_id: UUID
    name: str
    description: Optional[str] = None
    display_order: int
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class InspectionTemplateSectionPage(BaseModel):
    items: list[InspectionTemplateSectionOut]
    meta: PageMeta


class InspectionTemplateItemCreate(BaseModel):
    company_id: Optional[UUID] = None
    template_id: UUID
    section_id: Optional[UUID] = None
    asset_name: Optional[str] = Field(default=None, max_length=180)
    task_name: str = Field(..., max_length=255)
    instructions: Optional[str] = None
    event_type: str = Field(default="maintenance", max_length=40)
    periodicity: Optional[str] = Field(default=None, max_length=80)
    planned_months: list[Any] = Field(default_factory=list)
    requires_evidence: bool = False
    default_responsible_profile: Optional[str] = Field(default=None, max_length=60)
    default_duration_minutes: Optional[int] = None
    display_order: int = 0
    status: str = Field(default="active", max_length=30)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InspectionTemplateItemUpdate(BaseModel):
    company_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    asset_name: Optional[str] = Field(default=None, max_length=180)
    task_name: Optional[str] = Field(default=None, max_length=255)
    instructions: Optional[str] = None
    event_type: Optional[str] = Field(default=None, max_length=40)
    periodicity: Optional[str] = Field(default=None, max_length=80)
    planned_months: Optional[list[Any]] = None
    requires_evidence: Optional[bool] = None
    default_responsible_profile: Optional[str] = Field(default=None, max_length=60)
    default_duration_minutes: Optional[int] = None
    display_order: Optional[int] = None
    status: Optional[str] = Field(default=None, max_length=30)
    metadata: Optional[dict[str, Any]] = None


class InspectionTemplateItemOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    template_id: UUID
    section_id: Optional[UUID] = None
    asset_name: Optional[str] = None
    task_name: str
    instructions: Optional[str] = None
    event_type: str
    periodicity: Optional[str] = None
    planned_months: list[Any] = Field(default_factory=list)
    requires_evidence: bool
    default_responsible_profile: Optional[str] = None
    default_duration_minutes: Optional[int] = None
    display_order: int
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class InspectionTemplateItemPage(BaseModel):
    items: list[InspectionTemplateItemOut]
    meta: PageMeta


class CondominiumInspectionTemplateCreate(BaseModel):
    company_id: UUID
    condominium_id: UUID
    base_template_id: Optional[UUID] = None
    name: str = Field(..., max_length=150)
    template_type: str = Field(default="maintenance", max_length=80)
    version: int = 1
    status: str = Field(default="draft", max_length=30)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CondominiumInspectionTemplateUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    base_template_id: Optional[UUID] = None
    name: Optional[str] = Field(default=None, max_length=150)
    template_type: Optional[str] = Field(default=None, max_length=80)
    version: Optional[int] = None
    status: Optional[str] = Field(default=None, max_length=30)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    metadata: Optional[dict[str, Any]] = None


class CondominiumInspectionTemplateOut(AuditOut):
    id: UUID
    company_id: UUID
    condominium_id: UUID
    base_template_id: Optional[UUID] = None
    name: str
    template_type: str
    version: int
    status: str
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CondominiumInspectionTemplatePage(BaseModel):
    items: list[CondominiumInspectionTemplateOut]
    meta: PageMeta


class InspectionTemplateDuplicateToCondominiumRequest(BaseModel):
    condominium_id: UUID
    name: Optional[str] = Field(default=None, max_length=150)
    status: str = Field(default="draft", max_length=30)


class InspectionTemplateDuplicateToCondominiumOut(BaseModel):
    template: CondominiumInspectionTemplateOut
    items_created: int


class CondominiumInspectionItemCreate(BaseModel):
    company_id: UUID
    condominium_id: UUID
    condominium_template_id: UUID
    base_item_id: Optional[UUID] = None
    section_name: Optional[str] = Field(default=None, max_length=150)
    asset_name: Optional[str] = Field(default=None, max_length=180)
    task_name: str = Field(..., max_length=255)
    instructions: Optional[str] = None
    event_type: str = Field(default="maintenance", max_length=40)
    periodicity: Optional[str] = Field(default=None, max_length=80)
    planned_months: list[Any] = Field(default_factory=list)
    responsible_user_id: Optional[UUID] = None
    responsible_profile: Optional[str] = Field(default=None, max_length=60)
    provider_id: Optional[UUID] = None
    estimated_duration_minutes: Optional[int] = None
    priority: str = Field(default="medium", max_length=30)
    status: str = Field(default="active", max_length=30)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CondominiumInspectionItemUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    condominium_template_id: Optional[UUID] = None
    base_item_id: Optional[UUID] = None
    section_name: Optional[str] = Field(default=None, max_length=150)
    asset_name: Optional[str] = Field(default=None, max_length=180)
    task_name: Optional[str] = Field(default=None, max_length=255)
    instructions: Optional[str] = None
    event_type: Optional[str] = Field(default=None, max_length=40)
    periodicity: Optional[str] = Field(default=None, max_length=80)
    planned_months: Optional[list[Any]] = None
    responsible_user_id: Optional[UUID] = None
    responsible_profile: Optional[str] = Field(default=None, max_length=60)
    provider_id: Optional[UUID] = None
    estimated_duration_minutes: Optional[int] = None
    priority: Optional[str] = Field(default=None, max_length=30)
    status: Optional[str] = Field(default=None, max_length=30)
    metadata: Optional[dict[str, Any]] = None


class CondominiumInspectionItemOut(AuditOut):
    id: UUID
    company_id: UUID
    condominium_id: UUID
    condominium_template_id: UUID
    base_item_id: Optional[UUID] = None
    section_name: Optional[str] = None
    asset_name: Optional[str] = None
    task_name: str
    instructions: Optional[str] = None
    event_type: str
    periodicity: Optional[str] = None
    planned_months: list[Any] = Field(default_factory=list)
    responsible_user_id: Optional[UUID] = None
    responsible_profile: Optional[str] = None
    provider_id: Optional[UUID] = None
    estimated_duration_minutes: Optional[int] = None
    priority: str
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CondominiumInspectionItemPage(BaseModel):
    items: list[CondominiumInspectionItemOut]
    meta: PageMeta


class OperationalWorkCalendarCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    base_calendar_id: Optional[UUID] = None
    name: str = Field(..., max_length=150)
    calendar_type: str = Field(default="condominium", max_length=40)
    working_days: list[Any] = Field(default_factory=list)
    default_start_time: Optional[time] = None
    default_end_time: Optional[time] = None
    timezone: str = Field(default="America/Santiago", max_length=80)
    status: str = Field(default="active", max_length=30)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OperationalWorkCalendarUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    base_calendar_id: Optional[UUID] = None
    name: Optional[str] = Field(default=None, max_length=150)
    calendar_type: Optional[str] = Field(default=None, max_length=40)
    working_days: Optional[list[Any]] = None
    default_start_time: Optional[time] = None
    default_end_time: Optional[time] = None
    timezone: Optional[str] = Field(default=None, max_length=80)
    status: Optional[str] = Field(default=None, max_length=30)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    metadata: Optional[dict[str, Any]] = None


class OperationalWorkCalendarOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    base_calendar_id: Optional[UUID] = None
    name: str
    calendar_type: str
    working_days: list[Any] = Field(default_factory=list)
    default_start_time: Optional[time] = None
    default_end_time: Optional[time] = None
    timezone: str
    status: str
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OperationalWorkCalendarPage(BaseModel):
    items: list[OperationalWorkCalendarOut]
    meta: PageMeta


class OperationalCalendarExceptionCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    calendar_id: UUID
    exception_date: date
    exception_type: str = Field(..., max_length=40)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = Field(default=None, max_length=255)
    source: str = Field(default="condominium_override", max_length=40)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OperationalCalendarExceptionUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    calendar_id: Optional[UUID] = None
    exception_date: Optional[date] = None
    exception_type: Optional[str] = Field(default=None, max_length=40)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = Field(default=None, max_length=255)
    source: Optional[str] = Field(default=None, max_length=40)
    metadata: Optional[dict[str, Any]] = None


class OperationalCalendarExceptionOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    calendar_id: UUID
    exception_date: date
    exception_type: str
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = None
    source: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class OperationalCalendarExceptionPage(BaseModel):
    items: list[OperationalCalendarExceptionOut]
    meta: PageMeta


class PlannedOperationalEventCreate(BaseModel):
    company_id: UUID
    condominium_id: UUID
    condominium_template_item_id: Optional[UUID] = None
    calendar_id: Optional[UUID] = None
    assigned_user_id: Optional[UUID] = None
    title: str = Field(..., max_length=180)
    description: Optional[str] = None
    planned_date: date
    planned_start_time: Optional[time] = None
    planned_end_time: Optional[time] = None
    estimated_duration_minutes: Optional[int] = None
    assigned_profile: Optional[str] = Field(default=None, max_length=60)
    priority: str = Field(default="medium", max_length=30)
    status: str = Field(default="pending", max_length=40)
    event_type: str = Field(default="task", max_length=40)
    source_type: Optional[str] = Field(default=None, max_length=60)
    source_id: Optional[UUID] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlannedOperationalEventUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    condominium_template_item_id: Optional[UUID] = None
    calendar_id: Optional[UUID] = None
    assigned_user_id: Optional[UUID] = None
    title: Optional[str] = Field(default=None, max_length=180)
    description: Optional[str] = None
    planned_date: Optional[date] = None
    planned_start_time: Optional[time] = None
    planned_end_time: Optional[time] = None
    estimated_duration_minutes: Optional[int] = None
    assigned_profile: Optional[str] = Field(default=None, max_length=60)
    priority: Optional[str] = Field(default=None, max_length=30)
    status: Optional[str] = Field(default=None, max_length=40)
    event_type: Optional[str] = Field(default=None, max_length=40)
    source_type: Optional[str] = Field(default=None, max_length=60)
    source_id: Optional[UUID] = None
    metadata: Optional[dict[str, Any]] = None


class PlannedOperationalEventOut(AuditOut):
    id: UUID
    company_id: UUID
    condominium_id: UUID
    condominium_template_item_id: Optional[UUID] = None
    calendar_id: Optional[UUID] = None
    assigned_user_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    planned_date: date
    planned_start_time: Optional[time] = None
    planned_end_time: Optional[time] = None
    estimated_duration_minutes: Optional[int] = None
    assigned_profile: Optional[str] = None
    priority: str
    status: str
    event_type: str
    source_type: Optional[str] = None
    source_id: Optional[UUID] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlannedOperationalEventPage(BaseModel):
    items: list[PlannedOperationalEventOut]
    meta: PageMeta


class OperationalEventExecutionCreate(BaseModel):
    company_id: Optional[UUID] = None
    event_id: UUID
    executed_by_user_id: Optional[UUID] = None
    executed_at: Optional[datetime] = None
    result: str = Field(default="pending", max_length=60)
    comments: Optional[str] = None
    requires_follow_up: bool = False
    related_incident_id: Optional[UUID] = None
    related_ticket_id: Optional[UUID] = None
    validation_status: str = Field(default="not_validated", max_length=40)
    validated_by_user_id: Optional[UUID] = None
    validated_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OperationalEventExecutionUpdate(BaseModel):
    company_id: Optional[UUID] = None
    event_id: Optional[UUID] = None
    executed_by_user_id: Optional[UUID] = None
    executed_at: Optional[datetime] = None
    result: Optional[str] = Field(default=None, max_length=60)
    comments: Optional[str] = None
    requires_follow_up: Optional[bool] = None
    related_incident_id: Optional[UUID] = None
    related_ticket_id: Optional[UUID] = None
    validation_status: Optional[str] = Field(default=None, max_length=40)
    validated_by_user_id: Optional[UUID] = None
    validated_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class OperationalEventExecutionOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    event_id: UUID
    executed_by_user_id: Optional[UUID] = None
    executed_at: Optional[datetime] = None
    result: str
    comments: Optional[str] = None
    requires_follow_up: bool
    related_incident_id: Optional[UUID] = None
    related_ticket_id: Optional[UUID] = None
    validation_status: str
    validated_by_user_id: Optional[UUID] = None
    validated_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OperationalEventExecutionPage(BaseModel):
    items: list[OperationalEventExecutionOut]
    meta: PageMeta


class OperationalEventEvidenceCreate(BaseModel):
    company_id: Optional[UUID] = None
    event_id: UUID
    execution_id: Optional[UUID] = None
    attachment_id: Optional[UUID] = None
    evidence_type: str = Field(default="attachment", max_length=40)
    description: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OperationalEventEvidenceUpdate(BaseModel):
    company_id: Optional[UUID] = None
    event_id: Optional[UUID] = None
    execution_id: Optional[UUID] = None
    attachment_id: Optional[UUID] = None
    evidence_type: Optional[str] = Field(default=None, max_length=40)
    description: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class OperationalEventEvidenceOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    event_id: UUID
    execution_id: Optional[UUID] = None
    attachment_id: Optional[UUID] = None
    evidence_type: str
    description: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OperationalEventEvidencePage(BaseModel):
    items: list[OperationalEventEvidenceOut]
    meta: PageMeta


class OperationalRescheduleLogCreate(BaseModel):
    company_id: Optional[UUID] = None
    event_id: UUID
    previous_date: Optional[date] = None
    new_date: Optional[date] = None
    previous_assigned_user_id: Optional[UUID] = None
    new_assigned_user_id: Optional[UUID] = None
    reason: Optional[str] = Field(default=None, max_length=255)
    requested_by_user_id: Optional[UUID] = None
    approved_by_user_id: Optional[UUID] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OperationalRescheduleLogUpdate(BaseModel):
    company_id: Optional[UUID] = None
    event_id: Optional[UUID] = None
    previous_date: Optional[date] = None
    new_date: Optional[date] = None
    previous_assigned_user_id: Optional[UUID] = None
    new_assigned_user_id: Optional[UUID] = None
    reason: Optional[str] = Field(default=None, max_length=255)
    requested_by_user_id: Optional[UUID] = None
    approved_by_user_id: Optional[UUID] = None
    metadata: Optional[dict[str, Any]] = None


class OperationalRescheduleLogOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    event_id: UUID
    previous_date: Optional[date] = None
    new_date: Optional[date] = None
    previous_assigned_user_id: Optional[UUID] = None
    new_assigned_user_id: Optional[UUID] = None
    reason: Optional[str] = None
    requested_by_user_id: Optional[UUID] = None
    approved_by_user_id: Optional[UUID] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OperationalRescheduleLogPage(BaseModel):
    items: list[OperationalRescheduleLogOut]
    meta: PageMeta


class InspectionCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: UUID
    template_id: Optional[UUID] = None
    supervisor_id: Optional[UUID] = None
    inspection_type: str = Field(..., max_length=80)
    status: str = Field(default="draft", max_length=40)
    observations: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    signed_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InspectionUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    supervisor_id: Optional[UUID] = None
    inspection_type: Optional[str] = Field(default=None, max_length=80)
    status: Optional[str] = Field(default=None, max_length=40)
    observations: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    signed_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class InspectionOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: UUID
    template_id: Optional[UUID] = None
    supervisor_id: Optional[UUID] = None
    inspection_type: str
    status: str
    observations: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    signed_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InspectionPage(BaseModel):
    items: list[InspectionOut]
    meta: PageMeta


class InspectionAnswerCreate(BaseModel):
    company_id: Optional[UUID] = None
    inspection_id: UUID
    question_key: str = Field(..., max_length=100)
    question_label: str = Field(..., max_length=255)
    answer_type: str = Field(default="text", max_length=40)
    value: dict[str, Any] = Field(default_factory=dict)
    requires_action: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class InspectionAnswerUpdate(BaseModel):
    company_id: Optional[UUID] = None
    inspection_id: Optional[UUID] = None
    question_key: Optional[str] = Field(default=None, max_length=100)
    question_label: Optional[str] = Field(default=None, max_length=255)
    answer_type: Optional[str] = Field(default=None, max_length=40)
    value: Optional[dict[str, Any]] = None
    requires_action: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None


class InspectionAnswerOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    inspection_id: UUID
    question_key: str
    question_label: str
    answer_type: str
    value: dict[str, Any] = Field(default_factory=dict)
    requires_action: bool
    metadata: dict[str, Any] = Field(default_factory=dict)


class InspectionAnswerPage(BaseModel):
    items: list[InspectionAnswerOut]
    meta: PageMeta


class ReportCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: UUID
    incident_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    inspection_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    approved_by_id: Optional[UUID] = None
    report_type: str = Field(..., max_length=60)
    title: str = Field(..., max_length=180)
    status: str = Field(default="draft", max_length=40)
    content: dict[str, Any] = Field(default_factory=dict)
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReportUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    incident_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    inspection_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    approved_by_id: Optional[UUID] = None
    report_type: Optional[str] = Field(default=None, max_length=60)
    title: Optional[str] = Field(default=None, max_length=180)
    status: Optional[str] = Field(default=None, max_length=40)
    content: Optional[dict[str, Any]] = None
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class ReportOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: UUID
    incident_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    inspection_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    approved_by_id: Optional[UUID] = None
    report_type: str
    title: str
    status: str
    content: dict[str, Any] = Field(default_factory=dict)
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReportPage(BaseModel):
    items: list[ReportOut]
    meta: PageMeta


class ReportVersionCreate(BaseModel):
    company_id: Optional[UUID] = None
    report_id: UUID
    version_number: int
    source: str = Field(default="human", max_length=40)
    content: dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class ReportVersionUpdate(BaseModel):
    company_id: Optional[UUID] = None
    report_id: Optional[UUID] = None
    version_number: Optional[int] = None
    source: Optional[str] = Field(default=None, max_length=40)
    content: Optional[dict[str, Any]] = None
    notes: Optional[str] = None


class ReportVersionOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    report_id: UUID
    version_number: int
    source: str
    content: dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class ReportVersionPage(BaseModel):
    items: list[ReportVersionOut]
    meta: PageMeta


class CommunicationCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: UUID
    report_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    approved_by_id: Optional[UUID] = None
    communication_type: str = Field(..., max_length=60)
    title: str = Field(..., max_length=180)
    body: str
    status: str = Field(default="draft", max_length=40)
    audience: str = Field(default="committee", max_length=40)
    channels: list[Any] = Field(default_factory=list)
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommunicationUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    report_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    approved_by_id: Optional[UUID] = None
    communication_type: Optional[str] = Field(default=None, max_length=60)
    title: Optional[str] = Field(default=None, max_length=180)
    body: Optional[str] = None
    status: Optional[str] = Field(default=None, max_length=40)
    audience: Optional[str] = Field(default=None, max_length=40)
    channels: Optional[list[Any]] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class CommunicationOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: UUID
    report_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    approved_by_id: Optional[UUID] = None
    communication_type: str
    title: str
    body: str
    status: str
    audience: str
    channels: list[Any] = Field(default_factory=list)
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommunicationPage(BaseModel):
    items: list[CommunicationOut]
    meta: PageMeta


class CommunicationRecipientCreate(BaseModel):
    company_id: Optional[UUID] = None
    communication_id: UUID
    user_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    recipient_type: str = Field(default="user", max_length=40)
    channel: str = Field(..., max_length=40)
    destination: Optional[str] = Field(default=None, max_length=255)
    delivery_status: str = Field(default="pending", max_length=40)
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommunicationRecipientUpdate(BaseModel):
    company_id: Optional[UUID] = None
    communication_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    recipient_type: Optional[str] = Field(default=None, max_length=40)
    channel: Optional[str] = Field(default=None, max_length=40)
    destination: Optional[str] = Field(default=None, max_length=255)
    delivery_status: Optional[str] = Field(default=None, max_length=40)
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class CommunicationRecipientOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    communication_id: UUID
    user_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    recipient_type: str
    channel: str
    destination: Optional[str] = None
    delivery_status: str
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommunicationRecipientPage(BaseModel):
    items: list[CommunicationRecipientOut]
    meta: PageMeta


class AttachmentCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    uploaded_by_id: Optional[UUID] = None
    incident_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    inspection_id: Optional[UUID] = None
    report_id: Optional[UUID] = None
    communication_id: Optional[UUID] = None
    file_name: str = Field(..., max_length=255)
    file_path: str = Field(..., max_length=500)
    file_type: str = Field(..., max_length=80)
    mime_type: Optional[str] = Field(default=None, max_length=120)
    size_bytes: Optional[int] = None
    checksum: Optional[str] = Field(default=None, max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AttachmentUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    uploaded_by_id: Optional[UUID] = None
    incident_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    inspection_id: Optional[UUID] = None
    report_id: Optional[UUID] = None
    communication_id: Optional[UUID] = None
    file_name: Optional[str] = Field(default=None, max_length=255)
    file_path: Optional[str] = Field(default=None, max_length=500)
    file_type: Optional[str] = Field(default=None, max_length=80)
    mime_type: Optional[str] = Field(default=None, max_length=120)
    size_bytes: Optional[int] = None
    checksum: Optional[str] = Field(default=None, max_length=128)
    metadata: Optional[dict[str, Any]] = None


class AttachmentOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    uploaded_by_id: Optional[UUID] = None
    incident_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    inspection_id: Optional[UUID] = None
    report_id: Optional[UUID] = None
    communication_id: Optional[UUID] = None
    file_name: str
    file_path: str
    file_type: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AttachmentPage(BaseModel):
    items: list[AttachmentOut]
    meta: PageMeta


class AuditLogCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    action: str = Field(..., max_length=100)
    entity_type: str = Field(..., max_length=80)
    entity_id: Optional[UUID] = None
    previous_state: Optional[dict[str, Any]] = None
    new_state: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = Field(default=None, max_length=80)
    user_agent: Optional[str] = Field(default=None, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditLogUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    action: Optional[str] = Field(default=None, max_length=100)
    entity_type: Optional[str] = Field(default=None, max_length=80)
    entity_id: Optional[UUID] = None
    previous_state: Optional[dict[str, Any]] = None
    new_state: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = Field(default=None, max_length=80)
    user_agent: Optional[str] = Field(default=None, max_length=255)
    metadata: Optional[dict[str, Any]] = None


class AuditLogOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    action: str
    entity_type: str
    entity_id: Optional[UUID] = None
    previous_state: Optional[dict[str, Any]] = None
    new_state: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditLogPage(BaseModel):
    items: list[AuditLogOut]
    meta: PageMeta


class AIRequestCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    requested_by_id: Optional[UUID] = None
    provider: str = Field(..., max_length=60)
    model: str = Field(..., max_length=100)
    purpose: str = Field(..., max_length=80)
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: Optional[dict[str, Any]] = None
    status: str = Field(default="pending", max_length=40)
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cost_estimate: Optional[Decimal] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIRequestUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    requested_by_id: Optional[UUID] = None
    provider: Optional[str] = Field(default=None, max_length=60)
    model: Optional[str] = Field(default=None, max_length=100)
    purpose: Optional[str] = Field(default=None, max_length=80)
    input_payload: Optional[dict[str, Any]] = None
    output_payload: Optional[dict[str, Any]] = None
    status: Optional[str] = Field(default=None, max_length=40)
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cost_estimate: Optional[Decimal] = None
    metadata: Optional[dict[str, Any]] = None


class AIRequestOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    requested_by_id: Optional[UUID] = None
    provider: str
    model: str
    purpose: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: Optional[dict[str, Any]] = None
    status: str
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cost_estimate: Optional[Decimal] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIRequestPage(BaseModel):
    items: list[AIRequestOut]
    meta: PageMeta


class NotificationLogCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    communication_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    channel: str = Field(..., max_length=40)
    destination: Optional[str] = Field(default=None, max_length=255)
    status: str = Field(default="pending", max_length=40)
    provider_message_id: Optional[str] = Field(default=None, max_length=120)
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationLogUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    communication_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    channel: Optional[str] = Field(default=None, max_length=40)
    destination: Optional[str] = Field(default=None, max_length=255)
    status: Optional[str] = Field(default=None, max_length=40)
    provider_message_id: Optional[str] = Field(default=None, max_length=120)
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class NotificationLogOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    communication_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    channel: str
    destination: Optional[str] = None
    status: str
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationLogPage(BaseModel):
    items: list[NotificationLogOut]
    meta: PageMeta
