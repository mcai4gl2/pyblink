"""Compact Binary framing + schema-aware message encoding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterator, Tuple

from ..runtime.errors import DecodeError, EncodeError, RegistryError
from ..runtime.registry import TypeRegistry
from ..runtime.values import DecimalValue, Message, StaticGroupValue
from ..schema.model import (
    BinaryType,
    DynamicGroupRef,
    EnumType,
    FieldDef,
    GroupDef,
    ObjectType,
    PrimitiveKind,
    PrimitiveType,
    SequenceType,
    StaticGroupRef,
    TypeRef,
)
from .vlc import decode_vlc, encode_vlc


@dataclass(frozen=True, slots=True)
class Frame:
    """Represents a decoded Compact Binary message frame."""

    type_id: int
    payload: bytes
    length: int
    group: GroupDef | None = None


def encode_frame(type_id: int, payload: bytes) -> bytes:
    """
    Encode the Compact Binary length/type-id preamble.

    Args:
        type_id: Schema type identifier (unsigned).
        payload: Serialized fields + extension bytes.
    """

    if type_id < 0:
        raise EncodeError("Type id must be non-negative")
    type_id_bytes = encode_vlc(type_id)
    body = type_id_bytes + payload
    length_bytes = encode_vlc(len(body))
    return length_bytes + body


def decode_frame(
    buffer: bytes | memoryview,
    offset: int = 0,
    *,
    registry: TypeRegistry | None = None,
    strict: bool = True,
) -> Tuple[Frame, int]:
    """
    Decode a single Compact Binary frame from ``buffer``.

    Args:
        buffer: Raw byte payload containing a frame.
        offset: Starting offset in ``buffer``.
        registry: Optional type registry for resolving `type_id`.
        strict: Whether unknown type ids raise `DecodeError`.
    Returns:
        (Frame, new_offset)
    """

    mv = memoryview(buffer)
    length, cursor = decode_vlc(mv, offset)
    if length is None:
        raise DecodeError("Frame length cannot be NULL")
    end = cursor + length
    if end > len(mv):
        raise DecodeError("Truncated Compact Binary frame")
    type_id, cursor = decode_vlc(mv, cursor)
    if type_id is None:
        raise DecodeError("Frame type id cannot be NULL")
    payload = bytes(mv[cursor:end])
    group: GroupDef | None = None
    if registry:
        try:
            group = registry.get_group_by_id(type_id)
        except RegistryError as exc:
            if strict:
                raise DecodeError(str(exc)) from exc
            group = None
    return Frame(type_id=type_id, payload=payload, length=length, group=group), end


def iter_frames(
    buffer: bytes | memoryview,
    *,
    registry: TypeRegistry | None = None,
    strict: bool = True,
) -> Iterator[Frame]:
    """Yield frames sequentially from ``buffer``."""

    offset = 0
    mv = memoryview(buffer)
    while offset < len(mv):
        frame, offset = decode_frame(mv, offset, registry=registry, strict=strict)
        yield frame


def encode_message(message: Message, registry: TypeRegistry) -> bytes:
    """Encode ``message`` (fields only) and wrap it in a Compact Binary frame."""

    group = registry.get_group_by_name(message.type_name)
    if group.type_id is None:
        raise EncodeError(f"Group {group.name} is missing a type id and cannot be encoded")
    payload = _encode_group_instance(group, message.fields, registry)
    return encode_frame(group.type_id, payload)


def decode_message(
    buffer: bytes | memoryview,
    *,
    offset: int = 0,
    registry: TypeRegistry,
    strict: bool = True,
) -> Tuple[Message, int]:
    """
    Decode a message (frame + fields) from ``buffer``.

    Returns the ``Message`` plus the offset to the next frame.
    """

    frame, new_offset = decode_frame(buffer, offset, registry=registry, strict=strict)
    group = frame.group or registry.get_group_by_id(frame.type_id)
    fields, consumed = _decode_group_fields(group, memoryview(frame.payload), 0, registry)
    if consumed != len(frame.payload):
        raise DecodeError("Trailing bytes inside frame payload")
    message = Message(type_name=group.name, fields=fields)
    return message, new_offset


def _encode_group_instance(
    group: GroupDef, values: Dict[str, object], registry: TypeRegistry, *, is_optional: bool = False
) -> bytes:
    buffer = bytearray()
    for field in group.all_fields():
        value = values.get(field.name)
        if value is None and not field.optional:
            raise EncodeError(f"Missing required field {field.name} for {group.name}")
        buffer.extend(_encode_type(field.type_ref, value, field.optional, registry))
    return bytes(buffer)


def _encode_type(type_ref: TypeRef, value, optional: bool, registry: TypeRegistry) -> bytes:
    if isinstance(type_ref, PrimitiveType):
        return _encode_primitive(type_ref.primitive, value, optional)
    if isinstance(type_ref, BinaryType):
        return _encode_binary(type_ref, value, optional)
    if isinstance(type_ref, EnumType):
        return _encode_enum(type_ref, value, optional)
    if isinstance(type_ref, SequenceType):
        return _encode_sequence(type_ref, value, optional, registry)
    if isinstance(type_ref, StaticGroupRef):
        return _encode_static_group(type_ref.group, value, optional, registry)
    if isinstance(type_ref, DynamicGroupRef):
        raise EncodeError("Dynamic group encoding is not implemented yet")
    if isinstance(type_ref, ObjectType):
        raise EncodeError("Object type encoding is not implemented yet")
    raise EncodeError(f"Unsupported field type {type_ref}")


def _encode_primitive(kind: PrimitiveKind, value, optional: bool) -> bytes:
    if value is None:
        if not optional:
            raise EncodeError("Non-optional primitive field cannot be None")
        if kind == PrimitiveKind.DECIMAL:
            return encode_vlc(None)
        return encode_vlc(None)

    if kind == PrimitiveKind.BOOL:
        return encode_vlc(1 if bool(value) else 0)
    if kind == PrimitiveKind.DECIMAL:
        if isinstance(value, tuple):
            exponent, mantissa = value
        elif isinstance(value, DecimalValue):
            exponent, mantissa = value.exponent, value.mantissa
        else:
            raise EncodeError("Decimal fields require DecimalValue or (exponent, mantissa)")
        return encode_vlc(exponent) + encode_vlc(mantissa)
    if isinstance(value, bool):
        value = int(value)
    if not isinstance(value, int):
        raise EncodeError(f"Primitive {kind.value} expects an int-compatible value")
    return encode_vlc(value)


def _encode_binary(binary: BinaryType, value, optional: bool) -> bytes:
    if value is None:
        if not optional:
            raise EncodeError("Non-optional binary field cannot be None")
        return encode_vlc(None)
    if binary.kind == "string":
        if not isinstance(value, str):
            raise EncodeError("String fields expect str values")
        data = value.encode("utf-8")
    else:
        if not isinstance(value, (bytes, bytearray, memoryview)):
            raise EncodeError("Binary fields expect bytes-like values")
        data = bytes(value)
    if binary.kind == "fixed":
        if len(data) != (binary.size or 0):
            raise EncodeError(f"Fixed field requires exactly {binary.size} bytes")
        return data
    return encode_vlc(len(data)) + data


def _encode_enum(enum: EnumType, value, optional: bool) -> bytes:
    if value is None:
        if not optional:
            raise EncodeError("Non-optional enum field cannot be None")
        return encode_vlc(None)
    if isinstance(value, str):
        number = enum.to_value(value)
    else:
        number = int(value)
    return encode_vlc(number)


def _encode_sequence(
    sequence: SequenceType, value, optional: bool, registry: TypeRegistry
) -> bytes:
    if value is None:
        if not optional:
            raise EncodeError("Non-optional sequence cannot be None")
        return encode_vlc(None)
    if not isinstance(value, (list, tuple)):
        raise EncodeError("Sequence fields expect a list or tuple")
    buffer = bytearray()
    buffer.extend(encode_vlc(len(value)))
    for item in value:
        buffer.extend(_encode_type(sequence.element_type, item, False, registry))
    return bytes(buffer)


def _encode_static_group(
    group: GroupDef, value, optional: bool, registry: TypeRegistry
) -> bytes:
    if value is None:
        if optional:
            raise EncodeError("Optional static group encoding is not implemented")
        raise EncodeError(f"Static group {group.name} requires a value")
    if isinstance(value, StaticGroupValue):
        fields = value.fields
    elif isinstance(value, dict):
        fields = value
    else:
        raise EncodeError("Static group fields must be dict or StaticGroupValue")
    return _encode_group_instance(group, fields, registry)


def _decode_group_fields(
    group: GroupDef,
    payload: memoryview,
    offset: int,
    registry: TypeRegistry,
) -> Tuple[Dict[str, object], int]:
    fields: Dict[str, object] = {}
    cursor = offset
    for field in group.all_fields():
        value, cursor = _decode_type(field.type_ref, payload, cursor, field.optional, registry)
        fields[field.name] = value
    return fields, cursor


def _decode_type(
    type_ref: TypeRef,
    payload: memoryview,
    offset: int,
    optional: bool,
    registry: TypeRegistry,
) -> Tuple[object, int]:
    if isinstance(type_ref, PrimitiveType):
        return _decode_primitive(type_ref.primitive, payload, offset)
    if isinstance(type_ref, BinaryType):
        return _decode_binary(type_ref, payload, offset)
    if isinstance(type_ref, EnumType):
        value, new_offset = decode_vlc(payload, offset)
        if value is None:
            return (None, new_offset)
        return type_ref.to_symbol(int(value)), new_offset
    if isinstance(type_ref, SequenceType):
        size, cursor = decode_vlc(payload, offset)
        if size is None:
            return None, cursor
        items = []
        for _ in range(size):
            item, cursor = _decode_type(type_ref.element_type, payload, cursor, False, registry)
            items.append(item)
        return items, cursor
    if isinstance(type_ref, StaticGroupRef):
        values, cursor = _decode_group_fields(type_ref.group, payload, offset, registry)
        return StaticGroupValue(values), cursor
    if isinstance(type_ref, DynamicGroupRef):
        raise DecodeError("Dynamic group decoding not implemented")
    if isinstance(type_ref, ObjectType):
        raise DecodeError("Object type decoding not implemented")
    raise DecodeError(f"Unsupported type reference {type_ref}")


def _decode_primitive(kind: PrimitiveKind, payload: memoryview, offset: int):
    value, cursor = decode_vlc(payload, offset)
    if value is None:
        return None, cursor
    if kind == PrimitiveKind.BOOL:
        return bool(value), cursor
    if kind == PrimitiveKind.DECIMAL:
        mantissa, cursor2 = decode_vlc(payload, cursor)
        if mantissa is None:
            raise DecodeError("Decimal mantissa cannot be NULL")
        return DecimalValue(exponent=int(value), mantissa=int(mantissa)), cursor2
    return int(value), cursor


def _decode_binary(binary: BinaryType, payload: memoryview, offset: int):
    if binary.kind == "fixed":
        end = offset + (binary.size or 0)
        if end > len(payload):
            raise DecodeError("Truncated fixed binary field")
        data = bytes(payload[offset:end])
        return data, end
    length, cursor = decode_vlc(payload, offset)
    if length is None:
        return None, cursor
    end = cursor + length
    if end > len(payload):
        raise DecodeError("Truncated binary/string field")
    data = bytes(payload[cursor:end])
    if binary.kind == "string":
        return data.decode("utf-8"), end
    return data, end


__all__ = [
    "Frame",
    "decode_frame",
    "decode_message",
    "encode_frame",
    "encode_message",
    "iter_frames",
]
