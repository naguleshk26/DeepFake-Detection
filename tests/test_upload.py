import sys
import io
from pathlib import Path
from fastapi.testclient import TestClient

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app

client = TestClient(app)

def test_invalid_extension_upload():
    # Attempt uploading an executable script
    fake_exe = io.BytesIO(b"echo 'malicious'")
    response = client.post(
        "/api/analyze/image",
        files={"file": ("test.exe", fake_exe, "application/octet-stream")}
    )
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]

def test_empty_file_upload():
    empty_file = io.BytesIO(b"")
    response = client.post(
        "/api/analyze/image",
        files={"file": ("empty.jpg", empty_file, "image/jpeg")}
    )
    assert response.status_code == 400
    assert "File is empty" in response.json()["detail"]
