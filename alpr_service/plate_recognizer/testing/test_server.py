#!/usr/bin/env python3
"""
Quick server test - test API while server is running
"""

import requests
import json
import time
from pathlib import Path

def main():
    print("=" * 60)
    print("Testing plate_recognizer Server")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Testing /readyz endpoint...")
    try:
        response = requests.get("http://localhost:5000/readyz", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Server is running")
            print(f"   Message: {data.get('message')}")
            print(f"   CUDA: {data.get('cuda')}")
        else:
            print(f"   ✗ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ✗ Cannot connect to server")
        print("   Please start server first:")
        print("   cd d:\\CodingD\\ALPR-V2\\alpr_service\\plate_recognizer")
        print("   python main.py")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 2: Process endpoint
    print("\n2. Testing /api/v1/image/process endpoint...")
    test_image = r"D:\CodingD\ALPR\data\TEST_IMG\2024-07-04_14-27-19-856_TRG-004091_Lane1_18052-THA_10_CTX.jpg"
    
    if not Path(test_image).exists():
        print(f"   ⚠ Test image not found: {test_image}")
        print("   Skipping image test")
        return True
    
    try:
        with open(test_image, 'rb') as f:
            files = {'file': ('test.jpg', f, 'image/jpeg')}
            response = requests.post(
                "http://localhost:5000/api/v1/image/process",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            data = response.json()
            print("   ✓ API call successful")
            print(f"\n   Results:")
            print(f"   - Plate ID: {data.get('plate_id', 'N/A')}")
            print(f"   - Province: {data.get('province', 'N/A')}")
            print(f"   - Full Plate: {data.get('full_plate', 'N/A')}")
            print(f"   - Flag: {data.get('format_flag', 'N/A')}")
            print(f"   - Message: {data.get('message', 'N/A')}")
            
            print(f"\n   ✅ All tests PASSED!")
            print(f"\n   Services can now connect:")
            print(f"   • alpr_api_image")
            print(f"   • alpr_websocket_image")
            print(f"   • alpr_websocket_video")
            return True
        else:
            print(f"   ✗ API returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = main()
    print("\n" + "=" * 60)
    sys.exit(0 if success else 1)
