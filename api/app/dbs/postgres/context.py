from tortoise import Tortoise
from tortoise.exceptions import ConfigurationError

from app.core.settings import settings


class DbContext:
    def __init__(self):
        self.tortoise_config = {
            "connections": {
                "default": {
                    "engine": "tortoise.backends.asyncpg",
                    "credentials": {
                        "host": settings.postgres_host,
                        "port": settings.postgres_port,
                        "user": settings.postgres_user,
                        "password": settings.postgres_password,
                        "database": settings.postgres_db,
                        "minsize": 1,
                        "maxsize": 5,
                        "timeout": 10,
                    },
                }
            },
            "apps": {
                "models": {
                    "models": ["app.models.entities", "aerich.models"],
                    "default_connection": "default",
                }
            },
        }

    async def init(self, generate_schemas: bool = False):
        await Tortoise.init(config=self.tortoise_config)
        if generate_schemas:
            await Tortoise.generate_schemas()

    async def close(self):
        try:
            await Tortoise.close_connections()
        except ConfigurationError:
            return

    def get_connection(self):
        return Tortoise.get_connection("default")

    async def check_connection(self) -> dict:
        try:
            await self.get_connection().execute_query("SELECT 1")
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": f"Database connection failed: {exc}"}
