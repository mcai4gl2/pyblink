"""Binary analysis service for Native Binary format.

This service parses Native Binary messages and generates detailed section metadata
with byte offsets, enabling interactive binary inspection in the frontend.
"""

import logging
import struct
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent PyBlink directory to path
pyblink_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(pyblink_root))

from blink.codec import native
from blink.runtime.errors import DecodeError
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import Message
from blink.schema.compiler import compile_schema

logger = logging.getLogger(__name__)


class BinarySection:
    """Represents a section of binary data with metadata."""
    
    def __init__(
        self,
        id: str,
        type: str,
        start_offset: int,
        end_offset: int,
        label: str,
        data_type: Optional[str] = None,
        field_path: Optional[str] = None,
        raw_value: Optional[str] = None,
        interpreted_value: Optional[str] = None,
        color: str = "blue"
    ):
        self.id = id
        self.type = type  # 'header', 'field-name', 'field-value', 'nested'
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.label = label
        self.data_type = data_type
        self.field_path = field_path
        self.raw_value = raw_value
        self.interpreted_value = interpreted_value
        self.color = color
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "startOffset": self.start_offset,
            "endOffset": self.end_offset,
            "label": self.label,
            "dataType": self.data_type,
            "fieldPath": self.field_path,
            "rawValue": self.raw_value,
            "interpretedValue": self.interpreted_value,
            "color": self.color
        }


class MessageField:
    """Represents a field in the message structure."""
    
    def __init__(
        self,
        path: str,
        name: str,
        value: Any,
        type: str,
        binary_section_id: Optional[str] = None,
        children: Optional[List['MessageField']] = None
    ):
        self.path = path
        self.name = name
        self.value = value
        self.type = type
        self.binary_section_id = binary_section_id
        self.children = children or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": self.path,
            "name": self.name,
            "value": self.value,
            "type": self.type,
            "binarySectionId": self.binary_section_id,
            "children": [child.to_dict() for child in self.children]
        }


