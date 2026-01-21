"""Simple test script for the conversion API."""

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

print("Testing API...")

try:
    response = requests.post(API_URL, json=test_request)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")
