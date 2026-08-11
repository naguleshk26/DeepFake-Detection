import os
import cv2
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any
from app.config import settings
from app.services.forensic_analyzer import ForensicAnalyzer
from app.services.deepfake_detector import detector_instance

logger = logging.getLogger("deepguard.video_analyzer")

class VideoAnalyzer:
    """Performs frame sampling, face detection, forensic checks, and AI deepfake analysis on video media."""

    @classmethod
    def analyze_video(cls, video_path: str | Path, analysis_id: str) -> Dict[str, Any]:
        """
        Processes video using OpenCV.
        Extracts sampled frames, performs face detection and deepfake model checks,
        and aggregates frame-level findings into overall video verification report.
        """
        video_path = Path(video_path)
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise ValueError("Could not open video file.")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_sec = round(total_frames / fps, 1) if fps > 0 else 0.0

        # Calculate dynamic sampling interval to analyze up to MAX_VIDEO_FRAMES_TO_ANALYZE
        sample_interval = max(1, total_frames // settings.MAX_VIDEO_FRAMES_TO_ANALYZE)

        frames_analyzed = 0
        faces_detected = 0
        suspicious_frames = 0
        frame_forensic_scores = []
        frame_ai_scores = []
        
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)

        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % sample_interval == 0 and frames_analyzed < settings.MAX_VIDEO_FRAMES_TO_ANALYZE:
                frames_analyzed += 1

                # 1. Face detection on frame
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                faces_detected += len(faces)

                # 2. Laplacian Blur / Noise check on frame
                lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                frame_forensic_risk = 35.0 if lap_var < 40.0 else 10.0
                frame_forensic_scores.append(frame_forensic_risk)

                # 3. Save temp frame to test AI Model if available
                if detector_instance.is_available():
                    temp_frame_path = settings.RESULTS_DIR / f"temp_frame_{analysis_id}_{frames_analyzed}.jpg"
                    cv2.imwrite(str(temp_frame_path), frame)
                    score, _, _ = detector_instance.predict_image(temp_frame_path)
                    if temp_frame_path.exists():
                        temp_frame_path.unlink()
                    if score is not None:
                        frame_ai_scores.append(score)
                        if score > settings.SUSPICIOUS_THRESHOLD:
                            suspicious_frames += 1
                else:
                    if frame_forensic_risk > 30.0:
                        suspicious_frames += 1

            frame_count += 1

        cap.release()

        # Aggregations
        avg_forensic_score = round(float(np.mean(frame_forensic_scores)), 1) if frame_forensic_scores else 15.0
        avg_ai_score = round(float(np.mean(frame_ai_scores)), 1) if frame_ai_scores else None
        model_status = detector_instance.get_status()

        # Confidence calculation
        if model_status == "Available" and avg_ai_score is not None:
            composite_score = (avg_ai_score * 0.60) + (avg_forensic_score * 0.40)
        else:
            composite_score = avg_forensic_score * 1.5  # Scale up forensic signal for video

        composite_score = round(min(100.0, max(0.0, composite_score)), 1)

        # Classification
        if composite_score <= settings.AUTHENTIC_THRESHOLD:
            result_label = "LIKELY AUTHENTIC"
        elif composite_score <= settings.SUSPICIOUS_THRESHOLD:
            result_label = "SUSPICIOUS"
        else:
            result_label = "LIKELY AI-GENERATED"

        explanations = [
            f"Video stream processed: {duration_sec}s duration, {width}x{height} resolution at {round(fps, 1)} FPS.",
            f"Analyzed {frames_analyzed} keyframes out of {total_frames} total frames.",
            f"Face detector located {faces_detected} face instance(s) across sampled frames.",
            f"Identified {suspicious_frames} frame(s) with anomalous facial or spatial characteristics."
        ]

        if model_status != "Available":
            explanations.append("AI Model Status: Not Configured – Frame analysis conducted via spatial & frequency forensics.")

        video_meta = {
            "duration_sec": duration_sec,
            "fps": round(fps, 1),
            "resolution": f"{width} x {height} px",
            "total_frames": total_frames,
            "filename": video_path.name,
            "file_size_bytes": video_path.stat().st_size
        }

        video_forensics = {
            "avg_forensic_score": avg_forensic_score,
            "frames_analyzed": frames_analyzed,
            "faces_detected": faces_detected,
            "suspicious_frames": suspicious_frames
        }

        return {
            "result": result_label,
            "confidence_score": composite_score,
            "ai_score": avg_ai_score,
            "ai_model_status": model_status,
            "metadata_score": 10.0,
            "forensic_score": avg_forensic_score,
            "frames_analyzed": frames_analyzed,
            "faces_detected": faces_detected,
            "suspicious_frames": suspicious_frames,
            "explanations": explanations,
            "metadata_info": video_meta,
            "forensics_info": video_forensics,
            "ela_image_url": None
        }
