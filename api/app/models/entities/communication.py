from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class Communication(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="communications", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="communications", on_delete=fields.CASCADE)
    report = fields.ForeignKeyField("models.Report", related_name="communications", null=True, on_delete=fields.SET_NULL)
    created_by_user = fields.ForeignKeyField("models.User", related_name="created_communications", null=True, on_delete=fields.SET_NULL)
    approved_by = fields.ForeignKeyField("models.User", related_name="approved_communications", null=True, on_delete=fields.SET_NULL)
    communication_type = fields.CharField(max_length=60)
    title = fields.CharField(max_length=180)
    body = fields.TextField()
    status = fields.CharField(max_length=40, default="draft")
    audience = fields.CharField(max_length=40, default="committee")
    channels = fields.JSONField(default=list)
    scheduled_at = fields.DatetimeField(null=True)
    sent_at = fields.DatetimeField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "communications"
        indexes = (("company_id",), ("condominium_id", "status"), ("communication_type",), ("audience",), ("sent_at",))
