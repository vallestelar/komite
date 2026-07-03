from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class TaskChecklist(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="task_checklist_items", null=True, on_delete=fields.CASCADE)
    task = fields.ForeignKeyField("models.Task", related_name="checklist_items", on_delete=fields.CASCADE)
    label = fields.CharField(max_length=180)
    is_completed = fields.BooleanField(default=False)
    completed_at = fields.DatetimeField(null=True)
    completed_by = fields.ForeignKeyField("models.User", related_name="completed_checklist_items", null=True, on_delete=fields.SET_NULL)
    position = fields.IntField(default=0)

    class Meta:
        table = "task_checklists"
        indexes = (("company_id",), ("task_id", "position"),)
