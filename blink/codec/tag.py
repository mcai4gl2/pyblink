"""Tag Format codec for Blink protocol (Section 6).

The Tag format is a human-readable text representation with the syntax:
    @Type|field=value|field=value|[ extension ]

- One message per line
- Field order irrelevant
- Optional fields omitted
- Reserved chars: |[]{};#\\
"""

from __future__ import annotations

import re
from typing import Dict, Iterator, List, Tuple

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

# Reserved characters that need escaping
_RESERVED_CHARS = set("|[]{};#\\")

# Escape sequence patterns
_ESCAPE_PATTERNS = {
    r"\\n": "\n",
    r"\\x": None,  # Special case: \xNN
    r"\\u": None,  # Special case: \uXXXX
    r"\\U": None,  # Special case: \UXXXXXXXX
}


def _escape_char(c: str) -> str:
    """Escape a single character for Tag format."""
    if c == "\n":
        return r"\n"
    if c == "\r":
        return r"\r"
    if c == "\t":
        return r"\t"
    if c in _RESERVED_CHARS:
        return f"\\{c}"
    if ord(c) < 32 or ord(c) > 126:
        return f"\\x{ord(c):02x}"
    return c


def _escape_string(s: str) -> str:
    """Escape a string value for Tag format."""
    # Encode as UTF-8 bytes, then escape each byte
    result = []
    for byte in s.encode("utf-8"):
        result.append(_escape_char(chr(byte)))
    return "".join(result)


def _unescape_string(s: str) -> str:
    """Unescape a string value from Tag format."""
    result = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            next_char = s[i + 1]
            if next_char == "n":
                result.append("\n")
                i += 2
            elif next_char == "r":
                result.append("\r")
                i += 2
            elif next_char == "t":
                result.append("\t")
                i += 2
            elif next_char == "x" and i + 3 < len(s):
                # \xNN
                hex_val = s[i + 2 : i + 4]
                result.append(chr(int(hex_val, 16)))
                i += 4
            elif next_char == "u" and i + 5 < len(s):
                # \uXXXX
                hex_val = s[i + 2 : i + 6]
                result.append(chr(int(hex_val, 16)))
                i += 6
            elif next_char == "U" and i + 9 < len(s):
                # \UXXXXXXXX
                hex_val = s[i + 2 : i + 10]
                result.append(chr(int(hex_val, 16)))
                i += 10
            elif next_char in _RESERVED_CHARS:
                result.append(next_char)
                i += 2
            else:
                result.append(next_char)
                i += 2
        else:
            result.append(s[i])
            i += 1
    return "".join(result)


def _escape_binary(data: bytes) -> str:
    """Escape binary data as hex list: [3e 6d 4a]"""
    hex_bytes = " ".join(f"{b:02x}" for b in data)
    return f"[{hex_bytes}]"


def _unescape_binary(s: str) -> bytes:
    """Unescape binary data from hex list format: [3e 6d 4a]"""
    s = s.strip()
    if not (s.startswith("[") and s.endswith("]")):
        raise DecodeError(f"Invalid binary format: {s}")
    hex_str = s[1:-1].strip()
    if not hex_str:
        return b""
    hex_parts = hex_str.split()
    return bytes(int(part, 16) for part in hex_parts)


def _format_value(value, type_ref: TypeRef, registry: TypeRegistry, default_namespace: str | None) -> str:
    """Format a value as a Tag string."""
    if value is None:
        raise EncodeError("Cannot format None value in Tag format")

    if isinstance(type_ref, PrimitiveType):
        if type_ref.primitive == PrimitiveKind.BOOL:
            return "true" if value else "false"
        if type_ref.primitive == PrimitiveKind.DECIMAL:
            if isinstance(value, DecimalValue):
                return f"{value.mantissa}e{value.exponent}"
            elif isinstance(value, tuple):
                return f"{value[1]}e{value[0]}"
            else:
                raise EncodeError("Decimal values require DecimalValue or tuple")
        return str(int(value))

    if isinstance(type_ref, BinaryType):
        if type_ref.kind == "string":
            return _escape_string(str(value))
        else:
            return _escape_binary(bytes(value))

    if isinstance(type_ref, EnumType):
        return str(value)

    if isinstance(type_ref, SequenceType):
        if not isinstance(value, (list, tuple)):
            raise EncodeError("Sequence values must be list or tuple")
        items = [_format_value(item, type_ref.element_type, registry, default_namespace) for item in value]
        return f"{{{','.join(items)}}}"

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

    if isinstance(type_ref, StaticGroupRef):
        if isinstance(value, StaticGroupValue):
            fields = value.fields
        elif isinstance(value, dict):
            fields = value
        else:
            raise EncodeError("Static group values must be dict or StaticGroupValue")
        field_strs = []
        for field in type_ref.group.all_fields():
            if field.name not in fields or fields[field.name] is None:
                continue
            field_val = _format_value(fields[field.name], field.type_ref, registry, default_namespace)
            field_strs.append(f"{field.name}={field_val}")
        return f"{{{','.join(field_strs)}}}"

    raise EncodeError(f"Unsupported type for Tag format: {type_ref}")


