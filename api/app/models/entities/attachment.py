from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class Attachment(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="attachments", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="attachments", null=True, on_delete=fields.CASCADE)
    uploaded_by = fields.ForeignKeyField("models.User", related_name="uploaded_attachments", null=True, on_delete=fields.SET_NULL)
    incident = fields.ForeignKeyField("models.Incident", related_name="attachments", null=True, on_delete=fields.CASCADE)
    task = fields.ForeignKeyField("models.Task", related_name="attachments", null=True, on_delete=fields.CASCADE)
    inspection = fields.ForeignKeyField("models.Inspection", related_name="attachments", null=True, on_delete=fields.CASCADE)
    report = fields.ForeignKeyField("models.Report", related_name="attachments", null=True, on_delete=fields.CASCADE)
    communication = fields.ForeignKeyField("models.Communication", related_name="attachments", null=True, on_delete=fields.CASCADE)
    file_name = fields.CharField(max_length=255)
    file_path = fields.CharField(max_length=500)
    file_type = fields.CharField(max_length=80)
    mime_type = fields.CharField(max_length=120, null=True)
    size_bytes = fields.BigIntField(null=True)
    checksum = fields.CharField(max_length=128, null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "attachments"
        indexes = (("company_id",), ("condominium_id",), ("incident_id",), ("task_id",), ("inspection_id",), ("file_type",))
