import subprocess
import os

python_bin = "/Users/arnav/Desktop/Kalvium/kalvium-lesson-ai/backend/.venv/bin/python"
cmd = [python_bin, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]

process = subprocess.Popen(
    cmd, 
    cwd="/Users/arnav/Desktop/Kalvium/kalvium-lesson-ai/backend", 
    stdout=open("/Users/arnav/Desktop/Kalvium/kalvium-lesson-ai/backend/backend.log", "a"), 
    stderr=subprocess.STDOUT,
    start_new_session=True
)
print(f"Started backend with PID {process.pid}")
