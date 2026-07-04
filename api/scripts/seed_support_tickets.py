from __future__ import annotations

import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV_SITE_PACKAGES = ROOT / "venv" / "Lib" / "site-packages"
sys.path.insert(0, str(ROOT))
if VENV_SITE_PACKAGES.exists():
    sys.path.insert(0, str(VENV_SITE_PACKAGES))

from app.dbs.postgres.context import DbContext
from app.models.entities.company import Company
from app.models.entities.condominium import Condominium
from app.models.entities.support_ticket import SupportTicket


SEED_BATCH = "komite_dashboard_seed_20260704"


FAKE_COMPANIES = [
    {
        "name": "Andes Administracion",
        "rut": "DEMO-ANDES-001",
        "legal_name": "Andes Administracion SpA",
        "email": "soporte@andes-demo.cl",
        "phone": "+56 9 4100 1100",
        "condominiums": [
            {"name": "Mirador Los Andes", "units_count": 188, "commune": "Las Condes"},
            {"name": "Jardines del Sol", "units_count": 126, "commune": "Providencia"},
            {"name": "Parque Cordillera", "units_count": 244, "commune": "La Reina"},
        ],
    },
    {
        "name": "Pacifico Gestion",
        "rut": "DEMO-PACIFICO-001",
        "legal_name": "Pacifico Gestion Inmobiliaria Ltda",
        "email": "contacto@pacifico-demo.cl",
        "phone": "+56 9 4200 2200",
        "condominiums": [
            {"name": "Costa Serena", "units_count": 96, "commune": "La Serena"},
            {"name": "Bahia Azul", "units_count": 154, "commune": "Coquimbo"},
        ],
    },
    {
        "name": "Norte Urbano",
        "rut": "DEMO-NORTE-001",
        "legal_name": "Norte Urbano Administraciones SpA",
        "email": "mesa@norte-demo.cl",
        "phone": "+56 9 4300 3300",
        "condominiums": [
            {"name": "Altos del Desierto", "units_count": 210, "commune": "Antofagasta"},
            {"name": "Oasis Central", "units_count": 132, "commune": "Calama"},
            {"name": "Terrazas del Norte", "units_count": 178, "commune": "Iquique"},
        ],
    },
]


KOMPLEMENTA_CONDOMINIUMS = [
    {"name": "Ciudad del Encanto V", "units_count": 370, "commune": "La Serena"},
    {"name": "Espacio Uno III", "units_count": 168, "commune": "La Serena"},
    {"name": "Palmas de la Serena", "units_count": 423, "commune": "La Serena"},
    {"name": "Vista Sol", "units_count": 151, "commune": "Coquimbo"},
]


TICKET_PATTERNS = [
    ("Carga inicial de condominios", "data", "open", "high", 2),
    ("Consulta de usuarios del portal", "users", "pending", "medium", 5),
    ("Revision de audio IA", "ai", "in_progress", "urgent", 1),
    ("Ajuste de permisos mobile", "access", "resolved", "medium", -2),
    ("Error al generar informe", "reports", "open", "high", -1),
    ("Solicitud de capacitacion", "training", "closed", "low", -7),
]


async def main() -> None:
    db = DbContext()
    await db.init()
    try:
        await remove_previous_seed_tickets()
        komplementa = await get_or_create_komplementa()
        companies = [komplementa]

        for company_data in FAKE_COMPANIES:
            company = await ensure_company(company_data)
            companies.append(company)

        total_condominiums = 0
        total_tickets = 0

        for company in companies:
            condo_seed = KOMPLEMENTA_CONDOMINIUMS if company.name.strip().casefold() == "komplementa" else next(
                item["condominiums"] for item in FAKE_COMPANIES if item["name"] == company.name
            )
            condominiums = []
            for condo_data in condo_seed:
                condominium = await ensure_condominium(company, condo_data)
                condominiums.append(condominium)
            total_condominiums += len(condominiums)
            total_tickets += await create_company_tickets(company, condominiums)

        print(f"Seed completado: {len(companies)} empresas, {total_condominiums} condominios, {total_tickets} tickets.")
        print(f"Marcador de tickets: {SEED_BATCH}")
    finally:
        await db.close()


async def remove_previous_seed_tickets() -> None:
    tickets = await SupportTicket.all()
    for ticket in tickets:
        metadata = ticket.metadata if isinstance(ticket.metadata, dict) else {}
        if metadata.get("seed_batch") == SEED_BATCH:
            await ticket.delete()


async def get_or_create_komplementa() -> Company:
    for company in await Company.all():
        if company.name.strip().casefold() == "komplementa":
            return company
    return await Company.create(
        name="Komplementa",
        rut="KOMPLEMENTA-REAL",
        legal_name="Komplementa",
        email="contacto@komplementa.cl",
        status="active",
        metadata={"seed_note": "Creada solo porque no existia Komplementa en esta BBDD."},
    )


async def ensure_company(data: dict) -> Company:
    company = await Company.get_or_none(rut=data["rut"])
    if company:
        return company
    company = await Company.get_or_none(name=data["name"])
    if company:
        return company
    return await Company.create(
        name=data["name"],
        rut=data["rut"],
        legal_name=data["legal_name"],
        email=data["email"],
        phone=data["phone"],
        status="active",
        metadata={"seed_batch": SEED_BATCH},
    )


async def ensure_condominium(company: Company, data: dict) -> Condominium:
    condominium = await Condominium.get_or_none(company=company, name=data["name"])
    if condominium:
        return condominium
    return await Condominium.create(
        company=company,
        name=data["name"],
        address="Avenida Pacifico 5208",
        commune=data["commune"],
        city=data["commune"],
        region="Region Metropolitana" if data["commune"] in {"Las Condes", "Providencia", "La Reina"} else "Chile",
        towers_count=2,
        units_count=data["units_count"],
        status="active",
        metadata={"seed_batch": SEED_BATCH},
    )


async def create_company_tickets(company: Company, condominiums: list[Condominium]) -> int:
    today = date.today()
    created = 0
    for condo_index, condominium in enumerate(condominiums):
        ticket_count = 2 + (condo_index % 3)
        for pattern_index in range(ticket_count):
            subject, category, status, priority, due_offset = TICKET_PATTERNS[(condo_index + pattern_index) % len(TICKET_PATTERNS)]
            await SupportTicket.create(
                company=company,
                requester_name="Mesa de ayuda Komite",
                requester_email="soporte@komite.cl",
                subject=f"{subject} - {condominium.name}",
                description=f"Ticket de prueba real para visualizar el aporte de {condominium.name} en el dashboard.",
                category=category,
                priority=priority,
                status=status,
                due_date=today + timedelta(days=due_offset),
                metadata={
                    "seed_batch": SEED_BATCH,
                    "condominium_id": str(condominium.id),
                    "condominium_name": condominium.name,
                    "dashboard_seed": True,
                },
            )
            created += 1
    return created


if __name__ == "__main__":
    asyncio.run(main())
