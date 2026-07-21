from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class SignatureAsset(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="signature_assets", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="signature_assets", null=True, on_delete=fields.CASCADE)
    name = fields.CharField(max_length=150)
    signer_name = fields.CharField(max_length=150)
    signer_document = fields.CharField(max_length=40, null=True)
    signer_position = fields.CharField(max_length=120, null=True)
    storage_key = fields.CharField(max_length=500, null=True)
    content_type = fields.CharField(max_length=80, null=True)
    size_bytes = fields.IntField(null=True)
    status = fields.CharField(max_length=30, default="active")
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "signature_assets"
        indexes = (("company_id",), ("condominium_id",), ("status",))
