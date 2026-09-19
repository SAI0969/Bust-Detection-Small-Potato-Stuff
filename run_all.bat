@echo off
title AI NWP Forecast Bust Detection Platform
echo ========================================================
echo Launching AI Forecast Bust Detection & Confidence System
echo ========================================================
echo 1. Starting Backend...
start "Forecast Bust Detection Backend" cmd /c "%~dp0run_backend.bat"

echo 2. Waiting 3 seconds for backend initialization...
timeout /t 3 /nobreak >nul

echo 3. Starting Frontend...
start "Forecast Bust Detection Frontend" cmd /c "%~dp0run_frontend.bat"

echo 4. Opening Dashboard in Browser...
timeout /t 2 /nobreak >nul
start http://localhost:5173

echo System is running!
