from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class Incident(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="incidents", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="incidents", on_delete=fields.CASCADE)
    reported_by = fields.ForeignKeyField("models.User", related_name="reported_incidents", null=True, on_delete=fields.SET_NULL)
    assigned_to = fields.ForeignKeyField("models.User", related_name="assigned_incidents", null=True, on_delete=fields.SET_NULL)
    category = fields.CharField(max_length=80)
    priority = fields.CharField(max_length=30, default="medium")
    status = fields.CharField(max_length=40, default="new")
    original_description = fields.TextField()
    ai_description = fields.TextField(null=True)
    confidence_score = fields.FloatField(null=True)
    due_date = fields.DateField(null=True)
    closed_at = fields.DatetimeField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "incidents"
        indexes = (("company_id",), ("condominium_id", "status"), ("category",), ("priority",), ("due_date",))
