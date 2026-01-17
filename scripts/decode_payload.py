"""CLI to decode Compact Binary payloads into JSON using a Blink schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable

from blink.codec import compact
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import DecimalValue, Message, StaticGroupValue
from blink.schema.model import QName


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decode Compact Binary payloads to JSON.")
    parser.add_argument("--schema", required=True, help="Path to .blink schema file")
    parser.add_argument("--input", required=True, help="Binary file containing Compact Binary frames")
    parser.add_argument("--hex", action="store_true", help="Interpret input as hex string instead of raw bytes")
    parser.add_argument("--output", help="Optional path to write JSON (defaults to stdout)")
    return parser.parse_args()


def load_payload(path: str | Path, *, hex_mode: bool) -> bytes:
    data = Path(path).read_bytes()
    if not hex_mode:
        return data
    text = data.decode("utf-8").strip()
    return bytes.fromhex(text)


def message_to_json(message: Message) -> Dict[str, Any]:
    result: Dict[str, Any] = {"$type": str(message.type_name)}
    for key, value in message.fields.items():
        result[key] = _convert_value(value)
    if message.extensions:
        result["$extensions"] = [message_to_json(ext) for ext in message.extensions]
    return result


def _convert_value(value: Any) -> Any:
    if isinstance(value, DecimalValue):
        return {"exponent": value.exponent, "mantissa": value.mantissa}
    if isinstance(value, Message):
        return message_to_json(value)
    if isinstance(value, StaticGroupValue):
        return {k: _convert_value(v) for k, v in value.items()}
    if isinstance(value, dict):
        return {k: _convert_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_convert_value(item) for item in value]
    return value


def main() -> None:
    args = parse_args()
    registry = TypeRegistry.from_schema_file(args.schema)
    buffer = load_payload(args.input, hex_mode=args.hex)
    messages: Iterable[Message] = []
    cursor = 0
    output: list[Dict[str, Any]] = []
    while cursor < len(buffer):
        message, cursor = compact.decode_message(buffer, offset=cursor, registry=registry)
        output.append(message_to_json(message))
    text = json.dumps(output, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
