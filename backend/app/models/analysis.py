import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from app.database import Base

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # 'image' or 'video'
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=False)
    
    # Analysis Classification Output
    result = Column(String(50), nullable=False)  # 'LIKELY AUTHENTIC', 'SUSPICIOUS', 'LIKELY AI-GENERATED'
    confidence_score = Column(Float, nullable=False)  # 0.0 to 100.0
    
    # Sub-scores
    ai_score = Column(Float, nullable=True)
    ai_model_status = Column(String(50), nullable=False, default="Not Configured")  # 'Available' or 'Not Configured'
    metadata_score = Column(Float, nullable=False, default=0.0)
    forensic_score = Column(Float, nullable=False, default=0.0)
    
    # Video Metrics
    frames_analyzed = Column(Integer, nullable=False, default=0)
    faces_detected = Column(Integer, nullable=False, default=0)
    suspicious_frames = Column(Integer, nullable=False, default=0)
    
    # Details & JSON payload dumps
    status = Column(String(20), nullable=False, default="completed")
    explanations_json = Column(Text, nullable=True)  # JSON string list
    metadata_info_json = Column(Text, nullable=True)  # JSON dict
    forensics_info_json = Column(Text, nullable=True)  # JSON dict
    ela_image_path = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<Analysis {self.id} - {self.filename} - {self.result}>"
