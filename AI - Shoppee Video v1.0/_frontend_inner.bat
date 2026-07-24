@echo off
cd /d "%~dp0"
py scripts\shoppee_video_frontend.py --project-root "%CD%" --host 0.0.0.0 --port 8765 > frontend.log 2>&1
