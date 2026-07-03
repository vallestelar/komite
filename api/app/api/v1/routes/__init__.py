from .audio_router import router as audio_router
from .auth_router import router as auth_router
from .comunidad_feliz_router import router as comunidad_feliz_router
from .edifito_router import router as edifito_router
from .entities_router import entity_routers
from .user_router import router as user_router

all_routers = [
    audio_router,
    auth_router,
    comunidad_feliz_router,
    edifito_router,
    user_router,
    *entity_routers,
]
