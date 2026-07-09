from .audio_router import router as audio_router
from .auth_router import router as auth_router
from .backoffice_router import router as backoffice_router
from .comunidad_feliz_router import router as comunidad_feliz_router
from .edifito_router import router as edifito_router
from .entities_router import entity_routers
from .inspection_templates_router import router as inspection_templates_router
from .portal_assemblies_router import router as portal_assemblies_router
from .portal_inspections_router import router as portal_inspections_router
from .portal_maintenance_router import router as portal_maintenance_router
from .portal_neighbors_router import router as portal_neighbors_router
from .portal_operational_plan_router import router as portal_operational_plan_router
from .portal_team_router import router as portal_team_router
from .user_router import router as user_router

all_routers = [
    audio_router,
    auth_router,
    backoffice_router,
    comunidad_feliz_router,
    edifito_router,
    inspection_templates_router,
    portal_assemblies_router,
    portal_inspections_router,
    portal_maintenance_router,
    portal_neighbors_router,
    portal_operational_plan_router,
    portal_team_router,
    user_router,
    *entity_routers,
]
