from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class InspectionTemplateItem(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="inspection_template_items", null=True, on_delete=fields.CASCADE)
    template = fields.ForeignKeyField("models.InspectionTemplate", related_name="items", on_delete=fields.CASCADE)
    section = fields.ForeignKeyField("models.InspectionTemplateSection", related_name="items", null=True, on_delete=fields.SET_NULL)
    asset_name = fields.CharField(max_length=180, null=True)
    task_name = fields.CharField(max_length=255)
    instructions = fields.TextField(null=True)
    periodicity = fields.CharField(max_length=80, null=True)
    planned_months = fields.JSONField(default=list)
    requires_evidence = fields.BooleanField(default=False)
    default_responsible_profile = fields.CharField(max_length=60, null=True)
    default_duration_minutes = fields.IntField(null=True)
    display_order = fields.IntField(default=0)
    status = fields.CharField(max_length=30, default="active")
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "inspection_template_items"
        indexes = (("company_id",), ("template_id",), ("section_id",), ("periodicity",), ("status",), ("display_order",))

