@echo off
echo ===================================================
echo   Industrial Predictive Maintenance - React Frontend
echo ===================================================
cd /d "%~dp0frontend"

if not exist "node_modules\" (
    echo [1/2] Installing npm dependencies...
    npm install
) else (
    echo [1/2] npm dependencies already installed.
)

echo [2/2] Starting Vite Frontend on http://localhost:3000 ...
npm run dev
pause
