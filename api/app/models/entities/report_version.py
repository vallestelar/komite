from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class ReportVersion(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="report_versions", null=True, on_delete=fields.CASCADE)
    report = fields.ForeignKeyField("models.Report", related_name="versions", on_delete=fields.CASCADE)
    version_number = fields.IntField()
    source = fields.CharField(max_length=40, default="human")
    content = fields.JSONField(default=dict)
    notes = fields.TextField(null=True)

    class Meta:
        table = "report_versions"
        unique_together = (("report", "version_number"),)
        indexes = (("company_id",), ("report_id", "version_number"), ("source",))
