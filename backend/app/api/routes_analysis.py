import json
import uuid
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisResponse, AnalysisListItem, DeleteResponse
from app.utils.file_utils import sanitize_filename, validate_file_extension, check_file_size, safe_remove_file
from app.services.image_analyzer import ImageAnalyzer
from app.services.video_analyzer import VideoAnalyzer

router = APIRouter(prefix="/api", tags=["Analysis"])

def _format_analysis_response(analysis: Analysis) -> AnalysisResponse:
    """Helper to convert SQLAlchemy Analysis model to Pydantic AnalysisResponse."""
    explanations = json.loads(analysis.explanations_json) if analysis.explanations_json else []
    metadata_info = json.loads(analysis.metadata_info_json) if analysis.metadata_info_json else {}
    forensics_info = json.loads(analysis.forensics_info_json) if analysis.forensics_info_json else {}

    return AnalysisResponse(
        id=analysis.id,
        filename=analysis.filename,
        stored_filename=analysis.stored_filename,
        file_type=analysis.file_type,
        mime_type=analysis.mime_type,
        file_size=analysis.file_size,
        result=analysis.result,
        confidence_score=analysis.confidence_score,
        ai_score=analysis.ai_score,
        ai_model_status=analysis.ai_model_status,
        metadata_score=analysis.metadata_score,
        forensic_score=analysis.forensic_score,
        frames_analyzed=analysis.frames_analyzed,
        faces_detected=analysis.faces_detected,
        suspicious_frames=analysis.suspicious_frames,
        status=analysis.status,
        explanations=explanations,
        metadata_info=metadata_info,
        forensics_info=forensics_info,
        ela_image_url=analysis.ela_image_path,
        media_url=f"/uploads/{analysis.stored_filename}",
        created_at=analysis.created_at
    )

@router.post("/analyze/image", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and analyze image file for deepfake/manipulation detection."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing.")

    file_type = validate_file_extension(file.filename)
    if file_type != "image":
        raise HTTPException(status_code=400, detail="Invalid media type. Use /api/analyze/video for videos.")

    contents = await file.read()
    file_size = check_file_size(contents)

    analysis_id = str(uuid.uuid4())
    stored_name = sanitize_filename(file.filename)
    target_path = settings.UPLOAD_DIR / stored_name

    try:
        with open(target_path, "wb") as f:
            f.write(contents)

        # Run Image Analyzer
        analysis_data = ImageAnalyzer.analyze_image(target_path, analysis_id)

        # DB Record creation
        db_record = Analysis(
            id=analysis_id,
            filename=file.filename,
            stored_filename=stored_name,
            file_type="image",
            mime_type=file.content_type or "image/jpeg",
            file_size=file_size,
            result=analysis_data["result"],
            confidence_score=analysis_data["confidence_score"],
            ai_score=analysis_data["ai_score"],
            ai_model_status=analysis_data["ai_model_status"],
            metadata_score=analysis_data["metadata_score"],
            forensic_score=analysis_data["forensic_score"],
            frames_analyzed=1,
            faces_detected=analysis_data["faces_detected"],
            suspicious_frames=analysis_data["suspicious_frames"],
            status="completed",
            explanations_json=json.dumps(analysis_data["explanations"]),
            metadata_info_json=json.dumps(analysis_data["metadata_info"]),
            forensics_info_json=json.dumps(analysis_data["forensics_info"]),
            ela_image_path=analysis_data["ela_image_url"]
        )

        db.add(db_record)
        db.commit()
        db.refresh(db_record)

        return _format_analysis_response(db_record)

    except Exception as e:
        safe_remove_file(target_path)
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

@router.post("/analyze/video", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_video_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and analyze video file for deepfake/manipulation detection."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing.")

    file_type = validate_file_extension(file.filename)
    if file_type != "video":
        raise HTTPException(status_code=400, detail="Invalid media type. Use /api/analyze/image for images.")

    contents = await file.read()
    file_size = check_file_size(contents)

    analysis_id = str(uuid.uuid4())
    stored_name = sanitize_filename(file.filename)
    target_path = settings.UPLOAD_DIR / stored_name

    try:
        with open(target_path, "wb") as f:
            f.write(contents)

        # Run Video Analyzer
        analysis_data = VideoAnalyzer.analyze_video(target_path, analysis_id)

        # DB Record creation
        db_record = Analysis(
            id=analysis_id,
            filename=file.filename,
            stored_filename=stored_name,
            file_type="video",
            mime_type=file.content_type or "video/mp4",
            file_size=file_size,
            result=analysis_data["result"],
            confidence_score=analysis_data["confidence_score"],
            ai_score=analysis_data["ai_score"],
            ai_model_status=analysis_data["ai_model_status"],
            metadata_score=analysis_data["metadata_score"],
            forensic_score=analysis_data["forensic_score"],
            frames_analyzed=analysis_data["frames_analyzed"],
            faces_detected=analysis_data["faces_detected"],
            suspicious_frames=analysis_data["suspicious_frames"],
            status="completed",
            explanations_json=json.dumps(analysis_data["explanations"]),
            metadata_info_json=json.dumps(analysis_data["metadata_info"]),
            forensics_info_json=json.dumps(analysis_data["forensics_info"]),
            ela_image_path=None
        )

        db.add(db_record)
        db.commit()
        db.refresh(db_record)

        return _format_analysis_response(db_record)

    except Exception as e:
        safe_remove_file(target_path)
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")

@router.get("/analysis", response_model=List[AnalysisListItem])
def list_analyses(
    limit: int = Query(50, ge=1, le=200),
    file_type: str = Query(None, description="Filter by 'image' or 'video'"),
    search: str = Query(None, description="Search by filename"),
    db: Session = Depends(get_db)
):
    """Retrieve history list of past analyses."""
    query = db.query(Analysis)
    if file_type:
        query = query.filter(Analysis.file_type == file_type)
    if search:
        query = query.filter(Analysis.filename.ilike(f"%{search}%"))

    analyses = query.order_by(Analysis.created_at.desc()).limit(limit).all()
    return analyses

@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
def get_analysis_by_id(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """Fetch complete analysis report by ID."""
    record = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis report not found.")
    return _format_analysis_response(record)

@router.delete("/analysis/{analysis_id}", response_model=DeleteResponse)
def delete_analysis(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """Delete analysis report and clean up stored media files."""
    record = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis report not found.")

    # Remove media upload
    if record.stored_filename:
        safe_remove_file(settings.UPLOAD_DIR / record.stored_filename)

    # Remove ELA image artifact if exists
    if record.ela_image_path:
        ela_file = settings.RESULTS_DIR / Path(record.ela_image_path).name
        safe_remove_file(ela_file)

    db.delete(record)
    db.commit()

    return DeleteResponse(message="Analysis record deleted successfully", id=analysis_id)
