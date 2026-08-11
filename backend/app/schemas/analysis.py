from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict

class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    ai_model_status: str
    supported_image_formats: List[str]
    supported_video_formats: List[str]

class AnalysisResponse(BaseModel):
    id: str
    filename: str
    stored_filename: str
    file_type: str
    mime_type: Optional[str] = None
    file_size: int
    result: str
    confidence_score: float
    ai_score: Optional[float] = None
    ai_model_status: str
    metadata_score: float
    forensic_score: float
    frames_analyzed: int = 0
    faces_detected: int = 0
    suspicious_frames: int = 0
    status: str
    explanations: List[str] = []
    metadata_info: Dict[str, Any] = {}
    forensics_info: Dict[str, Any] = {}
    ela_image_url: Optional[str] = None
    media_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AnalysisListItem(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    result: str
    confidence_score: float
    ai_model_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DeleteResponse(BaseModel):
    message: str
    id: str
