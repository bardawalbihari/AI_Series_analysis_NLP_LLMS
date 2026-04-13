@echo off
REM Quick startup script for the Naruto NLP Project
setlocal

set "VENV_DIR=.venv"
set "NEED_INSTALL=0"

echo.
echo =====================================================
echo    Naruto Series Analysis - Gradio App
echo =====================================================
echo.

REM Check if virtual environment exists
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3.11 -m venv "%VENV_DIR%" 2>nul
    if errorlevel 1 (
        python -m venv "%VENV_DIR%"
    )

    call "%VENV_DIR%\Scripts\activate.bat"
    set "NEED_INSTALL=1"
) else (
    echo Activating virtual environment...
    call "%VENV_DIR%\Scripts\activate.bat"
    python -c "import gradio, transformers, pandas, dotenv" >nul 2>&1
    if errorlevel 1 (
        set "NEED_INSTALL=1"
    )
)

if "%NEED_INSTALL%"=="1" (
    echo Installing dependencies...
    pip install --upgrade pip
    pip install -r requirements.txt
)

if not exist .env (
    if exist .env_example (
        echo Creating .env from template...
        copy /Y .env_example .env >nul
    )
)

echo.
echo =====================================================
echo    Starting Gradio Application
echo =====================================================
echo.
echo The app will open at: http://127.0.0.1:7860
echo Press Ctrl+C to stop the server
echo The chatbot can use hosted or local Llama inference when available.
echo If those are unavailable, it will fall back to the local demo chatbot.
echo.

python gradio_app.py

pause
