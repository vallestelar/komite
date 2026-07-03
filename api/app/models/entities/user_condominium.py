from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class UserCondominium(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="user_condominium_memberships", null=True, on_delete=fields.CASCADE)
    user = fields.ForeignKeyField("models.User", related_name="condominium_memberships", on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="user_memberships", on_delete=fields.CASCADE)
    role = fields.ForeignKeyField("models.Role", related_name="user_condominiums", on_delete=fields.RESTRICT)
    unit = fields.ForeignKeyField("models.Unit", related_name="residents", null=True, on_delete=fields.SET_NULL)
    status = fields.CharField(max_length=30, default="active")
    receives_notifications = fields.BooleanField(default=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "user_condominiums"
        unique_together = (("user", "condominium", "role", "unit"),)
        indexes = (("company_id",), ("user_id",), ("condominium_id",), ("role_id",), ("status",))
