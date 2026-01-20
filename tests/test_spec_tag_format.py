"""Spec-driven tests for Blink Tag format."""

import pytest

from blink.codec import tag
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import Message
from blink.schema.model import QName


def _registry():
    schema_text = """
    namespace Demo

    Inner/1 -> u32 Id
    Msg/2 -> bool Flag, u32 [] Values, Inner* Child?
    """
    return TypeRegistry.from_schema_text(schema_text)


def test_tag_encode_sequence_uses_brackets_and_semicolons():
    registry = _registry()
    message = Message(
        type_name=QName("Demo", "Msg"),
        fields={"Flag": True, "Values": [1, 2, 3]},
    )
    encoded = tag.encode_tag(message, registry)
    assert "Values=[1;2;3]" in encoded


def test_tag_encode_bool_uses_y_n_tokens():
    registry = _registry()
    message = Message(
        type_name=QName("Demo", "Msg"),
        fields={"Flag": True},
    )
    encoded = tag.encode_tag(message, registry)
    assert "Flag=Y" in encoded


def test_tag_encode_dynamic_group_field_wrapped_in_braces():
    registry = _registry()
    child = Message(type_name=QName("Demo", "Inner"), fields={"Id": 1})
    message = Message(
        type_name=QName("Demo", "Msg"),
        fields={"Flag": True, "Child": child},
    )
    encoded = tag.encode_tag(message, registry)
    assert "Child={@Demo:Inner|Id=1}" in encoded


def test_tag_encode_extensions_use_semicolons():
    registry = _registry()
    extension_a = Message(type_name=QName("Demo", "Inner"), fields={"Id": 1})
    extension_b = Message(type_name=QName("Demo", "Inner"), fields={"Id": 2})
    message = Message(
        type_name=QName("Demo", "Msg"),
        fields={"Flag": False},
        extensions=(extension_a, extension_b),
    )
    encoded = tag.encode_tag(message, registry)
    assert "|[@Demo:Inner|Id=1;@Demo:Inner|Id=2]" in encoded


def test_tag_decode_accepts_y_n_and_semicolon_sequences():
    registry = _registry()
    encoded = "@Demo:Msg|Flag=Y|Values=[1;2]"
    decoded = tag.decode_tag(encoded, registry)
    assert decoded.fields["Flag"] is True
    assert decoded.fields["Values"] == [1, 2]
