import sys
import io
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app

client = TestClient(app)

def create_sample_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_full_image_analysis_pipeline():
    img_bytes = create_sample_jpeg_bytes()
    
    # 1. Analyze Image
    response = client.post(
        "/api/analyze/image",
        files={"file": ("sample_test.jpg", io.BytesIO(img_bytes), "image/jpeg")}
    )
    assert response.status_code == 201
    data = response.json()
    analysis_id = data["id"]
    assert data["filename"] == "sample_test.jpg"
    assert data["file_type"] == "image"
    assert "confidence_score" in data
    assert "result" in data
    assert isinstance(data["explanations"], list)
    
    # 2. Get Analysis by ID
    get_res = client.get(f"/api/analysis/{analysis_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == analysis_id

    # 3. List Analyses
    list_res = client.get("/api/analysis")
    assert list_res.status_code == 200
    ids = [item["id"] for item in list_res.json()]
    assert analysis_id in ids

    # 4. Delete Analysis
    del_res = client.delete(f"/api/analysis/{analysis_id}")
    assert del_res.status_code == 200
    assert del_res.json()["id"] == analysis_id

    # 5. Verify 404 after deletion
    get_res_after = client.get(f"/api/analysis/{analysis_id}")
    assert get_res_after.status_code == 404
