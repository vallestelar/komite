import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.security.passwords import hash_password
from app.core.settings import settings
from app.dbs.postgres.context import DbContext
from app.models.entities import Company, Role, User

ROLES = [
    ("vecino", "Vecino", {"scope": "community", "community": "read"}),
    ("comite", "Comite", {"scope": "community", "committee": "write"}),
    ("supervisor", "Supervisor", {"scope": "operations", "operations": "write"}),
    ("conserje", "Conserje", {"scope": "operations", "incidents": "create"}),
]


async def main() -> int:
    db = DbContext()
    await db.init(generate_schemas=False)

    try:
        for code, name, permissions in ROLES:
            role = await Role.get_or_none(code=code)
            if role:
                role.name = name
                role.permissions = permissions
                await role.save()
            else:
                await Role.create(
                    code=code,
                    name=name,
                    permissions=permissions,
                    is_system=True,
                )

        company, _ = await Company.get_or_create(
            name="Komite",
            defaults={
                "rut": None,
                "legal_name": "Komite",
                "email": settings.seed_admin_email,
                "status": "active",
            },
        )

        admin = await User.get_or_none(email=settings.seed_admin_email)
        if admin:
            admin.company = company
            admin.full_name = settings.seed_admin_full_name
            admin.company_profile = "project_manager"
            admin.status = "active"
            if not admin.password_hash:
                admin.password_hash = hash_password(settings.seed_admin_password)
            await admin.save()
            print(f"OK: admin actualizado: {settings.seed_admin_email}")
        else:
            await User.create(
                company=company,
                email=settings.seed_admin_email,
                password_hash=hash_password(settings.seed_admin_password),
                full_name=settings.seed_admin_full_name,
                status="active",
                company_profile="project_manager",
            )
            print(f"OK: admin creado: {settings.seed_admin_email}")

        print("OK: roles iniciales creados/actualizados.")
        return 0
    finally:
        await db.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
