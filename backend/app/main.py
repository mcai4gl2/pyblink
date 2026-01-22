"""FastAPI application for Blink Message Playground."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Blink Message Playground API",
    description="API for converting Blink messages between different formats",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "blink-playground-api"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Blink Message Playground API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Import and include routers
from app.api import convert, storage
from app.services.storage import cleanup_old_playgrounds

app.include_router(convert.router, prefix="/api", tags=["convert"])
app.include_router(storage.router)


@app.on_event("startup")
async def startup_event():
    """Run cleanup on application startup."""
    logger.info("Running startup cleanup of old playgrounds...")
    deleted, errors = cleanup_old_playgrounds()
    logger.info(f"Startup cleanup complete: deleted {deleted}, errors {errors}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
