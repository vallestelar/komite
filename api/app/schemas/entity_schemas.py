from __future__ import annotations

from datetime import date, datetime
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


class UnitCreate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: UUID
    building_id: Optional[UUID] = None
    identifier: str = Field(..., max_length=80)
    floor: Optional[str] = Field(default=None, max_length=20)
    unit_type: str = Field(default="apartment", max_length=30)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UnitUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    building_id: Optional[UUID] = None
    identifier: Optional[str] = Field(default=None, max_length=80)
    floor: Optional[str] = Field(default=None, max_length=20)
    unit_type: Optional[str] = Field(default=None, max_length=30)
    metadata: Optional[dict[str, Any]] = None


class UnitOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: UUID
    building_id: Optional[UUID] = None
    identifier: str
    floor: Optional[str] = None
    unit_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class UnitPage(BaseModel):
    items: list[UnitOut]
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
    condominium_id: UUID
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
    condominium_id: UUID
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
    inspection_type: str = Field(..., max_length=80)
    checklist_schema: list[Any] = Field(default_factory=list)
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class InspectionTemplateUpdate(BaseModel):
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    name: Optional[str] = Field(default=None, max_length=150)
    inspection_type: Optional[str] = Field(default=None, max_length=80)
    checklist_schema: Optional[list[Any]] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None


class InspectionTemplateOut(AuditOut):
    id: UUID
    company_id: Optional[UUID] = None
    condominium_id: Optional[UUID] = None
    name: str
    inspection_type: str
    checklist_schema: list[Any] = Field(default_factory=list)
    is_active: bool
    metadata: dict[str, Any] = Field(default_factory=dict)


class InspectionTemplatePage(BaseModel):
    items: list[InspectionTemplateOut]
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
