"""Storage API endpoints for save/load functionality."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services import storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["storage"])


# Request/Response Models

class SavePlaygroundRequest(BaseModel):
    """Request model for saving a playground."""
    schema_content: str = Field(..., alias="schema", description="Blink schema definition")
    input_format: str = Field(..., description="Input format (tag, json, xml, compact, native)")
    input_data: str = Field(..., description="Input message data")
    title: Optional[str] = Field(None, description="Optional playground title")
    description: Optional[str] = Field(None, description="Optional playground description")


class SavePlaygroundResponse(BaseModel):
    """Response model for save operation."""
    success: bool
    playground_id: str
    url: str
    message: str


class LoadPlaygroundResponse(BaseModel):
    """Response model for load operation."""
    success: bool
    playground: Optional[dict] = None
    error: Optional[str] = None


class StorageStatsResponse(BaseModel):
    """Response model for storage statistics."""
    total_playgrounds: int
    retention_days: int


# API Endpoints

@router.post("/save", response_model=SavePlaygroundResponse)
async def save_playground(request: SavePlaygroundRequest):
    """Save a playground and return shareable URL.
    
    Args:
        request: Save playground request
        
    Returns:
        Save response with playground ID and URL
        
    Raises:
        HTTPException: If save fails
    """
    try:
        # Validate input format
        valid_formats = ["tag", "json", "xml", "compact", "native"]
        if request.input_format not in valid_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid input_format. Must be one of: {', '.join(valid_formats)}"
            )
        
        # Save playground
        playground_id, file_path = storage.save_playground(
            schema=request.schema_content,
            input_format=request.input_format,
            input_data=request.input_data,
            title=request.title,
            description=request.description
        )
        
        # Generate shareable URL (frontend will use this)
        url = f"?p={playground_id}"
        
        logger.info(f"Saved playground {playground_id}")
        
        return SavePlaygroundResponse(
            success=True,
            playground_id=playground_id,
            url=url,
            message=f"Playground saved successfully with ID: {playground_id}"
        )
        
    except IOError as e:
        logger.error(f"IO error saving playground: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error saving playground: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save playground: {str(e)}")


@router.get("/load/{playground_id}", response_model=LoadPlaygroundResponse)
async def load_playground(playground_id: str):
    """Load a playground by ID.
    
    Args:
        playground_id: Playground ID
        
    Returns:
        Load response with playground data
        
    Raises:
        HTTPException: If playground not found or load fails
    """
    try:
        # Validate ID format (alphanumeric, 8 chars)
        if not playground_id.isalnum() or len(playground_id) != 8:
            raise HTTPException(
                status_code=400,
                detail="Invalid playground ID format"
            )
        
        # Load playground
        playground_data = storage.load_playground(playground_id)
        
        if playground_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"Playground {playground_id} not found"
            )
        
        logger.info(f"Loaded playground {playground_id}")
        
        return LoadPlaygroundResponse(
            success=True,
            playground=playground_data
        )
        
    except HTTPException:
        raise
    except IOError as e:
        logger.error(f"IO error loading playground: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error loading playground: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load playground: {str(e)}")


@router.get("/storage/stats", response_model=StorageStatsResponse)
async def get_storage_stats():
    """Get storage statistics.
    
    Returns:
        Storage statistics
    """
    try:
        total = storage.get_playground_count()
        
        return StorageStatsResponse(
            total_playgrounds=total,
            retention_days=storage.RETENTION_DAYS
        )
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/storage/cleanup")
async def trigger_cleanup():
    """Manually trigger cleanup of old playgrounds.
    
    Returns:
        Cleanup results
    """
    try:
        deleted, errors = storage.cleanup_old_playgrounds()
        
        return {
            "success": True,
            "deleted_count": deleted,
            "error_count": errors,
            "message": f"Cleanup complete: deleted {deleted} playgrounds, {errors} errors"
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))
