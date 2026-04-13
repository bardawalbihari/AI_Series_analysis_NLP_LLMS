#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR=".venv"

create_windows_venv() {
  py -3.11 -m venv "$VENV_DIR" 2>/dev/null || python -m venv "$VENV_DIR"
}

create_unix_venv() {
  python3.11 -m venv "$VENV_DIR" 2>/dev/null || python3 -m venv "$VENV_DIR"
}

if [[ "$OSTYPE" == msys* || "$OSTYPE" == cygwin* || "$OSTYPE" == win32* ]]; then
  PYTHON_BIN="$ROOT_DIR/$VENV_DIR/Scripts/python.exe"
  if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "Creating virtual environment..."
    create_windows_venv
  fi
else
  PYTHON_BIN="$ROOT_DIR/$VENV_DIR/bin/python"
  if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "Creating virtual environment..."
    create_unix_venv
  fi
fi

if ! "$PYTHON_BIN" -c "import gradio, transformers, pandas, dotenv, scipy, torch; assert hasattr(torch, 'Tensor')" >/dev/null 2>&1; then
  echo "Installing dependencies..."
  "$PYTHON_BIN" -m pip install --upgrade pip
  "$PYTHON_BIN" -m pip install -i https://pypi.org/simple -r requirements.txt
fi

if [[ ! -f .env && -f .env_example ]]; then
  cp .env_example .env
fi

APP_PORT="$($PYTHON_BIN - <<'PY'
import socket

port = 7860
while True:
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", port))
            print(port)
            break
        except OSError:
            port += 1
PY
)"

echo
echo "Starting app on http://127.0.0.1:${APP_PORT}"
echo
GRADIO_SERVER_PORT="$APP_PORT" "$PYTHON_BIN" gradio_app.py