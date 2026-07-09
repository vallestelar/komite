from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class Assembly(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="assemblies", on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="assemblies", on_delete=fields.CASCADE)
    event = fields.ForeignKeyField("models.PlannedOperationalEvent", related_name="assemblies", null=True, on_delete=fields.SET_NULL)
    title = fields.CharField(max_length=180)
    description = fields.TextField(null=True)
    assembly_type = fields.CharField(max_length=40, default="ordinary")
    status = fields.CharField(max_length=40, default="scheduled")
    scheduled_date = fields.DateField()
    scheduled_start_time = fields.TimeField(null=True)
    estimated_duration_minutes = fields.IntField(null=True)
    location = fields.CharField(max_length=180, null=True)
    modality = fields.CharField(max_length=40, default="presential")
    quorum_required = fields.IntField(null=True)
    attendees = fields.JSONField(default=list)
    agenda_items = fields.JSONField(default=list)
    conclusions = fields.TextField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "assemblies"
        indexes = (("company_id",), ("condominium_id", "status"), ("scheduled_date",), ("event_id",))
