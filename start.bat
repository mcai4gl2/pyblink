@echo off
REM Blink Message Playground - Startup Script (Batch)
REM Starts both backend and frontend servers

echo =========================================
echo   Blink Message Playground Startup
echo =========================================
echo.

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
