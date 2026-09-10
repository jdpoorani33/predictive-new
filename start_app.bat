@echo off
echo ===================================================
echo   Starting Industrial Predictive Maintenance System
echo ===================================================
cd /d "%~dp0"

echo Launching Backend API Server (FastAPI)...
start "Predictive Maintenance Backend (FastAPI)" cmd /c "run_backend.bat"

echo Launching Frontend Application (Vite / React)...
start "Predictive Maintenance Frontend (Vite/React)" cmd /c "run_frontend.bat"

echo Opening browser at http://localhost:3000 ...
timeout /t 4 >nul
start http://localhost:3000

echo Application startup sequence completed!
