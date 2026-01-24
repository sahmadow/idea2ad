#!/bin/bash
# Trap SIGINT to kill both processes when script is stopped
trap 'kill 0' SIGINT

echo "Starting LaunchAd..."
echo "Backend: https://localhost:8000"
echo "Frontend: https://localhost:5173"

# Start Backend
source venv/bin/activate
uvicorn app.main:app --reload --ssl-keyfile=./certs/key.pem --ssl-certfile=./certs/cert.pem &

# Start Frontend
cd frontend && npm run dev &

wait
