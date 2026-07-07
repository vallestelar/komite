from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class OperationalRescheduleLog(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="operational_reschedule_logs", null=True, on_delete=fields.CASCADE)
    event = fields.ForeignKeyField("models.PlannedOperationalEvent", related_name="reschedule_logs", on_delete=fields.CASCADE)
    previous_date = fields.DateField(null=True)
    new_date = fields.DateField(null=True)
    previous_assigned_user = fields.ForeignKeyField("models.User", related_name="previous_operational_reschedules", null=True, on_delete=fields.SET_NULL)
    new_assigned_user = fields.ForeignKeyField("models.User", related_name="new_operational_reschedules", null=True, on_delete=fields.SET_NULL)
    reason = fields.CharField(max_length=255, null=True)
    requested_by_user = fields.ForeignKeyField("models.User", related_name="requested_operational_reschedules", null=True, on_delete=fields.SET_NULL)
    approved_by_user = fields.ForeignKeyField("models.User", related_name="approved_operational_reschedules", null=True, on_delete=fields.SET_NULL)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "operational_reschedule_logs"
        indexes = (("company_id",), ("event_id",), ("previous_date",), ("new_date",), ("requested_by_user_id",), ("approved_by_user_id",))
