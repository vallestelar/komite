from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class InspectionTemplate(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="inspection_templates", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="inspection_templates", null=True, on_delete=fields.CASCADE)
    name = fields.CharField(max_length=150)
    inspection_type = fields.CharField(max_length=80)
    checklist_schema = fields.JSONField(default=list)
    is_active = fields.BooleanField(default=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "inspection_templates"
        indexes = (("company_id",), ("condominium_id",), ("inspection_type",), ("is_active",))

