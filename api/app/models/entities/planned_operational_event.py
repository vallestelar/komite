from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class PlannedOperationalEvent(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="planned_operational_events", on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="planned_operational_events", on_delete=fields.CASCADE)
    condominium_template_item = fields.ForeignKeyField("models.CondominiumInspectionItem", related_name="planned_events", null=True, on_delete=fields.SET_NULL)
    calendar = fields.ForeignKeyField("models.OperationalWorkCalendar", related_name="planned_events", null=True, on_delete=fields.SET_NULL)
    assigned_user = fields.ForeignKeyField("models.User", related_name="assigned_operational_events", null=True, on_delete=fields.SET_NULL)
    title = fields.CharField(max_length=180)
    description = fields.TextField(null=True)
    planned_date = fields.DateField()
    planned_start_time = fields.TimeField(null=True)
    planned_end_time = fields.TimeField(null=True)
    estimated_duration_minutes = fields.IntField(null=True)
    assigned_profile = fields.CharField(max_length=60, null=True)
    priority = fields.CharField(max_length=30, default="medium")
    status = fields.CharField(max_length=40, default="pending")
    source_type = fields.CharField(max_length=60, null=True)
    source_id = fields.UUIDField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "planned_operational_events"
        indexes = (("company_id",), ("condominium_id", "status"), ("condominium_template_item_id",), ("calendar_id",), ("assigned_user_id",), ("planned_date",), ("priority",))
