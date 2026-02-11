#!/usr/bin/env python3
import requests

response = requests.post('http://localhost:8000/api/v1/print', json={
    'printer': 'warehouse_test',
    'content': '^XA^FO50,50^A0N,50,50^FDTest Print^FS^XZ',
    'format': 'zpl',
    'copies': 1
})

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
