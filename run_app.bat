@echo off
REM Quick startup script for the Naruto NLP Project

echo.
echo =====================================================
echo    Naruto Series Analysis - Gradio App
echo =====================================================
echo.

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install --upgrade pip
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo.
echo =====================================================
echo    Starting Gradio Application
echo =====================================================
echo.
echo The app will open at: http://localhost:7860
echo Press Ctrl+C to stop the server
echo.

python gradio_app.py

pause
