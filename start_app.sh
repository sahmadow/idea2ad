#!/bin/bash
# Trap SIGINT to kill both processes when script is stopped
trap 'kill 0' SIGINT

echo "Starting LaunchAd..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"

# Start Backend
source venv/bin/activate
uvicorn app.main:app --reload &

# Start Frontend
cd frontend && npm run dev &

wait
