"""Tests for schema max-size annotations on string and binary types."""

from blink.codec import native
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import Message
from blink.schema.model import QName


def _compile_schema(schema_text: str) -> TypeRegistry:
    """Helper to compile schema text."""
    return TypeRegistry.from_schema_text(schema_text)


def test_string_max_size_annotation_accepted():
    """Test that string(N) syntax is accepted by schema parser."""
    registry = _compile_schema("""
        namespace Test
        Msg/1 -> string(100) Name
    """)
    
    group = registry.get_group_by_name(QName("Test", "Msg"))
    field = list(group.all_fields())[0]
    
    assert field.name == "Name"
    assert field.type_ref.kind == "string"
    assert field.type_ref.size == 100


def test_binary_max_size_annotation_accepted():
    """Test that binary(N) syntax is accepted by schema parser."""
    registry = _compile_schema("""
        namespace Test
        Msg/2 -> binary(256) Data
    """)
    
    group = registry.get_group_by_name(QName("Test", "Msg"))
    field = list(group.all_fields())[0]
    
    assert field.name == "Data"
    assert field.type_ref.kind == "binary"
    assert field.type_ref.size == 256


def test_inline_string_small_size():
    """Test inline string with small max-size (within 1-255 range)."""
    registry = _compile_schema("""
        namespace Test
        Msg/3 -> string(10) Code
    """)
    
    message = Message(
        type_name=QName("Test", "Msg"),
        fields={"Code": "ABC123"}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["Code"] == "ABC123"


def test_inline_string_max_boundary():
    """Test inline string at maximum boundary (255)."""
    registry = _compile_schema("""
        namespace Test
        Msg/4 -> string(255) LongText
    """)
    
    # Create a string that's exactly 255 bytes
    text = "A" * 255
    message = Message(
        type_name=QName("Test", "Msg"),
        fields={"LongText": text}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["LongText"] == text


def test_inline_string_min_boundary():
    """Test inline string at minimum boundary (1)."""
    registry = _compile_schema("""
        namespace Test
        Msg/5 -> string(1) SingleChar
    """)
    
    message = Message(
        type_name=QName("Test", "Msg"),
        fields={"SingleChar": "X"}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["SingleChar"] == "X"


def test_string_large_max_size_uses_offset():
    """Test that string(N) with N > 255 uses offset-based encoding."""
    registry = _compile_schema("""
        namespace Test
        Msg/6 -> string(1000) BigText
    """)
    
    text = "Hello World"
    message = Message(
        type_name=QName("Test", "Msg"),
        fields={"BigText": text}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["BigText"] == text


def test_string_without_max_size_uses_offset():
    """Test that string without max-size uses offset-based encoding."""
    registry = _compile_schema("""
        namespace Test
        Msg/7 -> string Unlimited
    """)
    
    text = "This can be any length"
    message = Message(
        type_name=QName("Test", "Msg"),
        fields={"Unlimited": text}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["Unlimited"] == text


def test_inline_string_shorter_than_capacity():
    """Test inline string with actual length less than capacity."""
    registry = _compile_schema("""
        namespace Test
        Msg/8 -> string(20) Name
    """)
    
    message = Message(
        type_name=QName("Test", "Msg"),
        fields={"Name": "Bob"}  # 3 bytes, capacity 20
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["Name"] == "Bob"


def test_inline_string_empty():
    """Test inline string with empty value."""
    registry = _compile_schema("""
        namespace Test
        Msg/9 -> string(10) Name
    """)
    
    message = Message(
        type_name=QName("Test", "Msg"),
        fields={"Name": ""}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["Name"] == ""


def test_inline_string_utf8_multibyte():
    """Test inline string with UTF-8 multibyte characters."""
    registry = _compile_schema("""
        namespace Test
        Msg/10 -> string(20) Text
    """)
    
    # UTF-8 multibyte: "Hello 世界" (11 bytes: 6 ASCII + 6 for 2 Chinese chars)
    message = Message(
        type_name=QName("Test", "Msg"),
        fields={"Text": "Hello 世界"}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["Text"] == "Hello 世界"


def test_optional_inline_string():
    """Test optional inline string field."""
    registry = _compile_schema("""
        namespace Test
        Msg/11 -> string(15) Name?
    """)
    
    # With value
    msg1 = Message(
        type_name=QName("Test", "Msg"),
        fields={"Name": "Alice"}
    )
    encoded1 = native.encode_native(msg1, registry)
    decoded1, _ = native.decode_native(encoded1, registry)
    assert decoded1.fields["Name"] == "Alice"
    
    # Without value (None)
    msg2 = Message(
        type_name=QName("Test", "Msg"),
        fields={"Name": None}
    )
    encoded2 = native.encode_native(msg2, registry)
    decoded2, _ = native.decode_native(encoded2, registry)
    assert decoded2.fields["Name"] is None


def test_mixed_inline_and_offset_strings():
    """Test message with both inline and offset-based strings."""
    registry = _compile_schema("""
        namespace Test
        Msg/12 -> string(10) ShortName, string LongDesc
    """)
    
    message = Message(
        type_name=QName("Test", "Msg"),
        fields={
            "ShortName": "Alice",
            "LongDesc": "This is a very long description that exceeds inline capacity"
        }
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["ShortName"] == "Alice"
    assert decoded.fields["LongDesc"] == "This is a very long description that exceeds inline capacity"


def test_binary_max_size_round_trip():
    """Test binary(N) max-size annotation."""
    registry = _compile_schema("""
        namespace Test
        Msg/13 -> binary(50) Data
    """)
    
    data = b"\x01\x02\x03\x04\x05"
    message = Message(
        type_name=QName("Test", "Msg"),
        fields={"Data": data}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["Data"] == data
