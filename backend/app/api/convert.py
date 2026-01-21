"""API endpoints for message conversion."""

import logging

from fastapi import APIRouter

from app.models.schemas import ConvertRequest, ConvertResponse
from app.services.converter import convert_message

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/convert", response_model=ConvertResponse)
async def convert(request: ConvertRequest):
    """Convert a Blink message between formats.
    
    Args:
        request: Conversion request with schema, input format, and data
        
    Returns:
        ConvertResponse with all format outputs or error
    """
    logger.info(f"Convert request: format={request.input_format}")
    
    # Validate input format
    valid_formats = ["tag", "json", "xml", "compact", "native"]
    if request.input_format.lower() not in valid_formats:
        return ConvertResponse(
            success=False,
            error=f"Invalid input format. Must be one of: {', '.join(valid_formats)}"
        )
    
    # Perform conversion
    success, outputs, error = convert_message(
        request.schema,
        request.input_format.lower(),
        request.input_data
    )
    
    if success:
        return ConvertResponse(
            success=True,
            outputs=outputs
        )
    else:
        return ConvertResponse(
            success=False,
            error=error
        )


@router.post("/validate-schema")
async def validate_schema(request: dict):
    """Validate a Blink schema.
    
    Args:
        request: Schema validation request
        
    Returns:
        Validation result
    """
    from app.services.converter import compile_blink_schema
    from blink.runtime.errors import SchemaError
    
    schema_text = request.get("schema", "")
    
    try:
        registry = compile_blink_schema(schema_text)
        
        # Extract group information from registry
        groups = []
        for group_name, group in registry._by_name.items():
            fields = []
            for field in group.all_fields():
                fields.append({
                    "name": field.name,
                    "type": str(field.type_ref)
                })
            
            groups.append({
                "name": group_name,
                "type_id": group.type_id,
                "fields": fields
            })
        
        return {
            "valid": True,
            "groups": groups
        }
        
    except SchemaError as e:
        return {
            "valid": False,
            "error": str(e)
        }
    except Exception as e:
        logger.exception("Unexpected error in validate_schema")
        return {
            "valid": False,
            "error": f"Unexpected error: {str(e)}"
        }
