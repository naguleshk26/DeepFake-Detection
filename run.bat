@echo off
TITLE DeepGuard Launcher
echo ====================================================================
echo      DeepGuard - AI Deepfake & Digital Media Authenticity Verification
echo ====================================================================
echo.

cd /d "%~dp0"

IF NOT EXIST "backend\venv" (
    echo [1/3] Creating Python Virtual Environment in backend\venv...
    python -m venv backend\venv
) ELSE (
    echo [1/3] Python Virtual Environment found in backend\venv.
)

echo [2/3] Activating virtual environment and installing dependencies...
call backend\venv\Scripts\activate.bat
pip install -r backend\requirements.txt --quiet

echo.
echo [3/3] Starting DeepGuard Application Server on http://localhost:8000...
start http://localhost:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir backend

pause
