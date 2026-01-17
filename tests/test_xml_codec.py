"""Tests for XML format codec."""

import pytest

from blink.codec import xmlfmt
from blink.runtime.errors import DecodeError, EncodeError
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import DecimalValue, Message, StaticGroupValue
from blink.schema.model import QName


def _compile_demo_schema(text: str) -> TypeRegistry:
    from blink.schema import compile_schema
    schema = compile_schema(text)
    return TypeRegistry.from_schema(schema)


def test_encode_decode_simple_message():
    registry = _compile_demo_schema(
        """
        namespace Demo
        Simple/1 -> u32 id, string name, bool active
        """
    )
    message = Message(
        type_name=QName("Demo", "Simple"),
        fields={"id": 42, "name": "test", "active": True},
    )
    encoded = xmlfmt.encode_xml(message, registry)
    decoded = xmlfmt.decode_xml(encoded, registry)
    assert decoded.type_name == message.type_name
    assert decoded.fields["id"] == 42
    assert decoded.fields["name"] == "test"
    assert decoded.fields["active"] is True


def test_encode_decode_with_decimal():
    registry = _compile_demo_schema(
        """
        namespace Demo
        Price/1 -> decimal amount, string currency
        """
    )
    message = Message(
        type_name=QName("Demo", "Price"),
        fields={"amount": DecimalValue(exponent=-2, mantissa=15005), "currency": "USD"},
    )
    encoded = xmlfmt.encode_xml(message, registry)
    decoded = xmlfmt.decode_xml(encoded, registry)
    assert decoded.fields["amount"].exponent == -2
    assert decoded.fields["amount"].mantissa == 15005
    assert decoded.fields["currency"] == "USD"


def test_encode_decode_with_static_group():
    registry = _compile_demo_schema(
        """
        namespace Demo
        Inner/1 -> u32 value, string label
        Outer/2 -> Inner data, u32 count
        """
    )
    message = Message(
        type_name=QName("Demo", "Outer"),
        fields={
            "data": {"value": 100, "label": "test"},
            "count": 5,
        },
    )
    encoded = xmlfmt.encode_xml(message, registry)
    decoded = xmlfmt.decode_xml(encoded, registry)
    assert decoded.fields["count"] == 5
    inner = decoded.fields["data"]
    assert isinstance(inner, StaticGroupValue)
    assert inner.fields["value"] == 100
    assert inner.fields["label"] == "test"


def test_encode_decode_with_sequence():
    registry = _compile_demo_schema(
        """
        namespace Demo
        List/1 -> u32 [] items
        """
    )
    message = Message(
        type_name=QName("Demo", "List"),
        fields={"items": [1, 2, 3, 4, 5]},
    )
    encoded = xmlfmt.encode_xml(message, registry)
    decoded = xmlfmt.decode_xml(encoded, registry)
    assert decoded.fields["items"] == [1, 2, 3, 4, 5]


def test_encode_decode_with_dynamic_group():
    registry = _compile_demo_schema(
        """
        namespace Demo
        Base/1 -> string name
        Derived/2 : Base -> u32 value
        Container/3 -> Base* payload
        """
    )
    message = Message(
        type_name=QName("Demo", "Container"),
        fields={
            "payload": Message(
                type_name=QName("Demo", "Derived"),
                fields={"name": "test", "value": 42},
            )
        },
    )
    encoded = xmlfmt.encode_xml(message, registry)
    decoded = xmlfmt.decode_xml(encoded, registry)
    payload = decoded.fields["payload"]
    assert isinstance(payload, Message)
    assert payload.type_name.name == "Derived"
    assert payload.fields["value"] == 42


def test_encode_decode_with_extensions():
    registry = _compile_demo_schema(
        """
        namespace Demo
        Base/1 -> u32 id
        """
    )
    message = Message(
        type_name=QName("Demo", "Base"),
        fields={"id": 1},
        extensions=(
            Message(
                type_name=QName("Demo", "Base"),
                fields={"id": 2},
            ),
        ),
    )
    encoded = xmlfmt.encode_xml(message, registry)
    decoded = xmlfmt.decode_xml(encoded, registry)
    assert len(decoded.extensions) == 1
    assert decoded.extensions[0].fields["id"] == 2


