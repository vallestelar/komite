from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class UnitContact(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="unit_contacts", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="unit_contacts", on_delete=fields.CASCADE)
    unit = fields.ForeignKeyField("models.Unit", related_name="contacts", on_delete=fields.CASCADE)
    user = fields.ForeignKeyField("models.User", related_name="unit_contacts", null=True, on_delete=fields.SET_NULL)
    relationship_type = fields.CharField(max_length=40, default="residente")
    full_name = fields.CharField(max_length=150)
    email = fields.CharField(max_length=255, null=True)
    phone = fields.CharField(max_length=40, null=True)
    document_type = fields.CharField(max_length=30, null=True)
    document_number = fields.CharField(max_length=40, null=True)
    address = fields.CharField(max_length=255, null=True)
    is_primary_contact = fields.BooleanField(default=False)
    receives_notifications = fields.BooleanField(default=True)
    start_date = fields.DateField(null=True)
    end_date = fields.DateField(null=True)
    status = fields.CharField(max_length=30, default="active")
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "unit_contacts"
        indexes = (
            ("company_id",),
            ("condominium_id",),
            ("unit_id",),
            ("user_id",),
            ("relationship_type",),
            ("status",),
            ("document_number",),
            ("email",),
        )
