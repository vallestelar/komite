from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PromptTemplate:
    key: str
    name: str
    purpose: str
    system_template: str
    user_template: str
    required_variables: tuple[str, ...] = ()
    optional_variables: tuple[str, ...] = ()
    default_temperature: float = 0.2
    default_max_tokens: int | None = None
    expects_json: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class _SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return ""


PROMPT_TEMPLATES: dict[str, PromptTemplate] = {
    "operational_report_draft": PromptTemplate(
        key="operational_report_draft",
        name="Borrador de informe operativo",
        purpose="operational_report_draft",
        required_variables=("event_title", "condominium_name"),
        optional_variables=("event_description", "execution_comments", "asset_name", "evidence_summary", "asset_history"),
        system_template=(
            "Eres Komite, un asistente operativo para administracion de condominios en Chile. "
            "Redactas informes verificables, sobrios y utiles para administradores, comites y proveedores. "
            "No inventes datos. Si falta informacion, dejala marcada como pendiente."
        ),
        user_template=(
            "Genera un borrador profesional para un informe de servicio.\n\n"
            "Condominio: {condominium_name}\n"
            "Trabajo: {event_title}\n"
            "Activo/equipo: {asset_name}\n"
            "Descripcion programada: {event_description}\n"
            "Comentarios de ejecucion: {execution_comments}\n"
            "Evidencias: {evidence_summary}\n"
            "Historial del activo: {asset_history}\n\n"
            "Devuelve secciones: resumen ejecutivo, trabajos realizados, incidencias detectadas, recomendaciones y pendientes de validacion."
        ),
        default_max_tokens=1800,
    ),
    "incident_summary": PromptTemplate(
        key="incident_summary",
        name="Resumen de incidencia",
        purpose="incident_summary",
        required_variables=("incident_text",),
        optional_variables=("condominium_name", "category", "history"),
        system_template=(
            "Eres Komite. Transformas reportes desordenados de incidencias en resumenes claros, accionables y sin exagerar."
        ),
        user_template=(
            "Resume esta incidencia para gestion interna.\n\n"
            "Condominio: {condominium_name}\n"
            "Categoria: {category}\n"
            "Historial relevante: {history}\n"
            "Texto original: {incident_text}\n\n"
            "Incluye: problema, impacto probable, urgencia sugerida, accion inmediata y datos faltantes."
        ),
        default_max_tokens=1200,
    ),
    "committee_message": PromptTemplate(
        key="committee_message",
        name="Comunicado al comite",
        purpose="committee_message",
        required_variables=("topic", "facts"),
        optional_variables=("tone", "next_steps", "condominium_name"),
        system_template=(
            "Eres Komite. Redactas comunicaciones para comites de administracion de condominios. "
            "Usa tono profesional, directo y transparente."
        ),
        user_template=(
            "Redacta un comunicado para el comite.\n\n"
            "Condominio: {condominium_name}\n"
            "Tema: {topic}\n"
            "Hechos confirmados: {facts}\n"
            "Proximos pasos: {next_steps}\n"
            "Tono deseado: {tone}\n\n"
            "No agregues hechos no confirmados."
        ),
        default_max_tokens=1000,
    ),
    "maintenance_recommendations": PromptTemplate(
        key="maintenance_recommendations",
        name="Recomendaciones de mantencion",
        purpose="maintenance_recommendations",
        required_variables=("asset_name", "observations"),
        optional_variables=("asset_type", "maintenance_history", "condominium_name"),
        system_template=(
            "Eres Komite. Ayudas a priorizar mantenciones de edificios residenciales con criterio operacional y preventivo."
        ),
        user_template=(
            "Propone recomendaciones para el activo indicado.\n\n"
            "Condominio: {condominium_name}\n"
            "Activo: {asset_name}\n"
            "Tipo: {asset_type}\n"
            "Observaciones: {observations}\n"
            "Historial: {maintenance_history}\n\n"
            "Ordena las recomendaciones por prioridad y separa acciones inmediatas, preventivas y datos a levantar."
        ),
        default_max_tokens=1400,
    ),
    "accounting_expense_summary": PromptTemplate(
        key="accounting_expense_summary",
        name="Resumen contable de gastos",
        purpose="accounting_expense_summary",
        required_variables=("expenses",),
        optional_variables=("period_name", "condominium_name"),
        system_template=(
            "Eres Komite. Explicas gastos comunes de forma clara para administracion y comite, sin emitir asesoria legal ni tributaria."
        ),
        user_template=(
            "Resume los gastos del periodo.\n\n"
            "Condominio: {condominium_name}\n"
            "Periodo: {period_name}\n"
            "Gastos: {expenses}\n\n"
            "Incluye principales categorias, variaciones llamativas, proveedores relevantes y puntos a revisar."
        ),
        default_max_tokens=1400,
    ),
    "generic_assistant": PromptTemplate(
        key="generic_assistant",
        name="Asistente general Komite",
        purpose="generic_assistant",
        required_variables=("prompt",),
        system_template=(
            "Eres Komite, un asistente para equipos que administran condominios. Responde de forma util, concreta y verificable."
        ),
        user_template="{prompt}",
        default_max_tokens=1600,
    ),
}


def list_prompt_templates() -> list[PromptTemplate]:
    return list(PROMPT_TEMPLATES.values())


def get_prompt_template(key: str) -> PromptTemplate:
    try:
        return PROMPT_TEMPLATES[key]
    except KeyError:
        allowed = ", ".join(sorted(PROMPT_TEMPLATES))
        raise ValueError(f"Prompt no registrado: {key}. Prompts disponibles: {allowed}")


def render_prompt(template: PromptTemplate, variables: dict[str, Any]) -> list[dict[str, str]]:
    missing = [key for key in template.required_variables if variables.get(key) in (None, "")]
    if missing:
        raise ValueError(f"Faltan variables requeridas para {template.key}: {', '.join(missing)}")

    clean_variables = _SafeFormatDict({key: _stringify(value) for key, value in variables.items()})
    return [
        {"role": "system", "content": template.system_template.format_map(clean_variables)},
        {"role": "user", "content": template.user_template.format_map(clean_variables)},
    ]


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set)):
        return "\n".join(f"- {_stringify(item)}" for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{key}: {_stringify(item)}" for key, item in value.items())
    return str(value)
