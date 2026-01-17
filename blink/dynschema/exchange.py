"""Dynamic Schema Exchange for Blink protocol (Section 9).

Supports runtime schema updates via reserved type IDs 16000-16383:
- GroupDecl/16000: Declare a new group type
- GroupDef/16001: Define a complete group with fields
- FieldDef/16002: Define a field
- Define/16003: Define a type alias
- TypeDef/16004: Base type definition
- And other schema transport messages
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..codec import compact
from ..runtime.errors import DecodeError, EncodeError, RegistryError, SchemaError
from ..runtime.registry import SchemaRegistry, TypeRegistry
from ..runtime.values import Message
from ..schema import compile_schema
from ..schema.model import (
    BinaryType,
    DynamicGroupRef,
    EnumType,
    FieldDef,
    GroupDef,
    ObjectType,
    PrimitiveKind,
    PrimitiveType,
    QName,
    SequenceType,
    StaticGroupRef,
    TypeRef,
)

# Reserved type IDs for schema transport messages
# Only these specific messages can update the schema at runtime
TYPE_ID_GROUP_DECL = 16000
TYPE_ID_GROUP_DEF = 16001
TYPE_ID_FIELD_DEF = 16002
TYPE_ID_DEFINE = 16003
TYPE_ID_TYPE_DEF = 16004
TYPE_ID_SYMBOL = 16019
TYPE_ID_SCHEMA_ANNOTATION = 16037  # Not in original schema but needed
TYPE_ID_ANNOTATED = 16038  # Not in original schema but needed
TYPE_ID_ANNOTATION = 16039  # Not in original schema but needed

# Type IDs that are part of Blink schema but are NOT schema transport messages
# These are just type definitions used to describe the schema structure
SCHEMA_DEFINITION_TYPE_IDS = {
    16005,  # Ref (actually 16010 in the schema)
    16006,  # DynRef (actually 16011 in the schema)
    16007,  # Sequence (actually 16012 in the schema)
    16008,  # String (actually 16013 in the schema)
    16009,  # Binary (actually 16014 in the schema)
    16010,  # Ref
    16011,  # DynRef
    16012,  # Sequence
    16013,  # String
    16014,  # Binary
    16015,  # Fixed
    16016,  # FixedDec
    16017,  # Number
    16018,  # Enum
    16019,  # Symbol
    16020,  # U8
    16021,  # I8
    16022,  # U16
    16023,  # I16
    16024,  # U32
    16025,  # I32
    16026,  # U64
    16027,  # I64
    16028,  # F64
    16029,  # Bool
    16030,  # Decimal
    16031,  # NanoTime
    16032,  # MilliTime
    16033,  # Date
    16034,  # TimeOfDayMilli
    16035,  # TimeOfDayNano
    16036,  # Object
}

# Reserved type ID range for schema transport messages
RESERVED_TYPE_ID_MIN = 16000
RESERVED_TYPE_ID_MAX = 16383


def is_schema_transport_message(type_id: int) -> bool:
    """Check if a type ID is a schema transport message (not just a schema definition)."""
    # Schema transport messages are specific IDs that can update the schema at runtime
    return type_id in {
        TYPE_ID_GROUP_DECL,
        TYPE_ID_GROUP_DEF,
        TYPE_ID_FIELD_DEF,
        TYPE_ID_DEFINE,
        TYPE_ID_TYPE_DEF,
        TYPE_ID_SYMBOL,
    }


def apply_schema_update(registry: SchemaRegistry, message: Message) -> None:
    """
    Apply a schema transport message to update the registry.

    Args:
        registry: A SchemaRegistry that supports schema updates
        message: A schema transport message (GroupDecl, GroupDef, etc.)

    Raises:
        SchemaError: If the schema update is invalid
        RegistryError: If the update conflicts with existing schema
    """
    type_id = registry.type_registry.get_group_by_name(message.type_name).type_id
    if type_id is None:
        raise SchemaError(f"Group {message.type_name} has no type ID")

    if not is_schema_transport_message(type_id):
        raise SchemaError(f"Type ID {type_id} is not a schema transport message")

    # Route to appropriate handler based on type ID
    if type_id == TYPE_ID_GROUP_DECL:
        _apply_group_decl(registry, message)
    elif type_id == TYPE_ID_GROUP_DEF:
        _apply_group_def(registry, message)
    else:
        # Other schema transport messages (FieldDef, Define, etc.)
        raise SchemaError(f"Schema transport message type {type_id} not yet implemented")


def _apply_group_decl(registry: SchemaRegistry, message: Message) -> None:
    """Apply a GroupDecl message to declare a new group type."""
    # GroupDecl: NsName Name, u64 Id
    name_data = message.fields.get("Name")
    if not name_data:
        raise SchemaError("GroupDecl missing Name field")

    # Handle both dict and StaticGroupValue
    if isinstance(name_data, dict):
        ns = name_data.get("Ns")
        name = name_data.get("Name")
    else:
        # Assume StaticGroupValue with a fields attribute
        ns = name_data.fields.get("Ns")
        name = name_data.fields.get("Name")

    if not name:
        raise SchemaError("GroupDecl missing Name.Name")

    type_id = message.fields.get("Id")
    if type_id is None:
        raise SchemaError("GroupDecl missing Id field")

    # Use the SchemaRegistry's apply_group_decl method
    registry.apply_group_decl({"Ns": ns, "Name": name}, type_id)


def _apply_group_def(registry: SchemaRegistry, message: Message) -> None:
    """Apply a GroupDef message to define a complete group."""
    # GroupDef: NsName Name, u64 Id?, FieldDef [] Fields, NsName Super?
    name_data = message.fields.get("Name")
    if not name_data:
        raise SchemaError("GroupDef missing Name field")

    # Handle both dict and StaticGroupValue
    if isinstance(name_data, dict):
        ns = name_data.get("Ns")
        name = name_data.get("Name")
    else:
        # Assume StaticGroupValue with a fields attribute
        ns = name_data.fields.get("Ns")
        name = name_data.fields.get("Name")

    if not name:
        raise SchemaError("GroupDef missing Name.Name")

    type_id = message.fields.get("Id")
    fields_data = message.fields.get("Fields")

    qname = QName(ns, name)

    # Validate type ID uniqueness
    if type_id is not None:
        for group in registry.type_registry._by_id.values():
            if group.type_id == type_id and group.name != qname:
                raise SchemaError(f"Type ID {type_id} already used by {group.name}")

    # Validate super reference
    super_data = message.fields.get("Super")
    if super_data:
        # Handle both dict and StaticGroupValue
        if isinstance(super_data, dict):
            super_ns = super_data.get("Ns")
            super_name = super_data.get("Name")
        else:
            super_ns = super_data.fields.get("Ns")
            super_name = super_data.fields.get("Name")

        if super_name:
            super_qname = QName(super_ns, super_name)
            # Check if super group exists
            try:
                registry.type_registry.get_group_by_name(super_qname)
            except RegistryError:
                raise SchemaError(f"Super group {super_qname} not found")

    # In a full implementation, this would add the complete group definition
    # For now, we just validate the structure and create a placeholder
    # Use apply_group_decl to register the type ID
    if type_id is not None:
        registry.apply_group_decl({"Ns": ns, "Name": name}, type_id)


def decode_with_schema_exchange(
    buffer: bytes | memoryview,
    registry: SchemaRegistry,
    *,
    offset: int = 0,
    strict: bool = True,
) -> Tuple[Message | None, int]:
    """
    Decode a message, applying schema updates for reserved type IDs.

    This function extends the standard decode_message to handle dynamic schema
    exchange. When a schema transport message (type ID 16000-16383) is encountered,
    it is applied to the registry before continuing with message decoding.

    Args:
        buffer: Raw byte payload containing Compact Binary frames
        registry: A SchemaRegistry that supports schema updates
        offset: Starting offset in buffer
        strict: Whether unknown type ids raise DecodeError

    Returns:
        (message, new_offset) where message is None if a schema update was applied,
        or the decoded message if it was an application message.
    """
    frame, new_offset = compact.decode_frame(buffer, offset, registry=registry.type_registry, strict=strict)

    # Check if this is a schema transport message
    if is_schema_transport_message(frame.type_id):
        group = frame.group or registry.type_registry.get_group_by_id(frame.type_id)
        fields, cursor = compact._decode_group_fields(group, memoryview(frame.payload), 0, registry.type_registry)
        schema_message = Message(type_name=group.name, fields=fields)

        # Apply the schema update
        apply_schema_update(registry, schema_message)

        # Return None to indicate schema update was applied
        return None, new_offset

    # Standard application message
    group = frame.group or registry.type_registry.get_group_by_id(frame.type_id)
    fields, cursor = compact._decode_group_fields(group, memoryview(frame.payload), 0, registry.type_registry)
    extensions: Tuple[Message, ...] = tuple()
    if cursor < len(frame.payload):
        extensions = tuple(compact._decode_extensions(memoryview(frame.payload)[cursor:], registry.type_registry))
    message = Message(type_name=group.name, fields=fields, extensions=extensions)
    return message, new_offset


def decode_stream_with_schema_exchange(
    buffer: bytes | memoryview,
    registry: SchemaRegistry,
    *,
    strict: bool = True,
) -> List[Message]:
    """
    Decode a stream of messages, applying schema updates for reserved type IDs.

    This function processes a stream of Compact Binary frames, applying any
    schema transport messages to the registry and returning only application
    messages.

    Args:
        buffer: Raw byte payload containing Compact Binary frames
        registry: A SchemaRegistry that supports schema updates
        strict: Whether unknown type ids raise DecodeError

    Returns:
        List of application messages (schema transport messages are filtered out)
    """
    messages: List[Message] = []
    offset = 0
    mv = memoryview(buffer)

    while offset < len(mv):
        message, offset = decode_with_schema_exchange(mv, registry, offset=offset, strict=strict)
        if message is not None:
            messages.append(message)

    return messages


def encode_schema_transport_message(message: Message, registry: TypeRegistry) -> bytes:
    """
    Encode a schema transport message to Compact Binary.

    Args:
        message: A schema transport message (GroupDecl, GroupDef, etc.)
        registry: Type registry for encoding

    Returns:
        Compact Binary encoded message
    """
    group = registry.get_group_by_name(message.type_name)
    if group.type_id is None:
        raise EncodeError(f"Group {group.name} is missing a type id and cannot be encoded")

    if not is_schema_transport_message(group.type_id):
        raise EncodeError(f"Type ID {group.type_id} is not a schema transport message")

    return compact.encode_message(message, registry)


def create_schema_exchange_registry(schema_file: str | None = None) -> SchemaRegistry:
    """
    Create a SchemaRegistry with the Blink schema loaded.

    Args:
        schema_file: Path to blink.blink schema file. If None, uses default.

    Returns:
        A SchemaRegistry with the Blink schema loaded
    """
    if schema_file is None:
        from pathlib import Path
        # exchange.py is at projects/pyblink/blink/dynschema/exchange.py
        # blink.blink is at projects/pyblink/schema/blink.blink
        root = Path(__file__).resolve().parents[2]
        schema_file = root / "schema" / "blink.blink"

    schema = compile_schema_file(str(schema_file))
    return SchemaRegistry(schema)


def compile_schema_file(path: str):
    """Compile a schema from a file path."""
    from pathlib import Path
    text = Path(path).read_text(encoding="utf-8")
    return compile_schema(text)


__all__ = [
    "SchemaRegistry",
    "is_schema_transport_message",
    "decode_with_schema_exchange",
    "decode_stream_with_schema_exchange",
    "encode_schema_transport_message",
    "create_schema_exchange_registry",
    "apply_schema_update",
    "RESERVED_TYPE_ID_MIN",
    "RESERVED_TYPE_ID_MAX",
]