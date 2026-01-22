# Blink Message Playground - Startup Script
# Starts both backend and frontend servers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Blink Message Playground Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a port is in use
function Test-Port {
    param($Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -InformationLevel Quiet
    return $connection
}

# Check if backend is already running
if (Test-Port 8000) {
    Write-Host "[WARNING] Backend port 8000 is already in use" -ForegroundColor Yellow
    Write-Host "The backend may already be running." -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "[1/2] Starting Backend Server..." -ForegroundColor Green
    Write-Host "      Location: backend/" -ForegroundColor Gray
    Write-Host "      URL: http://127.0.0.1:8000" -ForegroundColor Gray
    
    # Start backend in a new PowerShell window
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; Write-Host 'Starting Backend Server...' -ForegroundColor Green; .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
    
    Write-Host "      Status: Started in new window" -ForegroundColor Green
    Write-Host ""
    
    # Wait a bit for backend to start
    Start-Sleep -Seconds 3
}

# Check if frontend is already running
if (Test-Port 3000) {
    Write-Host "[WARNING] Frontend port 3000 is already in use" -ForegroundColor Yellow
    Write-Host "The frontend may already be running." -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "[2/2] Starting Frontend Server..." -ForegroundColor Green
    Write-Host "      Location: frontend/" -ForegroundColor Gray
    Write-Host "      URL: http://localhost:3000" -ForegroundColor Gray
    
    # Start frontend in a new PowerShell window
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; Write-Host 'Starting Frontend Server...' -ForegroundColor Green; npm start"
    
    Write-Host "      Status: Started in new window" -ForegroundColor Green
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Servers Starting!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API:  http://127.0.0.1:8000" -ForegroundColor White
Write-Host "Frontend App: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "API Docs:     http://127.0.0.1:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop the servers." -ForegroundColor Yellow
Write-Host ""
