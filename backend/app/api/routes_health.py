from fastapi import APIRouter
from app.config import settings
from app.schemas.analysis import HealthResponse
from app.services.deepfake_detector import detector_instance

router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def get_health_status():
    """System health check and configuration status."""
    return HealthResponse(
        status="ok",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        ai_model_status=detector_instance.get_status(),
        supported_image_formats=settings.ALLOWED_IMAGE_EXTENSIONS,
        supported_video_formats=settings.ALLOWED_VIDEO_EXTENSIONS
    )
