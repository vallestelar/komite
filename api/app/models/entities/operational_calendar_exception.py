from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class OperationalCalendarException(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="operational_calendar_exceptions", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="operational_calendar_exceptions", null=True, on_delete=fields.CASCADE)
    calendar = fields.ForeignKeyField("models.OperationalWorkCalendar", related_name="exceptions", on_delete=fields.CASCADE)
    exception_date = fields.DateField()
    exception_type = fields.CharField(max_length=40)
    start_time = fields.TimeField(null=True)
    end_time = fields.TimeField(null=True)
    reason = fields.CharField(max_length=255, null=True)
    source = fields.CharField(max_length=40, default="condominium_override")
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "operational_calendar_exceptions"
        indexes = (("company_id",), ("condominium_id",), ("calendar_id",), ("exception_date",), ("exception_type",), ("source",))
