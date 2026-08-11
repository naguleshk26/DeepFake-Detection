import os
from typing import Dict, Any, Tuple
from PIL import Image, ExifTags
from pathlib import Path

class MetadataAnalyzer:
    """Analyzes image metadata (EXIF, camera specs, editing software, dates)."""

    EDITING_SOFTWARE_KEYWORDS = [
        "photoshop", "gimp", "canva", "lightroom", "pixlr", "snapseed", 
        "after effects", "premiere", "affinity", "paint.net", "stable diffusion",
        "midjourney", "dall-e", "automatic1111", "comfyui", "faceapp", "deepface"
    ]

    @classmethod
    def analyze(cls, file_path: str | Path) -> Tuple[float, Dict[str, Any], list[str]]:
        """
        Extracts EXIF and file metadata.
        Returns:
            metadata_score (float 0-100) -> higher indicates suspicious metadata edits
            metadata_info (dict) -> structured metadata dictionary
            explanations (list of str) -> human readable findings
        """
        explanations = []
        info: Dict[str, Any] = {
            "available": False,
            "filename": Path(file_path).name,
            "file_size_bytes": 0,
            "dimensions": "Unknown",
            "format": "Unknown",
            "camera_make": None,
            "camera_model": None,
            "software": None,
            "date_time": None,
            "gps_info": None
        }

        try:
            file_path = Path(file_path)
            info["file_size_bytes"] = file_path.stat().st_size
            
            with Image.open(file_path) as img:
                info["dimensions"] = f"{img.width} x {img.height} px"
                info["width"] = img.width
                info["height"] = img.height
                info["format"] = img.format or file_path.suffix.replace('.', '').upper()
                
                # Extract EXIF if available
                exif_data = img._getexif() if hasattr(img, '_getexif') else None
                
                if exif_data:
                    info["available"] = True
                    for tag_id, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                        
                        if tag_name == "Make":
                            info["camera_make"] = str(value).strip()
                        elif tag_name == "Model":
                            info["camera_model"] = str(value).strip()
                        elif tag_name == "Software":
                            info["software"] = str(value).strip()
                        elif tag_name in ["DateTimeOriginal", "DateTimeDigitized", "DateTime"]:
                            if not info["date_time"]:
                                info["date_time"] = str(value).strip()
                        elif tag_name == "GPSInfo":
                            info["gps_info"] = "Present"
        except Exception as e:
            # Non-image or corrupted EXIF
            pass

        # Calculate metadata score and explanations
        score = 0.0

        if not info["available"]:
            explanations.append("Metadata unavailable or stripped (Common on social media & web uploads).")
            # Missing metadata is common, so assign neutral score (15.0) instead of flagging as fake automatically
            score = 15.0
        else:
            explanations.append("EXIF metadata successfully extracted.")
            
            # Check camera info
            if info["camera_make"] or info["camera_model"]:
                camera_str = f"{info['camera_make'] or ''} {info['camera_model'] or ''}".strip()
                explanations.append(f"Camera Hardware metadata detected: {camera_str}.")
            else:
                explanations.append("No camera hardware specs found in metadata.")
                score += 15.0

            # Check editing software
            if info["software"]:
                software_lower = info["software"].lower()
                detected_kw = [kw for kw in cls.EDITING_SOFTWARE_KEYWORDS if kw in software_lower]
                if detected_kw:
                    explanations.append(f"Editing software signature detected: '{info['software']}'.")
                    score += 45.0
                else:
                    explanations.append(f"Software tag present: '{info['software']}'.")
                    score += 20.0
            
            if info["date_time"]:
                explanations.append(f"Capture timestamp found: {info['date_time']}.")

        score = min(100.0, max(0.0, score))
        return score, info, explanations
