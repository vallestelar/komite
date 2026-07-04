from fastapi import APIRouter, Depends

from app.api.v1.crud_router_factory import serialize_model
from app.core.auth.dependencies import require_komite_employee
from app.models.entities import Company, Condominium, SupportTicket


router = APIRouter(prefix="/api/v1/backoffice", tags=["Backoffice"])


@router.get("/dashboard", dependencies=[Depends(require_komite_employee())])
async def dashboard_data() -> dict:
    companies = await Company.all().order_by("name")
    condominiums = await Condominium.all().order_by("name")
    tickets = await SupportTicket.all().order_by("-created_at")

    return {
        "companies": [serialize_model(item) for item in companies],
        "condominiums": [serialize_model(item) for item in condominiums],
        "tickets": [serialize_model(item) for item in tickets],
    }
