"""API endpoints for binary analysis."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.binary_analyzer import analyze_native_binary

logger = logging.getLogger(__name__)

router = APIRouter()


class AnalyzeBinaryRequest(BaseModel):
    """Request model for binary analysis."""
    schema: str
    binary_hex: str
    format: str = "native"  # Currently only supports 'native'


class AnalyzeBinaryResponse(BaseModel):
    """Response model for binary analysis."""
    success: bool
    sections: list = []
    fields: list = []
    error: str | None = None


@router.post("/analyze-binary", response_model=AnalyzeBinaryResponse)
async def analyze_binary(request: AnalyzeBinaryRequest):
    """Analyze a Native Binary message and generate section metadata.
    
    This endpoint parses a Native Binary message and returns detailed
    section metadata with byte offsets, enabling interactive binary
    inspection in the frontend.
    
    Args:
        request: Analysis request with schema and binary hex data
        
    Returns:
        AnalyzeBinaryResponse with sections and fields or error
    """
    logger.info(f"Binary analysis request: format={request.format}")
    
    # Validate format
    if request.format.lower() != "native":
        return AnalyzeBinaryResponse(
            success=False,
            error="Currently only 'native' format is supported"
        )
    
    # Perform analysis
    result = analyze_native_binary(
        request.schema,
        request.binary_hex
    )
    
    return AnalyzeBinaryResponse(
        success=result["success"],
        sections=result.get("sections", []),
        fields=result.get("fields", []),
        error=result.get("error")
    )
