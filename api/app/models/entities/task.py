from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class Task(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="tasks", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="tasks", on_delete=fields.CASCADE)
    incident = fields.ForeignKeyField("models.Incident", related_name="tasks", null=True, on_delete=fields.SET_NULL)
    assigned_to = fields.ForeignKeyField("models.User", related_name="assigned_tasks", null=True, on_delete=fields.SET_NULL)
    created_by_user = fields.ForeignKeyField("models.User", related_name="created_tasks", null=True, on_delete=fields.SET_NULL)
    title = fields.CharField(max_length=180)
    description = fields.TextField(null=True)
    status = fields.CharField(max_length=40, default="pending")
    priority = fields.CharField(max_length=30, default="medium")
    due_date = fields.DateField(null=True)
    completed_at = fields.DatetimeField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "tasks"
        indexes = (("company_id",), ("condominium_id", "status"), ("assigned_to_id",), ("due_date",), ("priority",))
