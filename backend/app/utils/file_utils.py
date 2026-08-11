import os
import uuid
import re
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from app.config import settings

def sanitize_filename(filename: str) -> str:
    """Strip dangerous characters and return a safe unique filename."""
    base_name = Path(filename).stem
    extension = Path(filename).suffix.lower()
    
    # Remove any non-alphanumeric chars except dashes and underscores
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', base_name)
    if not clean_name:
        clean_name = "upload"
        
    unique_suffix = uuid.uuid4().hex[:8]
    return f"{clean_name}_{unique_suffix}{extension}"

def validate_file_extension(filename: str) -> str:
    """Validate file extension against allowed image and video types."""
    ext = Path(filename).suffix.lower()
    if ext in settings.ALLOWED_IMAGE_EXTENSIONS:
        return "image"
    elif ext in settings.ALLOWED_VIDEO_EXTENSIONS:
        return "video"
    else:
        allowed = settings.ALLOWED_IMAGE_EXTENSIONS + settings.ALLOWED_VIDEO_EXTENSIONS
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(allowed)}"
        )

def check_file_size(file_bytes: bytes) -> int:
    """Verify that file size does not exceed MAX_UPLOAD_SIZE_MB."""
    size = len(file_bytes)
    if size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )
    if size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty (0 bytes)."
        )
    return size

def safe_remove_file(filepath: str | Path) -> None:
    """Safely attempt to remove a file from disk without throwing uncaught exceptions."""
    try:
        path = Path(filepath)
        if path.exists() and path.is_file():
            path.unlink()
    except Exception as e:
        print(f"Warning: Failed to delete file {filepath}: {str(e)}")
