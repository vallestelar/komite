from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class RefreshToken(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="refresh_tokens", on_delete=fields.CASCADE)
    token_hash = fields.CharField(max_length=64, unique=True)
    family_id = fields.UUIDField()
    expires_at = fields.DatetimeField()
    revoked_at = fields.DatetimeField(null=True)
    replaced_by = fields.ForeignKeyField(
        "models.RefreshToken",
        related_name="replaced_tokens",
        null=True,
        on_delete=fields.SET_NULL,
    )
    created_by_ip = fields.CharField(max_length=80, null=True)
    user_agent = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "refresh_tokens"
        indexes = (("user_id",), ("token_hash",), ("family_id",), ("expires_at",), ("revoked_at",))