def _format_message(message: Message, registry: TypeRegistry) -> str:
    """Format a complete message as a Tag string."""
    group = registry.get_group_by_name(message.type_name)
    parts = [f"@{group.name}"]

    for field in group.all_fields():
        value = message.fields.get(field.name)
        if value is None:
            continue
        field_str = _format_value(value, field.type_ref, registry, group.name.namespace)
        parts.append(f"{field.name}={field_str}")

    if message.extensions:
        ext_str = ",".join(_format_message(ext, registry) for ext in message.extensions)
        parts.append(f"[{ext_str}]")

    return "|".join(parts)


def encode_tag(message: Message, registry: TypeRegistry) -> str:
    """Encode a message to Tag format string."""
    return _format_message(message, registry)


def _parse_value(s: str, type_ref: TypeRef, registry: TypeRegistry, default_namespace: str | None):
    """Parse a value from Tag string."""
    if isinstance(type_ref, PrimitiveType):
        if type_ref.primitive == PrimitiveKind.BOOL:
            if s.lower() == "true":
                return True
            elif s.lower() == "false":
                return False
            else:
                raise DecodeError(f"Invalid boolean value: {s}")
        if type_ref.primitive == PrimitiveKind.DECIMAL:
            # Parse mantissa e exponent format: 15005e-2
            match = re.match(r"^(-?\d+)e(-?\d+)$", s)
            if not match:
                raise DecodeError(f"Invalid decimal format: {s}")
            mantissa = int(match.group(1))
            exponent = int(match.group(2))
            return DecimalValue(exponent=exponent, mantissa=mantissa)
        return int(s)

    if isinstance(type_ref, BinaryType):
        if type_ref.kind == "string":
            return _unescape_string(s)
        else:
            return _unescape_binary(s)

    if isinstance(type_ref, EnumType):
        return s

    if isinstance(type_ref, SequenceType):
        # Parse sequence as {item1,item2,...}
        if not (s.startswith("{") and s.endswith("}")):
            raise DecodeError(f"Invalid sequence format: {s}")
        inner = s[1:-1].strip()
        if not inner:
            return []
        items = []
        # Simple parsing - split by comma (doesn't handle nested commas)
        # For production, need proper parser
        parts = _split_tag_sequence(inner)
        for part in parts:
            items.append(_parse_value(part.strip(), type_ref.element_type, registry, default_namespace))
        return items

    if isinstance(type_ref, StaticGroupRef):
        # Parse static group as {field1=value1,field2=value2,...}
        if not (s.startswith("{") and s.endswith("}")):
            raise DecodeError(f"Invalid static group format: {s}")
        inner = s[1:-1].strip()
        if not inner:
            return StaticGroupValue({})
        fields = {}
        # Parse field=value pairs
        field_pairs = _split_tag_fields(inner)
        for pair in field_pairs:
            if "=" not in pair:
                continue
            field_name, field_value = pair.split("=", 1)
            field_name = field_name.strip()
            field_value = field_value.strip()
            field_def = _find_field(type_ref.group, field_name)
            if field_def:
                fields[field_name] = _parse_value(field_value, field_def.type_ref, registry, default_namespace)
        return StaticGroupValue(fields)

    if isinstance(type_ref, DynamicGroupRef) or isinstance(type_ref, ObjectType):
        # Dynamic group is encoded as a nested Tag message
        return decode_tag(s, registry)

    raise DecodeError(f"Unsupported type for Tag parsing: {type_ref}")


def _find_field(group: FieldDef, name: str) -> FieldDef | None:
    """Find a field definition by name."""
    for field in group.all_fields():
        if field.name == name:
            return field
    return None


def _split_tag_sequence(s: str) -> List[str]:
    """Split a Tag sequence by commas, respecting nested braces."""
    result = []
    current = []
    depth = 0
    for c in s:
        if c == "{" and depth == 0:
            current.append(c)
            depth += 1
        elif c == "}" and depth > 0:
            current.append(c)
            depth -= 1
        elif c == "," and depth == 0:
            result.append("".join(current))
            current = []
        else:
            current.append(c)
    if current:
        result.append("".join(current))
    return result


def _split_tag_fields(s: str) -> List[str]:
    """Split Tag field pairs by commas, respecting nested braces."""
    result = []
    current = []
    depth = 0
    for c in s:
        if c == "{":
            current.append(c)
            depth += 1
        elif c == "}" and depth > 0:
            current.append(c)
            depth -= 1
        elif c == "," and depth == 0:
            result.append("".join(current))
            current = []
        else:
            current.append(c)
    if current:
        result.append("".join(current))
    return result


