# Industrial Predictive Maintenance - PowerShell Launcher
Set-Location -Path $PSScriptRoot

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting Industrial Predictive Maintenance System" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

Write-Host "`n[1/3] Launching Backend API Server (FastAPI)..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList "/c run_backend.bat" -WorkingDirectory $PSScriptRoot

Write-Host "[2/3] Launching Frontend Application (Vite / React)..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList "/c run_frontend.bat" -WorkingDirectory $PSScriptRoot

Write-Host "[3/3] Opening Browser at http://localhost:3000 in 4 seconds..." -ForegroundColor Green
Start-Sleep -Seconds 4
Start-Process "http://localhost:3000"
