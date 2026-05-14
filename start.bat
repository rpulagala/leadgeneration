@echo off
echo ============================================
echo  Lead Generation Platform - Starting
echo ============================================
cd /d "%~dp0backend"

:: Activate venv if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo Starting server at http://localhost:8000
echo Press Ctrl+C to stop
echo.
python main.py
pause
