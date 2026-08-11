# DeepGuard – AI-Based Deepfake & Digital Media Authenticity Verification System

![DeepGuard Banner](https://img.shields.io/badge/DeepGuard-v1.0.0-06b6d4?style=for-the-badge&logo=shield)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?style=for-the-badge&logo=pytorch)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?style=for-the-badge&logo=opencv)

---

## 1. Project Overview

**DeepGuard** is a full-stack, enterprise-grade AI and digital media authenticity verification platform. Designed for cybersecurity professionals, forensic analysts, and general users, DeepGuard allows users to upload **images and videos** to detect deepfakes, AI-generated synthetic media, and digital manipulation.

The platform provides a **probabilistic confidence score**, an **explainable breakdown of risk factors**, **EXIF metadata extraction**, **Error Level Analysis (ELA) visual heatmaps**, **2D FFT frequency spectrum anomaly detection**, and **video frame face tracking**.

---

## 2. Key Features

- **Multi-Format Upload Support**: Analyzes JPG, JPEG, PNG, WEBP images and MP4, MOV, AVI videos (up to 50MB).
- **Error Level Analysis (ELA)**: Re-compresses JPEG data to generate visual difference heatmaps indicating localized edits and splices.
- **2D FFT Frequency Anomaly Detection**: Identifies periodic high-frequency checkerboard artifacts characteristic of GAN and Diffusion model upsamplers.
- **Noise Consistency Analysis**: Evaluates spatial standard deviation across image patches to detect composite splicing.
- **EXIF Metadata & Software Detection**: Extracts hardware specs (Make, Model, Lens), timestamps, and editing tool signatures (Photoshop, Canva, Stable Diffusion, Midjourney).
- **PyTorch Deepfake Neural Model**: Modular `DeepfakeDetector` PyTorch interface for evaluating synthetic face probability.
- **Video Frame & Face Tracking**: Samples video keyframes at optimal intervals, isolates face crops via OpenCV, and tracks frame-level suspicion metrics.
- **Configurable Risk Classification Thresholds**: Easily configure risk boundaries (`AUTHENTIC`, `SUSPICIOUS`, `LIKELY AI-GENERATED`) in `config.py`.
- **SQLite & SQLAlchemy History Log**: Stores full analysis reports, metrics, and media files for audit trailing and filtering.
- **Cybersecurity Dark UI**: Responsive dashboard with scanning HUD animations, radar charts (Chart.js), and ELA heatmap viewers.

---

## 3. Technology Stack

- **Frontend**: HTML5, Modern Vanilla CSS3 Design System, JavaScript (ES6+), Chart.js.
- **Backend**: Python 3.11, FastAPI, Uvicorn, Pydantic v2.
- **AI & Computer Vision**: PyTorch, Torchvision, OpenCV (`opencv-python-headless`), Pillow (PIL), NumPy.
- **Database**: SQLite 3, SQLAlchemy ORM.
- **Deployment**: Docker, Docker Compose.

---

## 4. Complete Project Structure

```text
DeepGuard/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app initializer & static mounts
│   │   ├── config.py                   # App config, threshold boundaries, paths
│   │   ├── database.py                 # SQLAlchemy engine & session setup
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes_analysis.py      # /api/analyze/image, /api/analyze/video, /api/analysis
│   │   │   └── routes_health.py        # /api/health status endpoint
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── analysis.py             # Analysis SQLAlchemy database model
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── analysis.py             # Pydantic request/response schemas
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── image_analyzer.py       # Master image analysis coordinator
│   │   │   ├── video_analyzer.py       # OpenCV video frame sampling & face analysis
│   │   │   ├── metadata_analyzer.py    # EXIF & software tag extraction
│   │   │   ├── forensic_analyzer.py    # ELA, noise, Laplacian, & FFT algorithms
│   │   │   └── deepfake_detector.py    # PyTorch face model interface
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── file_utils.py           # Secure naming & extension validation
│   │
│   ├── requirements.txt                # Python dependencies
│   └── Dockerfile                      # Backend container definition
│
├── frontend/
│   ├── index.html                      # Landing page with hero & feature grid
│   ├── analyze.html                    # Media upload & live scanner workspace
│   ├── results.html                    # Analysis report dashboard & radar chart
│   ├── history.html                    # Filterable audit log history table
│   ├── about.html                      # Educational methodology & disclaimers
│   │
│   ├── css/
│   │   └── style.css                   # Cyber-security dark theme CSS
│   │
│   └── js/
│       ├── app.js                      # Core JS & toast notification system
│       ├── analyze.js                  # Drag-and-drop & scanning HUD animation
│       ├── results.js                  # Report renderer & Chart.js integration
│       └── history.js                  # Table populator & delete handlers
│
├── uploads/                            # Stored media uploads (.gitkeep)
├── results/                            # Generated ELA heatmaps (.gitkeep)
│
├── tests/                              # Pytest test suite
│   ├── test_health.py                  # Health check unit test
│   ├── test_upload.py                  # File validation unit test
│   └── test_analysis.py                # End-to-end image analysis test
│
├── .env.example                        # Environment defaults
├── .gitignore                          # Git exclusion rules
├── docker-compose.yml                  # Docker orchestration file
├── run.bat                             # One-click Windows starter script
└── README.md                           # Documentation
```

---

## 5. Quick Start for Windows (VS Code)

### Option A: One-Click Launch (`run.bat`)
Double-click `run.bat` in the root folder. It automatically creates the virtual environment, installs requirements, launches FastAPI, and opens your default browser at `http://localhost:8000`.

### Option B: Manual Command Line Execution
Open PowerShell or Command Prompt in the `DeepGuard` root directory:

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create Python virtual environment
python -m venv venv

# 3. Activate virtual environment (Windows)
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Return to root directory and start application server
cd ..
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to:
👉 `http://127.0.0.1:8000`

---

## 6. Docker Deployment

To build and run DeepGuard inside Docker:

```bash
docker compose up --build
```

Access the application in your browser at `http://localhost:8000`.

---

## 7. AI Model Strategy & Setup

DeepGuard features a clean modular PyTorch detector in `backend/app/services/deepfake_detector.py`.

### How It Works:
1. **Weights Missing**: If no trained weights file is placed at `backend/app/weights/deepfake_detector.pth`, the detector explicitly reports `"AI Model Status: Not Configured"`. All confidence calculations strictly rely on genuine forensic signals (ELA, noise variance, FFT, metadata). **No fake predictions or random numbers are ever generated.**
2. **Plugging in Trained Weights**:
   - Place your trained PyTorch state dict (`.pth`) file at `backend/app/weights/deepfake_detector.pth`.
   - On server startup, DeepGuard automatically detects the weights, initializes PyTorch on CPU/GPU, and switches model status to `"Available"`.

---

## 8. API Endpoint Documentation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves Frontend Landing Page |
| `GET` | `/api/health` | Returns server health & AI model status |
| `POST` | `/api/analyze/image` | Uploads and analyzes image file |
| `POST` | `/api/analyze/video` | Uploads and analyzes video file |
| `GET` | `/api/analysis` | Retrieves paginated history log |
| `GET` | `/api/analysis/{id}` | Fetches complete analysis report by ID |
| `DELETE` | `/api/analysis/{id}` | Deletes record and cleans up files |

---

## 9. Running Tests

Run the unit and integration test suite using `pytest`:

```bash
# From the project root with venv activated:
pip install pytest
pytest tests/
```

---

## 10. System Disclaimer & Accuracy

> **Notice**: DeepGuard media verification results represent probabilistic predictions based on digital forensic signals, signal processing statistics, and AI models. Results do not constitute a 100% legal guarantee of media authenticity.
