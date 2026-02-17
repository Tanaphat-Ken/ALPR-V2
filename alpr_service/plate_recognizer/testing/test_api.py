#!/usr/bin/env python3
"""
Quick API test - start server and test endpoint
"""

import requests
import json
import time
import subprocess
import sys
import os

def test_api():
    """Test API endpoint"""
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:5000/readyz", timeout=2)
        if response.status_code == 200:
            print("✓ Server is already running")
            print(f"  Response: {response.json()}")
        else:
            print("✗ Server returned error")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Server is not running. Start it with:")
        print("  python main.py")
        return False
    except Exception as e:
        print(f"✗ Error checking server: {e}")
        return False
    
    # Test image path
    test_image = r"D:\CodingD\ALPR\data\TEST_IMG\2024-07-04_14-27-19-856_TRG-004091_Lane1_18052-THA_10_CTX.jpg"
    
    if not os.path.exists(test_image):
        print(f"\n✗ Test image not found: {test_image}")
        print("  Please provide a test image path")
        return False
    
    print(f"\n✓ Test image found: {test_image}")
    
    # Test /process endpoint
    print("\nTesting POST /api/v1/image/process...")
    try:
        with open(test_image, 'rb') as f:
            files = {'file': ('test.jpg', f, 'image/jpeg')}
            response = requests.post(
                "http://localhost:5000/api/v1/image/process",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ API call successful")
            print(f"\nResult:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"✗ API returned status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ API call failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("API Test")
    print("=" * 60)
    
    success = test_api()
    
    print("\n" + "=" * 60)
    if success:
        print("API test passed! ✓")
    else:
        print("API test failed! ✗")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
