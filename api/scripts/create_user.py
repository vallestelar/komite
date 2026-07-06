import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.security.passwords import hash_password
from app.dbs.postgres.context import DbContext
from app.models.entities import Company, Condominium, Role, User, UserCondominium


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crear usuario Komite")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--full-name", required=True)
    parser.add_argument("--company-name", default="Komite")
    parser.add_argument("--company-profile", default=None, choices=("project_manager", "supervisor", "ejecutivo"))
    parser.add_argument("--status", default="active")
    parser.add_argument("--condominium-id", default=None)
    parser.add_argument("--all-condominiums", action="store_true")
    parser.add_argument("--role-code", default=None)
    return parser.parse_args()


async def get_company(name: str) -> Company:
    company = await Company.get_or_none(name=name)
    if company:
        return company
    return await Company.create(name=name, legal_name=name, status="active")


async def assign_condominium(user: User, condominium_id: str, role_code: str | None) -> None:
    role_code = role_code or "supervisor"
    role = await Role.get_or_none(code=role_code)
    if not role:
        raise ValueError(f"No existe el rol '{role_code}'. Ejecuta primero scripts\\seed_auth.py")
    if role.code not in {"vecino", "comite", "supervisor", "conserje"}:
        raise ValueError(f"Rol no permitido para comunidad: '{role.code}'")

    condominium = await Condominium.get_or_none(id=UUID(condominium_id))
    if not condominium:
        raise ValueError(f"No existe el condominio '{condominium_id}'")

    existing = await UserCondominium.get_or_none(
        user=user,
        condominium=condominium,
        role=role,
        unit=None,
    )
    if existing:
        existing.status = "active"
        await existing.save()
        print(f"OK: membresia existente activada: {condominium.name} / {role.code}")
        return

    await UserCondominium.create(
        company_id=condominium.company_id,
        user=user,
        condominium=condominium,
        role=role,
        status="active",
    )
    print(f"OK: usuario asignado a {condominium.name} como {role.code}")


async def assign_all_condominiums(user: User, role_code: str | None) -> None:
    if not user.company_id:
        raise ValueError("El usuario necesita empresa para asignar todos los condominios")

    role_code = role_code or "supervisor"
    role = await Role.get_or_none(code=role_code)
    if not role:
        raise ValueError(f"No existe el rol '{role_code}'. Ejecuta primero scripts\\seed_auth.py")
    if role.code not in {"vecino", "comite", "supervisor", "conserje"}:
        raise ValueError(f"Rol no permitido para comunidad: '{role.code}'")

    existing = await UserCondominium.get_or_none(
        user=user,
        company_id=user.company_id,
        condominium_id=None,
        role=role,
        unit=None,
    )
    if existing:
        existing.status = "active"
        await existing.save()
        print(f"OK: membresia existente activada: todos los condominios / {role.code}")
        return

    await UserCondominium.create(
        company_id=user.company_id,
        user=user,
        condominium=None,
        role=role,
        status="active",
    )
    print(f"OK: usuario asignado a todos los condominios como {role.code}")


async def main() -> int:
    args = parse_args()
    db = DbContext()
    await db.init(generate_schemas=False)

    try:
        company = await get_company(args.company_name)
        user = await User.get_or_none(email=args.email)

        if user:
            user.company = company
            user.full_name = args.full_name
            user.password_hash = hash_password(args.password)
            user.company_profile = args.company_profile
            user.status = args.status
            await user.save()
            print(f"OK: usuario actualizado: {args.email}")
        else:
            user = await User.create(
                company=company,
                email=args.email,
                password_hash=hash_password(args.password),
                full_name=args.full_name,
                company_profile=args.company_profile,
                status=args.status,
            )
            print(f"OK: usuario creado: {args.email}")

        if args.all_condominiums:
            await assign_all_condominiums(user, args.role_code)
        elif args.condominium_id:
            await assign_condominium(user, args.condominium_id, args.role_code)

        return 0
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
        return 1
    finally:
        await db.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
