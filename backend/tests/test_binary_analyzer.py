"""Tests for binary analyzer service."""

import sys
from pathlib import Path

# Add parent directory to path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from app.services.binary_analyzer import analyze_native_binary


def test_basic_native_binary_analysis():
    """Test basic Native Binary analysis."""
    
    # Simple schema
    schema = """
namespace Demo

Company/1 -> 
    string CompanyName,
    i32 EmployeeCount
"""
    
    # Example Native Binary hex (this is a simplified example)
    # In reality, you would get this from encoding a message
    # For now, we'll test with a minimal valid header
    binary_hex = "10000000" + "0100000000000000" + "00000000"  # size + type_id + ext_offset
    
    result = analyze_native_binary(schema, binary_hex)
    
    print("Analysis Result:")
    print(f"Success: {result['success']}")
    print(f"Sections: {len(result.get('sections', []))}")
    print(f"Fields: {len(result.get('fields', []))}")
    
    if result['success']:
        print("\nSections:")
        for section in result['sections']:
            print(f"  - {section['label']}: offset {section['startOffset']}-{section['endOffset']}")
    else:
        print(f"Error: {result.get('error')}")


def test_with_real_message():
    """Test with a real encoded message."""
    
    schema = """
namespace Demo

Person/4 -> 
    string Name,
    i32 Age
"""
    
    # We would need to encode a real message to get valid binary data
    # For now, this is a placeholder test
    print("\nTest with real message:")
    print("(Would need to encode a real message first)")


if __name__ == "__main__":
    print("=" * 60)
    print("Binary Analyzer Tests")
    print("=" * 60)
    
    test_basic_native_binary_analysis()
    test_with_real_message()
    
    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)
