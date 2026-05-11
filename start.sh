#!/usr/bin/env bash
# Start PFIC Tool — backend + frontend dev servers
# Usage: ./start.sh

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== Starting PFIC Tool ==="
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API docs: http://localhost:8000/docs"
echo ""

# Backend
(
  cd "$ROOT/backend"
  python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!

# Frontend
(
  cd "$ROOT/frontend"
  npm run dev
) &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT INT TERM
wait
