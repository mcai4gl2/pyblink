# Blink Message Playground - Makefile
# Cross-platform build and run commands

.PHONY: help start start-backend start-frontend stop install test clean

# Default target
help:
	@echo "========================================="
	@echo "  Blink Message Playground - Commands"
	@echo "========================================="
	@echo ""
	@echo "Available targets:"
	@echo "  make start          - Start both backend and frontend"
	@echo "  make start-backend  - Start only the backend server"
	@echo "  make start-frontend - Start only the frontend server"
	@echo "  make install        - Install all dependencies"
	@echo "  make test           - Run all tests"
	@echo "  make test-backend   - Run backend tests"
	@echo "  make clean          - Clean build artifacts"
	@echo ""
	@echo "URLs:"
	@echo "  Backend:  http://127.0.0.1:8000"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API Docs: http://127.0.0.1:8000/docs"
	@echo ""

# Start both servers (Windows)
ifeq ($(OS),Windows_NT)
start:
	@echo "Starting servers on Windows..."
	@powershell -ExecutionPolicy Bypass -File start.ps1
else
# Start both servers (Unix/Linux/Mac)
start:
	@echo "========================================="
	@echo "  Starting Blink Message Playground"
	@echo "========================================="
	@echo ""
	@echo "[1/2] Starting Backend Server..."
	@cd backend && .venv/bin/python -m uvicorn app.main:app --reload --port 8000 &
	@echo "      Backend: http://127.0.0.1:8000"
	@echo ""
	@echo "[2/2] Starting Frontend Server..."
	@cd frontend && npm start &
	@echo "      Frontend: http://localhost:3000"
	@echo ""
	@echo "Press Ctrl+C to stop both servers."
endif

# Start backend only
start-backend:
	@echo "Starting Backend Server..."
ifeq ($(OS),Windows_NT)
	@cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
else
	@cd backend && .venv/bin/python -m uvicorn app.main:app --reload --port 8000
endif

# Start frontend only
start-frontend:
	@echo "Starting Frontend Server..."
	@cd frontend && npm start

# Install all dependencies
install:
	@echo "========================================="
	@echo "  Installing Dependencies"
	@echo "========================================="
	@echo ""
	@echo "[1/2] Installing Backend Dependencies..."
ifeq ($(OS),Windows_NT)
	@cd backend && python -m venv .venv && .venv\Scripts\pip.exe install -r requirements.txt
else
	@cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
endif
	@echo ""
	@echo "[2/2] Installing Frontend Dependencies..."
	@cd frontend && npm install
	@echo ""
	@echo "Installation complete!"

# Run all tests
test: test-backend
	@echo "All tests complete!"

# Run backend tests
test-backend:
	@echo "Running Backend Tests..."
ifeq ($(OS),Windows_NT)
	@cd backend && .venv\Scripts\python.exe -m pytest tests/ -v
else
	@cd backend && .venv/bin/python -m pytest tests/ -v
endif

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete!"
