import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageChops
from pathlib import Path
from typing import Tuple, Dict, Any
from app.config import settings

class ForensicAnalyzer:
    """Performs Digital Image Forensics: Error Level Analysis (ELA), Noise Variance, Laplacian Sharpness, and FFT Frequency Artifacts."""

    @classmethod
    def analyze(cls, image_path: str | Path, analysis_id: str) -> Tuple[float, Dict[str, Any], list[str], str]:
        """
        Runs forensic checks on target image.
        Returns:
            forensic_score (float 0-100) -> higher indicates higher risk of manipulation
            forensics_info (dict) -> metrics breakdown
            explanations (list of str) -> human readable explanations
            ela_image_url (str) -> relative URL path to generated ELA heatmap image
        """
        explanations = []
        forensics_info: Dict[str, Any] = {
            "ela_score": 0.0,
            "noise_variance": 0.0,
            "laplacian_var": 0.0,
            "fft_anomaly_score": 0.0,
            "ela_heatmap_generated": False
        }
        
        image_path = Path(image_path)
        ela_filename = f"ela_{analysis_id}.jpg"
        ela_save_path = settings.RESULTS_DIR / ela_filename
        ela_url_path = f"/results/{ela_filename}"

        # 1. Error Level Analysis (ELA)
        ela_score, ela_success = cls._perform_ela(image_path, ela_save_path)
        forensics_info["ela_score"] = round(ela_score, 2)
        forensics_info["ela_heatmap_generated"] = ela_success

        if ela_score > 35.0:
            explanations.append(f"ELA detected elevated compression error level difference ({round(ela_score, 1)}%). Indicates possible re-saving or splice edit.")
        elif ela_score > 20.0:
            explanations.append(f"Moderate ELA compression inconsistency detected ({round(ela_score, 1)}%).")
        else:
            explanations.append("ELA compression pattern appears uniform.")

        # 2. Open image in OpenCV for OpenCV-based forensic checks
        cv_img = cv2.imread(str(image_path))
        if cv_img is None:
            # Fallback if image load failed
            return min(100.0, max(0.0, ela_score)), forensics_info, explanations, ela_url_path if ela_success else ""

        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

        # 3. Noise Variance Analysis
        noise_var = cls._analyze_noise_consistency(gray)
        forensics_info["noise_variance"] = round(noise_var, 2)
        if noise_var > 40.0:
            explanations.append(f"Inconsistent spatial noise distribution across regions (Noise Variance: {round(noise_var, 1)}). Common in composite images.")
            noise_score = 40.0
        elif noise_var > 25.0:
            explanations.append(f"Slight noise distribution variance detected ({round(noise_var, 1)}).")
            noise_score = 20.0
        else:
            explanations.append("Noise distribution is consistent across image grid.")
            noise_score = 5.0

        # 4. Laplacian Blur / Edge Smoothness Variance
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        forensics_info["laplacian_var"] = round(lap_var, 2)
        if lap_var < 50.0:
            explanations.append(f"Image exhibits high blur/smoothing (Laplacian variance: {round(lap_var, 1)}), characteristic of AI generator blending.")
            lap_score = 30.0
        elif lap_var > 2000.0:
            explanations.append("Image contains sharp edge gradients typical of original camera focus.")
            lap_score = 5.0
        else:
            lap_score = 15.0

        # 5. FFT Frequency Domain Artifact Detection
        fft_score = cls._analyze_fft_spectrum(gray)
        forensics_info["fft_anomaly_score"] = round(fft_score, 2)
        if fft_score > 35.0:
            explanations.append(f"High-frequency spectrum anomaly detected ({round(fft_score, 1)}%), characteristic of GAN/Diffusion upsampling grids.")
        else:
            explanations.append("Frequency domain spectrum appears natural.")

        # Composite Forensic Score (weighted combination)
        total_forensic_score = (
            (ela_score * 0.35) +
            (noise_score * 0.25) +
            (lap_score * 0.15) +
            (fft_score * 0.25)
        )

        final_forensic_score = min(100.0, max(0.0, total_forensic_score))
        return round(final_forensic_score, 1), forensics_info, explanations, ela_url_path if ela_success else ""

    @classmethod
    def _perform_ela(cls, image_path: Path, output_path: Path, quality: int = 95) -> Tuple[float, bool]:
        """Perform Error Level Analysis (ELA) and export visual difference heatmap."""
        try:
            with Image.open(image_path).convert("RGB") as original:
                # Save temporary JPEG re-compressed version
                temp_jpg_path = output_path.parent / f"temp_resave_{output_path.name}"
                original.save(temp_jpg_path, "JPEG", quality=quality)

                with Image.open(temp_jpg_path).convert("RGB") as resaved:
                    # Calculate absolute difference
                    diff = ImageChops.difference(original, resaved)

                    # Calculate average error scale
                    extrema = diff.getextrema()
                    max_diff = max([ex[1] for ex in extrema])
                    if max_diff == 0:
                        max_diff = 1
                    scale = 255.0 / max_diff

                    # Enhance difference for visual heatmap
                    enhanced = ImageEnhance.Brightness(diff).enhance(scale * 1.5)
                    enhanced.save(output_path)

                # Clean up temporary resaved file
                if temp_jpg_path.exists():
                    temp_jpg_path.unlink()

                # Calculate average numerical score
                diff_np = np.array(diff, dtype=np.float32)
                mean_diff = np.mean(diff_np)
                ela_score = min(100.0, mean_diff * 4.0)
                return float(ela_score), True
        except Exception as e:
            return 0.0, False

    @classmethod
    def _analyze_noise_consistency(cls, gray_np: np.ndarray) -> float:
        """Calculates standard deviation of noise across grid tiles to find anomalies."""
        h, w = gray_np.shape
        tile_size = 32
        stds = []
        for y in range(0, h - tile_size, tile_size):
            for x in range(0, w - tile_size, tile_size):
                tile = gray_np[y:y+tile_size, x:x+tile_size]
                stds.append(np.std(tile))
        if not stds:
            return 0.0
        return float(np.std(stds))

    @classmethod
    def _analyze_fft_spectrum(cls, gray_np: np.ndarray) -> float:
        """Performs 2D FFT to detect grid artifacts common in AI synthesis."""
        try:
            # Downsample for computational speed if large
            h, w = gray_np.shape
            if h > 512 or w > 512:
                gray_np = cv2.resize(gray_np, (512, 512))

            f = np.fft.fft2(gray_np)
            fshift = np.fft.fftshift(f)
            magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1e-8)

            # Analyze ratio of high-frequency energy outside central low-pass region
            cy, cx = magnitude_spectrum.shape[0] // 2, magnitude_spectrum.shape[1] // 2
            r = 30
            y, x = np.ogrid[:magnitude_spectrum.shape[0], :magnitude_spectrum.shape[1]]
            mask = (x - cx)**2 + (y - cy)**2 > r**2

            high_freq_energy = np.mean(magnitude_spectrum[mask])
            total_energy = np.mean(magnitude_spectrum)

            ratio = (high_freq_energy / (total_energy + 1e-5)) * 10.0
            return float(min(100.0, max(0.0, ratio)))
        except Exception:
            return 0.0
