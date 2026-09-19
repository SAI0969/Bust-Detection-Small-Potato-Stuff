@echo off
title AI Forecast Bust Detection - Backend
echo ========================================================
echo Starting FastAPI Backend on http://localhost:8000
echo ========================================================
cd /d "%~dp0backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
