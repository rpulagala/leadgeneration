@echo off
echo ============================================
echo  Lead Generation Platform - Setup
echo ============================================

:: Check Python
python --version 2>nul
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+ from https://python.org
    echo Make sure to check "Add to PATH" during installation.
    pause
    exit /b 1
)

echo.
echo Creating virtual environment...
cd /d "%~dp0backend"
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Copy .env.example to backend\.env and fill in your email credentials
echo 2. Run start.bat to launch the application
echo.
pause
