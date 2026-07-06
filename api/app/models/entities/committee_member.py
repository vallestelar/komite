from __future__ import annotations

from tortoise import fields
from tortoise.signals import post_save

from app.models.entities.mixins import TimestampAuditMixin


class CommitteeMember(TimestampAuditMixin):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.Company", related_name="committee_members", null=True, on_delete=fields.CASCADE)
    condominium = fields.ForeignKeyField("models.Condominium", related_name="committee_members", on_delete=fields.CASCADE)
    user = fields.ForeignKeyField("models.User", related_name="committee_members", null=True, on_delete=fields.SET_NULL)
    unit_contact = fields.ForeignKeyField("models.UnitContact", related_name="committee_members", null=True, on_delete=fields.SET_NULL)
    unit = fields.ForeignKeyField("models.Unit", related_name="committee_members", null=True, on_delete=fields.SET_NULL)
    position = fields.CharField(max_length=80)
    full_name = fields.CharField(max_length=150)
    email = fields.CharField(max_length=255, null=True)
    phone = fields.CharField(max_length=40, null=True)
    start_date = fields.DateField(null=True)
    end_date = fields.DateField(null=True)
    status = fields.CharField(max_length=30, default="active")
    receives_notifications = fields.BooleanField(default=True)
    display_order = fields.IntField(default=0)
    notes = fields.TextField(null=True)
    metadata = fields.JSONField(default=dict)

    class Meta:
        table = "committee_members"
        indexes = (
            ("company_id",),
            ("condominium_id",),
            ("user_id",),
            ("unit_contact_id",),
            ("unit_id",),
            ("position",),
            ("status",),
        )


@post_save(CommitteeMember)
async def ensure_committee_role(sender, instance: CommitteeMember, created: bool, using_db, update_fields) -> None:
    if instance.status != "active" or not instance.condominium_id:
        return

    from app.models.entities.role import Role
    from app.models.entities.unit_contact import UnitContact
    from app.models.entities.user import User
    from app.models.entities.user_condominium import UserCondominium

    user_id = instance.user_id
    unit_id = instance.unit_id
    email = instance.email

    if not user_id and instance.unit_contact_id:
        contact = await UnitContact.get_or_none(id=instance.unit_contact_id)
        if contact:
            user_id = contact.user_id
            unit_id = unit_id or contact.unit_id
            email = email or contact.email

    if not user_id:
        user = await User.get_or_none(email=email) if email else None
        user_id = user.id if user else None

    if not user_id:
        return

    role = await Role.get_or_none(code="comite")
    if not role:
        return

    membership = await UserCondominium.get_or_none(
        user_id=user_id,
        condominium_id=instance.condominium_id,
        role_id=role.id,
    )

    metadata = {
        "source": "committee_member",
        "committee_member_id": str(instance.id),
    }

    if membership:
        changed = False
        if membership.status != "active":
            membership.status = "active"
            changed = True
        if membership.receives_notifications != instance.receives_notifications:
            membership.receives_notifications = instance.receives_notifications
            changed = True
        if not membership.unit_id and unit_id:
            membership.unit_id = unit_id
            changed = True
        if changed:
            membership.updated_by = "committee_member_sync"
            await membership.save()
        return

    await UserCondominium.create(
        company_id=instance.company_id,
        user_id=user_id,
        condominium_id=instance.condominium_id,
        role_id=role.id,
        unit_id=unit_id,
        status="active",
        receives_notifications=instance.receives_notifications,
        metadata=metadata,
        created_by="committee_member_sync",
        updated_by="committee_member_sync",
    )