class NativeBinaryAnalyzer:
    """Analyzes Native Binary messages and generates section metadata."""
    
    def __init__(self, data: bytes, registry: TypeRegistry):
        """Initialize analyzer.
        
        Args:
            data: Native Binary encoded bytes
            registry: Type registry with schema
        """
        self.data = data
        self.registry = registry
        self.sections: List[BinarySection] = []
        self.fields: List[MessageField] = []
        self.offset = 0
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze the binary data and generate section metadata.
        
        Returns:
            Dictionary with sections and fields
        """
        try:
            # Parse header
            self._parse_header()
            
            # Decode the message to get field values
            message, _ = native.decode_native(self.data, self.registry, offset=0)
            
            # Parse body fields
            self._parse_body(message)
            
            return {
                "success": True,
                "sections": [section.to_dict() for section in self.sections],
                "fields": [field.to_dict() for field in self.fields]
            }
            
        except Exception as e:
            logger.error(f"Binary analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "sections": [],
                "fields": []
            }
    
    def _parse_header(self):
        """Parse the Native Binary header (16 bytes)."""
        if len(self.data) < 16:
            raise DecodeError("Data too short for Native Binary header")
        
        # Message Size (4 bytes, u32 little-endian)
        size = struct.unpack("<I", self.data[0:4])[0]
        self.sections.append(BinarySection(
            id="header-size",
            type="header",
            start_offset=0,
            end_offset=4,
            label="Message Size",
            data_type="u32",
            raw_value=self.data[0:4].hex().upper(),
            interpreted_value=f"{size} bytes",
            color="blue"
        ))
        
        # Type ID (8 bytes, u64 little-endian)
        type_id = struct.unpack("<Q", self.data[4:12])[0]
        self.sections.append(BinarySection(
            id="header-type-id",
            type="header",
            start_offset=4,
            end_offset=12,
            label="Type ID",
            data_type="u64",
            raw_value=self.data[4:12].hex().upper(),
            interpreted_value=str(type_id),
            color="blue"
        ))
        
        # Extension Offset (4 bytes, u32 little-endian)
        ext_offset = struct.unpack("<I", self.data[12:16])[0]
        self.sections.append(BinarySection(
            id="header-ext-offset",
            type="header",
            start_offset=12,
            end_offset=16,
            label="Extension Offset",
            data_type="u32",
            raw_value=self.data[12:16].hex().upper(),
            interpreted_value=str(ext_offset),
            color="blue"
        ))
        
        self.offset = 16
    
    def _parse_body(self, message: Message):
        """Parse the message body fields.
        
        Args:
            message: Decoded message
        """
        # Get the group definition
        group = self.registry.get_group_by_id(message.type_id)
        
        # Parse each field
        for field_def in group.all_fields():
            field_name = field_def.name
            field_value = message.fields.get(field_name)
            
            if field_value is not None:
                self._parse_field(field_name, field_value, field_def, path=field_name)
    
    def _parse_field(self, name: str, value: Any, field_def: Any, path: str):
        """Parse a single field and create section metadata.
        
        Args:
            name: Field name
            value: Field value
            field_def: Field definition from schema
            path: JSON path to this field
        """
        # Determine field type
        field_type = self._get_field_type(value, field_def)
        
        # For now, we'll create a simplified section
        # In a full implementation, we would track exact byte positions
        section_id = f"field-{path.replace('.', '-').lower()}"
        
        # Estimate field size and create section
        # This is simplified - actual implementation would need precise offset tracking
        field_start = self.offset
        field_size = self._estimate_field_size(value, field_type)
        field_end = field_start + field_size
        
        # Create binary section
        section = BinarySection(
            id=section_id,
            type="field-value",
            start_offset=field_start,
            end_offset=field_end,
            label=name,
            field_path=path,
            data_type=field_type,
            raw_value=self.data[field_start:field_end].hex().upper() if field_end <= len(self.data) else "",
            interpreted_value=str(value),
            color=self._get_color_for_type(field_type)
        )
        self.sections.append(section)
        
        # Create message field
        field = MessageField(
            path=path,
            name=name,
            value=value,
            type=field_type,
            binary_section_id=section_id
        )
        self.fields.append(field)
        
        # Update offset
        self.offset = field_end
    
    def _get_field_type(self, value: Any, field_def: Any) -> str:
        """Determine the field type.
        
        Args:
            value: Field value
            field_def: Field definition
            
        Returns:
            Type string
        """
        if isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "i32"  # Simplified
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, float):
            return "f64"
        elif isinstance(value, bytes):
            return "binary"
        elif isinstance(value, Message):
            return "object"
        else:
            return "unknown"
    
    def _estimate_field_size(self, value: Any, field_type: str) -> int:
        """Estimate the size of a field in bytes.
        
        Args:
            value: Field value
            field_type: Field type
            
        Returns:
            Estimated size in bytes
        """
        if field_type == "bool":
            return 1
        elif field_type == "i32":
            return 4
        elif field_type == "i64":
            return 8
        elif field_type == "f64":
            return 8
        elif field_type == "string":
            # Length prefix (1-5 bytes VLC) + string bytes
            return 1 + len(str(value).encode('utf-8'))
        elif field_type == "binary":
            return len(value) if isinstance(value, bytes) else 0
        else:
            return 4  # Default estimate
    
    def _get_color_for_type(self, field_type: str) -> str:
        """Get color coding for field type.
        
        Args:
            field_type: Field type
            
        Returns:
            Color name
        """
        color_map = {
            "string": "green",
            "i32": "yellow",
            "i64": "yellow",
            "u32": "yellow",
            "u64": "yellow",
            "f64": "yellow",
            "bool": "purple",
            "binary": "orange",
            "object": "pink"
        }
        return color_map.get(field_type, "gray")


def analyze_native_binary(
    schema_text: str,
    binary_hex: str
) -> Dict[str, Any]:
    """Analyze a Native Binary message and generate section metadata.
    
    Args:
        schema_text: Blink schema definition
        binary_hex: Hex string of Native Binary data
        
    Returns:
        Analysis result with sections and fields
    """
    try:
        # Compile schema
        schema = compile_schema(schema_text)
        registry = TypeRegistry(schema)
        
        # Convert hex to bytes
        binary_data = bytes.fromhex(binary_hex.replace(" ", "").replace("\n", ""))
        
        # Create analyzer and analyze
        analyzer = NativeBinaryAnalyzer(binary_data, registry)
        return analyzer.analyze()
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "sections": [],
            "fields": []
        }
