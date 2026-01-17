"""Tests for Compact Binary framing + message encoding."""

from pathlib import Path

import pytest

from blink.codec import compact
from blink.runtime.errors import DecodeError
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import DecimalValue, Message
from blink.schema.model import QName


def test_encode_decode_frame_round_trip():
    payload = b"\x01\x02\x03"
    encoded = compact.encode_frame(42, payload)
    frame, offset = compact.decode_frame(encoded)
    assert frame.type_id == 42
    assert frame.payload == payload
    assert offset == len(encoded)


def test_decode_frame_truncated():
    payload = b"\x00"
    encoded = compact.encode_frame(1, payload)
    with pytest.raises(DecodeError):
        compact.decode_frame(encoded[:-1])


def test_decode_frame_with_registry():
    root = Path(__file__).resolve().parents[1]
    registry = TypeRegistry.from_schema_file(root / "schema" / "examples" / "trading.blink")
    payload = b"\x80"  # placeholder extension/fields
    encoded = compact.encode_frame(200, payload)
    frame, _ = compact.decode_frame(encoded, registry=registry)
    assert frame.group is not None
    assert frame.group.name.name == "Order"


def test_iter_frames_multiple():
    frame1 = compact.encode_frame(1, b"\x01")
    frame2 = compact.encode_frame(2, b"\x02\x03")
    buffer = frame1 + frame2
    frames = list(compact.iter_frames(buffer))
    assert [f.type_id for f in frames] == [1, 2]
    assert frames[1].payload == b"\x02\x03"


def test_encode_decode_message_round_trip():
    root = Path(__file__).resolve().parents[1]
    registry = TypeRegistry.from_schema_file(root / "schema" / "examples" / "trading.blink")
    message = Message(
        type_name=QName("Trading", "Order"),
        fields={
            "Instrument": {
                "Symbol": "AAPL",
                "Product": "EQUITY",
                "Currency": "USD",
                "Exchange": "NASDAQ",
            },
            "Routing": {"Venue": "XNAS", "Desk": "Alpha"},
            "Price": DecimalValue(exponent=-2, mantissa=15005),
            "Quantity": 100,
            "Side": "Buy",
            "Status": "Pending",
        },
    )

    encoded = compact.encode_message(message, registry)
    decoded, offset = compact.decode_message(encoded, registry=registry)
    assert offset == len(encoded)
    assert decoded.type_name == message.type_name
    assert decoded.fields["Quantity"] == 100
    assert decoded.fields["Side"] == "Buy"
    instrument = decoded.fields["Instrument"]
    assert instrument["Symbol"] == "AAPL"
    routing = decoded.fields["Routing"]
    assert routing["Venue"] == "XNAS"


def test_encode_decode_dynamic_group():
    root = Path(__file__).resolve().parents[1]
    registry = TypeRegistry.from_schema_file(root / "schema" / "examples" / "trading.blink")
    order = Message(
        type_name=QName("Trading", "AlgoOrder"),
        fields={
            "Instrument": {
                "Symbol": "AAPL",
                "Product": "EQUITY",
                "Currency": "USD",
                "Exchange": "NASDAQ",
            },
            "Routing": {"Venue": "XNAS"},
            "Price": DecimalValue(exponent=-2, mantissa=15025),
            "Quantity": 250,
            "Side": "Sell",
            "Status": "Working",
            "Strategy": "TWAP",
        },
    )
    event = Message(
        type_name=QName("Trading", "OrderEvent"),
        fields={
            "Payload": order,
            "EventType": "Modify",
        },
    )
    encoded = compact.encode_message(event, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    payload = decoded.fields["Payload"]
    assert isinstance(payload, Message)
    assert payload.type_name.name == "AlgoOrder"
    assert payload.fields["Strategy"] == "TWAP"


def test_encode_decode_dynamic_sequence():
    root = Path(__file__).resolve().parents[1]
    registry = TypeRegistry.from_schema_file(root / "schema" / "examples" / "trading.blink")

    orders = []
    for symbol in ["AAPL", "MSFT"]:
        orders.append(
            Message(
                type_name=QName("Trading", "Order"),
                fields={
                    "Instrument": {
                        "Symbol": symbol,
                        "Product": "EQUITY",
                        "Currency": "USD",
                        "Exchange": "NASDAQ",
                    },
                    "Routing": None,
                    "Price": DecimalValue(exponent=-2, mantissa=12000),
                    "Quantity": 10,
                    "Side": "Sell",
                },
            )
        )

    bulk = Message(
        type_name=QName("Trading", "BulkOrder"),
        fields={"Orders": orders},
    )

    encoded = compact.encode_message(bulk, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    decoded_orders = decoded.fields["Orders"]
    assert isinstance(decoded_orders, list)
    assert decoded_orders[0].fields["Instrument"]["Symbol"] == "AAPL"


def test_encode_decode_extensions():
    root = Path(__file__).resolve().parents[1]
    registry = TypeRegistry.from_schema_file(root / "schema" / "examples" / "trading.blink")
    base_order = Message(
        type_name=QName("Trading", "Order"),
        fields={
            "Instrument": {
                "Symbol": "AAPL",
                "Product": "EQUITY",
                "Currency": "USD",
                "Exchange": "NASDAQ",
            },
            "Price": DecimalValue(exponent=-2, mantissa=10000),
            "Quantity": 1,
            "Side": "Buy",
        },
    )
    event = Message(
        type_name=QName("Trading", "OrderEvent"),
        fields={"Payload": base_order, "EventType": "Ack"},
        extensions=(
            Message(
                type_name=QName("Trading", "Order"),
                fields={
                    "Instrument": {
                        "Symbol": "AAPL",
                        "Product": "EQUITY",
                        "Currency": "USD",
                        "Exchange": "NASDAQ",
                    },
                    "Price": DecimalValue(exponent=-2, mantissa=10050),
                    "Quantity": 1,
                    "Side": "Buy",
                    "Status": "Filled",
                },
            ),
        ),
    )
    encoded = compact.encode_message(event, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.extensions
    assert decoded.extensions[0].fields["Status"] == "Filled"
