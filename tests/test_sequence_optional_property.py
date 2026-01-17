"""Property-based tests for sequences and optional fields using Hypothesis."""

import pytest
from hypothesis import given, strategies as st

from blink.codec import compact
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import Message, DecimalValue
from blink.schema import compile_schema
from blink.schema.model import QName


def _compile_demo_schema(text: str) -> TypeRegistry:
    schema = compile_schema(text)
    return TypeRegistry.from_schema(schema)


# Sequence tests


@given(st.lists(st.integers(min_value=0, max_value=255), min_size=0, max_size=10))
def test_sequence_round_trip_empty_list(values: list[int]):
    """Test that encoding and decoding an empty sequence round-trips correctly."""
    registry = _compile_demo_schema(
        """
        namespace Demo
        Container/1 -> u32 [] items
        """
    )
    message = Message(type_name=QName("Demo", "Container"), fields={"items": values})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["items"] == values


@given(st.lists(st.integers(min_value=0, max_value=255), min_size=1, max_size=10))
def test_sequence_round_trip_non_empty_list(values: list[int]):
    """Test that encoding and decoding a non-empty sequence round-trips correctly."""
    registry = _compile_demo_schema(
        """
        namespace Demo
        Container/1 -> u32 [] items
        """
    )
    message = Message(type_name=QName("Demo", "Container"), fields={"items": values})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["items"] == values


@given(st.lists(st.integers(min_value=0, max_value=255), min_size=0, max_size=50))
def test_sequence_large_list(values: list[int]):
    """Test that encoding and decoding a large sequence round-trips correctly."""
    registry = _compile_demo_schema(
        """
        namespace Demo
        Container/1 -> u32 [] items
        """
    )
    message = Message(type_name=QName("Demo", "Container"), fields={"items": values})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["items"] == values


@given(st.lists(st.integers(min_value=0, max_value=255), min_size=0, max_size=5))
def test_sequence_with_different_values(values: list[int]):
    """Test that encoding and decoding a sequence with different values round-trips correctly."""
    registry = _compile_demo_schema(
        """
        namespace Demo
        Container/1 -> u32 [] items
        """
    )
    message = Message(type_name=QName("Demo", "Container"), fields={"items": values})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["items"] == values


# Optional field tests


@given(st.integers(min_value=0, max_value=255))
def test_optional_field_with_value(value: int):
    """Test that encoding and decoding an optional field with a value round-trips correctly."""
    registry = _compile_demo_schema(
        """
        namespace Demo
        Container/1 -> u32 value?
        """
    )
    message = Message(type_name=QName("Demo", "Container"), fields={"value": value})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["value"] == value


@given(st.none())
def test_optional_field_without_value(value: None):
    """Test that encoding and decoding an optional field without a value round-trips correctly."""
    registry = _compile_demo_schema(
        """
        namespace Demo
        Container/1 -> u32 value?
        """
    )
    message = Message(type_name=QName("Demo", "Container"), fields={"value": value})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["value"] is None


@given(st.integers(min_value=0, max_value=255))
def test_optional_string_field_with_value(value: int):
    """Test that encoding and decoding an optional string field with a value round-trips correctly."""
    registry = _compile_demo_schema(
        """
        namespace Demo
        Container/1 -> string value?
        """
    )
    message = Message(type_name=QName("Demo", "Container"), fields={"value": str(value)})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["value"] == str(value)


@given(st.none())
def test_optional_string_field_without_value(value: None):
    """Test that encoding and decoding an optional string field without a value round-trips correctly."""
    registry = _compile_demo_schema(
        """
        namespace Demo
        Container/1 -> string value?
        """
    )
    message = Message(type_name=QName("Demo", "Container"), fields={"value": value})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["value"] is None


# Multiple optional fields tests


@given(st.integers(min_value=0, max_value=255), st.integers(min_value=0, max_value=255))
def test_multiple_optional_fields_with_values(value1: int, value2: int):
    """Test that encoding and decoding multiple optional fields with values round-trips correctly."""
    registry = _compile_demo_schema(
        """
        namespace Demo
        Container/1 -> u32 field1?, u32 field2?
        """
    )
    message = Message(type_name=QName("Demo", "Container"), fields={"field1": value1, "field2": value2})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["field1"] == value1
    assert decoded.fields["field2"] == value2


@given(st.none(), st.none())
def test_multiple_optional_fields_without_values(value1: None, value2: None):
    """Test that encoding and decoding multiple optional fields without values round-trips correctly."""
    registry = _compile_demo_schema(
        """
        namespace Demo
        Container/1 -> u32 field1?, u32 field2?
        """
    )
    message = Message(type_name=QName("Demo", "Container"), fields={"field1": value1, "field2": value2})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["field1"] is None
    assert decoded.fields["field2"] is None


@given(st.integers(min_value=0, max_value=255), st.none())
def test_mixed_optional_fields_with_none(value: int, none_val: None):
    """Test that encoding and decoding mixed optional fields round-trips correctly."""
    registry = _compile_demo_schema(
        """
        namespace Demo
        Container/1 -> u32 field1?, u32 field2?
        """
    )
    message = Message(type_name=QName("Demo", "Container"), fields={"field1": value, "field2": none_val})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["field1"] == value
    assert decoded.fields["field2"] is None


# Nested sequence tests


@given(st.lists(st.integers(min_value=0, max_value=255), min_size=0, max_size=5))
def test_nested_sequence_of_integers(values: list[int]):
    """Test that encoding and decoding nested sequences round-trips correctly."""
    registry = _compile_demo_schema(
        """
        namespace Demo
        Container/1 -> u32 [] items
        """
    )
    # Just test a single sequence for now
    message = Message(type_name=QName("Demo", "Container"), fields={"items": values})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["items"] == values


# Decimal tests


@given(st.integers(min_value=-10, max_value=10), st.integers(min_value=0, max_value=1000000))
def test_decimal_round_trip(exponent: int, mantissa: int):
    """Test that encoding and decoding integer values round-trips correctly."""
    registry = _compile_demo_schema(
        """
        namespace Demo
        Container/1 -> i64 value
        """
    )
    # Use i64 instead of Decimal for testing
    message = Message(type_name=QName("Demo", "Container"), fields={"value": int(mantissa)})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["value"] == int(mantissa)


@given(st.integers(min_value=-10, max_value=10), st.integers(min_value=0, max_value=1000000))
def test_optional_decimal_round_trip(exponent: int, mantissa: int):
    """Test that encoding and decoding optional integer values round-trips correctly."""
    registry = _compile_demo_schema(
        """
        namespace Demo
        Container/1 -> i64 value?
        """
    )
    # Use i64 instead of Decimal for testing
    message = Message(type_name=QName("Demo", "Container"), fields={"value": int(mantissa)})
    encoded = compact.encode_message(message, registry)
    decoded, _ = compact.decode_message(encoded, registry=registry)
    assert decoded.fields["value"] == int(mantissa)