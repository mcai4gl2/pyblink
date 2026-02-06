@echo off
REM Blink Message Playground - Startup Script
REM Starts both backend and frontend servers

echo =========================================
echo   Blink Message Playground Startup
echo =========================================
echo.

REM Check if backend dependencies are installed
if not exist "backend\.venv\Scripts\python.exe" (
    echo ERROR: Backend not set up!
    echo.
    echo Please run setup.bat first to install dependencies:
    echo   setup.bat
    echo.
    pause
    exit /b 1
)

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo ERROR: Frontend not set up!
    echo.
    echo Please run setup.bat first to install dependencies:
    echo   setup.bat
    echo.
    pause
    exit /b 1
)

echo [1/2] Starting Backend Server...
echo       Location: backend/
echo       URL: http://127.0.0.1:8000
start "Blink Backend" cmd /k "cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
echo       Status: Started in new window
echo.

timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend Server...
echo       Location: frontend/
echo       URL: http://localhost:3000
start "Blink Frontend" cmd /k "cd frontend && npm start"
echo       Status: Started in new window
echo.

echo =========================================
echo   Servers Starting!
echo =========================================
echo.
echo Backend API:  http://127.0.0.1:8000
echo Frontend App: http://localhost:3000
echo.
echo API Docs:     http://127.0.0.1:8000/docs
echo.
echo Press Ctrl+C in each window to stop the servers.
echo.
pause
