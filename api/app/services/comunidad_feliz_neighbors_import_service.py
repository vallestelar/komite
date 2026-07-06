from __future__ import annotations

import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Any

from openpyxl import load_workbook

from app.models.entities import Unit, UnitContact


class ComunidadFelizNeighborsImportService:
    relationship_resident = "residente"

    async def import_charges(
        self,
        *,
        company_id: str | None,
        condominium_id: str,
        content: bytes,
    ) -> dict[str, Any]:
        rows = self._read_rows(content)
        summary = self._empty_summary(rows)
        details: list[dict[str, str]] = []

        for row in rows:
            unit, created_unit = await self._upsert_unit(company_id, condominium_id, row)
            summary["units_created" if created_unit else "units_updated"] += 1

            full_name = self._clean(row.get("resident_name"))
            if not full_name:
                continue

            contact, created_contact = await self._upsert_resident_contact(
                company_id=company_id,
                condominium_id=condominium_id,
                unit=unit,
                full_name=full_name,
                row=row,
            )
            summary["contacts_created" if created_contact else "contacts_updated"] += 1
            summary["users_skipped"] += 1
            details.append(
                {
                    "unit": unit.identifier,
                    "relationship_type": contact.relationship_type,
                    "full_name": contact.full_name,
                    "status": "creado" if created_contact else "actualizado",
                }
            )

        return {"summary": summary, "items": details[:200]}

    async def preview_charges(
        self,
        *,
        company_id: str | None,
        condominium_id: str,
        content: bytes,
    ) -> dict[str, Any]:
        rows = self._read_rows(content)
        summary = self._empty_summary(rows)
        details: list[dict[str, str]] = []

        for row in rows:
            identifier = self._clean(row.get("uco")) or "Sin identificador"
            unit = await Unit.get_or_none(condominium_id=condominium_id, identifier=identifier)
            summary["units_updated" if unit else "units_created"] += 1

            full_name = self._clean(row.get("resident_name"))
            if not full_name:
                continue

            existing_contact = await self._find_resident_contact(unit, full_name) if unit else None
            contact_status = "updated" if existing_contact else "created"
            summary[f"contacts_{contact_status}"] += 1
            summary["users_skipped"] += 1
            details.append(
                {
                    "unit": identifier,
                    "relationship_type": self.relationship_resident,
                    "full_name": full_name,
                    "status": "se va a crear" if contact_status == "created" else "se va a actualizar",
                }
            )

        return {"summary": summary, "items": details[:200]}

    def _empty_summary(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        return {
            "rows": len(rows),
            "units_created": 0,
            "units_updated": 0,
            "contacts_created": 0,
            "contacts_updated": 0,
            "contacts_skipped": 0,
            "users_created": 0,
            "users_updated": 0,
            "users_skipped": 0,
        }

    def _read_rows(self, content: bytes) -> list[dict[str, Any]]:
        workbook = load_workbook(BytesIO(content), data_only=True, read_only=True)
        sheet = workbook["Gastos comunes"] if "Gastos comunes" in workbook.sheetnames else workbook[workbook.sheetnames[0]]
        header_row = self._find_header_row(sheet)
        headers = [self._cell_text(cell.value) for cell in sheet[header_row]]
        indexes = self._build_indexes(headers)

        required = ["unidad", "residente"]
        if any(indexes.get(name) is None for name in required):
            raise ValueError("El informe no tiene las columnas Unidad y Residente esperadas.")

        rows: list[dict[str, Any]] = []
        for raw in sheet.iter_rows(min_row=header_row + 1, values_only=True):
            unit = self._value(raw, indexes["unidad"])
            unit_text = self._clean(unit)
            if not unit_text or unit_text.casefold() == "total":
                continue

            rows.append(
                {
                    "uco": unit_text,
                    "resident_name": self._cell_text(self._value(raw, indexes.get("residente"))),
                    "proration": self._value(raw, indexes.get("prorrateo")),
                    "month_total": self._value(raw, indexes.get("total_mes")),
                    "past_due_capital": self._value(raw, indexes.get("capital_atrasado")),
                    "interests_and_fines": self._value(raw, indexes.get("intereses_multas")),
                    "payments": self._value(raw, indexes.get("abonos")),
                    "charged_total": self._value(raw, indexes.get("total_cobrado")),
                    "credit_balance": self._value(raw, indexes.get("saldo_favor")),
                    "source_period": self._detect_period(sheet),
                }
            )

        if not rows:
            raise ValueError("El informe de Comunidad Feliz no contiene filas para importar.")
        return rows

    async def _upsert_unit(self, company_id: str | None, condominium_id: str, row: dict[str, Any]) -> tuple[Unit, bool]:
        identifier = self._clean(row.get("uco")) or "Sin identificador"
        unit = await Unit.get_or_none(condominium_id=condominium_id, identifier=identifier)
        created = unit is None
        if not unit:
            unit = Unit(company_id=company_id, condominium_id=condominium_id, identifier=identifier)

        unit.company_id = company_id
        unit.external_code = identifier
        unit.unit_type = "apartment"
        unit.proration_total = self._decimal_or_none(row.get("proration"))
        unit.proration = self._decimal_or_none(row.get("proration"))
        unit.metadata = {
            **(unit.metadata or {}),
            "comunidad_feliz": {
                "period": row.get("source_period"),
                "month_total": self._number_or_none(row.get("month_total")),
                "past_due_capital": self._number_or_none(row.get("past_due_capital")),
                "interests_and_fines": self._number_or_none(row.get("interests_and_fines")),
                "payments": self._number_or_none(row.get("payments")),
                "charged_total": self._number_or_none(row.get("charged_total")),
                "credit_balance": self._number_or_none(row.get("credit_balance")),
            },
        }
        await unit.save()
        return unit, created

    async def _upsert_resident_contact(
        self,
        *,
        company_id: str | None,
        condominium_id: str,
        unit: Unit,
        full_name: str,
        row: dict[str, Any],
    ) -> tuple[UnitContact, bool]:
        contact = await self._find_resident_contact(unit, full_name)
        created = contact is None
        if not contact:
            contact = UnitContact(
                company_id=company_id,
                condominium_id=condominium_id,
                unit=unit,
                relationship_type=self.relationship_resident,
                full_name=full_name,
            )

        contact.company_id = company_id
        contact.condominium_id = condominium_id
        contact.unit = unit
        contact.full_name = full_name
        contact.relationship_type = self.relationship_resident
        contact.is_primary_contact = contact.is_primary_contact or False
        if created:
            contact.receives_notifications = False
        contact.status = "active"
        contact.metadata = {
            **(contact.metadata or {}),
            "source": "comunidad_feliz",
            "source_period": row.get("source_period"),
        }
        await contact.save()
        return contact, created

    async def _find_resident_contact(self, unit: Unit | None, full_name: str) -> UnitContact | None:
        if not unit:
            return None
        return await UnitContact.get_or_none(
            unit_id=unit.id,
            relationship_type=self.relationship_resident,
            full_name=full_name,
        )

    def _find_header_row(self, sheet) -> int:
        for index, row in enumerate(sheet.iter_rows(), start=1):
            normalized = {self._normalize_header(self._cell_text(cell.value)) for cell in row}
            if {"unidad", "residente"}.issubset(normalized):
                return index
        raise ValueError("No se encontró la cabecera del informe de Comunidad Feliz.")

    def _build_indexes(self, headers: list[str]) -> dict[str, int | None]:
        groups: dict[str, list[int]] = {}
        for index, header in enumerate(headers):
            normalized = self._normalize_header(header)
            groups.setdefault(normalized, []).append(index)

        def idx(name: str) -> int | None:
            values = groups.get(self._normalize_header(name), [])
            return values[0] if values else None

        return {
            "unidad": idx("Unidad"),
            "residente": idx("Residente"),
            "prorrateo": idx("Prorrateo"),
            "total_mes": idx("Total mes"),
            "capital_atrasado": idx("Capital Atrasado"),
            "intereses_multas": idx("Intereses y multas"),
            "abonos": idx("Abonos"),
            "total_cobrado": idx("Total cobrado"),
            "saldo_favor": idx("Saldo a favor"),
        }

    def _detect_period(self, sheet) -> str | None:
        for row in sheet.iter_rows(min_row=1, max_row=min(sheet.max_row, 4), values_only=True):
            for value in row:
                text = self._cell_text(value)
                if text.casefold().startswith("gastos comunes"):
                    return text
        return None

    def _value(self, row: tuple[Any, ...], index: int | None) -> Any:
        if index is None or index >= len(row):
            return None
        return row[index]

    def _cell_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value).strip()

    def _normalize_header(self, value: str) -> str:
        text = unicodedata.normalize("NFKD", value)
        return "".join(ch for ch in text.casefold() if ch.isalnum() and not unicodedata.combining(ch))

    def _clean(self, value: Any) -> str | None:
        text = self._cell_text(value)
        return text if text else None

    def _decimal_or_none(self, value: Any) -> Decimal | None:
        text = self._clean(value)
        if not text:
            return None
        try:
            return Decimal(text.replace(",", "."))
        except (InvalidOperation, ValueError):
            return None

    def _number_or_none(self, value: Any) -> int | float | None:
        if value is None or value == "":
            return None
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (int, float)):
            return value
        try:
            number = Decimal(str(value).replace(",", "."))
        except (InvalidOperation, ValueError):
            return None
        return int(number) if number == number.to_integral_value() else float(number)
