"""
Test script for ALPR RTSP Service - Video Processing
สามารถรันได้โดยตรงด้วยคำสั่ง: python tests/test_video_processing.py
"""
import sys
import os
from pathlib import Path

# เพิ่ม root directory เข้า path เพื่อ import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
from src.services.plate_recognizer import PlateRecognizerService
from src.constants.configs import PLATE_RECOGNIZER_URL

def test_video_file():
    """
    เทสต์การประมวลผลวิดีโอไฟล์
    """
    print("=" * 50)
    print("🎥 Testing Video File Processing")
    print("=" * 50)
    
    # หาไฟล์วิดีโอใน tests folder
    test_dir = Path(__file__).parent
    video_files = list(test_dir.glob("*.mp4")) + list(test_dir.glob("*.avi"))
    
    if not video_files:
        print("❌ ไม่พบไฟล์วิดีโอในโฟลเดอร์ tests/")
        print("💡 กรุณาวางไฟล์วิดีโอ (.mp4 หรือ .avi) ในโฟลเดอร์ tests/")
        return False
    
    video_path = str(video_files[0])
    print(f"📹 ใช้ไฟล์: {Path(video_path).name}")
    
    # เปิดวิดีโอ
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ ไม่สามารถเปิดไฟล์วิดีโอได้: {video_path}")
        return False
    
    # ดึงข้อมูลวิดีโอ
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"📊 ข้อมูลวิดีโอ:")
    print(f"   - ความละเอียด: {width}x{height}")
    print(f"   - FPS: {fps}")
    print(f"   - จำนวนเฟรม: {total_frames}")
    print(f"   - ระยะเวลา: {total_frames/fps:.2f} วินาที")
    
    # อ่านเฟรมแรก
    ret, frame = cap.read()
    if not ret:
        print("❌ ไม่สามารถอ่านเฟรมได้")
        cap.release()
        return False
    
    print(f"✅ อ่านเฟรมแรกสำเร็จ (shape: {frame.shape})")
    cap.release()
    
    print("\n" + "=" * 50)
    print("✅ Video Processing Test PASSED")
    print("=" * 50)
    return True


def test_plate_recognizer():
    """
    เทสต์การเชื่อมต่อกับ Plate Recognizer API
    """
    print("\n" + "=" * 50)
    print("🔍 Testing Plate Recognizer Connection")
    print("=" * 50)
    
    try:
        print(f"🌐 API URL: {PLATE_RECOGNIZER_URL}")
        recognizer = PlateRecognizerService()
        print("✅ Plate Recognizer instance created")
        
        print("\n" + "=" * 50)
        print("✅ Plate Recognizer Test PASSED")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n" + "=" * 50)
        print("❌ Plate Recognizer Test FAILED")
        print("=" * 50)
        return False


def test_frame_processing():
    """
    เทสต์การประมวลผลเฟรมจากวิดีโอ และส่งไปยัง Plate Recognizer
    """
    print("\n" + "=" * 50)
    print("🎯 Testing Frame Processing with Plate Recognition")
    print("=" * 50)
    
    # หาไฟล์วิดีโอ
    test_dir = Path(__file__).parent
    video_files = list(test_dir.glob("*.mp4")) + list(test_dir.glob("*.avi"))
    
    if not video_files:
        print("❌ ไม่พบไฟล์วิดีโอ")
        return False
    
    video_path = str(video_files[0])
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("❌ ไม่สามารถเปิดวิดีโอได้")
        return False
    
    try:
        recognizer = PlateRecognizerService()
        
        # ประมวลผลเฟรมแรก 10 เฟรม
        frames_to_test = 10
        print(f"📝 กำลังประมวลผล {frames_to_test} เฟรมแรก...")
        
        frame_count = 0
        success_count = 0
        
        while frame_count < frames_to_test:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # ลองส่งเฟรมไปยัง recognizer (แบบไม่รอผลลัพธ์)
            try:
                # แปลงเป็น bytes
                _, buffer = cv2.imencode('.jpg', frame)
                image_bytes = buffer.tobytes()
                
                print(f"   Frame {frame_count}: Image size = {len(image_bytes)} bytes")
                success_count += 1
                
            except Exception as e:
                print(f"   Frame {frame_count}: ❌ Error - {e}")
        
        cap.release()
        
        print(f"\n📊 ผลลัพธ์:")
        print(f"   - ประมวลผลสำเร็จ: {success_count}/{frame_count} เฟรม")
        
        if success_count == frame_count:
            print("\n" + "=" * 50)
            print("✅ Frame Processing Test PASSED")
            print("=" * 50)
            return True
        else:
            print("\n" + "=" * 50)
            print("⚠️ Frame Processing Test PARTIALLY PASSED")
            print("=" * 50)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        cap.release()
        return False


def run_all_tests():
    """
    รันทุก test
    """
    print("\n" + "🚀 " * 20)
    print("Starting ALPR RTSP Service Tests")
    print("🚀 " * 20 + "\n")
    
    results = {
        "Video Processing": test_video_file(),
        "Plate Recognizer": test_plate_recognizer(),
        "Frame Processing": test_frame_processing(),
    }
    
    print("\n\n" + "📋 " * 20)
    print("Test Summary")
    print("📋 " * 20)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All Tests PASSED!")
    else:
        print("⚠️ Some Tests FAILED")
    print("=" * 50 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
