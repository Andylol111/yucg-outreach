#!/bin/bash
# Start YUCG Outreach - Backend + Frontend
cd "$(dirname "$0")"

echo "=== YUCG Outreach - Starting from scratch ==="

# 1. Backend setup
echo ""
echo "1. Setting up backend..."
cd backend
if [ ! -d "venv" ]; then
  echo "   Creating Python virtual environment..."
  python3 -m venv venv
fi
echo "   Activating venv and installing dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt
echo "   Starting backend on http://localhost:8000"
python -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# 2. Frontend setup
echo ""
echo "2. Setting up frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
  echo "   Installing npm dependencies..."
  npm install
fi
echo "   Starting frontend on http://localhost:5173"
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=== Both servers starting ==="
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both"
wait $BACKEND_PID $FRONTEND_PID
