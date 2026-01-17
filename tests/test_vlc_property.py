"""Property-based tests for VLC codec using Hypothesis."""

import pytest
from hypothesis import given, strategies as st

from blink.codec import vlc
from blink.runtime.errors import DecodeError


# VLC encoding/decode round-trip tests


@given(st.integers(min_value=0, max_value=2**63 - 1))
def test_vlc_round_trip_unsigned(value: int):
    """Test that VLC encoding and decoding round-trips for unsigned integers."""
    encoded = vlc.encode_vlc(value)
    decoded, offset = vlc.decode_vlc(encoded, 0)
    assert decoded == value
    assert offset == len(encoded)


@given(st.integers(min_value=-(2**63), max_value=2**63 - 1))
def test_vlc_round_trip_signed(value: int):
    """Test that VLC encoding and decoding round-trips for signed integers."""
    encoded = vlc.encode_vlc(value)
    decoded, offset = vlc.decode_vlc(encoded, 0)
    assert decoded == value
    assert offset == len(encoded)


@given(st.none())
def test_vlc_null_encoding(value: None):
    """Test that NULL encoding and decoding round-trips."""
    encoded = vlc.encode_vlc(value)
    decoded, offset = vlc.decode_vlc(encoded, 0)
    assert decoded is None
    assert offset == 1
    assert encoded == b"\xC0"


# Edge case tests


@given(st.integers(min_value=0, max_value=127))
def test_vlc_single_byte_stop_bit(value: int):
    """Test that the last byte has the stop bit set."""
    encoded = vlc.encode_vlc(value)
    assert encoded[-1] & 0x80 != 0


# Negative value tests


@given(st.integers(min_value=-(2**63), max_value=-129))
def test_vlc_negative_multi_byte_encoding(value: int):
    """Test that negative values < -128 encode to multiple bytes."""
    encoded = vlc.encode_vlc(value)
    assert len(encoded) >= 2


# Boundary value tests


@pytest.mark.parametrize("value", [0, 1, -1, 127, 128, -128, 255, 256, -255, -256])
def test_vlc_boundary_values(value: int):
    """Test VLC encoding/decoding at boundary values."""
    encoded = vlc.encode_vlc(value)
    decoded, offset = vlc.decode_vlc(encoded, 0)
    assert decoded == value


# Multiple value tests


@given(st.lists(st.integers(min_value=0, max_value=2**20 - 1), min_size=0, max_size=10))
def test_vlc_multiple_values_round_trip(values: list[int]):
    """Test that encoding and decoding multiple values round-trips correctly."""
    encoded = b"".join(vlc.encode_vlc(v) for v in values)
    decoded_values = []
    offset = 0
    for _ in values:
        decoded, offset = vlc.decode_vlc(encoded, offset)
        decoded_values.append(decoded)
    assert decoded_values == values


@given(st.integers(min_value=0, max_value=2**63 - 1), st.integers(min_value=0, max_value=100))
def test_vlc_decode_with_offset(value: int, offset: int):
    """Test that decoding with an offset works correctly."""
    prefix = bytes([0xFF] * offset)
    encoded = vlc.encode_vlc(value)
    buffer = prefix + encoded
    decoded, new_offset = vlc.decode_vlc(buffer, offset)
    assert decoded == value
    assert new_offset == offset + len(encoded)


# Error handling tests


@given(st.integers(min_value=0, max_value=100))
def test_vlc_decode_out_of_bounds(offset: int):
    """Test that decoding with an out-of-bounds offset raises DecodeError."""
    with pytest.raises(DecodeError):
        vlc.decode_vlc(b"", offset)


# Special value tests


@pytest.mark.parametrize("value", [0, 1, -1, 63, 64, 127, -64, -65])
def test_vlc_special_values(value: int):
    """Test VLC encoding/decoding for special values from the spec."""
    encoded = vlc.encode_vlc(value)
    decoded, offset = vlc.decode_vlc(encoded, 0)
    assert decoded == value
    assert offset == len(encoded)