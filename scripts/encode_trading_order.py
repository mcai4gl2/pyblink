"""Demo script encoding a trading OrderEvent into Compact Binary."""

from __future__ import annotations

from pathlib import Path

from blink.codec import compact
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import DecimalValue, Message
from blink.schema.model import QName

EXAMPLE_DIR = Path(__file__).resolve().parents[1] / "schema" / "examples"


def build_sample_event() -> Message:
    order = Message(
        type_name=QName("Trading", "AlgoOrder"),
        fields={
            "Instrument": {
                "Symbol": "AAPL",
                "Product": "EQUITY",
                "Currency": "USD",
                "Exchange": "NASDAQ",
            },
            "Routing": {"Venue": "XNAS", "Desk": "AlphaTeam"},
            "Price": DecimalValue(exponent=-2, mantissa=15025),
            "Quantity": 500,
            "Side": "Buy",
            "Status": "New",
            "Strategy": "VWAP",
        },
    )

    return Message(
        type_name=QName("Trading", "OrderEvent"),
        fields={
            "Payload": order,
            "EventType": "NewOrder",
            "AuditTrail": [
                {"$type": "Trading:Routing", "Venue": "XNAS", "Desk": "AlgoDesk"}
            ],
        },
    )


def main() -> None:
    schema_path = EXAMPLE_DIR / "trading.blink"
    registry = TypeRegistry.from_schema_file(schema_path)
    event = build_sample_event()
    payload = compact.encode_message(event, registry)
    print(f"Encoded OrderEvent ({len(payload)} bytes): {payload.hex()}")


if __name__ == "__main__":
    main()
