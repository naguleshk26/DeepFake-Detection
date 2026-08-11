import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend app directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app_name" in data
    assert "version" in data
    assert "ai_model_status" in data
    assert ".jpg" in data["supported_image_formats"]
    assert ".mp4" in data["supported_video_formats"]
