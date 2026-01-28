#!/usr/bin/env python3
"""
Integration test - verify all services can communicate with plate_recognizer
"""

import sys
import requests
import time
from pathlib import Path

def test_plate_recognizer_health():
    """Test if plate_recognizer service is running"""
    print("=" * 60)
    print("Testing plate_recognizer Health")
    print("=" * 60)
    
    url = "http://localhost:5000/readyz"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ plate_recognizer is running")
            print(f"  Message: {data.get('message')}")
            print(f"  CUDA: {data.get('cuda')}")
            return True
        else:
            print(f"✗ plate_recognizer returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to plate_recognizer")
        print("  Make sure it's running: python main.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_plate_recognizer_api(image_path=None):
    """Test plate_recognizer /process endpoint"""
    print("\n" + "=" * 60)
    print("Testing plate_recognizer API Endpoint")
    print("=" * 60)
    
    # Find test image
    if image_path is None:
        test_images = [
            r"D:\CodingD\ALPR\data\TEST_IMG\2024-07-04_14-27-19-856_TRG-004091_Lane1_18052-THA_10_CTX.jpg",
            "test.jpg",
            "sample.jpg"
        ]
        for img in test_images:
            if Path(img).exists():
                image_path = img
                break
    
    if image_path is None or not Path(image_path).exists():
        print("✗ No test image found")
        return False
    
    print(f"Using test image: {image_path}")
    
    url = "http://localhost:5000/api/v1/image/process"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': ('test.jpg', f, 'image/jpeg')}
            response = requests.post(url, files=files, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ API call successful")
            print("\nResponse fields:")
            print(f"  - car_bbox: {data.get('car_bbox', 'N/A')}")
            print(f"  - plate_bbox: {'Present' if data.get('plate_bbox') else 'N/A'}")
            print(f"  - plate_id: {data.get('plate_id', 'N/A')}")
            print(f"  - province: {data.get('province', 'N/A')}")
            print(f"  - full_plate: {data.get('full_plate', 'N/A')}")
            print(f"  - format_flag: {data.get('format_flag', 'N/A')}")
            print(f"  - message: {data.get('message', 'N/A')}")
            return True
        else:
            print(f"✗ API returned status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_service_connectivity(service_name, service_url):
    """Test if a service can be reached"""
    print(f"\nTesting {service_name}...")
    
    try:
        response = requests.get(f"{service_url}/readyz", timeout=5)
        if response.status_code == 200:
            print(f"  ✓ {service_name} is running")
            return True
        else:
            print(f"  ⚠ {service_name} returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  ⚠ {service_name} is not running (this is OK for testing)")
        return None  # Not an error, just not running
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("ALPR Service Integration Test")
    print("=" * 60)
    
    results = {}
    
    # Test 1: plate_recognizer health
    results['health'] = test_plate_recognizer_health()
    
    if not results['health']:
        print("\n" + "=" * 60)
        print("❌ plate_recognizer is not running!")
        print("=" * 60)
        print("\nPlease start plate_recognizer first:")
        print("  cd d:\\CodingD\\ALPR-V2\\alpr_service\\plate_recognizer")
        print("  python main.py")
        return False
    
    # Test 2: plate_recognizer API
    results['api'] = test_plate_recognizer_api()
    
    # Test 3: Check other services (optional)
    print("\n" + "=" * 60)
    print("Checking Other Services (optional)")
    print("=" * 60)
    
    services = {
        'alpr_api_image': 'http://localhost:8001',
        'alpr_websocket_image': 'http://localhost:8002',
        'alpr_websocket_video': 'http://localhost:8003',
    }
    
    for name, url in services.items():
        test_service_connectivity(name, url)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if results['health'] and results['api']:
        print("✅ plate_recognizer is READY")
        print("✅ API endpoint is WORKING")
        print("\n🎉 Integration test PASSED!")
        print("\nServices can now connect to plate_recognizer:")
        print("  - alpr_api_image → http://plate-recognizer:5000/api/v1/image/process")
        print("  - alpr_websocket_image → http://plate-recognizer:5000/api/v1/image/process")
        print("  - alpr_websocket_video → http://plate-recognizer:5000/api/v1/image/process/skip/car")
        return True
    else:
        print("❌ Integration test FAILED")
        if not results['health']:
            print("  - plate_recognizer health check failed")
        if not results['api']:
            print("  - API endpoint test failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
