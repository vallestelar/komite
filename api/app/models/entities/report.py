from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class Report(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="reports", on_delete=fields.CASCADE)
    incident = fields.ForeignKeyField("models.Incident", related_name="reports", null=True, on_delete=fields.SET_NULL)
    task = fields.ForeignKeyField("models.Task", related_name="reports", null=True, on_delete=fields.SET_NULL)
    inspection = fields.ForeignKeyField("models.Inspection", related_name="reports", null=True, on_delete=fields.SET_NULL)
    created_by_user = fields.ForeignKeyField("models.User", related_name="created_reports", null=True, on_delete=fields.SET_NULL)
    approved_by = fields.ForeignKeyField("models.User", related_name="approved_reports", null=True, on_delete=fields.SET_NULL)
    report_type = fields.CharField(max_length=60)
    title = fields.CharField(max_length=180)
    status = fields.CharField(max_length=40, default="draft")
    content = fields.JSONField(default=dict)
    approved_at = fields.DatetimeField(null=True)
    published_at = fields.DatetimeField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "reports"
        indexes = (("condominium_id", "status"), ("report_type",), ("published_at",))

