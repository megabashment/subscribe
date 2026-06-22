from fastapi import APIRouter
from subscribe import __version__
from subscribe.utils.device import detect_device
import subscribe.transcribe as transcribe_mod
from api.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        device=detect_device(),
        version=__version__,
        compute_type=transcribe_mod.last_compute_type,
    )
