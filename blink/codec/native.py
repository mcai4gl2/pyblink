"""Native Binary Format codec for Blink protocol.

The Native format uses fixed-width fields with predictable offsets.
Variable-sized values are placed in a data area with relative offsets.

Message Structure:
    u32 size        - Number of bytes following
    u64 typeId      - Schema type identifier  
    u32 extOffset   - Relative offset to extensions (0 if none)
    fields...       - Fixed-width fields
    data area       - Variable-sized values

Key differences from Compact format:
- Fixed-width fields at predictable offsets
- Little-endian byte order
- Relative offsets for variable data
- Optional fields have presence byte
- Inline strings for small fixed-capacity strings
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..runtime.errors import DecodeError, EncodeError
from ..runtime.registry import TypeRegistry
from ..runtime.values import DecimalValue, Message, StaticGroupValue
from ..schema.model import (
    BinaryType,
    DynamicGroupRef,
    EnumType,
    GroupDef,
    ObjectType,
    PrimitiveKind,
    PrimitiveType,
    QName,
    SequenceType,
    StaticGroupRef,
    TypeRef,
)


@dataclass(frozen=True, slots=True)
class NativeFrame:
    """Represents a decoded Native Binary message frame."""

    type_id: int
    payload: bytes
    size: int
    ext_offset: int
    group: GroupDef | None = None


class _DataAreaBuilder:
    """Helper to build data area and track offsets."""
    
    def __init__(self):
        self.buffer = bytearray()
        self.base_offset = 0  # Will be set to start of data area
    
    def add_data(self, data: bytes, field_position: int) -> int:
        """Add data and return relative offset from field_position."""
        # Offset is relative to the field itself
        offset = self.base_offset + len(self.buffer) - field_position
        self.buffer.extend(data)
        return offset
    
    def get_data(self) -> bytes:
        return bytes(self.buffer)


def encode_native(message: Message, registry: TypeRegistry) -> bytes:
    """Encode a message to Native Binary format.
    
    Args:
        message: Message to encode
        registry: Type registry for schema lookup
        
    Returns:
        Encoded bytes in Native Binary format
    """
    group = registry.get_group_by_name(message.type_name)
    if group.type_id is None:
        raise EncodeError(f"Group {group.name} is missing a type id")
    
    # Calculate fixed field sizes first
    fixed_size = 12  # typeId (8) + extOffset (4)
    for field in group.all_fields():
        if field.optional:
            fixed_size += 1  # presence byte
        fixed_size += _get_field_size(field.type_ref, registry)
    
    # Build data area with proper offsets
    data_builder = _DataAreaBuilder()
    data_builder.base_offset = fixed_size
    
    # Encode fields
    fields_data = _encode_group_fields(group, message.fields, data_builder, registry)
    
    # Encode extensions if present
    ext_offset = 0
    if message.extensions:
        # Extension offset is relative to the extOffset field (at offset 8)
        ext_offset = data_builder.base_offset + len(data_builder.buffer) - 8
        ext_data = _encode_extensions(message.extensions, registry)
        data_builder.buffer.extend(ext_data)
    
    # Build message: size + typeId + extOffset + fields + data
    type_id_bytes = struct.pack('<Q', group.type_id)
    ext_offset_bytes = struct.pack('<I', ext_offset)
    
    body = type_id_bytes + ext_offset_bytes + fields_data + data_builder.get_data()
    size_bytes = struct.pack('<I', len(body))
    
    return size_bytes + body


def decode_native(buffer: bytes | memoryview, registry: TypeRegistry, offset: int = 0) -> Tuple[Message, int]:
    """Decode a message from Native Binary format.
    
    Args:
        buffer: Raw bytes containing Native Binary message
        registry: Type registry for schema lookup
        offset: Starting offset in buffer
        
    Returns:
        Tuple of (decoded Message, next offset)
    """
    mv = memoryview(buffer)
    
    # Read size preamble (u32)
    if offset + 4 > len(mv):
        raise DecodeError("Truncated message: missing size preamble")
    size = struct.unpack('<I', mv[offset:offset+4])[0]
    offset += 4
    
    # Validate size
    if size < 12:  # Minimum: 8 (typeId) + 4 (extOffset)
        raise DecodeError(f"Invalid size: {size} (minimum 12)")
    
    end = offset + size
    if end > len(mv):
        raise DecodeError(f"Truncated message: size {size} exceeds buffer")
    
    # Read type ID (u64)
    type_id = struct.unpack('<Q', mv[offset:offset+8])[0]
    offset += 8
    
    # Read extension offset (u32)
    ext_offset_field_pos = offset
    ext_offset = struct.unpack('<I', mv[offset:offset+4])[0]
    offset += 4
    
    # Get group definition
    group = registry.get_group_by_id(type_id)
    
    # Decode fields
    fields, new_offset = _decode_group_fields(group, mv, offset, end, registry)
    
    # Decode extensions if present
    extensions: Tuple[Message, ...] = tuple()
    if ext_offset > 0:
        # Extension offset is relative to the extOffset field itself
        ext_location = ext_offset_field_pos + ext_offset
        extensions = _decode_extensions(mv, ext_location, end, registry)
    
    message = Message(type_name=group.name, fields=fields, extensions=extensions)
    return message, end


def _encode_group_fields(
    group: GroupDef,
    values: Dict[str, object],
    data_builder: _DataAreaBuilder,
    registry: TypeRegistry
) -> bytes:
    """Encode a group's fields.
    
    Returns:
        Fixed-width field bytes
    """
    fields_buffer = bytearray()
    
    for field in group.all_fields():
        value = values.get(field.name)
        if value is None and not field.optional:
            raise EncodeError(f"Missing required field {field.name}")
        
        # Field position is 12 (typeId + extOffset) + current buffer length
        field_position = 12 + len(fields_buffer)
        field_bytes = _encode_field(
            field.type_ref,
            value,
            field.optional,
            field_position,
            data_builder,
            registry
        )
        fields_buffer.extend(field_bytes)
    
    return bytes(fields_buffer)


def _encode_field(
    type_ref: TypeRef,
    value,
    optional: bool,
    field_position: int,
    data_builder: _DataAreaBuilder,
    registry: TypeRegistry
) -> bytes:
    """Encode a single field.
    
    Returns:
        Fixed-width field bytes
    """
    if optional:
        if value is None:
            # Presence byte (false) + zero bytes for the field
            field_size = _get_field_size(type_ref, registry)
            return bytes([0x00]) + bytes(field_size)
        else:
            # Presence byte (true) + actual field
            presence = bytes([0x01])
            field_bytes = _encode_value(type_ref, value, field_position + 1, data_builder, registry)
            return presence + field_bytes
    else:
        return _encode_value(type_ref, value, field_position, data_builder, registry)


def _encode_value(
    type_ref: TypeRef,
    value,
    field_position: int,
    data_builder: _DataAreaBuilder,
    registry: TypeRegistry
) -> bytes:
    """Encode a value (non-optional).
    
    Returns:
        Fixed-width field bytes
    """
    if isinstance(type_ref, PrimitiveType):
        return _encode_primitive_native(type_ref.primitive, value)
    
    if isinstance(type_ref, BinaryType):
        return _encode_binary_native(type_ref, value, field_position, data_builder)
    
    if isinstance(type_ref, EnumType):
        # Enum encoded as i32
        if isinstance(value, str):
            num_value = type_ref.to_value(value)
        else:
            num_value = int(value)
        return struct.pack('<i', num_value)
    
    if isinstance(type_ref, SequenceType):
        return _encode_sequence_native(type_ref, value, field_position, data_builder, registry)
    
    if isinstance(type_ref, StaticGroupRef):
        return _encode_static_group_native(type_ref.group, value, field_position, data_builder, registry)
    
    if isinstance(type_ref, (DynamicGroupRef, ObjectType)):
        return _encode_dynamic_group_native(value, field_position, data_builder, registry)
    
    raise EncodeError(f"Unsupported type for Native format: {type_ref}")


def _encode_primitive_native(kind: PrimitiveKind, value) -> bytes:
    """Encode a primitive value in Native format (fixed-width, little-endian)."""
    if kind == PrimitiveKind.BOOL:
        return bytes([0x01 if value else 0x00])
    
    if kind == PrimitiveKind.DECIMAL:
        if isinstance(value, DecimalValue):
            exp, mant = value.exponent, value.mantissa
        elif isinstance(value, tuple):
            exp, mant = value
        else:
            raise EncodeError("Decimal requires DecimalValue or tuple")
        # i8 exponent + i64 mantissa
        return struct.pack('<bq', exp, mant)
    
    if kind == PrimitiveKind.F64:
        # IEEE 754 double, little-endian
        return struct.pack('<d', float(value))
    
    # Integer types
    type_map = {
        PrimitiveKind.U8: '<B',
        PrimitiveKind.I8: '<b',
        PrimitiveKind.U16: '<H',
        PrimitiveKind.I16: '<h',
        PrimitiveKind.U32: '<I',
        PrimitiveKind.I32: '<i',
        PrimitiveKind.U64: '<Q',
        PrimitiveKind.I64: '<q',
        PrimitiveKind.MILLITIME: '<q',
        PrimitiveKind.NANOTIME: '<q',
        PrimitiveKind.DATE: '<i',
        PrimitiveKind.TIME_OF_DAY_MILLI: '<I',
        PrimitiveKind.TIME_OF_DAY_NANO: '<Q',
    }
    
    fmt = type_map.get(kind)
    if fmt:
        return struct.pack(fmt, int(value))
    
    raise EncodeError(f"Unsupported primitive kind: {kind}")


def _encode_binary_native(
    binary: BinaryType,
    value,
    field_position: int,
    data_builder: _DataAreaBuilder
) -> bytes:
    """Encode binary/string in Native format."""
    if binary.kind == "string":
        data = value.encode('utf-8') if isinstance(value, str) else bytes(value)
    else:
        data = bytes(value)
    
    if binary.kind == "fixed":
        # Fixed: inline bytes
        if len(data) != (binary.size or 0):
            raise EncodeError(f"Fixed field requires exactly {binary.size} bytes")
        return data
    
    # Check for inline string (max size 1-255)
    if binary.kind == "string" and binary.size and 1 <= binary.size <= 255:
        # Inline string: u8 size + capacity bytes
        if len(data) > binary.size:
            raise EncodeError(f"String exceeds max size {binary.size}")
        size_byte = bytes([len(data)])
        padded_data = data + bytes(binary.size - len(data))  # Pad with zeros
        return size_byte + padded_data
    
    # Variable size: offset in field, data in data area
    data_with_size = struct.pack('<I', len(data)) + data
    offset = data_builder.add_data(data_with_size, field_position)
    return struct.pack('<I', offset)


def _encode_sequence_native(
    sequence: SequenceType,
    value,
    field_position: int,
    data_builder: _DataAreaBuilder,
    registry: TypeRegistry
) -> bytes:
    """Encode a sequence in Native format."""
    if not isinstance(value, (list, tuple)):
        raise EncodeError("Sequence must be list or tuple")
    
    # Build sequence data: u32 count + items
    seq_data = bytearray()
    seq_data.extend(struct.pack('<I', len(value)))
    
    # For sequences, we need a nested data builder for item data
    # Items go inline in the sequence, but their variable data goes in the sequence's data area
    item_size = _get_field_size(sequence.element_type, registry)
    item_data_builder = _DataAreaBuilder()
    item_data_builder.base_offset = 4 + len(value) * item_size  # After count and all items
    
    for i, item in enumerate(value):
        item_pos = 4 + i * item_size
        item_bytes = _encode_value(sequence.element_type, item, item_pos, item_data_builder, registry)
        seq_data.extend(item_bytes)
    
    seq_data.extend(item_data_builder.get_data())
    
    # Add to main data area
    offset = data_builder.add_data(bytes(seq_data), field_position)
    return struct.pack('<I', offset)


def _encode_static_group_native(
    group: GroupDef,
    value,
    field_position: int,
    data_builder: _DataAreaBuilder,
    registry: TypeRegistry
) -> bytes:
    """Encode a static group inline."""
    if isinstance(value, StaticGroupValue):
        fields = value.fields
    elif isinstance(value, dict):
        fields = value
    else:
        raise EncodeError("Static group must be dict or StaticGroupValue")
    
    fields_buffer = bytearray()
    
    for field in group.all_fields():
        field_value = fields.get(field.name)
        field_pos = field_position + len(fields_buffer)
        field_bytes = _encode_field(
            field.type_ref,
            field_value,
            field.optional,
            field_pos,
            data_builder,
            registry
        )
        fields_buffer.extend(field_bytes)
    
    return bytes(fields_buffer)


def _encode_dynamic_group_native(
    value,
    field_position: int,
    data_builder: _DataAreaBuilder,
    registry: TypeRegistry
) -> bytes:
    """Encode a dynamic group."""
    if isinstance(value, Message):
        message = value
    elif isinstance(value, dict):
        type_hint = value.get("$type")
        if not type_hint:
            raise EncodeError("Dynamic group dict must have $type")
        qname = QName.parse(str(type_hint))
        fields = {k: v for k, v in value.items() if k != "$type"}
        message = Message(type_name=qname, fields=fields)
    else:
        raise EncodeError("Dynamic group must be Message or dict")
    
    # Encode as nested message (includes size preamble)
    encoded = encode_native(message, registry)
    
    # Add to data area
    offset = data_builder.add_data(encoded, field_position)
    return struct.pack('<I', offset)


def _encode_extensions(extensions: Tuple[Message, ...], registry: TypeRegistry) -> bytes:
    """Encode extensions as a sequence of dynamic groups."""
    buffer = bytearray()
    buffer.extend(struct.pack('<I', len(extensions)))  # Count
    
    # Build nested data for extensions
    ext_data_builder = _DataAreaBuilder()
    ext_data_builder.base_offset = 4 + len(extensions) * 4  # After count and all offsets
    
    for i, ext in enumerate(extensions):
        field_pos = 4 + i * 4
        encoded = encode_native(ext, registry)
        offset = ext_data_builder.add_data(encoded, field_pos)
        buffer.extend(struct.pack('<I', offset))
    
    buffer.extend(ext_data_builder.get_data())
    return bytes(buffer)


def _get_field_size(type_ref: TypeRef, registry: TypeRegistry) -> int:
    """Get the fixed size of a field in bytes."""
    if isinstance(type_ref, PrimitiveType):
        size_map = {
            PrimitiveKind.BOOL: 1,
            PrimitiveKind.U8: 1, PrimitiveKind.I8: 1,
            PrimitiveKind.U16: 2, PrimitiveKind.I16: 2,
            PrimitiveKind.U32: 4, PrimitiveKind.I32: 4,
            PrimitiveKind.U64: 8, PrimitiveKind.I64: 8,
            PrimitiveKind.F64: 8,
            PrimitiveKind.DECIMAL: 9,  # i8 + i64
            PrimitiveKind.MILLITIME: 8,
            PrimitiveKind.NANOTIME: 8,
            PrimitiveKind.DATE: 4,
            PrimitiveKind.TIME_OF_DAY_MILLI: 4,
            PrimitiveKind.TIME_OF_DAY_NANO: 8,
        }
        return size_map.get(type_ref.primitive, 0)
    
    if isinstance(type_ref, BinaryType):
        if type_ref.kind == "fixed":
            return type_ref.size or 0
        if type_ref.kind == "string" and type_ref.size and 1 <= type_ref.size <= 255:
            return 1 + type_ref.size  # u8 size + capacity
        return 4  # Offset
    
    if isinstance(type_ref, EnumType):
        return 4  # i32
    
    if isinstance(type_ref, (SequenceType, DynamicGroupRef, ObjectType)):
        return 4  # Offset
    
    if isinstance(type_ref, StaticGroupRef):
        # Sum of all field sizes
        total = 0
        for field in type_ref.group.all_fields():
            if field.optional:
                total += 1  # Presence byte
            total += _get_field_size(field.type_ref, registry)
        return total
    
    return 0


def _decode_group_fields(
    group: GroupDef,
    payload: memoryview,
    offset: int,
    end: int,
    registry: TypeRegistry
) -> Tuple[Dict[str, object], int]:
    """Decode fields from a group."""
    fields: Dict[str, object] = {}
    
    for field in group.all_fields():
        value, offset = _decode_field(
            field.type_ref,
            payload,
            offset,
            end,
            field.optional,
            registry
        )
        fields[field.name] = value
    
    return fields, offset


def _decode_field(
    type_ref: TypeRef,
    payload: memoryview,
    offset: int,
    end: int,
    optional: bool,
    registry: TypeRegistry
) -> Tuple[object, int]:
    """Decode a single field."""
    if optional:
        # Read presence byte
        if offset >= end:
            raise DecodeError("Truncated optional field")
        presence = payload[offset]
        offset += 1
        
        if presence == 0x00:
            # Field is null, skip the zero bytes
            field_size = _get_field_size(type_ref, registry)
            return None, offset + field_size
        elif presence != 0x01:
            # Weak error W11: invalid boolean
            pass  # Continue anyway
    
    return _decode_value(type_ref, payload, offset, end, registry)


def _decode_value(
    type_ref: TypeRef,
    payload: memoryview,
    offset: int,
    end: int,
    registry: TypeRegistry
) -> Tuple[object, int]:
    """Decode a value."""
    if isinstance(type_ref, PrimitiveType):
        return _decode_primitive_native(type_ref.primitive, payload, offset)
    
    if isinstance(type_ref, BinaryType):
        return _decode_binary_native(type_ref, payload, offset, end)
    
    if isinstance(type_ref, EnumType):
        value = struct.unpack('<i', payload[offset:offset+4])[0]
        return type_ref.to_symbol(value), offset + 4
    
    if isinstance(type_ref, SequenceType):
        return _decode_sequence_native(type_ref, payload, offset, end, registry)
    
    if isinstance(type_ref, StaticGroupRef):
        return _decode_static_group_native(type_ref.group, payload, offset, end, registry)
    
    if isinstance(type_ref, (DynamicGroupRef, ObjectType)):
        return _decode_dynamic_group_native(payload, offset, end, registry)
    
    raise DecodeError(f"Unsupported type: {type_ref}")


def _decode_primitive_native(kind: PrimitiveKind, payload: memoryview, offset: int) -> Tuple[object, int]:
    """Decode a primitive value."""
    if kind == PrimitiveKind.BOOL:
        value = payload[offset]
        return bool(value), offset + 1
    
    if kind == PrimitiveKind.DECIMAL:
        exp = struct.unpack('<b', payload[offset:offset+1])[0]
        mant = struct.unpack('<q', payload[offset+1:offset+9])[0]
        return DecimalValue(exponent=exp, mantissa=mant), offset + 9
    
    if kind == PrimitiveKind.F64:
        value = struct.unpack('<d', payload[offset:offset+8])[0]
        return value, offset + 8
    
    # Integer types
    type_map = {
        PrimitiveKind.U8: ('<B', 1),
        PrimitiveKind.I8: ('<b', 1),
        PrimitiveKind.U16: ('<H', 2),
        PrimitiveKind.I16: ('<h', 2),
        PrimitiveKind.U32: ('<I', 4),
        PrimitiveKind.I32: ('<i', 4),
        PrimitiveKind.U64: ('<Q', 8),
        PrimitiveKind.I64: ('<q', 8),
        PrimitiveKind.MILLITIME: ('<q', 8),
        PrimitiveKind.NANOTIME: ('<q', 8),
        PrimitiveKind.DATE: ('<i', 4),
        PrimitiveKind.TIME_OF_DAY_MILLI: ('<I', 4),
        PrimitiveKind.TIME_OF_DAY_NANO: ('<Q', 8),
    }
    
    fmt, size = type_map.get(kind, ('<I', 4))
    value = struct.unpack(fmt, payload[offset:offset+size])[0]
    return value, offset + size


def _decode_binary_native(
    binary: BinaryType,
    payload: memoryview,
    offset: int,
    end: int
) -> Tuple[object, int]:
    """Decode binary/string."""
    if binary.kind == "fixed":
        size = binary.size or 0
        data = bytes(payload[offset:offset+size])
        if binary.kind == "string":
            return data.decode('utf-8'), offset + size
        return data, offset + size
    
    # Check for inline string
    if binary.kind == "string" and binary.size and 1 <= binary.size <= 255:
        size_byte = payload[offset]
        capacity = binary.size
        data = bytes(payload[offset+1:offset+1+size_byte])
        return data.decode('utf-8'), offset + 1 + capacity
    
    # Variable size: read offset, then data
    rel_offset = struct.unpack('<I', payload[offset:offset+4])[0]
    data_location = offset + rel_offset
    
    if data_location + 4 > end:
        raise DecodeError("Invalid offset for binary data")
    
    data_size = struct.unpack('<I', payload[data_location:data_location+4])[0]
    data = bytes(payload[data_location+4:data_location+4+data_size])
    
    if binary.kind == "string":
        return data.decode('utf-8'), offset + 4
    return data, offset + 4


def _decode_sequence_native(
    sequence: SequenceType,
    payload: memoryview,
    offset: int,
    end: int,
    registry: TypeRegistry
) -> Tuple[List, int]:
    """Decode a sequence."""
    # Read offset
    rel_offset = struct.unpack('<I', payload[offset:offset+4])[0]
    data_location = offset + rel_offset
    
    # Read count
    count = struct.unpack('<I', payload[data_location:data_location+4])[0]
    data_offset = data_location + 4
    
    items = []
    for _ in range(count):
        item, data_offset = _decode_value(sequence.element_type, payload, data_offset, end, registry)
        items.append(item)
    
    return items, offset + 4


def _decode_static_group_native(
    group: GroupDef,
    payload: memoryview,
    offset: int,
    end: int,
    registry: TypeRegistry
) -> Tuple[StaticGroupValue, int]:
    """Decode a static group."""
    fields, new_offset = _decode_group_fields(group, payload, offset, end, registry)
    return StaticGroupValue(fields), new_offset


def _decode_dynamic_group_native(
    payload: memoryview,
    offset: int,
    end: int,
    registry: TypeRegistry
) -> Tuple[Message, int]:
    """Decode a dynamic group."""
    # Read offset
    rel_offset = struct.unpack('<I', payload[offset:offset+4])[0]
    data_location = offset + rel_offset
    
    # Decode the nested message (includes size preamble)
    message, _ = decode_native(payload, registry, data_location)
    
    return message, offset + 4


def _decode_extensions(
    payload: memoryview,
    offset: int,
    end: int,
    registry: TypeRegistry
) -> Tuple[Message, ...]:
    """Decode extensions."""
    # Read count
    if offset + 4 > end:
        return tuple()
    
    count = struct.unpack('<I', payload[offset:offset+4])[0]
    offset += 4
    
    extensions = []
    for _ in range(count):
        ext, offset = _decode_dynamic_group_native(payload, offset, end, registry)
        extensions.append(ext)
    
    return tuple(extensions)


__all__ = [
    "encode_native",
    "decode_native",
    "NativeFrame",
]
