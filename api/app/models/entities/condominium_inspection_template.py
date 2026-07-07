from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class CondominiumInspectionTemplate(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="condominium_inspection_templates", on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="condominium_inspection_templates", on_delete=fields.CASCADE)
    base_template = fields.ForeignKeyField("models.InspectionTemplate", related_name="condominium_versions", null=True, on_delete=fields.SET_NULL)
    name = fields.CharField(max_length=150)
    template_type = fields.CharField(max_length=80, default="maintenance")
    version = fields.IntField(default=1)
    status = fields.CharField(max_length=30, default="draft")
    effective_from = fields.DateField(null=True)
    effective_to = fields.DateField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "condominium_inspection_templates"
        indexes = (("company_id",), ("condominium_id",), ("base_template_id",), ("template_type",), ("status",), ("effective_from",))
