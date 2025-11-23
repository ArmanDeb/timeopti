#!/bin/bash

echo "🛑 Stopping all services..."

# Kill Backend (8000 or 8001)
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true

# Kill Frontend (4200)
lsof -ti:4200 | xargs kill -9 2>/dev/null || true

echo "✅ Services stopped."

echo "🧹 Cleaning caches..."
rm -rf frontend/.angular
rm -rf frontend/dist
# rm -rf backend/__pycache__ # Optional

echo "✅ Cache cleared."

echo "🚀 Starting Backend..."
cd backend
# Run in background, redirect output to log (use python -m to avoid venv issues)
nohup ./venv/bin/python -m uvicorn main:app --reload --port 8001 > backend_log.txt 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID). Logs in backend/backend_log.txt"

echo "🚀 Starting Frontend..."
cd ../frontend
# Run in background, redirect output to log
nohup npm start > frontend_log.txt 2>&1 &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID). Logs in frontend/frontend_log.txt"

echo "✨ All systems go! Please wait ~15-30 seconds for the frontend to compile."
echo "Then refresh your browser at http://localhost:4200"

