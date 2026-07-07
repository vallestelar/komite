from __future__ import annotations

import argparse
import asyncio
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
VENV_SITE_PACKAGES = ROOT / "venv" / "Lib" / "site-packages"
sys.path.insert(0, str(ROOT))
if VENV_SITE_PACKAGES.exists():
    sys.path.insert(0, str(VENV_SITE_PACKAGES))

SEED_KEY = "komite_annual_maintenance_template_20260707"
TEMPLATE_NAME = "Plan anual de mantenciones Komplementa"
DEFAULT_EXCEL_PATH = PROJECT_ROOT / "Formato Programación Mantenciones Anuales.xlsx"
SHEET_NAME = "Plan Anual"
SOURCE_FILE_NAME = DEFAULT_EXCEL_PATH.name

MONTH_NUMBER_BY_LABEL = {
    "ENE": 1,
    "FEB": 2,
    "MAR": 3,
    "ABR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AGO": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DIC": 12,
}

PERIODICITY_MAP = {
    "diario": "daily",
    "1 semana": "weekly",
    "1 mes": "monthly",
    "2 meses": "bimonthly",
    "3 meses": "quarterly",
    "4 meses": "four_monthly",
    "6 meses": "semiannual",
    "1 año": "annual",
    "2 años": "biennial",
    "permanente": "permanent",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea la plantilla base anual de mantenciones desde el Excel funcional.")
    parser.add_argument("--excel", default=str(DEFAULT_EXCEL_PATH), help="Ruta al XLSX de mantenciones.")
    parser.add_argument("--dry-run", action="store_true", help="Solo muestra el resumen, no escribe en BBDD.")
    args = parser.parse_args()

    excel_path = Path(args.excel)
    rows = parse_maintenance_rows(excel_path)
    sections = sorted({row["section_name"] for row in rows})

    print(f"Excel: {excel_path}")
    print(f"Hoja: {SHEET_NAME}")
    print(f"Plantilla: {TEMPLATE_NAME}")
    print(f"Secciones detectadas: {len(sections)}")
    print(f"Items detectados: {len(rows)}")

    if args.dry_run:
        for section in sections:
            total = sum(1 for row in rows if row["section_name"] == section)
            print(f"- {section}: {total} items")
        return

    asyncio.run(seed(rows, excel_path.name))


async def seed(rows: list[dict[str, Any]], source_file_name: str) -> None:
    from app.dbs.postgres.context import DbContext
    from app.models.entities.inspection_template import InspectionTemplate
    from app.models.entities.inspection_template_item import InspectionTemplateItem
    from app.models.entities.inspection_template_section import InspectionTemplateSection

    db = DbContext()
    await db.init()
    try:
        await remove_previous_seed()

        template = await InspectionTemplate.create(
            company_id=None,
            condominium_id=None,
            name=TEMPLATE_NAME,
            description="Plantilla base creada desde el formato anual de mantenciones. Sirve como catalogo maestro para que cada condominio la pueda heredar y ajustar.",
            template_type="maintenance",
            inspection_type="preventive",
            version=1,
            status="published",
            source_file_name=source_file_name,
            checklist_schema=[],
            is_active=True,
            metadata={
                "seed_key": SEED_KEY,
                "source_sheet": SHEET_NAME,
                "source_file": source_file_name,
                "month_cycle": ["ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "ENE", "FEB", "MAR"],
            },
        )

        sections_by_name: dict[str, InspectionTemplateSection] = {}
        for index, section_name in enumerate(unique_in_order(row["section_name"] for row in rows), start=1):
            sections_by_name[section_name] = await InspectionTemplateSection.create(
                company_id=None,
                template=template,
                name=title_case(section_name),
                description=None,
                display_order=index,
                status="active",
                metadata={"seed_key": SEED_KEY, "source_section": section_name},
            )

        for index, row in enumerate(rows, start=1):
            await InspectionTemplateItem.create(
                company_id=None,
                template=template,
                section=sections_by_name[row["section_name"]],
                asset_name=row["asset_name"],
                task_name=row["task_name"],
                instructions=row["task_name"],
                periodicity=row["periodicity"],
                planned_months=row["planned_months"],
                requires_evidence=False,
                default_responsible_profile="supervisor",
                default_duration_minutes=None,
                display_order=index,
                status="active",
                metadata={
                    "seed_key": SEED_KEY,
                    "excel_row": row["excel_row"],
                    "source_periodicity": row["source_periodicity"],
                    "planned_month_labels": row["planned_month_labels"],
                },
            )

        print(f"Seed completado: plantilla={template.id}, secciones={len(sections_by_name)}, items={len(rows)}.")
    finally:
        await db.close()


async def remove_previous_seed() -> None:
    from app.models.entities.inspection_template import InspectionTemplate
    from app.models.entities.inspection_template_item import InspectionTemplateItem
    from app.models.entities.inspection_template_section import InspectionTemplateSection

    templates = await InspectionTemplate.filter(name=TEMPLATE_NAME)
    for template in templates:
        metadata = template.metadata if isinstance(template.metadata, dict) else {}
        if metadata.get("seed_key") == SEED_KEY or template.source_file_name == SOURCE_FILE_NAME:
            await InspectionTemplateItem.filter(template_id=template.id).delete()
            await InspectionTemplateSection.filter(template_id=template.id).delete()
            await template.delete()


def parse_maintenance_rows(excel_path: Path) -> list[dict[str, Any]]:
    values = read_xlsx_sheet(excel_path, SHEET_NAME)
    month_labels = [normalize_text(values.get((3, column))) for column in range(5, 17)]
    rows: list[dict[str, Any]] = []
    current_section = ""
    max_row = max((row for row, _ in values), default=0)

    for row_number in range(5, max_row + 1):
        section_value = normalize_text(values.get((row_number, 1)))
        asset_name = normalize_text(values.get((row_number, 2)))
        task_name = normalize_text(values.get((row_number, 3)))
        source_periodicity = normalize_text(values.get((row_number, 4)))

        if section_value:
            current_section = section_value
        if not task_name:
            continue
        if not current_section:
            raise ValueError(f"Fila {row_number}: item sin seccion.")

        planned_month_labels = [
            month_labels[index]
            for index, column in enumerate(range(5, 17))
            if normalize_text(values.get((row_number, column)))
        ]
        planned_months = [MONTH_NUMBER_BY_LABEL[label] for label in planned_month_labels if label in MONTH_NUMBER_BY_LABEL]

        rows.append(
            {
                "excel_row": row_number,
                "section_name": current_section,
                "asset_name": asset_name or None,
                "task_name": task_name,
                "source_periodicity": source_periodicity,
                "periodicity": normalize_periodicity(source_periodicity),
                "planned_month_labels": planned_month_labels,
                "planned_months": planned_months,
            }
        )

    return rows


def read_xlsx_sheet(excel_path: Path, sheet_name: str) -> dict[tuple[int, int], Any]:
    if not excel_path.exists():
        raise FileNotFoundError(f"No existe el Excel: {excel_path}")

    with zipfile.ZipFile(excel_path) as workbook:
        shared_strings = read_shared_strings(workbook)
        sheet_path = resolve_sheet_path(workbook, sheet_name)
        root = ET.fromstring(workbook.read(sheet_path))

    values: dict[tuple[int, int], Any] = {}
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    for cell in root.findall(".//a:c", ns):
        ref = cell.attrib.get("r")
        if not ref:
            continue
        value = read_cell_value(cell, shared_strings)
        if value is None:
            continue
        values[cell_ref_to_position(ref)] = value
    return values


def read_shared_strings(workbook: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return []
    root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    strings = []
    for item in root.findall("a:si", ns):
        parts = [text.text or "" for text in item.findall(".//a:t", ns)]
        strings.append("".join(parts))
    return strings


def resolve_sheet_path(workbook: zipfile.ZipFile, sheet_name: str) -> str:
    ns = {
        "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    }
    workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
    sheet = next((item for item in workbook_root.findall(".//a:sheet", ns) if item.attrib.get("name") == sheet_name), None)
    if sheet is None:
        raise ValueError(f"No se encontro la hoja {sheet_name!r}.")
    rel_id = sheet.attrib[f"{{{ns['r']}}}id"]

    rels_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    relation = next((item for item in rels_root.findall("rel:Relationship", ns) if item.attrib.get("Id") == rel_id), None)
    if relation is None:
        raise ValueError(f"No se encontro la relacion de la hoja {sheet_name!r}.")
    target = relation.attrib["Target"]
    return f"xl/{target}" if not target.startswith("/") else target.lstrip("/")


def read_cell_value(cell: ET.Element, shared_strings: list[str]) -> Any:
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    cell_type = cell.attrib.get("t")
    value_node = cell.find("a:v", ns)

    if cell_type == "inlineStr":
        text_node = cell.find(".//a:t", ns)
        return text_node.text if text_node is not None else None
    if value_node is None:
        return None
    raw = value_node.text
    if raw is None:
        return None
    if cell_type == "s":
        return shared_strings[int(raw)]
    return raw


def cell_ref_to_position(ref: str) -> tuple[int, int]:
    match = re.fullmatch(r"([A-Z]+)(\d+)", ref)
    if not match:
        raise ValueError(f"Referencia de celda no valida: {ref}")
    letters, row = match.groups()
    column = 0
    for letter in letters:
        column = column * 26 + (ord(letter) - ord("A") + 1)
    return int(row), column


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split()).strip()


def normalize_periodicity(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized not in PERIODICITY_MAP:
        return "on_demand"
    return PERIODICITY_MAP[normalized]


def unique_in_order(values: Any) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def title_case(value: str) -> str:
    keep_upper = {"gas"}
    words = []
    for word in value.split():
        words.append(word.upper() if word.casefold() in keep_upper else word.capitalize())
    return " ".join(words)


if __name__ == "__main__":
    main()
