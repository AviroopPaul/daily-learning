#!/bin/bash
# Local dev startup script
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Load .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Install Python deps if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
  echo "Installing Python dependencies..."
  pip install -r backend/requirements.txt
fi

# Start backend
echo "Starting backend on http://localhost:8080"
PYTHONPATH="$ROOT" python3 -m uvicorn backend.main:app \
  --host 0.0.0.0 \
  --port 8080 \
  --reload \
  --reload-dir backend &
BACKEND_PID=$!

# Start frontend dev server (separate terminal for hot reload)
if [ "${1}" = "--frontend" ]; then
  echo "Starting frontend dev server on http://localhost:5173"
  cd frontend && npm install && npm run dev &
  FRONTEND_PID=$!
fi

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
