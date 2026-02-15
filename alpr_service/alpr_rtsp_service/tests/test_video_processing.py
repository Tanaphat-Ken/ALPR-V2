# test_video_rtsp_detection.py
import sys
import os
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
os.chdir(str(root_dir))

import cv2
import httpx
import numpy as np
from src.models.tracker import VideoPlateTracker
import json
import time
from datetime import datetime

def send_to_plate_recognizer(frame: np.ndarray):
    """
    ส่ง frame ไปที่ plate_recognizer และคืนผลลัพธ์
    
    Args:
        frame: numpy array (BGR) ของ frame ต้นฉบับ
        
    Returns:
        dict: ผลลัพธ์จาก API หรือ None ถ้าไม่สำเร็จ
    """
    PLATE_RECOG_HOST = os.getenv("PLATE_RECOG_HOST", "http://localhost:5000")
    endpoint = f"{PLATE_RECOG_HOST}/api/v1/image/process/from-plate-crop"
    
    try:
        # แปลง frame เป็น jpg bytes
        _, buffer = cv2.imencode('.jpg', frame)
        image_bytes = buffer.tobytes()
        
        files = {"file": ("frame.jpg", image_bytes, "image/jpeg")}
        response = httpx.post(endpoint, files=files, timeout=30.0)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   📥 Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
        else:
            print(f"   ⚠️  API Error: {response.status_code}")
            return None
            
    except httpx.ConnectError:
        print(f"   ❌ ไม่สามารถเชื่อมต่อไปที่ {endpoint}")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_video_with_tracking(video_path: str, max_frames: int = None, skip_frames: int = 0):
    """
    ทดสอบการประมวลผลวิดีโอด้วย tracking + plate recognition
    
    Args:
        video_path: path ไฟล์วิดีโอ
        max_frames: จำนวน frame สูงสุดที่จะประมวลผล (None = ทั้งหมด)
        skip_frames: ข้าม frame ที่ไม่ต้องการประมวลผล (เพิ่มความเร็ว)
    """
    
    print("🚗 กำลังโหลด tracker...")
    tracker = VideoPlateTracker()
    
    # เปิดวิดีโอ
    if not os.path.exists(video_path):
        print(f"❌ ไม่เจอไฟล์ {video_path}")
        return
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ ไม่สามารถเปิดวิดีโอได้")
        return
    
    # ข้อมูลวิดีโอ
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"\n📹 ข้อมูลวิดีโอ:")
    print(f"   - ไฟล์: {Path(video_path).name}")
    print(f"   - ความละเอียด: {width}x{height}")
    print(f"   - FPS: {fps:.2f}")
    print(f"   - จำนวนเฟรม: {total_frames}")
    print(f"   - ระยะเวลา: {total_frames/fps:.2f} วินาที")
    
    if max_frames:
        print(f"   - จำกัดประมวลผล: {max_frames} เฟรม")
    if skip_frames:
        print(f"   - ข้ามเฟรมทุกๆ: {skip_frames} เฟรม")
    
    print(f"\n🔍 เริ่มประมวลผล...\n")
    
    # สถิติ
    frame_count = 0
    processed_count = 0
    plate_detected_count = 0
    plate_recognized_count = 0
    results = []
    
    start_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # ข้าม frame ถ้าต้องการ
            if skip_frames > 0 and frame_count % (skip_frames + 1) != 0:
                continue
            
            # จำกัดจำนวน frame
            if max_frames and processed_count >= max_frames:
                break
            
            processed_count += 1
            
            # ประมวลผล frame ด้วย tracker
            plate_crop, detected = tracker.process_frame(frame)
            
            if detected and plate_crop is not None:
                plate_detected_count += 1
                timestamp = frame_count / fps
                
                print(f"✅ Frame {frame_count} ({timestamp:.2f}s): Detected plate!")
                
                # บันทึกรูป plate
                output_dir = Path("tests/output_plates")
                output_dir.mkdir(exist_ok=True)
                plate_filename = f"plate_frame_{frame_count:06d}.jpg"
                plate_path = output_dir / plate_filename
                cv2.imwrite(str(plate_path), plate_crop)
                print(f"   💾 Saved: {plate_filename}")
                
                # ส่งไป recognizer
                print(f"   📤 Sending to recognizer...")
                result = send_to_plate_recognizer(plate_crop)  # ส่ง plate_crop แทน frame
                
                if result and result.get('format_flag') == 'complete':
                    plate_recognized_count += 1
                    plate_id = result.get('plate_id', 'N/A')
                    province = result.get('province', 'N/A')
                    full_plate = result.get('full_plate', 'N/A')
                    
                    print(f"   🎯 Result: {full_plate}")
                    print(f"      - Plate: {plate_id}")
                    print(f"      - Province: {province}")
                    
                    results.append({
                        'frame': frame_count,
                        'timestamp': timestamp,
                        'plate_id': plate_id,
                        'province': province,
                        'full_plate': full_plate,
                        'saved_path': str(plate_path)
                    })
                else:
                    print(f"   ⚠️  Recognition failed or incomplete")
                
                print()  # blank line
            
            # แสดง progress ทุกๆ 30 frame
            if processed_count % 30 == 0:
                elapsed = time.time() - start_time
                fps_processing = processed_count / elapsed
                print(f"📊 Progress: {processed_count}/{total_frames if not max_frames else max_frames} frames, "
                      f"{fps_processing:.1f} fps, {plate_detected_count} plates detected")
    
    except KeyboardInterrupt:
        print("\n⚠️  หยุดการประมวลผลโดยผู้ใช้")
    
    finally:
        cap.release()
        elapsed_time = time.time() - start_time
        
        # สรุปผล
        print("\n" + "="*60)
        print("📊 สรุปผลการทดสอบ")
        print("="*60)
        print(f"⏱️  เวลาที่ใช้: {elapsed_time:.2f} วินาที")
        print(f"📹 Frame ที่ประมวลผล: {processed_count}")
        print(f"🎯 Plate ที่ detect ได้: {plate_detected_count}")
        print(f"✅ Plate ที่อ่านได้: {plate_recognized_count}")
        print(f"⚡ ความเร็วประมวลผล: {processed_count/elapsed_time:.2f} fps")
        
        if results:
            print(f"\n📋 รายการป้ายที่อ่านได้ทั้งหมด:")
            print("-"*60)
            for i, r in enumerate(results, 1):
                print(f"{i}. Frame {r['frame']} ({r['timestamp']:.2f}s): {r['full_plate']}")
            
            # บันทึกผลลัพธ์เป็น JSON
            output_json = Path("tests/recognition_results.json")
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump({
                    'test_time': datetime.now().isoformat(),
                    'video_file': str(video_path),
                    'summary': {
                        'total_frames': total_frames,
                        'processed_frames': processed_count,
                        'plates_detected': plate_detected_count,
                        'plates_recognized': plate_recognized_count,
                        'processing_time': elapsed_time,
                        'fps': processed_count/elapsed_time
                    },
                    'results': results
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 บันทึกผลลัพธ์ที่: {output_json}")
        
        print("="*60 + "\n")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 RTSP Video Processing + Plate Recognition Test")
    print("="*60 + "\n")
    
    # ระบุ path วิดีโอ
    video_path = r"tests/TC2ML_L 192.168.40.226_001_2025-08-12-07-00-00_2025-08-12-07-21-03.mp4"
    
    # ทดสอบ - ประมวลผล 300 เฟรมแรก (ประมาณ 10 วินาที ถ้า 30fps)
    # ข้ามเฟรมทุกๆ 2 เฟรม (ประมวลผลเฟรมที่ 1, 4, 7, 10, ... เพื่อเพิ่มความเร็ว)
    test_video_with_tracking(
        video_path=video_path,
        max_frames=None,      #
        skip_frames=2        # ข้าม 2 เฟรม (ประมวลผลทุกเฟรมที่ 3)
    )
    
    print("✅ Test Complete\n")