"""
Test script for ALPR API Image Service

Usage:
    python test_api_image.py [image_path] [--token TOKEN]

Example:
    python test_api_image.py test_images/car.jpg --token API
"""

import requests
import argparse
import os
import sys
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8089"
UPLOAD_ENDPOINT = "/api/v1/images/upload-image"
DEFAULT_TOKEN = "API"  # token key from database

def test_upload_image(image_path: str, token: str):
    """
    Test image upload to ALPR API Image Service

    Args:
        image_path: Path to the test image
        token: Bearer token for authentication
    """

    # Validate image file exists
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file not found: {image_path}")
        return False

    # Determine content type
    ext = Path(image_path).suffix.lower()
    content_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif'
    }

    content_type = content_type_map.get(ext)
    if not content_type:
        print(f"❌ Error: Unsupported image format: {ext}")
        return False

    print("=" * 70)
    print("🚀 ALPR API Image Service Test")
    print("=" * 70)
    print(f"\n📸 Test Image: {image_path}")
    print(f"🔑 Token: {token}")
    print(f"🌐 API Endpoint: {API_BASE_URL}{UPLOAD_ENDPOINT}")
    print(f"📊 Content-Type: {content_type}")

    # Prepare request
    headers = {
        "Authorization": f"Bearer {token}"
    }

    file_size = os.path.getsize(image_path)
    print(f"📦 File Size: {file_size / 1024:.2f} KB")
    print("\n" + "-" * 70 + "\n")

    try:
        # Open and send image
        with open(image_path, 'rb') as f:
            files = {
                'file': (os.path.basename(image_path), f, content_type)
            }

            print("📤 Uploading image to API...")
            response = requests.post(
                f"{API_BASE_URL}{UPLOAD_ENDPOINT}",
                headers=headers,
                files=files,
                timeout=60
            )

        # Check response
        print(f"📡 Response Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success! Image processed successfully")
            print("\n📋 Response Data:")
            print(f"   Message: {result.get('message')}")
            print(f"   User ID: {result.get('user_id')}")
            print(f"   Saved Filename: {result.get('filename')}")

            model_response = result.get('model_response', {})
            if model_response:
                print("\n🚗 Plate Recognition Results:")
                print(f"   Plate ID: {model_response.get('plate_id')}")
                print(f"   Province: {model_response.get('province')}")
                print(f"   Full Plate: {model_response.get('full_plate')}")
                print(f"   Format Flag: {model_response.get('format_flag')}")
                print(f"   Message: {model_response.get('message')}")

            return True

        elif response.status_code == 401:
            print(f"\n❌ Authentication Failed: {response.json().get('detail')}")
            print("\n💡 Tip: Check if token exists and is not expired")
            return False

        elif response.status_code == 403:
            print(f"\n❌ Forbidden: {response.json().get('detail')}")
            print("\n💡 Tip: Check subscription status and quota")
            return False

        else:
            print(f"\n❌ Error: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Detail: {error_detail}")
            except:
                print(f"   Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Cannot connect to API service")
        print("💡 Tip: Make sure the API service is running on port 8089")
        return False

    except requests.exceptions.Timeout:
        print("\n❌ Timeout Error: Request timed out after 60 seconds")
        return False

    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")
        return False

    finally:
        print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Test ALPR API Image Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_api_image.py test_images/car.jpg
  python test_api_image.py test_images/car.jpg --token API
  python test_api_image.py ../test_frames/frame_001285.jpg --token API
        """
    )

    parser.add_argument(
        'image_path',
        help='Path to the test image'
    )

    parser.add_argument(
        '--token',
        default=DEFAULT_TOKEN,
        help=f'Bearer token for authentication (default: {DEFAULT_TOKEN})'
    )

    args = parser.parse_args()

    # Run test
    success = test_upload_image(args.image_path, args.token)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
