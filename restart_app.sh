#!/bin/bash

# Don't exit on error for migrations, but exit for critical errors
set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping all services...${NC}"

# Function to kill process on port
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ ! -z "$pids" ]; then
        echo -e "${YELLOW}   Killing process on port $port...${NC}"
        echo $pids | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

# Kill Backend (8000 or 8001)
kill_port 8000
kill_port 8001

# Kill Frontend (4200)
kill_port 4200

# Wait a bit to ensure ports are free
sleep 2

echo -e "${GREEN}✅ Services stopped.${NC}"

echo -e "${BLUE}🧹 Cleaning caches...${NC}"
rm -rf frontend/.angular 2>/dev/null || true
rm -rf frontend/dist 2>/dev/null || true
# rm -rf backend/__pycache__ # Optional

echo -e "${GREEN}✅ Cache cleared.${NC}"

# Check if backend venv exists
if [ ! -d "backend/venv" ]; then
    echo -e "${RED}❌ Backend virtual environment not found!${NC}"
    echo -e "${YELLOW}   Please run: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt${NC}"
    exit 1
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Frontend node_modules not found. Installing dependencies...${NC}"
    cd frontend
    npm install
    cd ..
fi

echo -e "${BLUE}🗄️  Applying database migrations...${NC}"
cd backend
source venv/bin/activate
# Apply migrations, show only errors
MIGRATION_OUTPUT=$(python -m alembic upgrade head 2>&1)
MIGRATION_EXIT=$?
if [ $MIGRATION_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ Migrations applied successfully.${NC}"
elif echo "$MIGRATION_OUTPUT" | grep -q "overlaps\|already exists"; then
    echo -e "${YELLOW}⚠️  Migration warning (non-critical), continuing...${NC}"
else
    echo -e "${RED}❌ Migration error:${NC}"
    echo "$MIGRATION_OUTPUT" | grep -i error || echo "$MIGRATION_OUTPUT"
    echo -e "${YELLOW}   Continuing anyway...${NC}"
fi
cd ..

echo -e "${BLUE}🚀 Starting Backend...${NC}"
cd backend
# Run in background, redirect output to log
nohup ./venv/bin/python -m uvicorn main:app --reload --port 8000 > backend_log.txt 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}   Backend started (PID: $BACKEND_PID). Logs in backend/backend_log.txt${NC}"

# Wait for backend to be ready
echo -e "${YELLOW}   Waiting for backend to be ready...${NC}"
BACKEND_READY=false
for i in {1..30}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Backend is ready!${NC}"
        BACKEND_READY=true
        break
    fi
    sleep 1
done

if [ "$BACKEND_READY" = false ]; then
    echo -e "${RED}   ⚠️  Backend did not start in time.${NC}"
    echo -e "${YELLOW}   Check logs: tail -f backend/backend_log.txt${NC}"
fi

cd ..

echo -e "${BLUE}🚀 Starting Frontend...${NC}"
cd frontend
# Run in background, redirect output to log
nohup npm start > frontend_log.txt 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}   Frontend started (PID: $FRONTEND_PID). Logs in frontend/frontend_log.txt${NC}"
cd ..

echo ""
echo -e "${GREEN}✨ All systems go!${NC}"
echo -e "${BLUE}   Backend:  http://localhost:8000 (PID: $BACKEND_PID)${NC}"
echo -e "${BLUE}   Frontend: http://localhost:4200 (PID: $FRONTEND_PID)${NC}"
echo -e "${YELLOW}   Please wait ~15-30 seconds for the frontend to compile.${NC}"
echo -e "${YELLOW}   Then refresh your browser at http://localhost:4200${NC}"
echo ""
echo -e "${BLUE}📋 To view logs:${NC}"
echo -e "   Backend:  tail -f backend/backend_log.txt"
echo -e "   Frontend: tail -f frontend/frontend_log.txt"
echo ""
echo -e "${BLUE}🛑 To stop:${NC}"
echo -e "   kill $BACKEND_PID $FRONTEND_PID"
echo -e "   or run this script again"

