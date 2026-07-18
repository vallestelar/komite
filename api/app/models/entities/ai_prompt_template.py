from __future__ import annotations

from tortoise import fields

from app.models.entities.mixins import TimestampAuditMixin


class AIPromptTemplate(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="ai_prompt_templates", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="ai_prompt_templates", null=True, on_delete=fields.CASCADE)
    key = fields.CharField(max_length=120)
    name = fields.CharField(max_length=180)
    description = fields.TextField(null=True)
    purpose = fields.CharField(max_length=100)
    module = fields.CharField(max_length=80, default="general")
    asset_type = fields.CharField(max_length=80, null=True)
    system_template = fields.TextField()
    user_template = fields.TextField()
    required_variables = fields.JSONField(default=list)
    optional_variables = fields.JSONField(default=list)
    default_model = fields.CharField(max_length=120, null=True)
    default_temperature = fields.FloatField(default=0.2)
    default_max_tokens = fields.IntField(null=True)
    reasoning_enabled = fields.BooleanField(default=False)
    expects_json = fields.BooleanField(default=False)
    version = fields.IntField(default=1)
    status = fields.CharField(max_length=30, default="draft")
    is_active = fields.BooleanField(default=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "ai_prompt_templates"
        unique_together = (("company_id", "condominium_id", "key", "version"),)
        indexes = (
            ("company_id",),
            ("condominium_id",),
            ("key",),
            ("purpose",),
            ("module",),
            ("asset_type",),
            ("status",),
            ("is_active",),
        )
