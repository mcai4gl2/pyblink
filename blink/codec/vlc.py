"""Variable Length Coding (VLC) helpers for Blink Compact Binary."""

from __future__ import annotations

from typing import Iterable, Tuple

from ..runtime.errors import DecodeError, EncodeError

NULL_BYTE = 0xC0
STOP_BIT = 0x80
SIGN_BIT = 0x40
DATA_MASK = 0x7F


def _encode_chunks(value: int, *, force_extended: bool = False) -> bytes:
    result = bytearray()
    remaining = value
    is_first = True
    while True:
        byte = remaining & DATA_MASK
        remaining >>= 7
        sign_set = byte & SIGN_BIT
        done = (remaining == 0 and sign_set == 0) or (remaining == -1 and sign_set != 0)
        if force_extended and is_first and done:
            done = False
        if done:
            byte |= STOP_BIT
        result.append(byte & 0xFF)
        if done:
            break
        is_first = False
    return bytes(result)


def encode_vlc(value: int | None) -> bytes:
    """
    Encode an integer into Blink's stop-bit VLC representation.

    The implementation is compatible with the FAST-style stop-bit algorithm:
    - Bytes are emitted little-endian, 7 bits of payload each.
    - The stop bit (0x80) marks the final byte.
    - Signed integers use two's complement (bit 0x40 acts as the sign bit).
    - A dedicated NULL sentinel is encoded as the single byte 0xC0.
    """

    if value is None:
        return bytes([NULL_BYTE])

    if not isinstance(value, int):
        raise EncodeError("VLC only supports integer values")

    encoded = _encode_chunks(value)
    if encoded == bytes([NULL_BYTE]):
        encoded = _encode_chunks(value, force_extended=True)
    return encoded


def decode_vlc(buffer: bytes | memoryview, offset: int = 0) -> Tuple[int | None, int]:
    """
    Decode a VLC integer from ``buffer`` starting at ``offset``.

    Returns a tuple of the decoded integer (or ``None`` if the NULL sentinel
    is encountered) and the new offset.
    """

    mv = memoryview(buffer)
    if offset >= len(mv):
        raise DecodeError("Offset beyond end of buffer")

    first = mv[offset]
    if first == NULL_BYTE:
        return None, offset + 1

    shift = 0
    value = 0
    index = offset

    while True:
        if index >= len(mv):
            raise DecodeError("Truncated VLC value")
        byte = mv[index]
        index += 1
        value |= (byte & DATA_MASK) << shift
        shift += 7
        if byte & STOP_BIT:
            if byte & SIGN_BIT:
                value |= -1 << shift
            return value, index

    raise DecodeError("Missing stop bit in VLC value")


__all__ = ["encode_vlc", "decode_vlc", "NULL_BYTE"]
