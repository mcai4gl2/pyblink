"""Spec-driven tests for Blink Compact Binary format."""

from blink.codec import compact
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import Message
from blink.schema.model import QName


def test_compact_f64_round_trip():
    schema_text = """
    namespace Demo

    Quote/1 -> f64 Price
    """
    registry = TypeRegistry.from_schema_text(schema_text)
    message = Message(type_name=QName("Demo", "Quote"), fields={"Price": 1.5})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["Price"] == 1.5


def test_compact_optional_fixed_includes_presence_byte():
    schema_text = """
    namespace Demo

    Token/1 -> fixed(4) Value?
    """
    registry = TypeRegistry.from_schema_text(schema_text)
    message = Message(
        type_name=QName("Demo", "Token"),
        fields={"Value": b"\x01\x02\x03\x04"},
    )
    encoded = compact.encode_message(message, registry)
    frame, _ = compact.decode_frame(encoded)
    assert frame.payload.startswith(b"\x01\x01\x02\x03\x04")
