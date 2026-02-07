#!/usr/bin/env python3
"""
WebSocket Video ALPR Testing Script
Tests the alpr_websocket_video service with plate_recognizer integration
"""

import asyncio
import websockets
import sys
from pathlib import Path
import json
import numpy as np
import cv2

# Configuration
# WEBSOCKET_URL = "ws://localhost:5000/video/VIDEO_WEBSOCKET"  # For Docker deployment
WEBSOCKET_URL = "ws://localhost:8091/video/VIDEO_WEBSOCKET"  # For local testing
TOKEN = "VIDEO_WEBSOCKET"
# Use multiple test images to simulate video frames
TEST_IMAGES = [
    r"C:\Users\Tanaphat\Desktop\Coding\ALPR-V2\alpr_service\plate_recognizer\testing\output_video\Picked\Largest_TC2ML_L_192.168.40.226_001_2025-08-12-07-00-00_2025-08-12-07-21-03\perfect\frame_005130.jpg",
    r"C:\Users\Tanaphat\Desktop\Coding\ALPR-V2\alpr_service\plate_recognizer\testing\output_video\Picked\Largest_TC2ML_L_192.168.40.226_001_2025-08-12-07-00-00_2025-08-12-07-21-03\perfect\frame_005130.jpg",
    r"C:\Users\Tanaphat\Desktop\Coding\ALPR-V2\alpr_service\plate_recognizer\testing\output_video\Picked\Largest_TC2ML_L_192.168.40.226_001_2025-08-12-07-00-00_2025-08-12-07-21-03\perfect\frame_005130.jpg",
    r"C:\Users\Tanaphat\Desktop\Coding\ALPR-V2\alpr_service\plate_recognizer\testing\output_video\Picked\Largest_TC2ML_L_192.168.40.226_001_2025-08-12-07-00-00_2025-08-12-07-21-03\perfect\frame_005130.jpg",
]


async def test_websocket_video():
    """Test WebSocket video connection and frame processing"""

    print("=" * 70)
    print("🚀 WebSocket Video ALPR Service Test")
    print("=" * 70)
    print()

    # Check if test images exist
    test_images = []
    for img_path in TEST_IMAGES:
        path = Path(img_path)
        if path.exists():
            test_images.append(path)
        else:
            print(f"⚠️  Image not found: {path.name}")

    if not test_images:
        print("❌ No test images found!")
        print("Please provide valid image paths")
        return

    print(f"📸 Test Images: {len(test_images)} frames")
    for idx, img in enumerate(test_images, 1):
        print(f"   {idx}. {img.name} ({img.stat().st_size / 1024:.2f} KB)")
    print(f"🔑 Token: {TOKEN}")
    print(f"🌐 WebSocket: {WEBSOCKET_URL}")
    print()
    print("-" * 70)
    print()

    try:
        print("🔌 Connecting to WebSocket...")

        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print("✅ Connected successfully!")
            print()

            # Send frames
            response_count = 0

            # Create a task to receive responses
            async def receive_responses():
                nonlocal response_count
                try:
                    while True:
                        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        response_count += 1

                        print(f"📩 Response #{response_count}:")

                        # Try to parse as JSON
                        try:
                            data = json.loads(response)
                            print(f"   Plate ID: {data.get('plate_id', 'N/A')}")
                            print(f"   Province: {data.get('province', 'N/A')}")
                            print(f"   Full Plate: {data.get('full_plate', 'N/A')}")
                            print(f"   Flag: {data.get('format_flag', 'N/A')}")
                            if 'image' in data:
                                print(f"   Image: [base64 data included]")
                        except json.JSONDecodeError:
                            print(f"   {response}")

                        print()

                except asyncio.TimeoutError:
                    print("⏱️  No more responses (timeout)")
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 Connection closed by server")

            # Start receiving responses in background
            receiver = asyncio.create_task(receive_responses())

            # Send all frames
            for idx, image_path in enumerate(test_images, 1):
                print(f"📤 Sending frame {idx}/{len(test_images)}: {image_path.name}...")

                with open(image_path, 'rb') as f:
                    image_data = f.read()

                await websocket.send(image_data)
                print(f"✅ Sent {len(image_data)} bytes")
                print()

                # Wait a bit between frames (simulate video rate)
                await asyncio.sleep(0.5)

            # IMPORTANT: Send a blank/black frame to trigger tracker finalization
            # This forces the tracker to output the last tracked car
            print("📤 Sending blank frame to trigger tracker finalization...")
            blank_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
            _, blank_encoded = cv2.imencode('.jpg', blank_frame)
            await websocket.send(blank_encoded.tobytes())
            print("✅ Sent blank frame")
            print()

            # Give time for remaining responses
            print("⏳ Waiting for remaining responses...")
            await asyncio.sleep(5)

            # Cancel receiver
            receiver.cancel()
            try:
                await receiver
            except asyncio.CancelledError:
                pass

            print()
            print("=" * 70)
            print(f"✅ Test completed! Sent {len(test_images)} + 1 blank frame, received {response_count} responses")
            print("=" * 70)

    except Exception as e:
        error_type = type(e).__name__

        if "InvalidStatus" in error_type or "StatusCode" in error_type:
            status = getattr(getattr(e, 'response', None), 'status_code', None) or getattr(e, 'status_code', None)
            print(f"❌ Connection failed with status code: {status}")
            if status == 4001:
                print("   → Token validation failed. Check if token exists in database.")
            elif status == 1011:
                 print("   → Internal server error")
            print()
        elif isinstance(e, ConnectionRefusedError):
            print("❌ Connection refused!")
            print("   → Make sure alpr_websocket_video service is running on port 8091")
            print("   → Start it with: python main.py")
            print()
        else:
            print(f"❌ Error: {type(e).__name__}: {e}")
            print()


if __name__ == "__main__":
    asyncio.run(test_websocket_video())
