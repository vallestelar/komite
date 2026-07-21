from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class SignaturePermission(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="signature_permissions", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="signature_permissions", null=True, on_delete=fields.CASCADE)
    signature = fields.ForeignKeyField("models.SignatureAsset", related_name="permissions", on_delete=fields.CASCADE)
    user = fields.ForeignKeyField("models.User", related_name="signature_permissions", on_delete=fields.CASCADE)
    can_use = fields.BooleanField(default=True)
    status = fields.CharField(max_length=30, default="active")
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "signature_permissions"
        indexes = (("company_id",), ("condominium_id",), ("signature_id",), ("user_id",), ("status",))
        unique_together = (("signature_id", "user_id", "condominium_id"),)
