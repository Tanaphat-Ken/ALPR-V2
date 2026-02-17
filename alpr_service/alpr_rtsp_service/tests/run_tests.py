"""
Main Test Runner
รันเทสต์ทั้งหมดในโฟลเดอร์ tests
รันด้วย: python -m tests.run_tests (จาก root folder)
หรือ: python run_tests.py (จาก tests folder)
"""
import sys
import os
from pathlib import Path

# เพิ่ม root directory เข้า path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
os.chdir(str(root_dir))  # เปลี่ยน working directory

# Import test modules
try:
    import test_camera_config
    import test_video_processing
    
    # Import functions
    test_load_camera_config = test_camera_config.test_load_camera_config
    test_validate_camera_fields = test_camera_config.test_validate_camera_fields
    test_video_file = test_video_processing.test_video_file
    test_plate_recognizer = test_video_processing.test_plate_recognizer
    test_frame_processing = test_video_processing.test_frame_processing
    
except ImportError as e:
    print(f"❌ Error importing test modules: {e}")
    print("💡 กรุณาตรวจสอบว่าไฟล์ test อยู่ใน tests folder")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def run_all_tests():
    """
    รันเทสต์ทั้งหมด
    """
    print("\n" + "🧪 " * 25)
    print(" " * 10 + "ALPR RTSP Service - Test Suite")
    print("🧪 " * 25 + "\n")
    
    test_results = {}
    
    # Camera Configuration Tests
    print("\n" + "📹 " * 20)
    print("Camera Configuration Tests")
    print("📹 " * 20)
    
    try:
        test_results['Load Camera Config'] = test_load_camera_config()
        test_results['Field Validation'] = test_validate_camera_fields()
    except Exception as e:
        print(f"❌ Camera tests error: {e}")
        test_results['Camera Tests'] = False
    
    # Video Processing Tests
    print("\n" + "🎥 " * 20)
    print("Video Processing Tests")
    print("🎥 " * 20)
    
    try:
        test_results['Video File Processing'] = test_video_file()
        test_results['Plate Recognizer'] = test_plate_recognizer()
        test_results['Frame Processing'] = test_frame_processing()
    except Exception as e:
        print(f"❌ Video processing tests error: {e}")
        test_results['Video Tests'] = False
    
    # Summary
    print("\n\n" + "📊 " * 25)
    print(" " * 15 + "Test Summary")
    print("📊 " * 25 + "\n")
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<50} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    total = passed + failed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 70)
    print(f"Total Tests: {total} | Passed: {passed} | Failed: {failed} | Pass Rate: {pass_rate:.1f}%")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 " * 15)
        print(" " * 15 + "All Tests PASSED!")
        print("🎉 " * 15 + "\n")
        return True
    else:
        print("\n⚠️ " * 15)
        print(" " * 10 + f"{failed} Test(s) FAILED - Please Review")
        print("⚠️ " * 15 + "\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
