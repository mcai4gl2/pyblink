"""JSON Mapping codec for Blink protocol (Section 7).

The JSON format maps Blink messages to JSON objects with the following rules:
- Message object requires $type and optional $extension array
- Integers with |mantissa| < 1e15 remain numeric; others serialized as decimal strings
- NaN/Inf/-Inf use quoted tokens
- Binary values encode as UTF-8 strings when valid, or list of hex strings otherwise
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict, List

from ..runtime.errors import DecodeError, EncodeError
from ..runtime.registry import TypeRegistry
from ..runtime.values import DecimalValue, Message, StaticGroupValue
from ..schema.model import (
    BinaryType,
    DynamicGroupRef,
    EnumType,
    FieldDef,
    ObjectType,
    PrimitiveKind,
    PrimitiveType,
    QName,
    SequenceType,
    StaticGroupRef,
    TypeRef,
)

# Numeric threshold for JSON number vs string
NUMERIC_THRESHOLD = 1e15


def _is_safe_json_number(value: int) -> bool:
    """Check if an integer can be safely represented as a JSON number."""
    return abs(value) < NUMERIC_THRESHOLD


def _format_value(value: Any, type_ref: TypeRef, registry: TypeRegistry, default_namespace: str | None) -> Any:
    """Format a value as JSON-compatible data."""
    if value is None:
        return None

    if isinstance(type_ref, PrimitiveType):
        if type_ref.primitive == PrimitiveKind.BOOL:
            return bool(value)
        if type_ref.primitive == PrimitiveKind.DECIMAL:
            if isinstance(value, DecimalValue):
                exponent, mantissa = value.exponent, value.mantissa
            elif isinstance(value, tuple):
                exponent, mantissa = value
            else:
                raise EncodeError("Decimal values require DecimalValue or tuple")
            # Per spec: if |mantissa| < 1e15, encode as JSON number
            if abs(mantissa) < NUMERIC_THRESHOLD:
                # Calculate the actual decimal value
                return mantissa * (10 ** exponent)
            # Otherwise format as mantissa e exponent string
            return f"{mantissa}e{exponent}"
        if type_ref.primitive == PrimitiveKind.F64:
            float_val = float(value)
            if math.isnan(float_val):
                return "NaN"
            if math.isinf(float_val):
                return "Inf" if float_val > 0 else "-Inf"
            return float_val
        # Time/date types: encode as strings in Tag format per spec
        if type_ref.primitive in (
            PrimitiveKind.MILLITIME,
            PrimitiveKind.NANOTIME,
            PrimitiveKind.DATE,
            PrimitiveKind.TIME_OF_DAY_MILLI,
            PrimitiveKind.TIME_OF_DAY_NANO,
        ):
            # For now, encode as string representation of the integer
            # TODO: Implement proper ISO 8601 formatting per Tag spec
            return str(int(value))
        # Integer types
        int_val = int(value)
        if _is_safe_json_number(int_val):
            return int_val
        else:
            return str(int_val)

    if isinstance(type_ref, BinaryType):
        if type_ref.kind == "string":
            return str(value)
        else:
            # Binary data: try UTF-8, otherwise hex array
            data = bytes(value)
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return [f"{b:02x}" for b in data]

    if isinstance(type_ref, EnumType):
        return str(value)

    if isinstance(type_ref, SequenceType):
        if not isinstance(value, (list, tuple)):
            raise EncodeError("Sequence values must be list or tuple")
        return [_format_value(item, type_ref.element_type, registry, default_namespace) for item in value]

    if isinstance(type_ref, StaticGroupRef):
        if isinstance(value, StaticGroupValue):
            fields = value.fields
        elif isinstance(value, dict):
            fields = value
        else:
            raise EncodeError("Static group values must be dict or StaticGroupValue")
        result = {}
        for field in type_ref.group.all_fields():
            if field.name not in fields or fields[field.name] is None:
                continue
            result[field.name] = _format_value(fields[field.name], field.type_ref, registry, default_namespace)
        return result

    if isinstance(type_ref, DynamicGroupRef) or isinstance(type_ref, ObjectType):
        if isinstance(value, Message):
            message = value
        elif isinstance(value, dict):
            type_hint = value.get("$type")
            if type_hint:
                qname = QName.parse(str(type_hint), default_namespace or type_ref.group.name.namespace)
            else:
                qname = type_ref.group.name
            fields = {k: v for k, v in value.items() if k != "$type"}
            message = Message(type_name=qname, fields=fields)
        else:
            raise EncodeError("Dynamic group values must be dict or Message")
        return _format_message(message, registry)

    raise EncodeError(f"Unsupported type for JSON format: {type_ref}")


def _format_message(message: Message, registry: TypeRegistry) -> Dict[str, Any]:
    """Format a complete message as JSON object."""
    group = registry.get_group_by_name(message.type_name)
    result: Dict[str, Any] = {"$type": str(group.name)}

    for field in group.all_fields():
        value = message.fields.get(field.name)
        if value is None:
            continue
        result[field.name] = _format_value(value, field.type_ref, registry, group.name.namespace)

    if message.extensions:
        result["$extension"] = [_format_message(ext, registry) for ext in message.extensions]

    return result


def encode_json(message: Message, registry: TypeRegistry) -> str:
    """Encode a message to JSON string."""
    data = _format_message(message, registry)
    return json.dumps(data, indent=2, ensure_ascii=False)


def _parse_value(raw: Any, type_ref: TypeRef, registry: TypeRegistry, default_namespace: str | None) -> Any:
    """Parse a value from JSON data."""
    if raw is None:
        return None

    if isinstance(type_ref, PrimitiveType):
        if type_ref.primitive == PrimitiveKind.BOOL:
            if isinstance(raw, bool):
                return raw
            if isinstance(raw, str):
                if raw.lower() == "true":
                    return True
                elif raw.lower() == "false":
                    return False
            raise DecodeError(f"Invalid boolean value: {raw}")
        if type_ref.primitive == PrimitiveKind.DECIMAL:
            if isinstance(raw, (int, float)):
                # If it's a JSON number, convert to decimal
                # Convert to string to preserve precision, then parse
                str_val = str(raw)
                if 'e' in str_val.lower():
                    # Scientific notation: parse it
                    parts = str_val.lower().split('e')
                    mantissa = float(parts[0])
                    exponent = int(parts[1])
                    # Normalize to integer mantissa
                    while mantissa != int(mantissa) and mantissa != 0:
                        mantissa *= 10
                        exponent -= 1
                    return DecimalValue(exponent=exponent, mantissa=int(mantissa))
                elif '.' in str_val:
                    # Decimal notation: count decimal places
                    parts = str_val.split('.')
                    decimal_places = len(parts[1])
                    # Remove the decimal point
                    mantissa = int(parts[0] + parts[1])
                    exponent = -decimal_places
                    return DecimalValue(exponent=exponent, mantissa=mantissa)
                else:
                    # Integer
                    return DecimalValue(exponent=0, mantissa=int(raw))
            elif isinstance(raw, str):
                # Parse mantissa e exponent format: 15005e-2
                parts = raw.split("e")
                if len(parts) != 2:
                    raise DecodeError(f"Invalid decimal format: {raw}")
                mantissa = int(parts[0])
                exponent = int(parts[1])
                return DecimalValue(exponent=exponent, mantissa=mantissa)
            elif isinstance(raw, dict) and "exponent" in raw and "mantissa" in raw:
                return DecimalValue(exponent=int(raw["exponent"]), mantissa=int(raw["mantissa"]))
            raise DecodeError(f"Invalid decimal value: {raw}")
        if type_ref.primitive == PrimitiveKind.F64:
            if isinstance(raw, str):
                if raw == "NaN":
                    return float("nan")
                if raw == "Inf":
                    return float("inf")
                if raw == "-Inf":
                    return float("-inf")
            return float(raw)
        # Time/date types: parse from strings per spec
        if type_ref.primitive in (
            PrimitiveKind.MILLITIME,
            PrimitiveKind.NANOTIME,
            PrimitiveKind.DATE,
            PrimitiveKind.TIME_OF_DAY_MILLI,
            PrimitiveKind.TIME_OF_DAY_NANO,
        ):
            # For now, parse as integer from string
            # TODO: Implement proper ISO 8601 parsing per Tag spec
            if isinstance(raw, str):
                return int(raw)
            return int(raw)
        # Integer types
        if isinstance(raw, int):
            return raw
        if isinstance(raw, str):
            return int(raw)
        raise DecodeError(f"Invalid integer value: {raw}")

    if isinstance(type_ref, BinaryType):
        if type_ref.kind == "string":
            return str(raw)
        else:
            # Binary data: hex array or string
            if isinstance(raw, str):
                try:
                    return raw.encode("utf-8")
                except UnicodeEncodeError:
                    pass
            if isinstance(raw, list):
                # Per spec: each hex list entry can contain multiple hex pairs with spaces
                result = bytearray()
                for part in raw:
                    # Split by whitespace and parse each hex pair
                    hex_pairs = part.split()
                    for hex_pair in hex_pairs:
                        result.append(int(hex_pair, 16))
                return bytes(result)
            raise DecodeError(f"Invalid binary value: {raw}")

    if isinstance(type_ref, EnumType):
        return str(raw)

    if isinstance(type_ref, SequenceType):
        if not isinstance(raw, list):
            raise DecodeError("Sequence values must be a list")
        return [_parse_value(item, type_ref.element_type, registry, default_namespace) for item in raw]

    if isinstance(type_ref, StaticGroupRef):
        if not isinstance(raw, dict):
            raise DecodeError("Static group values must be objects")
        fields = {}
        for field in type_ref.group.all_fields():
            if field.name not in raw:
                continue
            fields[field.name] = _parse_value(raw[field.name], field.type_ref, registry, default_namespace)
        return StaticGroupValue(fields)

    if isinstance(type_ref, DynamicGroupRef) or isinstance(type_ref, ObjectType):
        if not isinstance(raw, dict):
            raise DecodeError("Dynamic group values must be objects")
        return _parse_message(raw, registry, default_namespace or type_ref.group.name.namespace)

    raise DecodeError(f"Unsupported type for JSON parsing: {type_ref}")


def _parse_message(data: Dict[str, Any], registry: TypeRegistry, default_namespace: str | None) -> Message:
    """Parse a message from JSON object."""
    if "$type" not in data:
        raise DecodeError("JSON message must include $type")

    type_name = data["$type"]
    qname = QName.parse(str(type_name), default_namespace)
    group = registry.get_group_by_name(qname)

    fields: Dict[str, Any] = {}
    for field in group.all_fields():
        if field.name not in data:
            continue
        fields[field.name] = _parse_value(data[field.name], field.type_ref, registry, group.name.namespace)

    extensions: List[Message] = []
    if "$extension" in data:
        if not isinstance(data["$extension"], list):
            raise DecodeError("$extension must be an array")
        for ext_data in data["$extension"]:
            extensions.append(_parse_message(ext_data, registry, group.name.namespace))

    return Message(type_name=qname, fields=fields, extensions=tuple(extensions))


def decode_json(s: str, registry: TypeRegistry) -> Message:
    """Decode a message from JSON string."""
    data = json.loads(s)
    return _parse_message(data, registry, None)


def encode_json_stream(messages: List[Message], registry: TypeRegistry) -> str:
    """Encode multiple messages to JSON array per spec."""
    # Per spec: streams should be wrapped in a JSON array
    data = [_format_message(msg, registry) for msg in messages]
    return json.dumps(data, indent=2, ensure_ascii=False)


def decode_json_stream(s: str, registry: TypeRegistry) -> List[Message]:
    """Decode multiple messages from JSON array per spec."""
    data = json.loads(s)
    if not isinstance(data, list):
        raise DecodeError("JSON stream must be an array")
    return [_parse_message(item, registry, None) for item in data]


__all__ = [
    "encode_json",
    "decode_json",
    "encode_json_stream",
    "decode_json_stream",
]