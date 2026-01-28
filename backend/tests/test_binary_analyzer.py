"""Tests for binary analyzer service."""

import sys
from pathlib import Path

# Add parent directory to path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from app.services.binary_analyzer import analyze_native_binary
from blink.schema.compiler import compile_schema
from blink.runtime.registry import TypeRegistry
from blink.runtime.values import Message, QName
from blink.codec.native import encode_native

def test_full_roundtrip_analysis():
    """Test analysis by encoding a real message and then analyzing it."""
    
    schema_text = """
namespace Demo

Person/4 -> 
    string Name,
    i32 Age
"""
    schema = compile_schema(schema_text)
    registry = TypeRegistry(schema)
    
    # Create valid message
    msg = Message(
        type_name=QName("Demo", "Person"),
        fields={
            "Name": "Alice",
            "Age": 30
        }
    )
    
    # Encode to Native Binary
    binary_data = encode_native(msg, registry)
    binary_hex = binary_data.hex()
    
    print(f"Encoded Hex: {binary_hex}")
    
    # Analyze
    result = analyze_native_binary(schema_text, binary_hex)
    
    print("Analysis Result:")
    print(f"Success: {result['success']}")
    if 'error' in result:
        print(f"Error: {result['error']}")
        return

    print(f"Sections: {len(result['sections'])}")
    print(f"Fields: {len(result['fields'])}")
    
    # Verify core sections exist
    sections = result['sections']
    labels = [s['label'] for s in sections]
    print(f"Labels: {labels}")
    
    assert "Message Size" in labels
    assert "Type ID" in labels
    assert "NamePtr" in labels
    assert "Alice" in [s.get('interpretedValue') for s in sections]
    assert "30" in [s.get('interpretedValue') for s in sections]

if __name__ == "__main__":
    print("=" * 60)
    print("Binary Analyzer Tests")
    print("=" * 60)
    
    test_full_roundtrip_analysis()
    
    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)
