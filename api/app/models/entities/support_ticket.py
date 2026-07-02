from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class SupportTicket(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="support_tickets", on_delete=fields.CASCADE)
    created_by_user = fields.ForeignKeyField("models.User", related_name="created_support_tickets", null=True, on_delete=fields.SET_NULL)
    assigned_to = fields.ForeignKeyField("models.User", related_name="assigned_support_tickets", null=True, on_delete=fields.SET_NULL)
    requester_name = fields.CharField(max_length=150, null=True)
    requester_email = fields.CharField(max_length=255, null=True)
    subject = fields.CharField(max_length=180)
    description = fields.TextField(null=True)
    category = fields.CharField(max_length=80, default="general")
    priority = fields.CharField(max_length=30, default="medium")
    status = fields.CharField(max_length=40, default="open")
    due_date = fields.DateField(null=True)
    resolved_at = fields.DatetimeField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "support_tickets"
        indexes = (("company_id", "status"), ("assigned_to_id",), ("priority",), ("due_date",))
