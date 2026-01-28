"""Conversion service for Blink messages."""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

# Add parent PyBlink directory to path
pyblink_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(pyblink_root))

from blink.codec import compact, jsonfmt, native, tag, xmlfmt
from blink.runtime.errors import DecodeError, EncodeError, SchemaError
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import Message
from blink.schema.compiler import compile_schema

logger = logging.getLogger(__name__)


def compile_blink_schema(schema_text: str) -> TypeRegistry:
    """Compile Blink schema text into a TypeRegistry.
    
    Args:
        schema_text: Blink schema definition
        
    Returns:
        TypeRegistry with compiled schema
        
    Raises:
        SchemaError: If schema is invalid
    """
    try:
        schema = compile_schema(schema_text)
        return TypeRegistry(schema)
    except Exception as e:
        logger.error(f"Schema compilation failed: {e}")
        raise SchemaError(str(e))


def decode_message(
    input_format: str,
    input_data: str,
    registry: TypeRegistry
) -> Message:
    """Decode message from input format.
    
    Args:
        input_format: Format name (tag, json, xml, compact, native)
        input_data: Input data string
        registry: Type registry with schema
        
    Returns:
        Decoded Message object
        
    Raises:
        DecodeError: If decoding fails
    """
    try:
        if input_format == "tag":
            return tag.decode_tag(input_data, registry)
        
        elif input_format == "json":
            return jsonfmt.decode_json(input_data, registry)
        
        elif input_format == "xml":
            return xmlfmt.decode_xml(input_data, registry)
        
        elif input_format == "compact":
            # Convert hex string to bytes
            hex_bytes = bytes.fromhex(input_data.replace(" ", "").replace("\n", ""))
            message, _ = compact.decode_message(hex_bytes, registry=registry, offset=0)
            return message
        
        elif input_format == "native":
            # Convert hex string to bytes
            hex_bytes = bytes.fromhex(input_data.replace(" ", "").replace("\n", ""))
            message, _ = native.decode_native(hex_bytes, registry, offset=0)
            return message
        
        else:
            raise DecodeError(f"Unknown input format: {input_format}")
            
    except Exception as e:
        logger.error(f"Decode failed for format {input_format}: {e}")
        raise DecodeError(f"Failed to decode {input_format}: {str(e)}")


def encode_to_all_formats(
    message: Message,
    registry: TypeRegistry
) -> Dict[str, Any]:
    """Encode message to all supported formats.
    
    Args:
        message: Message to encode
        registry: Type registry with schema
        
    Returns:
        Dictionary with all format outputs
    """
    outputs = {}
    
    try:
        # Tag format
        outputs["tag"] = tag.encode_tag(message, registry)
    except Exception as e:
        logger.warning(f"Tag encoding failed: {e}")
        outputs["tag"] = f"Error: {str(e)}"
    
    try:
        # JSON format
        outputs["json"] = jsonfmt.encode_json(message, registry)
    except Exception as e:
        logger.warning(f"JSON encoding failed: {e}")
        outputs["json"] = f"Error: {str(e)}"
    
    try:
        # XML format
        outputs["xml"] = xmlfmt.encode_xml(message, registry)
    except Exception as e:
        logger.warning(f"XML encoding failed: {e}")
        outputs["xml"] = f"Error: {str(e)}"
    
    try:
        # Compact Binary format
        compact_bytes = compact.encode_message(message, registry)
        outputs["compact_binary"] = {
            "hex": format_hex(compact_bytes),
            "rawHex": compact_bytes.hex(),
            "decoded": decode_compact_binary(compact_bytes, message, registry)
        }
    except Exception as e:
        logger.warning(f"Compact binary encoding failed: {e}")
        outputs["compact_binary"] = {"hex": f"Error: {str(e)}", "rawHex": "", "decoded": {}}
    
    try:
        # Native Binary format
        native_bytes = native.encode_native(message, registry)
        outputs["native_binary"] = {
            "hex": format_hex(native_bytes),
            "rawHex": native_bytes.hex(),
            "decoded": decode_native_binary(native_bytes, message, registry)
        }
    except Exception as e:
        logger.warning(f"Native binary encoding failed: {e}")
        outputs["native_binary"] = {"hex": f"Error: {str(e)}", "rawHex": "", "decoded": {}}
    
    return outputs


