from fastapi import APIRouter
from subscribe import __version__
from subscribe.utils.device import detect_device
from api.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        device=detect_device(),
        version=__version__,
    )
