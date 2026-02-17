#!/usr/bin/env python3
"""
Quick test script to verify new pipeline works correctly
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.image_processor import ImageProcessor
from PIL import Image
import numpy as np
import cv2

def test_pipeline():
    """Test new pipeline with a sample image"""
    
    print("=" * 60)
    print("Testing New ALPR Pipeline")
    print("=" * 60)
    
    # Initialize processor
    print("\n1. Initializing ImageProcessor...")
    try:
        processor = ImageProcessor()
        print("   ✓ ImageProcessor initialized successfully")
    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}")
        return False
    
    # Check if we have a test image
    test_image_paths = [
        r"D:\CodingD\ALPR\data\TEST_IMG\2024-07-04_14-27-19-856_TRG-004091_Lane1_18052-THA_10_CTX.jpg",
        "test.jpg",
        "sample.jpg"
    ]
    
    test_image = None
    for path in test_image_paths:
        if os.path.exists(path):
            test_image = path
            break
    
    if test_image is None:
        print("\n2. No test image found. Skipping image processing test.")
        print(f"   Tried: {test_image_paths}")
        print("\n   To test with your own image, run:")
        print(f"   python {__file__} /path/to/image.jpg")
        return True  # Still success if models loaded
    
    print(f"\n2. Loading test image: {test_image}")
    try:
        image = Image.open(test_image)
        print(f"   ✓ Image loaded: {image.size} ({image.mode})")
    except Exception as e:
        print(f"   ✗ Failed to load image: {e}")
        return False
    
    print("\n3. Processing image through pipeline...")
    try:
        result = processor.read(image)
        print("   ✓ Processing complete")
        
        print("\n4. Results:")
        print(f"   - Plate ID: {result.get('plate_id', 'N/A')}")
        print(f"   - Province: {result.get('province', 'N/A')}")
        print(f"   - Full Plate: {result.get('full_plate', 'N/A')}")
        print(f"   - Plate BBox: {result.get('plate_bbox', 'N/A')}")
        print(f"   - Flag: {result.get('format_flag', 'N/A')}")
        print(f"   - Message: {result.get('message', 'N/A')}")
        
    except Exception as e:
        print(f"   ✗ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    return True

if __name__ == "__main__":
    # If image path provided as argument
    if len(sys.argv) > 1:
        test_image_path = sys.argv[1]
        if os.path.exists(test_image_path):
            from models.image_processor import ImageProcessor
            from PIL import Image
            
            processor = ImageProcessor()
            image = Image.open(test_image_path)
            result = processor.read(image)
            
            print("\nResult:")
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"Error: Image not found: {test_image_path}")
            sys.exit(1)
    else:
        success = test_pipeline()
        sys.exit(0 if success else 1)
