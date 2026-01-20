"""Tests for Dynamic Schema Exchange functionality."""

import pytest

from blink.dynschema.exchange import (
    SchemaRegistry,
    create_schema_exchange_registry,
    decode_with_schema_exchange,
    decode_stream_with_schema_exchange,
    encode_schema_transport_message,
    is_schema_transport_message,
    RESERVED_TYPE_ID_MIN,
    RESERVED_TYPE_ID_MAX,
)
from blink.codec import compact
from blink.runtime.errors import DecodeError, SchemaError
from blink.runtime.values import Message
from blink.schema.model import QName


def test_is_schema_transport_message():
    """Test detection of schema transport type IDs."""
    assert is_schema_transport_message(16000)  # GroupDecl
    assert is_schema_transport_message(16001)  # GroupDef
    assert is_schema_transport_message(16002)  # Define
    assert is_schema_transport_message(16027)  # SchemaAnnotation
    # These are schema definitions, NOT schema transport messages
    assert not is_schema_transport_message(16003)  # Ref
    assert not is_schema_transport_message(16004)  # DynRef
    assert not is_schema_transport_message(16010)  # U8
    assert not is_schema_transport_message(15999)
    assert not is_schema_transport_message(16384)


def test_create_schema_exchange_registry():
    """Test creating a SchemaRegistry."""
    registry = create_schema_exchange_registry()
    assert isinstance(registry, SchemaRegistry)
    assert registry.schema is not None

    # Verify Blink schema is loaded
    group_decl = registry.type_registry.get_group_by_id(16000)
    assert group_decl is not None
    assert group_decl.name.name == "GroupDecl"


def test_encode_schema_transport_message():
    """Test encoding a schema transport message."""
    registry = create_schema_exchange_registry()

    # Create a GroupDecl message
    message = Message(
        type_name=QName("Blink", "GroupDecl"),
        fields={
            "Name": {"Ns": "Test", "Name": "MyType"},
            "Id": 100,
        },
    )

    encoded = encode_schema_transport_message(message, registry.type_registry)
    assert encoded is not None
    assert len(encoded) > 0


def test_encode_non_schema_transport_message_raises():
    """Test that encoding non-reserved type IDs raises an error."""
    registry = create_schema_exchange_registry()

    # Try to encode an application message without type ID
    message = Message(
        type_name=QName("Blink", "NsName"),
        fields={"Ns": "Test", "Name": "MyType"},
    )

    with pytest.raises(Exception):  # Should raise EncodeError or similar
        encode_schema_transport_message(message, registry.type_registry)


def test_decode_with_schema_exchange_application_message():
    """Test decoding an application message through schema exchange."""
    registry = create_schema_exchange_registry()

    # Create and encode a simple application message (using a group with type ID)
    message = Message(
        type_name=QName("Blink", "Ref"),
        fields={"Type": {"Ns": "Test", "Name": "MyType"}},
    )

    encoded = compact.encode_message(message, registry.type_registry)
    decoded, offset = decode_with_schema_exchange(encoded, registry)

    assert decoded is not None
    assert decoded.type_name == message.type_name
    assert decoded.fields["Type"]["Ns"] == "Test"
    assert decoded.fields["Type"]["Name"] == "MyType"


def test_decode_with_schema_exchange_group_decl():
    """Test decoding a GroupDecl schema transport message."""
    registry = create_schema_exchange_registry()

    # Create a GroupDecl message
    message = Message(
        type_name=QName("Blink", "GroupDecl"),
        fields={
            "Name": {"Ns": "Test", "Name": "MyType"},
            "Id": 100,
        },
    )

    encoded = compact.encode_message(message, registry.type_registry)
    decoded, offset = decode_with_schema_exchange(encoded, registry)

    # Schema transport messages return None (they're applied to registry)
    assert decoded is None
    assert offset == len(encoded)


def test_decode_stream_with_schema_exchange():
    """Test decoding a stream with mixed schema and application messages."""
    registry = create_schema_exchange_registry()

    # Create a mix of messages
    messages = [
        # Schema transport message
        Message(
            type_name=QName("Blink", "GroupDecl"),
            fields={
                "Name": {"Ns": "Test", "Name": "MyType"},
                "Id": 100,
            },
        ),
        # Application message (using a group with type ID)
        Message(
            type_name=QName("Blink", "Ref"),
            fields={"Type": {"Ns": "Test", "Name": "MyType"}},
        ),
        # Another application message
        Message(
            type_name=QName("Blink", "DynRef"),
            fields={"Type": {"Ns": "Another", "Name": "OtherType"}},
        ),
    ]

    # Encode all messages
    buffer = bytearray()
    for msg in messages:
        buffer.extend(compact.encode_message(msg, registry.type_registry))

    # Decode stream - should return only application messages
    decoded = decode_stream_with_schema_exchange(bytes(buffer), registry)

    # Schema transport messages are filtered out
    assert len(decoded) == 2
    assert decoded[0].type_name.name == "Ref"
    assert decoded[1].type_name.name == "DynRef"


def test_schema_exchange_registry_apply_group_decl():
    """Test applying a GroupDecl to the registry."""
    registry = create_schema_exchange_registry()

    # Create a GroupDecl message
    message = Message(
        type_name=QName("Blink", "GroupDecl"),
        fields={
            "Name": {"Ns": "Test", "Name": "MyType"},
            "Id": 100,
        },
    )

    # Apply the schema update (should not raise)
    from blink.dynschema.exchange import apply_schema_update
    apply_schema_update(registry, message)


def test_schema_exchange_registry_apply_group_decl_missing_name():
    """Test that GroupDecl without Name raises an error."""
    registry = create_schema_exchange_registry()

    # Create an invalid GroupDecl message
    message = Message(
        type_name=QName("Blink", "GroupDecl"),
        fields={"Id": 100},
    )

    with pytest.raises(SchemaError):
        from blink.dynschema.exchange import apply_schema_update
        apply_schema_update(registry, message)


def test_schema_exchange_registry_apply_group_def():
    """Test applying a GroupDef to the registry."""
    registry = create_schema_exchange_registry()

    # Create a GroupDef message
    message = Message(
        type_name=QName("Blink", "GroupDef"),
        fields={
            "Name": {"Ns": "Test", "Name": "MyGroup"},
            "Id": 101,
            "Fields": [],
        },
    )

    # Apply the schema update (should not raise)
    from blink.dynschema.exchange import apply_schema_update
    apply_schema_update(registry, message)


def test_reserved_type_id_constants():
    """Test that reserved type ID constants are correct."""
    assert RESERVED_TYPE_ID_MIN == 16000
    assert RESERVED_TYPE_ID_MAX == 16383


def test_is_schema_transport_message_edge_cases():
    """Test edge cases for schema transport message detection."""
    # Test specific schema transport messages
    assert is_schema_transport_message(16000)  # GroupDecl
    assert is_schema_transport_message(16001)  # GroupDef
    # Test schema definitions (NOT transport messages)
    assert not is_schema_transport_message(16003)  # Ref
    assert not is_schema_transport_message(16010)  # U8
    # Test outside reserved range
    assert not is_schema_transport_message(15999)
    assert not is_schema_transport_message(16384)
