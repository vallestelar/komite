from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class CondominiumOperationalStaff(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="condominium_operational_staff", on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="operational_staff", null=True, on_delete=fields.CASCADE)
    user = fields.ForeignKeyField("models.User", related_name="operational_condominiums", on_delete=fields.CASCADE)
    portal_profile = fields.CharField(max_length=60)
    responsibility = fields.CharField(max_length=120, null=True)
    is_primary = fields.BooleanField(default=False)
    start_date = fields.DateField(null=True)
    end_date = fields.DateField(null=True)
    status = fields.CharField(max_length=30, default="active")
    notes = fields.TextField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "condominium_operational_staff"
        indexes = (
            ("company_id",),
            ("condominium_id",),
            ("user_id",),
            ("portal_profile",),
            ("status",),
        )
        unique_together = (("condominium_id", "user_id", "portal_profile"),)