def format_hex(data: bytes, bytes_per_row: int = 16) -> str:
    """Format bytes as hex string with spacing.
    
    Args:
        data: Bytes to format
        bytes_per_row: Number of bytes per row
        
    Returns:
        Formatted hex string
    """
    hex_str = data.hex().upper()
    # Add space every 2 characters (1 byte)
    spaced = " ".join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
    
    # Split into rows
    bytes_list = spaced.split(" ")
    rows = []
    for i in range(0, len(bytes_list), bytes_per_row):
        row_bytes = bytes_list[i:i+bytes_per_row]
        offset = f"{i:04X}: "
        rows.append(offset + " ".join(row_bytes))
    
    return "\n".join(rows)


def decode_compact_binary(
    data: bytes,
    message: Message,
    registry: TypeRegistry
) -> Dict[str, Any]:
    """Create decoded view of compact binary message.
    
    Args:
        data: Encoded bytes
        message: Original message
        registry: Type registry
        
    Returns:
        Decoded view dictionary
    """
    try:
        # Parse basic structure
        from blink.codec.vlc import decode_vlc
        
        offset = 0
        size, offset = decode_vlc(data, offset)
        type_id, offset = decode_vlc(data, offset)
        
        # Get group info
        group = registry.get_group_by_id(type_id)
        
        fields = []
        for field in group.all_fields():
            field_name = field.name
            field_value = message.fields.get(field_name)
            
            fields.append({
                "name": field_name,
                "value": str(field_value) if field_value is not None else "null",
                "bytes": ""  # TODO: Extract actual bytes
            })
        
        return {
            "size": size if size is not None else len(data),
            "type_id": type_id,
            "fields": fields
        }
    except Exception as e:
        logger.error(f"Failed to decode compact binary view: {e}")
        return {"size": len(data), "type_id": 0, "fields": []}


def decode_native_binary(
    data: bytes,
    message: Message,
    registry: TypeRegistry
) -> Dict[str, Any]:
    """Create decoded view of native binary message.
    
    Args:
        data: Encoded bytes
        message: Original message
        registry: Type registry
        
    Returns:
        Decoded view dictionary
    """
    try:
        import struct
        
        # Parse header
        size = struct.unpack("<I", data[0:4])[0]
        type_id = struct.unpack("<Q", data[4:12])[0]
        ext_offset = struct.unpack("<I", data[12:16])[0]
        
        # Get group info
        group = registry.get_group_by_id(type_id)
        
        fields = []
        for field in group.all_fields():
            field_name = field.name
            field_value = message.fields.get(field_name)
            
            fields.append({
                "name": field_name,
                "value": str(field_value) if field_value is not None else "null",
                "bytes": "",  # TODO: Extract actual bytes
                "offset": None  # TODO: Calculate offset
            })
        
        return {
            "size": size,
            "type_id": type_id,
            "ext_offset": ext_offset,
            "fields": fields
        }
    except Exception as e:
        logger.error(f"Failed to decode native binary view: {e}")
        return {"size": len(data), "type_id": 0, "ext_offset": 0, "fields": []}


def convert_message(
    schema_text: str,
    input_format: str,
    input_data: str
) -> Tuple[bool, Dict[str, Any] | None, str | None]:
    """Convert a message between formats.
    
    Args:
        schema_text: Blink schema definition
        input_format: Input format name
        input_data: Input message data
        
    Returns:
        Tuple of (success, outputs_dict, error_message)
    """
    try:
        # Compile schema
        registry = compile_blink_schema(schema_text)
        
        # Decode input
        message = decode_message(input_format, input_data, registry)
        
        # Encode to all formats
        outputs = encode_to_all_formats(message, registry)
        
        return True, outputs, None
        
    except SchemaError as e:
        return False, None, f"Schema error: {str(e)}"
    except DecodeError as e:
        return False, None, f"Decode error: {str(e)}"
    except EncodeError as e:
        return False, None, f"Encode error: {str(e)}"
    except Exception as e:
        logger.exception("Unexpected error in convert_message")
        return False, None, f"Unexpected error: {str(e)}"
