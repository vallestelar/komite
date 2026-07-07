from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class InspectionTemplateSection(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="inspection_template_sections", null=True, on_delete=fields.CASCADE)
    template = fields.ForeignKeyField("models.InspectionTemplate", related_name="sections", on_delete=fields.CASCADE)
    name = fields.CharField(max_length=150)
    description = fields.TextField(null=True)
    display_order = fields.IntField(default=0)
    status = fields.CharField(max_length=30, default="active")
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "inspection_template_sections"
        indexes = (("company_id",), ("template_id",), ("status",), ("display_order",))

