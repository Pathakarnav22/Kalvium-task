#!/bin/zsh
cd /Users/arnav/Desktop/Kalvium/kalvium-lesson-ai/backend
source .venv/bin/activate
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
