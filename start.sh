#!/bin/bash

# PrivacyGram - Start Script
# This script starts both backend and frontend servers

echo "========================================"
echo "Starting PrivacyGram Application"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend server
echo ""
echo "Starting backend server on port 5000..."
cd backend
python app.py &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend server
echo "Starting frontend server on port 8000..."
cd frontend
python -m http.server 8000 &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "✓ Application is running!"
echo "========================================"
echo ""
echo "Backend:  http://localhost:5000"
echo "Frontend: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "========================================"
echo ""

# Wait for processes
wait
