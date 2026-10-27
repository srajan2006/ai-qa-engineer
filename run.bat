@echo off
title AI QA ENGINEER - Multi-Agent Testing Platform
echo ========================================================
echo          AI QA ENGINEER PLATFORM LAUNCHER
echo ========================================================
echo.

cd /d "%~dp0"

IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [INFO] Virtual environment not found. Creating venv...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Python not found in PATH or failed to create venv.
        pause
        exit /b 1
    )
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
    echo [INFO] Installing requirements...
    pip install -r requirements.txt
) ELSE (
    echo [INFO] Activating existing virtual environment...
    call venv\Scripts\activate.bat
)

IF NOT EXIST ".env" (
    echo [INFO] Creating .env from .env.example...
    copy .env.example .env >nul
)

echo.
echo ========================================================
echo Starting FastAPI Server on http://localhost:8000
echo Open your browser and navigate to: http://localhost:8000
echo ========================================================
echo.

python backend/main.py

pause
