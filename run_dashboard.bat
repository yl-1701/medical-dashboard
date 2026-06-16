@echo off
title MediCare Clinic Dashboard - Launcher
echo ===================================================
echo   🏥 MEDICARE CLINIC DASHBOARD LAUNCHER
echo ===================================================
echo.

:: Check for Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo and check the option "Add Python to PATH" during installation.
    echo.
    pause
    exit /b
)

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo [INFO] Creating Python virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [WARNING] Failed to create virtual environment. Trying direct installation...
    )
)

:: Activate virtual environment and install requirements
if exist venv\Scripts\activate (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate
    echo [INFO] Checking / Installing dependencies...
    pip install -r requirements.txt
) else (
    echo [INFO] Installing dependencies globally...
    pip install -r requirements.txt
)

echo.
echo [INFO] Starting MediCare Clinic Dashboard...
echo [INFO] The dashboard should open automatically in your browser shortly.
echo [INFO] Close this window to stop the server.
echo.

streamlit run app.py

pause
