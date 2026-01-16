"""Tests for the VLC codec helpers."""

import pytest

from blink.codec import vlc
from blink.runtime.errors import DecodeError, EncodeError


@pytest.mark.parametrize(
    "value",
    [
        None,
        0,
        1,
        -1,
        63,
        64,
        127,
        -64,
        -65,
        2**31 - 1,
        -(2**31),
        2**63 - 1,
        -(2**63),
    ],
)
def test_vlc_round_trip(value):
    encoded = vlc.encode_vlc(value)
    decoded, offset = vlc.decode_vlc(encoded, 0)
    assert decoded == value
    assert offset == len(encoded)


def test_vlc_decode_with_offset():
    payload = b"\x00" + vlc.encode_vlc(12345)
    decoded, offset = vlc.decode_vlc(payload, 1)
    assert decoded == 12345
    assert offset == len(payload)


def test_vlc_null_encoding():
    assert vlc.encode_vlc(None) == b"\xC0"
    decoded, offset = vlc.decode_vlc(b"\xC0")
    assert decoded is None
    assert offset == 1


def test_vlc_negative_value_not_null():
    encoded = vlc.encode_vlc(-64)
    assert encoded != b"\xC0"
    decoded, _ = vlc.decode_vlc(encoded)
    assert decoded == -64


def test_vlc_decode_truncated():
    with pytest.raises(DecodeError):
        vlc.decode_vlc(b"\x01")


def test_vlc_decode_out_of_bounds():
    with pytest.raises(DecodeError):
        vlc.decode_vlc(b"", 0)


def test_vlc_encode_non_int_raises():
    with pytest.raises(EncodeError):
        vlc.encode_vlc("42")  # type: ignore[arg-type]
