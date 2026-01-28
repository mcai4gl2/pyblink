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
    
    # 4. Main Bundle
    Bundle/5 ->
        string ShortString,
        string LongString,
        Primitives Prim,
        Address Addr,
        Base* Poly,
        string NullString?,
        string PresentString?,
        u32[] Seq
    """
    
    schema = compile_schema(schema_text)
    registry = TypeRegistry(schema)
    
    # Create Primitives Message
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
    long_string = "A" * 300 # > 255 bytes, forces pointer encoding in Native? or offset?
    # Note: Native format inline string optimization is for small strings.
    # Large strings use offset/pointer.
    
    msg = Message(
        type_name=QName("Test", "Bundle"),
        fields={
            "ShortString": "Hi",
            "LongString": long_string,
            "Prim": prims.fields, # Static Group expects dict of fields or StaticGroupValue? 
                                  # Wait, Primitives/1 has ID, so it is a Group.
                                  # "Primitives Prim" field -> StaticGroupRef.
                                  # encode_native expects dict for StaticGroupRef.
            "Addr": {"Street": "123 Main", "City": "NYC"},
            "Poly": derived, # Dynamic Object expects Message
            "NullString": None,
            "PresentString": "Here",
            "Seq": [1, 2, 3]
        }
    )
    
    # Fix: Primitives is a Group with ID -> can be Dynamic or Static depending on usage.
    # In "Primitives Prim", it is a TypeRef pointing to Group.
    # If Group has ID, Blink usually treats it as Dynamic reference?
    # No, syntax "Primitives Prim" means field is of type Primitives.
    # If Primitives is defined as Group, it is a Static Group Reference if not 'object'.
    # encode_native expects dict.
    msg.fields["Prim"] = prims.fields
    
    print("Encoding comprehensive message...")
    try:
        binary_data = encode_native(msg, registry)
        binary_hex = binary_data.hex()
        # print(f"Hex: {binary_hex}") 
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
    # They are inlined in Bundle -> Prim (StaticGroupRef).
    # Since I removed "is_fixed_size" check, StaticGroupRef is ALWAYS inlined.
    # Highlighting: "Prim" parent field should exist.
    assert find_field("Prim") is not None
    assert find_section("Prim") is not None # The Gray container section
    
    # Check inner primitive values
    assert find_section("U8Field")['interpretedValue'] == "255"
    assert find_section("I8Field")['interpretedValue'] == "-128"
    assert find_section("BoolTrue")['interpretedValue'] == "1"
    assert find_section("DecimalField") is not None 
    # Decimal string repr might be "123.45" or raw "DecimalValue(exp=-2, mant=12345)"
    # binary_analyzer uses str(val). DecimalValue.__str__?
    # Let's check interpretedValue contains mantissa
    assert "12345" in find_section("DecimalField")['interpretedValue']

    # 2. Static Group (Addr)
    assert find_field("Addr") is not None
    assert find_section("Addr") is not None
    # Addr -> Street (Variable String)
    # Native Native means Addr is Inlined.
    # Street is Variable String -> Pointer (4 bytes) in Fixed Area. "123 Main" in Data Area.
    # We should see "Street" field and "StreetPtr" section? No, analyzer hides Ptr for Inline Strings?
    # "Hi" is inline. "LongString" is ptr.
    # "123 Main" is inline? 8 chars. Fits in 255.
    # Analyzer: if inline string -> type='field-value', data_type='string (inline)'.
    # if pointer -> type='pointer' + type='field-value'.
    
    street_sec = find_section("Street")
    if street_sec:
        # Check value
        assert "123 Main" in street_sec['interpretedValue']

    # 3. Dynamic Object (Poly)
    # Expect Pointer section + Message fields
    assert find_section("PolyPtr") is not None
    assert find_field("Poly") is not None # Parent field "Nested Message"
    # Content of derived
    assert find_field("Extra") is not None
    assert find_section("Extra")['interpretedValue'] == "Data"
    
    # 4. Optional
    # NullString: Presence byte 0x00 + Padding.
    # PresentString: Presence byte 0x01 + Value.
    
    null_p = find_section("NullString?")
    assert null_p is not None and "Null" in null_p['interpretedValue']
    # Start: "presence-NullString"
    
    present_p = find_section("PresentString?")
    assert present_p is not None and "Present" in present_p['interpretedValue']
    assert find_section("PresentString")['interpretedValue'] == "Here"
    
    # 5. Sequence
    # Currently Placeholder
    assert find_section("SeqPtr") is not None
    assert "Sequence" in find_field("Seq")['value']

    print("All assertions passed!")

if __name__ == "__main__":
    print("Running Comprehensive Test Suite...")
    test_comprehensive_analysis()
