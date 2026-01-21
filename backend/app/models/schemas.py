"""Pydantic models for API requests and responses."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ConvertRequest(BaseModel):
    """Request model for message conversion."""
    
    schema: str = Field(..., description="Blink schema definition")
    input_format: str = Field(..., description="Input format: tag, json, xml, compact, native")
    input_data: str = Field(..., description="Input message data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema": "namespace Demo\nPerson/1 -> string Name, u32 Age",
                "input_format": "json",
                "input_data": '{"$type":"Demo:Person","Name":"Alice","Age":30}'
            }
        }


class BinaryFieldInfo(BaseModel):
    """Information about a decoded binary field."""
    
    name: str
    value: str | int | float | None
    bytes: str
    offset: Optional[int] = None


class BinaryDecodedView(BaseModel):
    """Decoded view of a binary message."""
    
    size: int
    type_id: int
    ext_offset: Optional[int] = None
    fields: List[BinaryFieldInfo]


class BinaryOutput(BaseModel):
    """Binary format output with hex and decoded views."""
    
    hex: str
    decoded: BinaryDecodedView


class ConvertResponse(BaseModel):
    """Response model for message conversion."""
    
    success: bool
    outputs: Optional[Dict[str, str | BinaryOutput]] = None
    error: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "outputs": {
                    "tag": "@Demo:Person|Name=Alice|Age=30",
                    "json": '{"$type":"Demo:Person","Name":"Alice","Age":30}',
                    "xml": "<Demo:Person><Name>Alice</Name><Age>30</Age></Demo:Person>",
                    "compact_binary": {
                        "hex": "0F 01 05 41 6C 69 63 65 1E",
                        "decoded": {
                            "size": 15,
                            "type_id": 1,
                            "fields": []
                        }
                    },
                    "native_binary": {
                        "hex": "15 00 00 00 01 00 00 00...",
                        "decoded": {
                            "size": 21,
                            "type_id": 1,
                            "ext_offset": 0,
                            "fields": []
                        }
                    }
                }
            }
        }


class ValidateSchemaRequest(BaseModel):
    """Request model for schema validation."""
    
    schema: str = Field(..., description="Blink schema definition")


class GroupInfo(BaseModel):
    """Information about a schema group."""
    
    name: str
    type_id: Optional[int]
    fields: List[Dict[str, str]]


class ValidateSchemaResponse(BaseModel):
    """Response model for schema validation."""
    
    valid: bool
    groups: Optional[List[GroupInfo]] = None
    error: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
