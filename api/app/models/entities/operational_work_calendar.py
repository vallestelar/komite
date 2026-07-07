from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class OperationalWorkCalendar(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="operational_work_calendars", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="operational_work_calendars", null=True, on_delete=fields.CASCADE)
    base_calendar = fields.ForeignKeyField("models.OperationalWorkCalendar", related_name="derived_calendars", null=True, on_delete=fields.SET_NULL)
    name = fields.CharField(max_length=150)
    calendar_type = fields.CharField(max_length=40, default="condominium")
    working_days = fields.JSONField(default=list)
    default_start_time = fields.TimeField(null=True)
    default_end_time = fields.TimeField(null=True)
    timezone = fields.CharField(max_length=80, default="America/Santiago")
    status = fields.CharField(max_length=30, default="active")
    effective_from = fields.DateField(null=True)
    effective_to = fields.DateField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "operational_work_calendars"
        indexes = (("company_id",), ("condominium_id",), ("base_calendar_id",), ("calendar_type",), ("status",))

