from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Sequence, Type
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from tortoise.exceptions import IntegrityError
from tortoise.expressions import Q
from tortoise.models import Model
from pydantic import BaseModel

from app.core.auth.dependencies import require_access_token, require_komite_employee, user_is_komite_employee
from app.models.entities import Communication, Condominium, Incident, Inspection, Report, Task
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


async def _read_filters(model: Type[Model], request: Request) -> dict[str, Any]:
    if await user_is_komite_employee(request.state.user):
        return {}

    db_fields = set(model._meta.db_fields)
    company_id = request.state.company_id
    active_condominium_id = request.state.condominium_id
    allowed_condominium_ids = [
        str(item.get("id"))
        for item in getattr(request.state, "condominiums", [])
        if isinstance(item, dict) and item.get("id")
    ]

    if model.__name__ == "Company":
        return {"id": company_id} if company_id else {"id__isnull": True}

    if model.__name__ == "Condominium":
        return {"id__in": allowed_condominium_ids}

    if "condominium_id" in db_fields:
        if active_condominium_id:
            return {"condominium_id": active_condominium_id}
        return {"condominium_id__in": allowed_condominium_ids}

    if "company_id" in db_fields:
        return {"company_id": company_id} if company_id else {"company_id__isnull": True}

    return {}


async def _derive_company_id(data: dict[str, Any]) -> Any:
    if data.get("company_id"):
        return data["company_id"]

    if data.get("condominium_id"):
        condominium = await Condominium.get_or_none(id=data["condominium_id"])
        return condominium.company_id if condominium else None

    parent_lookups = (
        ("incident_id", Incident),
        ("task_id", Task),
        ("inspection_id", Inspection),
        ("report_id", Report),
        ("communication_id", Communication),
    )
    for field_name, parent_model in parent_lookups:
        if data.get(field_name):
            parent = await parent_model.get_or_none(id=data[field_name])
            return getattr(parent, "company_id", None) if parent else None

    return None


async def _with_tenant_data(
    model: Type[Model],
    data: dict[str, Any],
    request: Request,
    *,
    default_to_request_company: bool,
) -> dict[str, Any]:
    db_fields = set(model._meta.db_fields)
    if "company_id" not in db_fields:
        return data

    company_id = await _derive_company_id(data)
    if company_id:
        data["company_id"] = company_id
    elif default_to_request_company and request.state.company_id:
        data["company_id"] = request.state.company_id

    if not await user_is_komite_employee(request.state.user):
        if not request.state.company_id or str(data.get("company_id")) != str(request.state.company_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El registro no pertenece a tu empresa",
            )

    return data


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
    router = APIRouter(prefix=prefix, tags=[tag])

    async def get_service():
        return service_factory.get(model)

    async def create_item(
        request: Request,
        payload=Body(...),
        svc=Depends(get_service),
    ):
        try:
            data = await _with_tenant_data(
                model,
                payload.model_dump(),
                request,
                default_to_request_company=True,
            )
            obj = await svc.create(**data)
            return response_schema(**serialize_model(obj))
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Conflicto de integridad: {exc}",
            )

    async def list_items(
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=200),
        q: str | None = Query(None),
        order_by: list[str] | None = Query(None),
        svc=Depends(get_service),
    ):
        search_q = _search_query(q, search_fields)
        q_args = [search_q] if search_q is not None else []
        filters = await _read_filters(model, request)
        result = await svc.list_paginated(
            page,
            page_size,
            *q_args,
            order_by=order_by,
            **filters,
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

    async def get_item(request: Request, obj_id: UUID, svc=Depends(get_service)):
        filters = await _read_filters(model, request)
        pk_name = model._meta.pk_attr
        if pk_name in filters and str(filters[pk_name]) != str(obj_id):
            obj = None
        else:
            query_filters = {**filters, pk_name: obj_id}
            items = await svc.list(limit=1, **query_filters)
            obj = items[0] if items else None
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{tag} no encontrado",
            )
        return response_schema(**serialize_model(obj))

    async def update_item(
        request: Request,
        obj_id: UUID,
        payload=Body(...),
        svc=Depends(get_service),
    ):
        try:
            data = await _with_tenant_data(
                model,
                payload.model_dump(exclude_unset=True),
                request,
                default_to_request_company=False,
            )
            obj = await svc.update(obj_id, **data)
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

    write_dependencies = [Depends(require_komite_employee())]
    read_dependencies = [Depends(require_access_token())]

    router.add_api_route("/", create_item, methods=["POST"], response_model=response_schema, status_code=status.HTTP_201_CREATED, dependencies=write_dependencies)
    router.add_api_route("/", list_items, methods=["GET"], response_model=page_schema, dependencies=read_dependencies)
    router.add_api_route("/{obj_id}", get_item, methods=["GET"], response_model=response_schema, dependencies=read_dependencies)
    router.add_api_route("/{obj_id}", update_item, methods=["PATCH"], response_model=response_schema, dependencies=write_dependencies)
    router.add_api_route("/{obj_id}", delete_item, methods=["DELETE"], dependencies=write_dependencies)

    return router
