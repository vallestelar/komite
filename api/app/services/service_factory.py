from __future__ import annotations

from typing import Type

from tortoise.models import Model

from app.dbs.postgres.generic_repository import GenericRepository
from app.services.generic_service import GenericService


class ServiceFactory:
    def __init__(self):
        self._cache: dict[Type[Model], GenericService] = {}

    def get(self, model: Type[Model]) -> GenericService:
        if model not in self._cache:
            self._cache[model] = GenericService(GenericRepository(model))
        return self._cache[model]


service_factory = ServiceFactory()

