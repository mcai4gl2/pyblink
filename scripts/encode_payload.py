"""CLI to encode JSON payloads into Compact Binary using a Blink schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from blink.codec import compact
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import DecimalValue, Message
from blink.schema.model import (
    BinaryType,
    DynamicGroupRef,
    EnumType,
    PrimitiveKind,
    PrimitiveType,
    QName,
    SequenceType,
    StaticGroupRef,
    TypeRef,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Encode a JSON payload via Blink Compact Binary.")
    parser.add_argument("--schema", required=True, help="Path to .blink schema file")
    parser.add_argument("--type", required=True, help="Qualified message type (e.g., Trading:OrderEvent)")
    parser.add_argument("--input", required=True, help="Path to JSON payload")
    return parser.parse_args()


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def build_message(registry: TypeRegistry, type_name: str, data: Dict[str, Any]) -> Message:
    qname = QName.parse(type_name)
    group = registry.get_group_by_name(qname)
    fields = _convert_fields(group, data, registry)
    extensions_payload = data.get("$extensions", [])
    extensions = tuple(
        _convert_extension(registry, qname.namespace, entry) for entry in extensions_payload
    )
    return Message(type_name=qname, fields=fields, extensions=extensions)


def _convert_fields(group, data: Dict[str, Any], registry: TypeRegistry) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for field in group.all_fields():
        if field.name not in data:
            continue
        result[field.name] = _convert_value(field.type_ref, data[field.name], registry, group.name.namespace)
    return result


def _convert_value(
    type_ref: TypeRef,
    raw: Any,
    registry: TypeRegistry,
    default_namespace: str | None,
):
    if raw is None:
        return None
    if isinstance(type_ref, PrimitiveType):
        if type_ref.primitive == PrimitiveKind.DECIMAL:
            if isinstance(raw, dict):
                return DecimalValue(exponent=int(raw["exponent"]), mantissa=int(raw["mantissa"]))
            raise ValueError("Decimal fields require {'exponent','mantissa'} objects")
        if type_ref.primitive == PrimitiveKind.BOOL:
            return bool(raw)
        return int(raw)
    if isinstance(type_ref, BinaryType):
        if type_ref.kind == "string":
            return str(raw)
        return bytes(raw)
    if isinstance(type_ref, EnumType):
        return raw
    if isinstance(type_ref, SequenceType):
        if not isinstance(raw, list):
            raise ValueError("Sequence fields require a list")
        return [
            _convert_value(type_ref.element_type, item, registry, default_namespace) for item in raw
        ]
    if isinstance(type_ref, StaticGroupRef):
        if raw is None:
            return None
        if not isinstance(raw, dict):
            raise ValueError("Static group fields require objects")
        return _convert_fields(type_ref.group, raw, registry)
    if isinstance(type_ref, DynamicGroupRef):
        if not isinstance(raw, dict):
            raise ValueError("Dynamic group fields require objects with optional $type")
        type_hint = raw.get("$type") or str(type_ref.group.name)
        qname = QName.parse(type_hint, default_namespace or type_ref.group.name.namespace)
        nested = {k: v for k, v in raw.items() if k != "$type"}
        message = build_message(registry, str(qname), nested)
        return message
    raise ValueError(f"Unsupported field type {type_ref}")


def _convert_extension(
    registry: TypeRegistry, default_namespace: str | None, payload: Dict[str, Any]
) -> Message:
    type_hint = payload.get("$type")
    if not type_hint:
        raise ValueError("Extension entries must include '$type'")
    qname = QName.parse(str(type_hint), default_namespace)
    group = registry.get_group_by_name(qname)
    fields = _convert_fields(
        group,
        {k: v for k, v in payload.items() if k != "$type"},
        registry,
    )
    return Message(type_name=qname, fields=fields)


def main() -> None:
    args = parse_args()
    registry = TypeRegistry.from_schema_file(args.schema)
    payload = load_json(args.input)
    message = build_message(registry, args.type, payload)
    encoded = compact.encode_message(message, registry)
    print(encoded.hex())


if __name__ == "__main__":
    main()