def test_encode_decode_binary_utf8():
    registry = _compile_demo_schema(
        """
        namespace Demo
        Data/1 -> binary payload
        """
    )
    message = Message(
        type_name=QName("Demo", "Data"),
        fields={"payload": b"hello"},
    )
    encoded = xmlfmt.encode_xml(message, registry)
    decoded = xmlfmt.decode_xml(encoded, registry)
    assert decoded.fields["payload"] == b"hello"


def test_encode_decode_binary_hex():
    registry = _compile_demo_schema(
        """
        namespace Demo
        Data/1 -> binary payload
        """
    )
    message = Message(
        type_name=QName("Demo", "Data"),
        fields={"payload": b"\x00\x01\x02\xff"},
    )
    encoded = xmlfmt.encode_xml(message, registry)
    # Check that binary attribute is set
    assert 'binary="yes"' in encoded
    decoded = xmlfmt.decode_xml(encoded, registry)
    assert decoded.fields["payload"] == b"\x00\x01\x02\xff"


def test_encode_decode_stream():
    registry = _compile_demo_schema(
        """
        namespace Demo
        Item/1 -> u32 id, string name
        """
    )
    messages = [
        Message(type_name=QName("Demo", "Item"), fields={"id": 1, "name": "first"}),
        Message(type_name=QName("Demo", "Item"), fields={"id": 2, "name": "second"}),
    ]
    encoded = xmlfmt.encode_xml_stream(messages, registry)
    decoded = xmlfmt.decode_xml_stream(encoded, registry)
    assert len(decoded) == 2
    assert decoded[0].fields["id"] == 1
    assert decoded[1].fields["id"] == 2


def test_round_trip_with_all_types():
    registry = _compile_demo_schema(
        """
        namespace Demo
        AllTypes/1 ->
            u32 int_val,
            i32 signed_val,
            bool bool_val,
            string str_val,
            binary bin_val,
            decimal dec_val,
            u32 [] seq_val
        """
    )
    message = Message(
        type_name=QName("Demo", "AllTypes"),
        fields={
            "int_val": 42,
            "signed_val": -100,
            "bool_val": True,
            "str_val": "test",
            "bin_val": b"\x01\x02\x03",
            "dec_val": DecimalValue(exponent=-2, mantissa=15005),
            "seq_val": [1, 2, 3],
        },
    )
    encoded = xmlfmt.encode_xml(message, registry)
    decoded = xmlfmt.decode_xml(encoded, registry)
    assert decoded.fields["int_val"] == 42
    assert decoded.fields["signed_val"] == -100
    assert decoded.fields["bool_val"] is True
    assert decoded.fields["str_val"] == "test"
    assert decoded.fields["bin_val"] == b"\x01\x02\x03"
    assert decoded.fields["dec_val"].exponent == -2
    assert decoded.fields["dec_val"].mantissa == 15005
    assert decoded.fields["seq_val"] == [1, 2, 3]


def test_encode_optional_fields_omitted():
    registry = _compile_demo_schema(
        """
        namespace Demo
        Optional/1 -> u32 required, u32 opt?
        """
    )
    message = Message(
        type_name=QName("Demo", "Optional"),
        fields={"required": 1},
    )
    encoded = xmlfmt.encode_xml(message, registry)
    decoded = xmlfmt.decode_xml(encoded, registry)
    assert decoded.fields["required"] == 1
    assert "opt" not in decoded.fields


def test_encode_decode_with_namespace():
    registry = _compile_demo_schema(
        """
        namespace MyNamespace
        Item/1 -> u32 id
        """
    )
    message = Message(
        type_name=QName("MyNamespace", "Item"),
        fields={"id": 42},
    )
    encoded = xmlfmt.encode_xml(message, registry)
    # Check that namespace is present
    assert "{MyNamespace}" in encoded or "MyNamespace" in encoded
    decoded = xmlfmt.decode_xml(encoded, registry)
    assert decoded.fields["id"] == 42