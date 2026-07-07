from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class InspectionTemplate(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="inspection_templates", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="inspection_templates", null=True, on_delete=fields.CASCADE)
    name = fields.CharField(max_length=150)
    description = fields.TextField(null=True)
    template_type = fields.CharField(max_length=80, default="inspection")
    inspection_type = fields.CharField(max_length=80)
    version = fields.IntField(default=1)
    status = fields.CharField(max_length=30, default="active")
    source_file_name = fields.CharField(max_length=255, null=True)
    checklist_schema = fields.JSONField(default=list)
    is_active = fields.BooleanField(default=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "inspection_templates"
        indexes = (("company_id",), ("condominium_id",), ("template_type",), ("inspection_type",), ("status",), ("is_active",))
