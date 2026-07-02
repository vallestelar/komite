from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class IncidentEvent(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    incident = fields.ForeignKeyField("models.Incident", related_name="events", on_delete=fields.CASCADE)
    user = fields.ForeignKeyField("models.User", related_name="incident_events", null=True, on_delete=fields.SET_NULL)
    event_type = fields.CharField(max_length=60)
    previous_status = fields.CharField(max_length=40, null=True)
    new_status = fields.CharField(max_length=40, null=True)
    comment = fields.TextField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "incident_events"
        indexes = (("incident_id",), ("event_type",), ("created_at",))

