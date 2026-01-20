"""Spec-driven tests for Blink JSON format."""

import json

from blink.codec import jsonfmt
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import DecimalValue, Message
from blink.schema.model import QName


def _registry():
    schema_text = """
    namespace Demo

    Packet/1 -> binary Data
    Event/2 -> decimal Price, millitime Timestamp, date TradeDate
    """
    return TypeRegistry.from_schema_text(schema_text)


def test_json_decimal_encodes_as_number_when_mantissa_small():
    registry = _registry()
    message = Message(
        type_name=QName("Demo", "Event"),
        fields={
            "Price": DecimalValue(exponent=-2, mantissa=10000),
            "Timestamp": 0,
            "TradeDate": 0,
        },
    )
    payload = jsonfmt.encode_json(message, registry)
    decoded = json.loads(payload)
    assert isinstance(decoded["Price"], (int, float))


def test_json_time_and_date_are_strings():
    registry = _registry()
    message = Message(
        type_name=QName("Demo", "Event"),
        fields={
            "Price": DecimalValue(exponent=0, mantissa=1),
            "Timestamp": 0,
            "TradeDate": 0,
        },
    )
    payload = jsonfmt.encode_json(message, registry)
    decoded = json.loads(payload)
    assert isinstance(decoded["Timestamp"], str)
    assert isinstance(decoded["TradeDate"], str)


def test_json_stream_is_wrapped_array():
    registry = _registry()
    messages = [
        Message(type_name=QName("Demo", "Packet"), fields={"Data": b"abc"}),
        Message(type_name=QName("Demo", "Packet"), fields={"Data": b"def"}),
    ]
    payload = jsonfmt.encode_json_stream(messages, registry)
    decoded = json.loads(payload)
    assert isinstance(decoded, list)
    assert len(decoded) == 2


def test_json_hex_list_allows_whitespace_groups():
    registry = _registry()
    payload = json.dumps(
        {"$type": "Demo:Packet", "Data": ["3e 6d 3c ea"]}
    )
    decoded = jsonfmt.decode_json(payload, registry)
    assert decoded.fields["Data"] == bytes.fromhex("3e6d3cea")
