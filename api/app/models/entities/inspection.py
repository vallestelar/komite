from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class Inspection(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="inspections", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="inspections", on_delete=fields.CASCADE)
    template = fields.ForeignKeyField("models.InspectionTemplate", related_name="inspections", null=True, on_delete=fields.SET_NULL)
    supervisor = fields.ForeignKeyField("models.User", related_name="inspections", null=True, on_delete=fields.SET_NULL)
    inspection_type = fields.CharField(max_length=80)
    status = fields.CharField(max_length=40, default="draft")
    observations = fields.TextField(null=True)
    latitude = fields.FloatField(null=True)
    longitude = fields.FloatField(null=True)
    signed_at = fields.DatetimeField(null=True)
    submitted_at = fields.DatetimeField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "inspections"
        indexes = (("company_id",), ("condominium_id", "status"), ("supervisor_id",), ("inspection_type",), ("submitted_at",))
