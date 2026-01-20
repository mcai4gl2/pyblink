"""Tests for Native Binary format codec."""

import pytest
from blink.codec import native
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import DecimalValue, Message
from blink.schema.model import QName


def _compile_schema(schema_text: str) -> TypeRegistry:
    """Helper to compile schema text."""
    return TypeRegistry.from_schema_text(schema_text)


def test_native_hello_world():
    """Test the Hello World example from the spec."""
    registry = _compile_schema("""
        namespace Demo
        Hello/1 -> string Greeting
    """)
    
    message = Message(
        type_name=QName("Demo", "Hello"),
        fields={"Greeting": "Hello World"}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.type_name == message.type_name
    assert decoded.fields["Greeting"] == "Hello World"


def test_native_optional_fields():
    """Test optional fields with presence byte."""
    registry = _compile_schema("""
        namespace Demo
        Bill/2 -> u32 Amount, u32 Tip?
    """)
    
    # Message without optional field
    msg1 = Message(
        type_name=QName("Demo", "Bill"),
        fields={"Amount": 100}
    )
    
    encoded1 = native.encode_native(msg1, registry)
    decoded1, _ = native.decode_native(encoded1, registry)
    assert decoded1.fields["Amount"] == 100
    assert decoded1.fields["Tip"] is None
    
    # Message with optional field
    msg2 = Message(
        type_name=QName("Demo", "Bill"),
        fields={"Amount": 1000, "Tip": 100}
    )
    
    encoded2 = native.encode_native(msg2, registry)
    decoded2, _ = native.decode_native(encoded2, registry)
    assert decoded2.fields["Amount"] == 1000
    assert decoded2.fields["Tip"] == 100


def test_native_variable_strings():
    """Test variable-size strings with offsets."""
    registry = _compile_schema("""
        namespace Demo
        Person/3 -> string FirstName, string LastName
    """)
    
    message = Message(
        type_name=QName("Demo", "Person"),
        fields={"FirstName": "George", "LastName": "Blink"}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["FirstName"] == "George"
    assert decoded.fields["LastName"] == "Blink"


def test_native_integer_types():
    """Test various integer types."""
    registry = _compile_schema("""
        namespace Demo
        Numbers/4 -> u8 Byte, i16 Short, u32 Int, i64 Long
    """)
    
    message = Message(
        type_name=QName("Demo", "Numbers"),
        fields={"Byte": 17, "Short": -1, "Int": 17, "Long": -9223372036854775808}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["Byte"] == 17
    assert decoded.fields["Short"] == -1
    assert decoded.fields["Int"] == 17
    assert decoded.fields["Long"] == -9223372036854775808


def test_native_inline_string():
    """Test inline string with fixed capacity."""
    registry = _compile_schema("""
        namespace Demo
        Hello/1 -> string (12) Greeting
    """)
    
    message = Message(
        type_name=QName("Demo", "Hello"),
        fields={"Greeting": "Hello World"}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["Greeting"] == "Hello World"


def test_native_fixed_binary():
    """Test fixed-size binary."""
    registry = _compile_schema("""
        namespace Demo
        InetAddr/5 -> fixed (4) Addr
    """)
    
    message = Message(
        type_name=QName("Demo", "InetAddr"),
        fields={"Addr": b"\x3e\x6d\x3c\xea"}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["Addr"] == b"\x3e\x6d\x3c\xea"


def test_native_boolean():
    """Test boolean encoding."""
    registry = _compile_schema("""
        namespace Demo
        Flag/6 -> bool Value
    """)
    
    msg_true = Message(type_name=QName("Demo", "Flag"), fields={"Value": True})
    msg_false = Message(type_name=QName("Demo", "Flag"), fields={"Value": False})
    
    encoded_true = native.encode_native(msg_true, registry)
    encoded_false = native.encode_native(msg_false, registry)
    
    decoded_true, _ = native.decode_native(encoded_true, registry)
    decoded_false, _ = native.decode_native(encoded_false, registry)
    
    assert decoded_true.fields["Value"] is True
    assert decoded_false.fields["Value"] is False


def test_native_decimal():
    """Test decimal encoding."""
    registry = _compile_schema("""
        namespace Demo
        Price/7 -> decimal Amount
    """)
    
    message = Message(
        type_name=QName("Demo", "Price"),
        fields={"Amount": DecimalValue(exponent=-2, mantissa=15005)}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["Amount"].exponent == -2
    assert decoded.fields["Amount"].mantissa == 15005


def test_native_f64():
    """Test f64 encoding."""
    registry = _compile_schema("""
        namespace Demo
        Measurement/8 -> f64 Value
    """)
    
    message = Message(
        type_name=QName("Demo", "Measurement"),
        fields={"Value": 1.23456789}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert abs(decoded.fields["Value"] - 1.23456789) < 1e-8


def test_native_sequence():
    """Test sequence encoding."""
    registry = _compile_schema("""
        namespace Demo
        Chart/4 -> u32 [] Xvals, u32 [] Yvals
    """)
    
    message = Message(
        type_name=QName("Demo", "Chart"),
        fields={"Xvals": [0, 10, 20], "Yvals": [1, 17, 0]}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["Xvals"] == [0, 10, 20]
    assert decoded.fields["Yvals"] == [1, 17, 0]


def test_native_static_group():
    """Test static group encoding."""
    registry = _compile_schema("""
        namespace Demo
        Point -> u32 X, u32 Y
        Rect/5 -> Point Pos, u32 Width, u32 Height
    """)
    
    message = Message(
        type_name=QName("Demo", "Rect"),
        fields={"Pos": {"X": 3, "Y": 4}, "Width": 10, "Height": 10}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["Pos"].fields["X"] == 3
    assert decoded.fields["Pos"].fields["Y"] == 4
    assert decoded.fields["Width"] == 10
    assert decoded.fields["Height"] == 10


def test_native_sequence_of_static_groups():
    """Test sequence of static groups."""
    registry = _compile_schema("""
        namespace Demo
        Point -> u32 X, u32 Y
        Path/6 -> Point [] Points
    """)
    
    message = Message(
        type_name=QName("Demo", "Path"),
        fields={"Points": [{"X": 1, "Y": 1}, {"X": 10, "Y": 2}]}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    points = decoded.fields["Points"]
    assert len(points) == 2
    assert points[0].fields["X"] == 1
    assert points[0].fields["Y"] == 1
    assert points[1].fields["X"] == 10
    assert points[1].fields["Y"] == 2


def test_native_dynamic_group():
    """Test dynamic group encoding."""
    registry = _compile_schema("""
        namespace Demo
        Shape
        Rect/7 : Shape -> u32 Wdt, u32 Hgt
        Circle/8 : Shape -> u32 Rad
        Canvas/9 -> Shape* [] Shapes
    """)
    
    rect = Message(type_name=QName("Demo", "Rect"), fields={"Wdt": 2, "Hgt": 3})
    circle = Message(type_name=QName("Demo", "Circle"), fields={"Rad": 3})
    
    message = Message(
        type_name=QName("Demo", "Canvas"),
        fields={"Shapes": [rect, circle]}
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    shapes = decoded.fields["Shapes"]
    assert len(shapes) == 2
    assert shapes[0].type_name == QName("Demo", "Rect")
    assert shapes[0].fields["Wdt"] == 2
    assert shapes[0].fields["Hgt"] == 3
    assert shapes[1].type_name == QName("Demo", "Circle")
    assert shapes[1].fields["Rad"] == 3


def test_native_extensions():
    """Test message extensions."""
    registry = _compile_schema("""
        namespace Demo
        Mail/10 -> string Subject, string Body
        Trace/11 -> string Hop
    """)
    
    trace1 = Message(type_name=QName("Demo", "Trace"), fields={"Hop": "local.eg.org"})
    trace2 = Message(type_name=QName("Demo", "Trace"), fields={"Hop": "mail.eg.org"})
    
    message = Message(
        type_name=QName("Demo", "Mail"),
        fields={"Subject": "Hello", "Body": "How are you?"},
        extensions=(trace1, trace2)
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["Subject"] == "Hello"
    assert decoded.fields["Body"] == "How are you?"
    assert len(decoded.extensions) == 2
    assert decoded.extensions[0].fields["Hop"] == "local.eg.org"
    assert decoded.extensions[1].fields["Hop"] == "mail.eg.org"


def test_native_round_trip_complex():
    """Test round-trip with complex message."""
    registry = _compile_schema("""
        namespace Demo
        AllTypes/1 ->
            u32 int_val,
            i32 signed_val,
            bool bool_val,
            string str_val,
            binary bin_val,
            decimal dec_val,
            f64 float_val,
            u32 [] seq_val
    """)
    
    message = Message(
        type_name=QName("Demo", "AllTypes"),
        fields={
            "int_val": 42,
            "signed_val": -100,
            "bool_val": True,
            "str_val": "test",
            "bin_val": b"\x01\x02\x03",
            "dec_val": DecimalValue(exponent=-2, mantissa=15005),
            "float_val": 3.14159,
            "seq_val": [1, 2, 3],
        },
    )
    
    encoded = native.encode_native(message, registry)
    decoded, _ = native.decode_native(encoded, registry)
    
    assert decoded.fields["int_val"] == 42
    assert decoded.fields["signed_val"] == -100
    assert decoded.fields["bool_val"] is True
    assert decoded.fields["str_val"] == "test"
    assert decoded.fields["bin_val"] == b"\x01\x02\x03"
    assert decoded.fields["dec_val"].exponent == -2
    assert decoded.fields["dec_val"].mantissa == 15005
    assert abs(decoded.fields["float_val"] - 3.14159) < 1e-5
    assert decoded.fields["seq_val"] == [1, 2, 3]
