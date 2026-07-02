from __future__ import annotations

from typing import Any, Generic, Optional, Sequence, TypeVar

from tortoise.expressions import Q
from tortoise.models import Model

from app.dbs.postgres.generic_repository import GenericRepository, PageResult

T = TypeVar("T", bound=Model)


class GenericService(Generic[T]):
    def __init__(self, repository: GenericRepository[T]):
        self.repository = repository

    async def create(self, **data: Any) -> T:
        return await self.repository.create(**data)

    async def get(self, pk: Any) -> Optional[T]:
        return await self.repository.get(pk)

    async def update(self, pk: Any, **data: Any) -> Optional[T]:
        return await self.repository.update(pk, **data)

    async def delete(self, pk: Any) -> int:
        return await self.repository.delete(pk)

    async def list(
        self,
        *q: Q,
        order_by: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        **filters: Any,
    ) -> list[T]:
        return await self.repository.list(*q, order_by=order_by, limit=limit, offset=offset, **filters)

    async def list_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        *q: Q,
        order_by: Optional[Sequence[str]] = None,
        **filters: Any,
    ) -> PageResult[T]:
        return await self.repository.list_paginated(
            page,
            page_size,
            *q,
            order_by=order_by,
            **filters,
        )
