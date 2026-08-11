import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Calculate base directories
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
ROOT_DIR = BACKEND_DIR.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "DeepGuard"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-Based Deepfake & Digital Media Authenticity Verification System"
    
    # Directory Paths
    PROJECT_ROOT: Path = ROOT_DIR
    UPLOAD_DIR: Path = ROOT_DIR / "uploads"
    RESULTS_DIR: Path = ROOT_DIR / "results"
    
    # File Upload Limits
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_UPLOAD_SIZE_BYTES: int = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    ALLOWED_IMAGE_EXTENSIONS: list[str] = [".jpg", ".jpeg", ".png", ".webp"]
    ALLOWED_VIDEO_EXTENSIONS: list[str] = [".mp4", ".mov", ".avi"]
    
    # Configurable Classification Thresholds (Manipulation Probability %)
    AUTHENTIC_THRESHOLD: float = 30.0
    SUSPICIOUS_THRESHOLD: float = 70.0
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR}/deepguard.db")
    
    # AI Model Settings
    MODEL_PATH: Path = APP_DIR / "weights" / "deepfake_detector.pth"
    VIDEO_FRAME_SAMPLE_INTERVAL: int = 30  # Extract frame every N frames
    MAX_VIDEO_FRAMES_TO_ANALYZE: int = 30  # Limit max frames

settings = Settings()

# Ensure required directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

