from .audio_router import router as audio_router
from .ai_router import router as ai_router
from .ai_prompt_templates_router import router as ai_prompt_templates_router
from .auth_router import router as auth_router
from .backoffice_router import router as backoffice_router
from .comunidad_feliz_router import router as comunidad_feliz_router
from .company_logo_router import router as company_logo_router
from .edifito_router import router as edifito_router
from .entities_router import entity_routers
from .external_service_orders_router import portal_router as external_service_orders_portal_router
from .external_service_orders_router import public_router as external_service_orders_public_router
from .inspection_templates_router import router as inspection_templates_router
from .portal_assemblies_router import router as portal_assemblies_router
from .portal_accounting_router import router as portal_accounting_router
from .portal_inspections_router import router as portal_inspections_router
from .portal_maintenance_router import router as portal_maintenance_router
from .portal_neighbors_router import router as portal_neighbors_router
from .portal_notifications_router import router as portal_notifications_router
from .portal_operational_plan_router import router as portal_operational_plan_router
from .portal_reports_router import router as portal_reports_router
from .portal_team_router import router as portal_team_router
from .residence_certificate_router import router as residence_certificate_router
from .signature_assets_router import router as signature_assets_router
from .user_router import router as user_router

all_routers = [
    ai_router,
    ai_prompt_templates_router,
    audio_router,
    auth_router,
    backoffice_router,
    comunidad_feliz_router,
    company_logo_router,
    edifito_router,
    external_service_orders_portal_router,
    external_service_orders_public_router,
    inspection_templates_router,
    portal_accounting_router,
    portal_assemblies_router,
    portal_inspections_router,
    portal_maintenance_router,
    portal_neighbors_router,
    portal_notifications_router,
    portal_operational_plan_router,
    portal_reports_router,
    portal_team_router,
    residence_certificate_router,
    signature_assets_router,
    user_router,
    *entity_routers,
]
