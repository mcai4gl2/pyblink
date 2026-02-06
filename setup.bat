@echo off
REM Blink Message Playground - Setup Script
REM Installs all dependencies for backend and frontend

echo =========================================
echo   Blink Message Playground Setup
echo =========================================
echo.

echo [1/3] Setting up Backend...
echo       Location: backend/
cd backend

REM Check if virtual environment exists
if exist ".venv" (
    echo       Virtual environment already exists
) else (
    echo       Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo       ERROR: Failed to create virtual environment
        echo       Make sure Python is installed and in PATH
        pause
        exit /b 1
    )
)

echo       Installing Python dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

if errorlevel 1 (
    echo       ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo       Backend setup complete!
echo.

cd ..

echo [2/3] Setting up Frontend...
echo       Location: frontend/
cd frontend

echo       Installing Node dependencies...
call npm install

if errorlevel 1 (
    echo       ERROR: Failed to install Node dependencies
    echo       Make sure Node.js and npm are installed
    pause
    exit /b 1
)

echo       Frontend setup complete!
echo.

cd ..

echo [3/3] Installing PyBlink package...
echo       Location: root/

REM Install in development mode
backend\.venv\Scripts\python.exe -m pip install -e .

if errorlevel 1 (
    echo       WARNING: Failed to install PyBlink package
    echo       This may affect some functionality
)

echo.
echo =========================================
echo   Setup Complete!
echo =========================================
echo.
echo You can now run: start.bat
echo.
pause
