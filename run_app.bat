@echo off
REM Quick startup script for the Naruto NLP Project
setlocal

set "VENV_DIR=.venv"
set "NEED_INSTALL=0"
set "PYTHON_CMD="
set "APP_PORT="

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
    python -c "import gradio, transformers, pandas, dotenv, scipy, torch; assert hasattr(torch, 'Tensor')" >nul 2>&1
    if errorlevel 1 (
        set "NEED_INSTALL=1"
    )
)

set "PYTHON_CMD=%CD%\%VENV_DIR%\Scripts\python.exe"

if "%NEED_INSTALL%"=="1" (
    echo Installing dependencies...
    "%PYTHON_CMD%" -m pip install --upgrade pip
    "%PYTHON_CMD%" -m pip install -i https://pypi.org/simple -r requirements.txt
)

if not exist .env (
    if exist .env_example (
        echo Creating .env from template...
        copy /Y .env_example .env >nul
    )
)

for /f %%P in ('"%PYTHON_CMD%" -c "import socket; port=7860
while True:
    with socket.socket() as s:
        try:
            s.bind(('127.0.0.1', port))
            print(port)
            break
        except OSError:
            port += 1"') do set "APP_PORT=%%P"

echo.
echo =====================================================
echo    Starting Gradio Application
echo =====================================================
echo.
echo The app will open at: http://127.0.0.1:%APP_PORT%
echo Press Ctrl+C to stop the server
echo.

set "GRADIO_SERVER_PORT=%APP_PORT%"
"%PYTHON_CMD%" gradio_app.py

pause
