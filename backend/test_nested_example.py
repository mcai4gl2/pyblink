"""Test the new nested classes and subclasses example via API."""

import json

import requests

# API endpoint
API_URL = "http://127.0.0.1:8000/api/convert"

# Schema with nested classes and subclasses
SCHEMA = """namespace Demo

# Base class for address information
Address/1 -> string Street, string City, u32 ZipCode

# Employee class with nested Address
Employee/2 -> string Name, u32 Age, Address HomeAddress

# Manager subclass extends Employee with additional fields
Manager/3 : Employee -> string Department, u32 TeamSize

# Company class with nested Manager
Company/4 -> string CompanyName, Manager CEO"""

# Test data - JSON input
JSON_INPUT = '{"$type":"Demo:Company","CompanyName":"TechCorp","CEO":{"$type":"Demo:Manager","Name":"Alice","Age":45,"HomeAddress":{"$type":"Demo:Address","Street":"123 Main St","City":"San Francisco","ZipCode":94102},"Department":"Engineering","TeamSize":50}}'

print("=" * 80)
print("Testing Nested Classes and Subclasses Example")
print("=" * 80)
print(f"\nSchema:\n{SCHEMA}")
print(f"\nInput Format: JSON")
print(f"\nInput Data:\n{json.dumps(json.loads(JSON_INPUT), indent=2)}")
print("\n" + "=" * 80)

test_request = {
    "schema": SCHEMA,
    "input_format": "json",
    "input_data": JSON_INPUT
}

try:
    response = requests.post(API_URL, json=test_request)
    
    if response.status_code == 200:
        result = response.json()
        
        if result["success"]:
            print("\n[SUCCESS] CONVERSION SUCCESSFUL!")
            print("\n" + "-" * 80)
            
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
                print(f"  Hex: {compact['hex']}")
                decoded = compact['decoded']
                print(f"  Size: {decoded['size']} bytes")
                print(f"  Type ID: {decoded['type_id']}")
            
            # Native Binary
            if "native_binary" in outputs:
                native = outputs["native_binary"]
                print("\nNative Binary:")
                print(f"  Hex: {native['hex']}")
                decoded = native['decoded']
                print(f"  Size: {decoded['size']} bytes")
                print(f"  Type ID: {decoded['type_id']}")
            
            print("\n" + "=" * 80)
            print("[SUCCESS] Test completed successfully!")
            print("=" * 80)
            
            # Print formats for copying to App.tsx
            print("\n" + "=" * 80)
            print("FORMATS FOR App.tsx:")
            print("=" * 80)
            print(f"\njson: `{outputs['json']}`")
            print(f"\ntag: `{outputs['tag']}`")
            print(f"\nxml: `{outputs['xml']}`")
            print(f"\ncompact: `{compact['hex']}`")
            print(f"\nnative: `{native['hex']}`")
            
        else:
            print(f"\n[ERROR] Conversion failed: {result.get('error')}")
    else:
        print(f"\n[ERROR] HTTP Error {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n[ERROR] Could not connect to API server")
    print("Make sure the server is running on http://127.0.0.1:8000")
except Exception as e:
    print(f"\n[ERROR] Error: {e}")
