from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Sequence, Type
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from tortoise.exceptions import IntegrityError
from tortoise.expressions import Q
from tortoise.models import Model
from pydantic import BaseModel

from app.core.auth.dependencies import require_komite_employee
from app.services.service_factory import service_factory


def _jsonable(value: Any) -> Any:
    if isinstance(value, UUID) or value.__class__.__name__ == "UUID":
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def serialize_model(obj: Model) -> dict[str, Any]:
    data: dict[str, Any] = {}

    for field_name in obj._meta.db_fields:
        if hasattr(obj, field_name):
            data[field_name] = _jsonable(getattr(obj, field_name))

    return data


def _search_query(search: str | None, search_fields: Sequence[str]) -> Q | None:
    if not search or not search_fields:
        return None

    query: Q | None = None
    for field in search_fields:
        item = Q(**{f"{field}__icontains": search})
        query = item if query is None else query | item
    return query


def create_crud_router(
    *,
    model: Type[Model],
    prefix: str,
    tag: str,
    create_schema: Type[BaseModel],
    update_schema: Type[BaseModel],
    response_schema: Type[BaseModel],
    page_schema: Type[BaseModel],
    search_fields: Sequence[str] = (),
) -> APIRouter:
    router = APIRouter(
        prefix=prefix,
        tags=[tag],
        dependencies=[Depends(require_komite_employee())],
    )

    async def get_service():
        return service_factory.get(model)

    async def create_item(
        payload=Body(...),
        svc=Depends(get_service),
    ):
        try:
            obj = await svc.create(**payload.model_dump())
            return response_schema(**serialize_model(obj))
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Conflicto de integridad: {exc}",
            )

    async def list_items(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=200),
        q: str | None = Query(None),
        order_by: list[str] | None = Query(None),
        svc=Depends(get_service),
    ):
        search_q = _search_query(q, search_fields)
        q_args = [search_q] if search_q is not None else []
        result = await svc.list_paginated(
            page,
            page_size,
            *q_args,
            order_by=order_by,
        )
        return {
            "items": [response_schema(**serialize_model(item)) for item in result.items],
            "meta": {
                "total": result.total,
                "page": result.page,
                "page_size": result.page_size,
                "pages": result.pages,
            },
        }

    async def get_item(obj_id: UUID, svc=Depends(get_service)):
        obj = await svc.get(obj_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{tag} no encontrado",
            )
        return response_schema(**serialize_model(obj))

    async def update_item(
        obj_id: UUID,
        payload=Body(...),
        svc=Depends(get_service),
    ):
        try:
            obj = await svc.update(obj_id, **payload.model_dump(exclude_unset=True))
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Conflicto de integridad: {exc}",
            )

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{tag} no encontrado",
            )
        return response_schema(**serialize_model(obj))

    async def delete_item(obj_id: UUID, svc=Depends(get_service)):
        deleted = await svc.delete(obj_id)
        if deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{tag} no encontrado",
            )
        return {"deleted": deleted}

    create_item.__annotations__["payload"] = create_schema
    create_item.__annotations__["return"] = response_schema
    list_items.__annotations__["return"] = page_schema
    get_item.__annotations__["return"] = response_schema
    update_item.__annotations__["payload"] = update_schema
    update_item.__annotations__["return"] = response_schema

    router.add_api_route("/", create_item, methods=["POST"], response_model=response_schema, status_code=status.HTTP_201_CREATED)
    router.add_api_route("/", list_items, methods=["GET"], response_model=page_schema)
    router.add_api_route("/{obj_id}", get_item, methods=["GET"], response_model=response_schema)
    router.add_api_route("/{obj_id}", update_item, methods=["PATCH"], response_model=response_schema)
    router.add_api_route("/{obj_id}", delete_item, methods=["DELETE"])

    return router
