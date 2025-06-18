from fastapi import APIRouter
from app.services.health_service import perform_health_check
from app.models.health import HealthResponse

router = APIRouter()

@router.get(
    "/health",
    summary="Check backend health",
    description="Returns health status of the PitchPilot backend.",
    response_model=HealthResponse,
    tags=["System"]
)
async def health_check():
    return perform_health_check()
