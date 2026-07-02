from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Iterable, List, Optional, Sequence, Type, TypeVar

from tortoise.expressions import Q
from tortoise.models import Model
from tortoise.queryset import QuerySet
from uuid6 import uuid7

T = TypeVar("T", bound=Model)


@dataclass
class PageResult(Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class GenericRepository(Generic[T]):
    def __init__(self, model: Type[T], *, default_filters: Optional[dict[str, Any]] = None):
        self.model = model
        self.default_filters = default_filters or {}

    @property
    def pk_name(self) -> str:
        return self.model._meta.pk_attr

    def _base_qs(self) -> QuerySet[T]:
        return self.model.all()

    def _apply_filters(self, qs: QuerySet[T], *q: Q, **filters: Any) -> QuerySet[T]:
        merged = {**self.default_filters, **filters}
        return qs.filter(*q, **merged) if q or merged else qs

    async def create(self, **data: Any) -> T:
        if "id" not in data:
            data["id"] = uuid7()
        return await self.model.create(**data)

    async def get(self, pk: Any) -> Optional[T]:
        return await self.model.get_or_none(**{self.pk_name: pk}, **self.default_filters)

    async def update(self, pk: Any, **data: Any) -> Optional[T]:
        obj = await self.get(pk)
        if not obj:
            return None
        for key, value in data.items():
            setattr(obj, key, value)
        await obj.save()
        return obj

    async def delete(self, pk: Any) -> int:
        return await self.model.filter(**{self.pk_name: pk}, **self.default_filters).delete()

    async def list(
        self,
        *q: Q,
        order_by: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        **filters: Any,
    ) -> List[T]:
        qs = self._apply_filters(self._base_qs(), *q, **filters)
        if order_by:
            qs = qs.order_by(*order_by)
        if offset:
            qs = qs.offset(offset)
        if limit:
            qs = qs.limit(limit)
        return await qs

    async def list_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        *q: Q,
        order_by: Optional[Sequence[str]] = None,
        **filters: Any,
    ) -> PageResult[T]:
        page = max(page, 1)
        page_size = max(page_size, 1)
        qs = self._apply_filters(self._base_qs(), *q, **filters)
        if order_by:
            qs = qs.order_by(*order_by)

        total = await qs.count()
        items = await qs.offset((page - 1) * page_size).limit(page_size)
        pages = (total + page_size - 1) // page_size
        return PageResult(items=items, total=total, page=page, page_size=page_size, pages=pages)

    async def add_m2m(self, instance: T, relation: str, targets: Iterable[Model]) -> None:
        await getattr(instance, relation).add(*targets)

