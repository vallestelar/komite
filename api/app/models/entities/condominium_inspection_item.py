from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class CondominiumInspectionItem(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="condominium_inspection_items", on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="condominium_inspection_items", on_delete=fields.CASCADE)
    condominium_template = fields.ForeignKeyField("models.CondominiumInspectionTemplate", related_name="items", on_delete=fields.CASCADE)
    base_item = fields.ForeignKeyField("models.InspectionTemplateItem", related_name="condominium_items", null=True, on_delete=fields.SET_NULL)
    section_name = fields.CharField(max_length=150, null=True)
    asset_name = fields.CharField(max_length=180, null=True)
    task_name = fields.CharField(max_length=255)
    instructions = fields.TextField(null=True)
    event_type = fields.CharField(max_length=40, default="maintenance")
    periodicity = fields.CharField(max_length=80, null=True)
    planned_months = fields.JSONField(default=list)
    responsible_user = fields.ForeignKeyField("models.User", related_name="responsible_condominium_inspection_items", null=True, on_delete=fields.SET_NULL)
    responsible_profile = fields.CharField(max_length=60, null=True)
    provider_id = fields.UUIDField(null=True)
    estimated_duration_minutes = fields.IntField(null=True)
    priority = fields.CharField(max_length=30, default="medium")
    status = fields.CharField(max_length=30, default="active")
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "condominium_inspection_items"
        indexes = (("company_id",), ("condominium_id",), ("condominium_template_id",), ("base_item_id",), ("event_type",), ("responsible_user_id",), ("priority",), ("status",))
