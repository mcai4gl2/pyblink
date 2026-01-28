"""Binary analysis service for Native Binary format.

This service parses Native Binary messages and generates detailed section metadata
with byte offsets, enabling interactive binary inspection in the frontend.
"""

import logging
import struct
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent PyBlink directory to path
pyblink_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(pyblink_root))

from blink.runtime.errors import DecodeError
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import DecimalValue, Message, StaticGroupValue
from blink.schema.compiler import compile_schema
from blink.schema.model import (
    BinaryType,
    DynamicGroupRef,
    EnumType,
    GroupDef,
    ObjectType,
    PrimitiveKind,
    PrimitiveType,
    SequenceType,
    StaticGroupRef,
    TypeRef,
)

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
        self.type = type  # 'header', 'field-name', 'field-value', 'nested', 'pointer', 'data'
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
    """Analyzes Native Binary messages and generates section metadata with precise offset tracking."""
    
    def __init__(self, data: bytes, registry: TypeRegistry):
        self.data = data
        self.mv = memoryview(data)
        self.registry = registry
        self.sections: List[BinarySection] = []
        self.fields: List[MessageField] = []
        
    def analyze(self) -> Dict[str, Any]:
        """Analyze the binary data."""
        try:
            self._decode_message_recursive(
                offset=0, 
                path="", 
                is_root=True
            )
            
            return {
                "success": True,
                "sections": [section.to_dict() for section in self.sections],
                "fields": [field.to_dict() for field in self.fields]
            }
        except Exception as e:
            logger.error(f"Binary analysis failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "sections": [],
                "fields": []
            }

    def _decode_message_recursive(self, offset: int, path: str, is_root: bool = False) -> Tuple[Message, int]:
        """Decode a message and record sections."""
        start_offset = offset
        
        # 1. Size (4 bytes)
        if offset + 4 > len(self.mv):
            raise DecodeError("Truncated message size")
        size = struct.unpack('<I', self.mv[offset:offset+4])[0]
        
        if is_root:
            self.sections.append(BinarySection(
                id="header-size", type="header", start_offset=offset, end_offset=offset+4,
                label="Message Size", data_type="u32", 
                interpreted_value=f"{size} bytes", color="blue"
            ))
        offset += 4
        
        end = offset + size if is_root else offset + size # Wait, this logic depends on where 'size' is relative to. 
        # In Native format root message: size includes everything AFTER size preamble. 
        # Actually in decode_native: end = offset + size (where offset is 4).
        # So size is bytes FOLLOWING the size field.
        
        # 2. Type ID (8 bytes)
        type_id = struct.unpack('<Q', self.mv[offset:offset+8])[0]
        if is_root:
            self.sections.append(BinarySection(
                id="header-type-id", type="header", start_offset=offset, end_offset=offset+8,
                label="Type ID", data_type="u64", 
                interpreted_value=str(type_id), color="blue"
            ))
        offset += 8
        
        # 3. Extension Offset (4 bytes)
        ext_offset_pos = offset
        ext_offset = struct.unpack('<I', self.mv[offset:offset+4])[0]
        if is_root:
            self.sections.append(BinarySection(
                id="header-ext-offset", type="header", start_offset=offset, end_offset=offset+4,
                label="Ext Offset", data_type="u32", 
                interpreted_value=str(ext_offset), color="blue"
            ))
        offset += 4
        
        # Get Group
        group = self.registry.get_group_by_id(type_id)
        if not group:
            raise DecodeError(f"Unknown type ID: {type_id}")
            
        # Decode fields
        fields_dict, offset = self._decode_group_fields(group, offset, path)
        
        # Decode extensions (skip for now to keep simple, logic is similar)
        
        return Message(type_name=group.name, fields=fields_dict), offset

    def _decode_group_fields(self, group: GroupDef, offset: int, base_path: str) -> Tuple[Dict[str, Any], int]:
        fields = {}
        
        for field in group.all_fields():
            field_path = f"{base_path}.{field.name}" if base_path else field.name
            
            # Record start of field in fixed area
            field_start = offset
            
            value, offset = self._decode_field(
                field.type_ref, offset, field.optional, field.name, field_path
            )
            
            if value is not None:
                fields[field.name] = value
                
                # Check if we already added a section for this field (e.g. pointer)
                # If it was a primitive inline field, we should add a section now
                # If it was a variable field, _decode_field added the pointer/data sections
                
                # Heuristic: if no section added for this exact range, add one
                # Actually _decode_value should prevent handling this here to allow specific type handling
                pass

        return fields, offset

    def _decode_field(self, type_ref: TypeRef, offset: int, optional: bool, name: str, path: str) -> Tuple[Any, int]:
        if optional:
            presence = self.mv[offset]
            self.sections.append(BinarySection(
                id=f"presence-{path}", type="presence", start_offset=offset, end_offset=offset+1,
                label=f"{name}?", data_type="bool", interpreted_value="Present" if presence else "Null", color="purple"
            ))
            offset += 1
            
            if presence == 0x00:
                 # Skip zero bytes for null field
                size = self._get_fixed_size(type_ref)
                self.sections.append(BinarySection(
                    id=f"null-{path}", type="padding", start_offset=offset, end_offset=offset+size,
                    label=f"{name} (Null)", data_type="padding", interpreted_value="Null", color="gray"
                ))
                return None, offset + size
        
        return self._decode_value(type_ref, offset, name, path)

    def _decode_value(self, type_ref: TypeRef, offset: int, name: str, path: str) -> Tuple[Any, int]:
        
        section_id = f"field-{path.replace('.', '-').lower()}"
        
        # Primitives
        if isinstance(type_ref, PrimitiveType):
            fmt, size, py_type, color = self._get_primitive_info(type_ref.primitive)
            val = struct.unpack(fmt, self.mv[offset:offset+size])[0]
            
            # Decimal special handling
            if type_ref.primitive == PrimitiveKind.DECIMAL:
                 # exp (1) + mant (8)
                 exp = struct.unpack('<b', self.mv[offset:offset+1])[0]
                 mant = struct.unpack('<q', self.mv[offset+1:offset+9])[0]
                 val = DecimalValue(exp, mant)
                 
            self.sections.append(BinarySection(
                id=section_id, type="field-value", start_offset=offset, end_offset=offset+size,
                label=name, field_path=path, data_type=py_type, 
                interpreted_value=str(val), color=color
            ))
            
            self.fields.append(MessageField(path, name, str(val), py_type, section_id))
            return val, offset + size

        # Strings / Binary
        if isinstance(type_ref, BinaryType):
            if type_ref.kind == "string":
                 # Variable or Inline?
                 # Assuming variable for simplified logic unless type_ref specifies size
                 # Native format supports inline strings if size is set
                 if type_ref.size and 1 <= type_ref.size <= 255:
                     # Inline string
                     size_byte = self.mv[offset]
                     capacity = type_ref.size
                     str_bytes = bytes(self.mv[offset+1:offset+1+size_byte])
                     val = str_bytes.decode('utf-8')
                     
                     self.sections.append(BinarySection(
                         id=section_id, type="field-value", start_offset=offset, end_offset=offset+1+capacity,
                         label=name, field_path=path, data_type="string (inline)",
                         interpreted_value=val, color="green"
                     ))
                     self.fields.append(MessageField(path, name, val, "string", section_id))
                     return val, offset + 1 + capacity
                 else:
                     # Pointer string
                     rel_offset = struct.unpack('<I', self.mv[offset:offset+4])[0]
                     
                     # 1. Pointer Section
                     self.sections.append(BinarySection(
                         id=f"{section_id}-ptr", type="pointer", start_offset=offset, end_offset=offset+4,
                         label=f"{name}Ptr", field_path=path, data_type="u32",
                         interpreted_value=f"-> +{rel_offset}", color="orange"
                     ))
                     
                     # 2. Data Section
                     data_loc = offset + rel_offset
                     data_size = struct.unpack('<I', self.mv[data_loc:data_loc+4])[0]
                     str_bytes = bytes(self.mv[data_loc+4:data_loc+4+data_size])
                     val = str_bytes.decode('utf-8')
                     
                     self.sections.append(BinarySection(
                         id=section_id, type="field-value", start_offset=data_loc, end_offset=data_loc+4+data_size,
                         label=name, field_path=path, data_type="string",
                         interpreted_value=val, color="green"
                     ))
                     
                     self.fields.append(MessageField(path, name, val, "string", section_id))
                     return val, offset + 4
        
        # Nested Objects
        if isinstance(type_ref, ObjectType):
             rel_offset = struct.unpack('<I', self.mv[offset:offset+4])[0]
             
             self.sections.append(BinarySection(
                 id=f"{section_id}-ptr", type="pointer", start_offset=offset, end_offset=offset+4,
                 label=f"{name}Ptr", field_path=path, data_type="u32",
                 interpreted_value=f"-> +{rel_offset}", color="pink"
             ))
             
             data_loc = offset + rel_offset
             
             # Recursively decode
             decoded_msg, _ = self._decode_message_recursive(data_loc, path)
             
             self.fields.append(MessageField(path, name, "Nested Message", "object", section_id))
             return decoded_msg, offset + 4

        # Check for other variable types (Sequence, DynamicGroup, etc)
        # Simplified for MVP: Treat others as "Unknown" or just pointer skips if complex
        # Implement Sequence (common)
        if isinstance(type_ref, SequenceType):
             rel_offset = struct.unpack('<I', self.mv[offset:offset+4])[0]
             
             self.sections.append(BinarySection(
                 id=f"{section_id}-ptr", type="pointer", start_offset=offset, end_offset=offset+4,
                 label=f"{name}Ptr", field_path=path, data_type="u32",
                 interpreted_value=f"-> +{rel_offset}", color="orange"
             ))
             
             # Recursion would be needed for content
             # For MVP, just mark the pointer
             
             self.fields.append(MessageField(path, name, "Sequence[...] (Details WIP)", "sequence", f"{section_id}-ptr"))
             return [], offset + 4

        # Fallback
        return None, offset + 4

    def _get_fixed_size(self, type_ref: TypeRef) -> int:
        if isinstance(type_ref, PrimitiveType):
            _, size, _, _ = self._get_primitive_info(type_ref.primitive)
            return size
        return 4 # Check Native spec for others
        
    def _get_primitive_info(self, kind: PrimitiveKind) -> Tuple[str, int, str, str]:
        # returns (struct_fmt, size, type_name, color)
        info = {
            PrimitiveKind.BOOL: ('<B', 1, "bool", "purple"),
            PrimitiveKind.U8: ('<B', 1, "u8", "yellow"),
            PrimitiveKind.I8: ('<b', 1, "i8", "yellow"),
            PrimitiveKind.U16: ('<H', 2, "u16", "yellow"),
            PrimitiveKind.I16: ('<h', 2, "i16", "yellow"),
            PrimitiveKind.U32: ('<I', 4, "u32", "yellow"),
            PrimitiveKind.I32: ('<i', 4, "i32", "yellow"),
            PrimitiveKind.U64: ('<Q', 8, "u64", "yellow"),
            PrimitiveKind.I64: ('<q', 8, "i64", "yellow"),
            PrimitiveKind.F64: ('<d', 8, "f64", "yellow"),
            PrimitiveKind.DECIMAL: ('<x', 9, "decimal", "yellow"), # Special
        }
        return info.get(kind, ('<I', 4, "unknown", "gray"))


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
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "sections": [],
            "fields": []
        }

