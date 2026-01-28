"""Tests for binary analyzer service."""

import sys
from pathlib import Path

# Add parent directory to path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from app.services.binary_analyzer import analyze_native_binary
from blink.schema.compiler import compile_schema
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import Message, QName, DecimalValue
from blink.codec.native import encode_native

def test_comprehensive_analysis():
    """Test analysis with a comprehensive schema covering most data types."""
    
    schema_text = """
    namespace Test
    
    # 1. Primitives Group
    Primitives/1 ->
        u8  U8Field,
        i8  I8Field,
        u16 U16Field,
        i16 I16Field,
        u32 U32Field,
        i32 I32Field,
        u64 U64Field,
        i64 I64Field,
        bool BoolTrue,
        bool BoolFalse,
        f64 F64Field,
        decimal DecimalField
        
    # 2. Static Group (Nested Struct)
    Address/2 ->
        string Street,
        string City
        
    # 3. Dynamic Object (Polymorphism)
    Base/3 -> string Type
    Derived/4 : Base -> string Extra
    
    # 4. Enums
    Color = Red/1 | Green/2

    # 4. Main Bundle (Bump ID)
    Bundle/5 ->
        string ShortString,
        string LongString,
        Primitives Prim,
        Address Addr,
        Base* Poly,
        string NullString?,
        string PresentString?,
        u32[] Seq,
        Color MyColor

    """
    
    schema = compile_schema(schema_text)
    registry = TypeRegistry(schema)
    
    # Create Primitives Message
    # ... (same)
    prims = Message(
        type_name=QName("Test", "Primitives"),
        fields={
            "U8Field": 255,
            "I8Field": -128,
            "U16Field": 65535,
            "I16Field": -32768,
            "U32Field": 4294967295,
            "I32Field": -2147483648,
            "U64Field": 1234567890123456789,
            "I64Field": -1234567890123456789,
            "BoolTrue": True,
            "BoolFalse": False,
            "F64Field": 3.14159,
            "DecimalField": DecimalValue(exponent=-2, mantissa=12345) # 123.45
        }
    )
    
    # Create Derived Object for Polymorphism
    derived = Message(
        type_name=QName("Test", "Derived"),
        fields={
            "Type": "Derived",
            "Extra": "Data"
        }
    )
    
    # Create Main Bundle
    long_string = "A" * 300
    
    msg = Message(
        type_name=QName("Test", "Bundle"),
        fields={
            "ShortString": "Hi",
            "LongString": long_string,
            "Prim": prims.fields, 
            "Addr": {"Street": "123 Main", "City": "NYC"},
            "Poly": derived, 
            "NullString": None,
            "PresentString": "Here",
            "Seq": [1, 2, 3],
            "MyColor": "Green"
        }
    )
    
    msg.fields["Prim"] = prims.fields
    
    print("Encoding comprehensive message...")
    try:
        binary_data = encode_native(msg, registry)
        binary_hex = binary_data.hex()
    except Exception as e:
        print(f"Encoding FAIL: {e}")
        raise e

    print("Analyzing message...")
    result = analyze_native_binary(schema_text, binary_hex)
    
    if not result['success']:
        print(f"Analysis Failed: {result.get('error')}")
        raise RuntimeError(result.get('error'))
        
    sections = result['sections']
    fields = result['fields']
    
    print(f"Sections found: {len(sections)}")
    print(f"Fields found: {len(fields)}")
    
    # Helpers
    def find_section(label):
        return next((s for s in sections if s['label'] == label), None)
    
    def find_field(name):
        return next((f for f in fields if f['name'] == name), None)

    # Assertions
    
    # 1. Primitives
    assert find_field("Prim") is not None
    assert find_section("Prim") is not None 
    assert find_section("U8Field")['interpretedValue'] == "255"
    assert find_section("I8Field")['interpretedValue'] == "-128"
    assert find_section("BoolTrue")['interpretedValue'] == "1"
    assert find_section("DecimalField") is not None 
    assert "12345" in find_section("DecimalField")['interpretedValue']

    # 2. Static Group (Addr)
    assert find_field("Addr") is not None
    assert find_section("Addr") is not None
    street_sec = find_section("Street")
    if street_sec:
        assert "123 Main" in street_sec['interpretedValue']

    # 3. Dynamic Object (Poly)
    assert find_section("PolyPtr") is not None
    assert find_field("Poly") is not None 
    assert find_field("Extra") is not None
    assert find_section("Extra")['interpretedValue'] == "Data"
    
    # 4. Optional
    null_p = find_section("NullString?")
    assert null_p is not None and "Null" in null_p['interpretedValue']
    present_p = find_section("PresentString?")
    assert present_p is not None and "Present" in present_p['interpretedValue']
    assert find_section("PresentString")['interpretedValue'] == "Here"
    
    # 5. Sequence
    assert find_section("SeqPtr") is not None
    assert "Sequence" in find_field("Seq")['value']

    # 6. Enum
    color_sec = find_section("MyColor")
    assert color_sec is not None
    assert color_sec['dataType'] == "enum"
    # "Green (2)"
    assert "Green" in color_sec['interpretedValue']
    assert "(2)" in color_sec['interpretedValue']

    print("All assertions passed!")

if __name__ == "__main__":
    print("Running Comprehensive Test Suite...")
    test_comprehensive_analysis()
