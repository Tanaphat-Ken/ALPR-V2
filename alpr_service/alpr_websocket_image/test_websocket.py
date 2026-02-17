#!/usr/bin/env python3
"""
WebSocket ALPR Testing Script
Tests the alpr_websocket_image service with plate_recognizer integration
"""

import asyncio
import websockets
import sys
from pathlib import Path
import json

# Configuration
WEBSOCKET_URL = "ws://localhost:8090/ws/v1/uploads"
TOKEN = "WEBSOCKET"
TEST_IMAGE = r"C:\Users\Tanaphat\Downloads\test_images\test_images\213\2024-07-05_22-34-02-404_TRG-010646_Lane4_3ขฎ6717-THA_10.jpg"


async def test_websocket_connection():
    """Test WebSocket connection and image processing"""

    print("=" * 70)
    print("🚀 WebSocket ALPR Service Test")
    print("=" * 70)
    print()

    # Check if test image exists
    image_path = Path(TEST_IMAGE)
    if not image_path.exists():
        print(f"❌ Error: Test image not found at {TEST_IMAGE}")
        print("Please provide a valid image path as argument:")
        print(f"  python {sys.argv[0]} <path_to_image.jpg>")
        return

    print(f"📸 Test Image: {image_path.name}")
    print(f"📦 Image Size: {image_path.stat().st_size / 1024:.2f} KB")
    print(f"🔑 Token: {TOKEN}")
    print(f"🌐 WebSocket: {WEBSOCKET_URL}")
    print()
    print("-" * 70)
    print()

    try:
        # Prepare headers with Bearer token
        headers = {
            "Authorization": f"Bearer {TOKEN}"
        }

        print("🔌 Connecting to WebSocket...")

        async with websockets.connect(WEBSOCKET_URL, additional_headers=headers) as websocket:
            print("✅ Connected successfully!")
            print()

            # Wait for initial response (token confirmation)
            try:
                initial_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 Server: {initial_response}")
                print()
            except asyncio.TimeoutError:
                print("⚠️  No initial response from server")
                print()

            # Read and send image
            print("📤 Sending image...")
            with open(image_path, 'rb') as f:
                image_data = f.read()

            await websocket.send(image_data)
            print(f"✅ Sent {len(image_data)} bytes")
            print()

            # Receive responses
            print("⏳ Waiting for processing results...")
            print()

            response_count = 0
            while True:
                try:
                    # Wait for response with timeout
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    response_count += 1

                    print(f"📩 Response #{response_count}:")
                    print(f"   {response}")

                    # Try to parse as JSON for better display
                    if response.startswith("{"):
                        try:
                            data = json.loads(response)
                            print("\n   Parsed JSON:")
                            for key, value in data.items():
                                print(f"      {key}: {value}")
                        except json.JSONDecodeError:
                            pass

                    print()

                    # Check if this is the final response (contains "Model API response")
                    if "Model API response" in response:
                        print("✅ Processing complete!")
                        break

                except asyncio.TimeoutError:
                    print("⏱️  Timeout waiting for response")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 Connection closed by server")
                    break

            print()
            print("=" * 70)
            print(f"✅ Test completed! Received {response_count} responses")
            print("=" * 70)

    except Exception as e:
        # Handle connection errors
        error_type = type(e).__name__

        if "InvalidStatus" in error_type or "StatusCode" in error_type:
            status = getattr(getattr(e, 'response', None), 'status_code', None) or getattr(e, 'status_code', None)
            print(f"❌ Connection failed with status code: {status}")
            if status == 403:
                print("   → Token validation failed. Check if token exists in database.")
            elif status == 401:
                print("   → Unauthorized. Check Authorization header format.")
            print()
        elif isinstance(e, ConnectionRefusedError):
            print("❌ Connection refused!")
            print("   → Make sure alpr_websocket_image service is running on port 8090")
            print("   → Start it with: python main.py")
            print()
        else:
            print(f"❌ Error: {type(e).__name__}: {e}")
            print()


async def test_with_custom_image(image_path: str):
    """Test with custom image path"""
    global TEST_IMAGE
    TEST_IMAGE = image_path
    await test_websocket_connection()


if __name__ == "__main__":
    # Check for custom image path argument
    if len(sys.argv) > 1:
        custom_image = sys.argv[1]
        asyncio.run(test_with_custom_image(custom_image))
    else:
        asyncio.run(test_websocket_connection())
