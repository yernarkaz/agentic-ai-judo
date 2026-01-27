#!/bin/bash
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting Judo Analysis Server..."
# Listen on all interfaces so mobile app can connect
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
