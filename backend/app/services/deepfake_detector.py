import os
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from app.config import settings

logger = logging.getLogger("deepguard.detector")

# Try importing torch and torchvision
TORCH_AVAILABLE = False
try:
    import torch
    import torch.nn as nn
    import torchvision.transforms as transforms
    from PIL import Image
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

class LightweightFaceNet(nn.Module if TORCH_AVAILABLE else object):
    """
    Standard PyTorch CNN architecture for face deepfake detection.
    Pre-trained weights can be loaded directly into this model.
    """
    def __init__(self):
        if not TORCH_AVAILABLE:
            return
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4))
        )
        self.classifier = nn.Sequential(
            nn.Linear(128 * 4 * 4, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)


class DeepfakeDetector:
    """
    Deepfake AI Detection Interface using PyTorch.
    Checks for PyTorch environment and trained model weights at settings.MODEL_PATH.
    If model is missing or PyTorch is absent, explicitly reports 'Not Configured'.
    """

    _instance = None

    def __init__(self):
        self.model = None
        self.device = "cpu"
        self.model_loaded = False
        self.model_status_text = "Not Configured"
        self.transform = None

        self._load_model()

    def _load_model(self):
        """Loads PyTorch model if PyTorch is installed and model weights exist."""
        if not TORCH_AVAILABLE:
            self.model_status_text = "PyTorch Not Installed"
            logger.info("PyTorch dependency not found. AI model marked as Not Configured.")
            return

        model_path = Path(settings.MODEL_PATH)
        if not model_path.exists():
            self.model_status_text = "Not Configured"
            logger.info(f"AI model weight file not found at '{model_path}'. DeepfakeDetector operating in forensic-only mode.")
            return

        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = LightweightFaceNet()
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()

            self.transform = transforms.Compose([
                transforms.Resize((128, 128)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])

            self.model_loaded = True
            self.model_status_text = "Available"
            logger.info(f"AI Deepfake Detection PyTorch Model loaded successfully on {self.device}.")
        except Exception as e:
            self.model_loaded = False
            self.model_status_text = "Error Loading Weights"
            logger.error(f"Failed to load AI model weights: {str(e)}")

    def is_available(self) -> bool:
        """Returns True only if PyTorch model is initialized and ready for inference."""
        return self.model_loaded

    def get_status(self) -> str:
        """Returns current model status ('Available' or 'Not Configured')."""
        return "Available" if self.model_loaded else "Not Configured"

    def predict_image(self, image_path: str | Path) -> Tuple[Optional[float], str, str]:
        """
        Performs AI deepfake model inference on an image file.
        Returns:
            ai_score: float (0.0 to 100.0) or None if model unavailable
            status_str: 'Available' or 'Not Configured'
            explanation: description of model output or missing status
        """
        if not self.model_loaded:
            return None, "Not Configured", "AI Model Status: Not Configured – Forensic & metadata analysis performed."

        try:
            with Image.open(image_path).convert("RGB") as img:
                input_tensor = self.transform(img).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    prob = self.model(input_tensor).item()

                ai_score = round(prob * 100.0, 1)
                explanation = f"AI Deepfake Model evaluated synthetic facial feature likelihood at {ai_score}%."
                return ai_score, "Available", explanation
        except Exception as e:
            return None, "Error", f"AI Inference failed: {str(e)}"

# Global singleton detector instance
detector_instance = DeepfakeDetector()
