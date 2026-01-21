"""Test script for the conversion API."""

import requests

# API endpoint
API_URL = "http://127.0.0.1:8000/api/convert"

# Test data
test_request = {
    "schema": """namespace Demo
Person/1 -> string Name, u32 Age""",
    "input_format": "json",
    "input_data": '{"$type":"Demo:Person","Name":"Alice","Age":30}'
}

print("Testing Blink Message Playground API...")
print("=" * 60)
print(f"\nSchema:\n{test_request['schema']}")
print(f"\nInput Format: {test_request['input_format']}")
print(f"\nInput Data:\n{test_request['input_data']}")
print("\n" + "=" * 60)

# Make request
try:
    response = requests.post(API_URL, json=test_request)
    response.raise_for_status()
    
    result = response.json()
    
    if result["success"]:
        print("\n✅ Conversion successful!")
        print("\nOutputs:")
        print("-" * 60)
        
        outputs = result["outputs"]
        
        # Tag format
        if "tag" in outputs:
            print("\n📝 Tag Format:")
            print(outputs['tag'])
        
        # JSON format
        if "json" in outputs:
            print("\n📄 JSON Format:")
            print(outputs['json'])
        
        # XML format
        if "xml" in outputs:
            print("\n🔖 XML Format:")
            print(outputs['xml'])
        
        # Compact Binary
        if "compact_binary" in outputs:
            compact = outputs["compact_binary"]
            print("\n💾 Compact Binary:")
            print(f"Hex:\n{compact['hex']}")
            print(f"\nDecoded:")
            print(f"  Size: {compact['decoded']['size']}")
            print(f"  Type ID: {compact['decoded']['type_id']}")
            print(f"  Fields: {len(compact['decoded']['fields'])}")
        
        # Native Binary
        if "native_binary" in outputs:
            native = outputs["native_binary"]
            print("\n🔧 Native Binary:")
            print(f"Hex:\n{native['hex']}")
            print(f"\nDecoded:")
            print(f"  Size: {native['decoded']['size']}")
            print(f"  Type ID: {native['decoded']['type_id']}")
            print(f"  Ext Offset: {native['decoded']['ext_offset']}")
            print(f"  Fields: {len(native['decoded']['fields'])}")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        
    else:
        print(f"\n❌ Conversion failed: {result.get('error')}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ Error: Could not connect to API server")
    print("Make sure the server is running on http://127.0.0.1:8000")
except Exception as e:
    print(f"\n❌ Error: {e}")
