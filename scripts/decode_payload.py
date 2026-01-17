"""CLI to decode Compact Binary payloads into JSON using a Blink schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable

from blink.codec import compact
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import DecimalValue, Message, StaticGroupValue
from blink.schema.model import QName


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Decode Compact Binary payloads to JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Decode binary file to JSON
  %(prog)s --schema schema.blink --input payload.bin

  # Decode hex string from file
  %(prog)s --schema schema.blink --input payload.txt --hex

  # Decode hex string from stdin
  echo "a1b2c3" | %(prog)s --schema schema.blink --input - --hex

  # Pretty print with custom indentation
  %(prog)s --schema schema.blink --input payload.bin --indent 4 --sort-keys

  # Compact output
  %(prog)s --schema schema.blink --input payload.bin --compact
        """,
    )
    parser.add_argument("--schema", required=True, help="Path to .blink schema file")
    parser.add_argument(
        "--input",
        required=True,
        help="Binary file containing Compact Binary frames (use '-' for stdin)",
    )
    parser.add_argument("--hex", action="store_true", help="Interpret input as hex string instead of raw bytes")
    parser.add_argument("--output", help="Optional path to write JSON (defaults to stdout)")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation (default: 2, use 0 for compact)")
    parser.add_argument("--sort-keys", action="store_true", help="Sort JSON keys alphabetically")
    parser.add_argument("--compact", action="store_true", help="Compact JSON output (no indentation)")
    parser.add_argument("--format", choices=["json", "tag", "xml"], default="json", help="Output format (default: json)")
    return parser.parse_args()


def load_payload(path: str | Path, *, hex_mode: bool) -> bytes:
    if path == "-":
        # Read from stdin
        data = sys.stdin.buffer.read()
    else:
        data = Path(path).read_bytes()

    if not hex_mode:
        return data

    # Decode hex string
    if isinstance(data, bytes):
        text = data.decode("utf-8").strip()
    else:
        text = data.strip()

    # Remove any whitespace or newlines from hex string
    text = "".join(text.split())
    return bytes.fromhex(text)


def message_to_json(message: Message, sort_keys: bool = False) -> Dict[str, Any]:
    result: Dict[str, Any] = {"$type": str(message.type_name)}
    for key, value in message.fields.items():
        result[key] = _convert_value(value)
    if message.extensions:
        result["$extensions"] = [message_to_json(ext, sort_keys) for ext in message.extensions]

    if sort_keys:
        return dict(sorted(result.items()))
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

    # Decode messages
    cursor = 0
    messages: list[Message] = []
    while cursor < len(buffer):
        message, cursor = compact.decode_message(buffer, offset=cursor, registry=registry)
        messages.append(message)

    # Format output
    if args.format == "json":
        output = [message_to_json(msg, sort_keys=args.sort_keys) for msg in messages]
        indent = None if args.compact or args.indent == 0 else args.indent
        text = json.dumps(output, indent=indent, sort_keys=args.sort_keys)
    elif args.format == "tag":
        from blink.codec import tag
        tag_messages = [tag.encode_tag(msg, registry) for msg in messages]
        text = "\n".join(tag_messages)
    elif args.format == "xml":
        from blink.codec import xmlfmt
        xml_messages = [xmlfmt.encode_xml(msg, registry) for msg in messages]
        text = "\n".join(xml_messages)
    else:
        text = json.dumps([message_to_json(msg) for msg in messages])

    # Write output
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
