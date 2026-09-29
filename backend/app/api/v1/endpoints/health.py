from fastapi import APIRouter
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Health check endpoint to verify backend operational status."""
    return HealthResponse(
        status="ok",
        service="sanjeevani-grid-backend",
    )
