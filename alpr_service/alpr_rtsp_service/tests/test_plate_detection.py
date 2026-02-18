# test_plate_detection.py
import sys
import os
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
os.chdir(str(root_dir))

import cv2
import httpx
import numpy as np
import supervision as sv
from src.models.tracker import VideoPlateTracker
import json

def test_detection_only(image_path: str):
    """ทดสอบ detect plate จากรูปเดียว (ไม่ใช้ tracking)"""
    
    print("🚗 กำลังโหลด tracker...")
    tracker = VideoPlateTracker()
    
    if not os.path.exists(image_path):
        print(f"❌ ไม่เจอไฟล์ {image_path}")
        return None, None
    
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"❌ ไม่สามารถอ่านไฟล์ {image_path}")
        return None, None
    
    print(f"✅ โหลดรูปสำเร็จ: {frame.shape}")
    
    print("🔍 กำลัง detect plate...")
    
    try:
        results = tracker.model(frame, imgsz=1280, verbose=False)[0]
        detections = sv.Detections.from_ultralytics(results)
        detections = detections[np.isin(detections.class_id, [0])]
        
        print(f"📊 พบ detection: {len(detections)} ป้าย")
        
        if len(detections) > 0:
            print("✅ Detected plate(s)!")
            
            for i, (bbox, conf, class_id) in enumerate(zip(detections.xyxy, detections.confidence, detections.class_id)):
                x1, y1, x2, y2 = bbox
                print(f"\n  Plate {i+1}:")
                print(f"    - Confidence: {conf:.2f}")
                print(f"    - Bbox: [{int(x1)}, {int(y1)}, {int(x2)}, {int(y2)}]")
                print(f"    - Area: {int((x2-x1) * (y2-y1))} pixels")
            
            best_idx = np.argmax(detections.confidence)
            best_bbox = detections.xyxy[best_idx]
            best_conf = detections.confidence[best_idx]
            
            print(f"\n🎯 เลือกป้ายที่ดีที่สุด (confidence: {best_conf:.2f})")
            
            x1, y1, x2, y2 = best_bbox
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            plate_crop = frame[y1:y2, x1:x2]
            
            cv2.imwrite("tests/detected_plate.jpg", plate_crop)
            print(f"💾 บันทึกรูป plate ที่: tests/detected_plate.jpg")
            
            frame_with_bbox = frame.copy()
            cv2.rectangle(frame_with_bbox, (x1, y1), (x2, y2), (0, 255, 0), 3)
            cv2.putText(frame_with_bbox, f"{best_conf:.2f}", (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imwrite("tests/detected_with_bbox.jpg", frame_with_bbox)
            print(f"💾 บันทึกรูปต้นฉบับที่มี bbox: tests/detected_with_bbox.jpg")
            
            return image_path, [x1, y1, x2, y2]  # คืนรูปต้นฉบับ + bbox
            
        else:
            print("❌ No plate detected")
            return None, None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def send_to_plate_recognizer(image_path: str):
    """ส่งรูปเต็มไปให้ Recognizer detect เอง"""
    
    PLATE_RECOG_HOST = os.getenv("PLATE_RECOG_HOST", "http://localhost:5000")
    endpoint = f"{PLATE_RECOG_HOST}/api/v1/image/process"
    
    try:
        with open(image_path, "rb") as f:
            files = {"file": ("image.jpg", f, "image/jpeg")}
            
            print(f"🌐 Sending full image to: {endpoint}")
            response = httpx.post(endpoint, files=files, timeout=30.0)
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ สำเร็จ! ผลลัพธ์:")
                print(f"   License Plate: {result.get('plate_id', 'N/A')}")
                print(f"   Province: {result.get('province', 'N/A')}")
                print(f"   Full Plate: {result.get('full_plate', 'N/A')}")
                print(f"   Format Flag: {result.get('format_flag', 'N/A')}")
                print(f"\n📋 Full Response:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
    except httpx.ConnectError:
        print(f"\n❌ ไม่สามารถเชื่อมต่อไปที่ {endpoint}")
        print("💡 ตรวจสอบว่า plate_recognizer service กำลังรันอยู่หรือไม่")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 RTSP Plate Detection & Recognition Test")
    print("="*60 + "\n")
    
    test_image = r"tests/test_images_500_set2/2024-07-05_16-48-01-051_TRG-008925_Lane4_3กธ7403-THA_10.jpg"
    
    # ทดสอบ detection
    detected_image, detected_bbox = test_detection_only(test_image)
    
    # ส่งรูปต้นฉบับไป recognizer
    if detected_image:
        print("\n" + "-"*60)
        print("📤 กำลังส่งรูปต้นฉบับไปที่ Plate Recognizer Service")
        print("-"*60 + "\n")
        send_to_plate_recognizer(detected_image)
    
    print("\n" + "="*60)
    print("✅ Test Complete")
    print("="*60 + "\n")