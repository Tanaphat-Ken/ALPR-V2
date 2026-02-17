"""
Test script for Camera Configuration
เทสต์การโหลดและตรวจสอบ configuration ของกล้อง
รันด้วย: python tests/test_camera_config.py
"""
import sys
import json
from pathlib import Path

# เพิ่ม root directory เข้า path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.camera import Camera


def test_load_camera_config():
    """
    เทสต์การโหลด cameras.json
    """
    print("=" * 50)
    print("📹 Testing Camera Configuration")
    print("=" * 50)
    
    config_path = Path(__file__).parent.parent / "configs" / "cameras.json"
    
    if not config_path.exists():
        print(f"❌ ไม่พบไฟล์ config: {config_path}")
        return False
    
    print(f"📂 Loading config from: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # รองรับทั้ง format เก่า {"cameras": [...]} และ format ใหม่ [...]
        if isinstance(config_data, dict):
            cameras = config_data.get('cameras', [])
        elif isinstance(config_data, list):
            cameras = config_data
        else:
            print("❌ รูปแบบ config ไม่ถูกต้อง")
            return False
            
        print(f"\n✅ พบกล้องทั้งหมด: {len(cameras)} ตัว\n")
        
        if not cameras:
            print("⚠️ ไม่มีกล้องในไฟล์ config")
            return False
        
        # แสดงรายละเอียดแต่ละกล้อง
        for idx, cam_data in enumerate(cameras, 1):
            print(f"📹 กล้องที่ {idx}:")
            print(f"   - Camera ID: {cam_data.get('id')}")
            print(f"   - Name: {cam_data.get('name')}")
            print(f"   - RTSP URL: {cam_data.get('rtsp_url')}")
            print(f"   - Location: {cam_data.get('location', 'N/A')}")
            print(f"   - Enabled: {cam_data.get('enabled', False)}")
            
            # ลองสร้าง Camera object
            try:
                camera = Camera(
                    id=cam_data.get('id'),
                    name=cam_data.get('name'),
                    rtsp_url=cam_data.get('rtsp_url'),
                    location=cam_data.get('location', 'Unknown'),
                    enabled=cam_data.get('enabled', False),
                    fps=cam_data.get('fps', 10),
                    frame_skip=cam_data.get('frame_skip', 3)
                )
                print(f"   ✅ Camera object created successfully")
            except Exception as e:
                print(f"   ❌ Error creating Camera object: {e}")
                return False
            
            print()
        
        print("=" * 50)
        print("✅ Camera Configuration Test PASSED")
        print("=" * 50)
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_validate_camera_fields():
    """
    เทสต์การตรวจสอบ fields ที่จำเป็นในแต่ละกล้อง
    """
    print("\n" + "=" * 50)
    print("🔍 Testing Camera Field Validation")
    print("=" * 50)
    
    config_path = Path(__file__).parent.parent / "configs" / "cameras.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # รองรับทั้ง format เก่า {"cameras": [...]} และ format ใหม่ [...]
        if isinstance(config_data, dict):
            cameras = config_data.get('cameras', [])
        elif isinstance(config_data, list):
            cameras = config_data
        else:
            print("❌ รูปแบบ config ไม่ถูกต้อง")
            return False
            
        required_fields = ['id', 'name', 'rtsp_url']
        
        all_valid = True
        
        for idx, cam_data in enumerate(cameras, 1):
            print(f"\n📹 กล้องที่ {idx}:")
            
            # ตรวจสอบ required fields
            for field in required_fields:
                if field in cam_data and cam_data[field]:
                    print(f"   ✅ {field}: OK")
                else:
                    print(f"   ❌ {field}: Missing or Empty")
                    all_valid = False
            
            # ตรวจสอบ optional fields
            optional_fields = ['location', 'enabled', 'fps', 'frame_skip']
            for field in optional_fields:
                if field in cam_data:
                    print(f"   ℹ️  {field}: {cam_data[field]}")
        
        print("\n" + "=" * 50)
        if all_valid:
            print("✅ Field Validation Test PASSED")
        else:
            print("❌ Field Validation Test FAILED")
        print("=" * 50)
        
        return all_valid
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "🚀 " * 20)
    print("Starting Camera Configuration Tests")
    print("🚀 " * 20 + "\n")
    
    result1 = test_load_camera_config()
    result2 = test_validate_camera_fields()
    
    print("\n\n" + "📋 " * 20)
    print("Test Summary")
    print("📋 " * 20)
    print(f"Load Camera Config: {'✅ PASSED' if result1 else '❌ FAILED'}")
    print(f"Field Validation: {'✅ PASSED' if result2 else '❌ FAILED'}")
    
    if result1 and result2:
        print("\n🎉 All Tests PASSED!\n")
        sys.exit(0)
    else:
        print("\n⚠️ Some Tests FAILED\n")
        sys.exit(1)
