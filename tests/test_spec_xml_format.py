"""Spec-driven tests for Blink XML format."""

import xml.etree.ElementTree as ET

from blink.codec import xmlfmt
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import Message
from blink.schema.model import QName


def _registry():
    schema_text = """
    namespace Demo

    Payload/1 -> binary Data
    Ext/2 -> string Info
    Envelope/3 -> string Body
    """
    return TypeRegistry.from_schema_text(schema_text)


def test_xml_extension_namespace_matches_spec():
    registry = _registry()
    extension = Message(type_name=QName("Demo", "Ext"), fields={"Info": "x"})
    message = Message(
        type_name=QName("Demo", "Envelope"),
        fields={"Body": "Hello"},
        extensions=(extension,),
    )
    encoded = xmlfmt.encode_xml(message, registry)
    assert "http://blinkprotocol.org/ns/blink" in encoded


def test_xml_stream_has_root_wrapper():
    registry = _registry()
    messages = [
        Message(type_name=QName("Demo", "Envelope"), fields={"Body": "a"}),
        Message(type_name=QName("Demo", "Envelope"), fields={"Body": "b"}),
    ]
    encoded = xmlfmt.encode_xml_stream(messages, registry)
    assert encoded.lstrip().startswith("<root")


def test_xml_binary_valid_utf8_is_text():
    registry = _registry()
    message = Message(
        type_name=QName("Demo", "Payload"),
        fields={"Data": b\"\\xc3\\xa4\"},
    )
    encoded = xmlfmt.encode_xml(message, registry)
    root = ET.fromstring(encoded)
    data = root.find("Data")
    assert data is not None
    assert data.text == \"\\u00e4\"
