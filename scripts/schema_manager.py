"""CLI to manage Blink schemas and apply schema transport messages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from blink.dynschema.exchange import (
    SchemaRegistry,
    apply_schema_update,
    create_schema_exchange_registry,
    decode_stream_with_schema_exchange,
    encode_schema_transport_message,
    is_schema_transport_message,
)
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import Message
from blink.schema import compile_schema
from blink.schema.model import QName


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage Blink schemas and apply schema transport messages.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply schema transport messages from a binary file
  %(prog)s apply --schema schema.blink --input updates.bin

  # Apply schema transport messages from stdin
  cat updates.bin | %(prog)s apply --schema schema.blink --input -

  # Export current schema to JSON
  %(prog)s export --schema schema.blink --output schema.json

  # Validate a schema file
  %(prog)s validate --schema schema.blink

  # Create a GroupDecl message
  %(prog)s create-group-decl --ns Test --name MyType --id 100
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Apply command
    apply_parser = subparsers.add_parser("apply", help="Apply schema transport messages")
    apply_parser.add_argument("--schema", required=True, help="Path to .blink schema file")
    apply_parser.add_argument("--input", required=True, help="Binary file with schema updates (use '-' for stdin)")
    apply_parser.add_argument("--output", help="Optional path to export updated schema as JSON")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export schema to JSON")
    export_parser.add_argument("--schema", required=True, help="Path to .blink schema file")
    export_parser.add_argument("--output", required=True, help="Output JSON file")
    export_parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a schema file")
    validate_parser.add_argument("--schema", required=True, help="Path to .blink schema file")

    # Create GroupDecl command
    create_decl_parser = subparsers.add_parser("create-group-decl", help="Create a GroupDecl message")
    create_decl_parser.add_argument("--ns", required=True, help="Namespace")
    create_decl_parser.add_argument("--name", required=True, help="Group name")
    create_decl_parser.add_argument("--id", type=int, required=True, help="Type ID")
    create_decl_parser.add_argument("--output", help="Output file (default: stdout)")
    create_decl_parser.add_argument("--hex", action="store_true", help="Output as hex string")

    return parser.parse_args()


def load_payload(path: str) -> bytes:
    if path == "-":
        return sys.stdin.buffer.read()
    return Path(path).read_bytes()


def export_schema(registry: TypeRegistry, output_path: str, pretty: bool = False) -> None:
    """Export schema to JSON."""
    schema_data = {
        "groups": {},
    }

    # Export groups
    for type_id, group in registry._by_id.items():
        schema_data["groups"][str(group.name)] = {
            "type_id": type_id,
            "namespace": group.name.namespace,
            "fields": [
                {
                    "name": field.name,
                    "optional": field.optional,
                    "type": str(field.type_ref),
                }
                for field in group.all_fields()
            ],
        }

    # Write output
    indent = 2 if pretty else None
    text = json.dumps(schema_data, indent=indent, default=str)
    Path(output_path).write_text(text + "\n", encoding="utf-8")
    print(f"Schema exported to {output_path}")


def validate_schema(schema_path: str) -> int:
    """Validate a schema file."""
    try:
        schema = compile_schema_file(schema_path)
        print(f"Schema '{schema_path}' is valid")
        print(f"  Namespace: {schema.namespace or '(global)'}")
        print(f"  Groups: {len(schema.groups)}")
        print(f"  Type IDs: {len(schema.type_ids)}")
        return 0
    except Exception as e:
        print(f"Schema '{schema_path}' is invalid: {e}", file=sys.stderr)
        return 1


def compile_schema_file(path: str):
    """Compile a schema from a file path."""
    text = Path(path).read_text(encoding="utf-8")
    return compile_schema(text)


def create_group_decl(ns: str, name: str, type_id: int, output: str | None, hex_mode: bool) -> None:
    """Create a GroupDecl message."""
    # Create a registry with the Blink schema
    registry = create_schema_exchange_registry()

    # Create the GroupDecl message
    message = Message(
        type_name=QName("Blink", "GroupDecl"),
        fields={
            "Name": {"Ns": ns, "Name": name},
            "Id": type_id,
        },
    )

    # Encode the message
    encoded = encode_schema_transport_message(message, registry.type_registry)

    # Write output
    if output:
        Path(output).write_bytes(encoded)
        print(f"GroupDecl message written to {output}")
    else:
        if hex_mode:
            print(encoded.hex())
        else:
            sys.stdout.buffer.write(encoded)


def main() -> None:
    args = parse_args()

    if not args.command:
        print("Error: No command specified", file=sys.stderr)
        print("Use --help for usage information", file=sys.stderr)
        sys.exit(1)

    if args.command == "apply":
        # Apply schema transport messages
        registry = create_schema_exchange_registry(args.schema)
        buffer = load_payload(args.input)

        # Decode and apply schema updates
        messages = decode_stream_with_schema_exchange(buffer, registry)

        print(f"Applied {len(messages)} schema transport messages")

        # Export updated schema if requested
        if args.output:
            export_schema(registry.type_registry, args.output, pretty=True)

    elif args.command == "export":
        # Export schema to JSON
        registry = TypeRegistry.from_schema_file(args.schema)
        export_schema(registry, args.output, pretty=args.pretty)

    elif args.command == "validate":
        # Validate schema
        sys.exit(validate_schema(args.schema))

    elif args.command == "create-group-decl":
        # Create a GroupDecl message
        create_group_decl(args.ns, args.name, args.id, args.output, args.hex)


if __name__ == "__main__":
    main()