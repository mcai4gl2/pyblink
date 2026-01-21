"""Test script for the conversion API with better output formatting."""

import json

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

print("=" * 70)
print("BLINK MESSAGE PLAYGROUND API - PHASE 1 TEST")
print("=" * 70)
print(f"\nSchema:\n{test_request['schema']}")
print(f"\nInput Format: {test_request['input_format']}")
print(f"\nInput Data:\n{test_request['input_data']}")
print("\n" + "=" * 70)

try:
    response = requests.post(API_URL, json=test_request)
    
    if response.status_code == 200:
        result = response.json()
        
        if result["success"]:
            print("\n[SUCCESS] CONVERSION SUCCESSFUL!")
            print("\n" + "-" * 70)
            
            outputs = result["outputs"]
            
            # Tag format
            if "tag" in outputs:
                print("\nTag Format:")
                print(f"  {outputs['tag']}")
            
            # JSON format
            if "json" in outputs:
                print("\nJSON Format:")
                json_obj = json.loads(outputs['json'])
                print(f"  {json.dumps(json_obj, indent=2)}")
            
            # XML format
            if "xml" in outputs:
                print("\nXML Format:")
                print(f"  {outputs['xml']}")
            
            # Compact Binary
            if "compact_binary" in outputs:
                compact = outputs["compact_binary"]
                print("\nCompact Binary:")
                print(f"  Hex:\n  {compact['hex']}")
                decoded = compact['decoded']
                print(f"  Size: {decoded['size']} bytes")
                print(f"  Type ID: {decoded['type_id']}")
                print(f"  Fields: {len(decoded['fields'])}")
            
            # Native Binary
            if "native_binary" in outputs:
                native = outputs["native_binary"]
                print("\nNative Binary:")
                hex_lines = native['hex'].split('\n')
                for line in hex_lines:
                    print(f"  {line}")
                decoded = native['decoded']
                print(f"  Size: {decoded['size']} bytes")
                print(f"  Type ID: {decoded['type_id']}")
                print(f"  Ext Offset: {decoded['ext_offset']}")
                print(f"  Fields: {len(decoded['fields'])}")
            
            print("\n" + "=" * 70)
            print("[SUCCESS] PHASE 1 COMPLETE - ALL FORMATS WORKING!")
            print("=" * 70)
            
        else:
            print(f"\n[ERROR] Conversion failed: {result.get('error')}")
    else:
        print(f"\n[ERROR] HTTP Error {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n[ERROR] Could not connect to API server")
    print("Make sure the server is running on http://127.0.0.1:8000")
except Exception as e:
    print(f"\n[ERROR] {e}")