def _parse_field_pair(pair: str) -> Tuple[str, str]:
    """Parse a field=value pair."""
    if "=" not in pair:
        raise DecodeError(f"Invalid field pair: {pair}")
    name, value = pair.split("=", 1)
    return name.strip(), value.strip()


def decode_tag(s: str, registry: TypeRegistry) -> Message:
    """Decode a message from Tag format string."""
    s = s.strip()
    if not s.startswith("@"):
        raise DecodeError(f"Invalid Tag format: missing @ prefix")

    # Split by | but respect nested []
    parts = _split_tag_parts(s[1:])  # Skip @

    if not parts:
        raise DecodeError(f"Invalid Tag format: no type specified")

    type_name = parts[0]
    qname = QName.parse(type_name)
    group = registry.get_group_by_name(qname)

    fields: Dict[str, object] = {}
    extensions: List[Message] = []

    for part in parts[1:]:
        part = part.strip()
        if part.startswith("[") and part.endswith("]"):
            # Parse extensions
            ext_inner = part[1:-1].strip()
            if ext_inner:
                ext_messages = _split_tag_extensions(ext_inner)
                for ext_msg in ext_messages:
                    extensions.append(decode_tag(ext_msg.strip(), registry))
        else:
            # Parse field=value
            name, value = _parse_field_pair(part)
            field_def = _find_field(group, name)
            if field_def:
                fields[name] = _parse_value(value, field_def.type_ref, registry, group.name.namespace)

    return Message(type_name=qname, fields=fields, extensions=tuple(extensions))


def _split_tag_parts(s: str) -> List[str]:
    """Split Tag parts by |, respecting nested [], {}, and @ symbols, and escaped characters."""
    result = []
    current = []
    bracket_depth = 0
    brace_depth = 0
    at_depth = 0  # Track depth of nested @ symbols
    escaped = False  # Track if we're inside an escape sequence

    i = 0
    while i < len(s):
        c = s[i]

        if escaped:
            # Inside an escape sequence - just add the character and move on
            current.append(c)
            escaped = False
            i += 1
            continue

        if c == "\\":
            # Start of an escape sequence
            current.append(c)
            escaped = True
            i += 1
            continue

        if c == "@" and bracket_depth == 0 and brace_depth == 0 and at_depth == 0:
            # New @ symbol - this might be a nested message
            at_depth += 1
            current.append(c)
        elif c == "@" and bracket_depth == 0 and brace_depth == 0 and at_depth > 0:
            # Another @ symbol while already inside a nested message
            at_depth += 1
            current.append(c)
        elif c == "[":
            current.append(c)
            bracket_depth += 1
        elif c == "]" and bracket_depth > 0:
            current.append(c)
            bracket_depth -= 1
        elif c == "{":
            current.append(c)
            brace_depth += 1
        elif c == "}" and brace_depth > 0:
            current.append(c)
            brace_depth -= 1
        elif c == "|" and bracket_depth == 0 and brace_depth == 0 and at_depth == 0:
            # Split at | only if we're not inside any nested structure
            result.append("".join(current))
            current = []
        else:
            current.append(c)

        i += 1

    if current:
        result.append("".join(current))

    return result


def _split_tag_extensions(s: str) -> List[str]:
    """Split extension messages by commas, respecting nested @ symbols."""
    result = []
    current = []
    depth = 0
    in_type = False

    for c in s:
        if c == "@" and depth == 0:
            if current:
                result.append("".join(current))
                current = []
            current.append(c)
            in_type = True
        elif c == "[":
            current.append(c)
            depth += 1
        elif c == "]" and depth > 0:
            current.append(c)
            depth -= 1
        elif c == "{" and depth == 0:
            current.append(c)
            brace_depth = 1
            # Count braces
            for remaining in s[s.index(c) + 1:]:
                if remaining == "{":
                    brace_depth += 1
                elif remaining == "}":
                    brace_depth -= 1
                    if brace_depth == 0:
                        break
        elif c == "," and depth == 0 and not in_type:
            if current:
                result.append("".join(current))
                current = []
        else:
            current.append(c)
            in_type = False

    if current:
        result.append("".join(current))

    return result


def encode_tag_stream(messages: List[Message], registry: TypeRegistry) -> str:
    """Encode multiple messages to Tag format (one per line)."""
    return "\n".join(encode_tag(msg, registry) for msg in messages)


def decode_tag_stream(s: str, registry: TypeRegistry) -> Iterator[Message]:
    """Decode multiple messages from Tag format (one per line)."""
    for line in s.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            yield decode_tag(line, registry)


__all__ = [
    "encode_tag",
    "decode_tag",
    "encode_tag_stream",
    "decode_tag_stream",
]