import os
import cv2
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
from app.config import settings
from app.services.metadata_analyzer import MetadataAnalyzer
from app.services.forensic_analyzer import ForensicAnalyzer
from app.services.deepfake_detector import detector_instance

logger = logging.getLogger("deepguard.image_analyzer")

class ImageAnalyzer:
    """Master orchestrator for single image analysis."""

    @classmethod
    def analyze_image(cls, image_path: str | Path, analysis_id: str) -> Dict[str, Any]:
        """
        Runs metadata, forensic, face detection, and AI model checks on an image.
        Returns a complete dictionary suitable for storing in Analysis model.
        """
        image_path = Path(image_path)
        all_explanations = []

        # 1. Metadata Analysis
        meta_score, meta_info, meta_reasons = MetadataAnalyzer.analyze(image_path)
        all_explanations.extend(meta_reasons)

        # 2. Forensic Analysis (ELA, Noise, Laplacian, FFT)
        forensic_score, forensic_info, forensic_reasons, ela_url = ForensicAnalyzer.analyze(image_path, analysis_id)
        all_explanations.extend(forensic_reasons)

        # 3. Face Detection using OpenCV Haar Cascade
        faces_count = cls._detect_faces(image_path)
        if faces_count > 0:
            all_explanations.append(f"Face detection identified {faces_count} face(s) in image.")
        else:
            all_explanations.append("No human faces detected in image.")

        # 4. AI Deepfake Model Detection
        ai_score, model_status, ai_reason = detector_instance.predict_image(image_path)
        all_explanations.append(ai_reason)

        # 5. Composite Confidence Score Calculation
        if model_status == "Available" and ai_score is not None:
            # Weighted average when AI model is active
            composite_score = (ai_score * 0.50) + (forensic_score * 0.35) + (meta_score * 0.15)
        else:
            # Forensic + Metadata weighted average when AI model is Not Configured
            composite_score = (forensic_score * 0.70) + (meta_score * 0.30)
            all_explanations.append("Confidence score calculated strictly from available digital forensics and metadata signals.")

        composite_score = round(min(100.0, max(0.0, composite_score)), 1)

        # 6. Classification based on Configurable Thresholds
        if composite_score <= settings.AUTHENTIC_THRESHOLD:
            result_label = "LIKELY AUTHENTIC"
        elif composite_score <= settings.SUSPICIOUS_THRESHOLD:
            result_label = "SUSPICIOUS"
        else:
            result_label = "LIKELY AI-GENERATED"

        return {
            "result": result_label,
            "confidence_score": composite_score,
            "ai_score": ai_score,
            "ai_model_status": model_status,
            "metadata_score": meta_score,
            "forensic_score": forensic_score,
            "faces_detected": faces_count,
            "frames_analyzed": 1,
            "suspicious_frames": 1 if composite_score > settings.SUSPICIOUS_THRESHOLD else 0,
            "explanations": all_explanations,
            "metadata_info": meta_info,
            "forensics_info": forensic_info,
            "ela_image_url": ela_url
        }

    @classmethod
    def _detect_faces(cls, image_path: Path) -> int:
        """Detect faces using OpenCV Haar cascade."""
        try:
            cv_img = cv2.imread(str(image_path))
            if cv_img is None:
                return 0
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            face_cascade = cv2.CascadeClassifier(cascade_path)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            return len(faces)
        except Exception:
            return 0
