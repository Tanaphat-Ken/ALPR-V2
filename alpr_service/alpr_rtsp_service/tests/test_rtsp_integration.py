"""
RTSP Service Integration Test
ทดสอบการทำงานของ RTSP Service โดยจำลองการประมวลผลวิดีโอจริง

Test ว่า:
1. เชื่อมต่อกับ plate_recognizer service ได้หรือไม่
2. VideoPlateTracker detect plate ได้หรือไม่
3. ส่งไปอ่านป้ายได้หรือไม่
4. บันทึกข้อมูลได้หรือไม่

Note:
- HEVC decoder warnings ([hevc @ ...] Could not find ref with POC) เป็นเรื่องปกติ
  สาเหตุ: วิดีโอ RTSP มี corrupted frames จากการ record/stream
  ผลกระทบ: บาง frame อาจเพี้ยน แต่ไม่ crash และยังอ่านป้ายได้
  การแก้: ตั้ง OPENCV_FFMPEG_CAPTURE_OPTIONS='loglevel;quiet' และตรวจสอบ corrupted frames
"""
import sys
import os
from pathlib import Path


# ✅ ใหม่ (ถูก)
# ตั้ง env ก่อน!
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'loglevel;quiet'
os.environ['OPENCV_LOG_LEVEL'] = 'SILENT'

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
os.chdir(str(root_dir))

import cv2  # import หลัง set env
import asyncio
import numpy as np
from io import BytesIO
from datetime import datetime
from fastapi import UploadFile

from src.models.tracker import VideoPlateTracker
from src.services.plate_recognizer import PlateRecognizerService
from src.services.database import DatabaseService
from src.constants import configs
from src.utils.logging import logger


class RTSPIntegrationTest:
    """จำลองการทำงานของ RTSP Service"""
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.tracker = VideoPlateTracker()
        self.plate_recognizer = PlateRecognizerService()
        self.database_service = DatabaseService(enabled=configs.DATABASE_ENABLED)
        
        # Statistics
        self.total_frames = 0
        self.processed_frames = 0
        self.plates_detected = 0
        self.plates_recognized = 0
        self.corrupted_frames = 0  # เพิ่ม: นับ corrupted frames
        self.results = []
    
    async def test_service_connection(self):
        """ทดสอบการเชื่อมต่อกับ services"""
        print("🔌 ทดสอบการเชื่อมต่อ services...\n")
        
        # Test plate_recognizer connection
        try:
            # สร้าง dummy image สำหรับทดสอบ
            dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
            _, buffer = cv2.imencode('.jpg', dummy_img)
            
            image_stream = BytesIO(buffer.tobytes())
            image_stream.seek(0)
            image_file = UploadFile(
                file=image_stream,
                filename="test.jpg",
                size=len(buffer.tobytes())
            )
            
            # ลองเชื่อมต่อ (จะ error ถ้าไม่มี plate แต่อย่างน้อยรู้ว่าเชื่อมต่อได้)
            try:
                response = await self.plate_recognizer.process_plate_crop(image_file)
                print(f"✅ plate_recognizer service: OK ({configs.PLATE_RECOG_BASE_URL})")
            except Exception as e:
                if "404" in str(e) or "422" in str(e):
                    print(f"✅ plate_recognizer service: Connected (response: {e})")
                else:
                    print(f"❌ plate_recognizer service: Error - {e}")
                    return False
        except Exception as e:
            print(f"❌ plate_recognizer service: Connection failed - {e}")
            return False
        
        # Test database (ถ้า enabled)
        if self.database_service.enabled:
            print(f"✅ database service: ENABLED")
        else:
            print(f"ℹ️  database service: DISABLED (file logging only)")
        
        print()
        return True
    
    async def process_video(self, max_frames: int = None, skip_frames: int = 2):
        """
        ประมวลผลวิดีโอ (จำลอง RTSP stream)
        
        Args:
            max_frames: จำนวน frame สูงสุดที่จะประมวลผล
            skip_frames: ข้ามเฟรมเพื่อเพิ่มความเร็ว
        """
        print(f"📹 เปิดวิดีโอ: {Path(self.video_path).name}\n")
        
        if not os.path.exists(self.video_path):
            print(f"❌ ไม่พบไฟล์: {self.video_path}")
            return False
        
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"❌ ไม่สามารถเปิดวิดีโอได้")
            return False
        
        # ข้อมูลวิดีโอ
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"📊 ข้อมูลวิดีโอ:")
        print(f"   - ความละเอียด: {width}x{height}")
        print(f"   - FPS: {fps:.2f}")
        print(f"   - จำนวนเฟรม: {self.total_frames}")
        print(f"   - ระยะเวลา: {self.total_frames/fps:.2f} วินาที")
        if max_frames:
            print(f"   - จำกัดประมวลผล: {max_frames} เฟรม")
        if skip_frames > 0:
            print(f"   - ข้ามเฟรม: ทุกๆ {skip_frames} เฟรม")
        print()
        
        start_time = asyncio.get_event_loop().time()
        frame_count = 0
        
        print("🚀 เริ่มประมวลผล...\n")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # ตรวจสอบ corrupted frame (จาก HEVC decoder errors)
                if frame is None or frame.size == 0:
                    self.corrupted_frames += 1
                    continue
                
                # ข้าม frame (เพื่อเพิ่มความเร็ว)
                if skip_frames > 0 and frame_count % (skip_frames + 1) != 0:
                    continue
                
                # จำกัดจำนวน frame
                if max_frames and self.processed_frames >= max_frames:
                    break
                
                self.processed_frames += 1
                
                # จำลอง RTSP Reader: process_frame with tracker
                plate_crop, plate_detected = self.tracker.process_frame(frame)
                
                if plate_crop is not None and plate_detected:
                    self.plates_detected += 1
                    timestamp = frame_count / fps
                    
                    print(f"✅ Frame {frame_count} ({timestamp:.2f}s): Detected plate!")
                    
                    # จำลอง rtsp_handler: process_detection
                    result = await self._process_detection(
                        camera_id="test_camera",
                        plate_crop=plate_crop,
                        frame_count=frame_count,
                        timestamp=timestamp
                    )
                    
                    if result:
                        self.results.append(result)
                    
                    print()  # blank line
                
                # Progress report
                if self.processed_frames % 30 == 0:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    processing_fps = self.processed_frames / elapsed if elapsed > 0 else 0
                    print(f"📊 Progress: {self.processed_frames}/{self.total_frames} frames, "
                          f"{processing_fps:.1f} fps, {self.plates_detected} plates detected\n")
        
        except KeyboardInterrupt:
            print("\n⚠️  หยุดการทดสอบโดยผู้ใช้")
        
        finally:
            cap.release()
            elapsed_time = asyncio.get_event_loop().time() - start_time
            
            # สรุปผล
            self._print_summary(elapsed_time)
            
        return True
    
    async def _process_detection(
        self, 
        camera_id: str, 
        plate_crop: np.ndarray, 
        frame_count: int,
        timestamp: float
    ) -> dict:
        """
        จำลอง process_detection() จาก rtsp_handler.py
        """
        try:
            # บันทึกรูป plate crop
            output_dir = Path("tests/output_plates")
            output_dir.mkdir(exist_ok=True)
            
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            plate_filename = f"plate_{camera_id}_{timestamp_str}.jpg"
            plate_path = output_dir / plate_filename
            
            cv2.imwrite(str(plate_path), plate_crop)
            print(f"   💾 Saved: {plate_filename}")
            
            # เตรียม UploadFile สำหรับส่งไป plate_recognizer
            success, encoded = cv2.imencode('.jpg', plate_crop)
            if not success:
                print("   ❌ Failed to encode plate crop")
                return None
            
            image_stream = BytesIO(encoded.tobytes())
            image_stream.seek(0)
            image_file = UploadFile(
                file=image_stream,
                filename=plate_filename,
                size=len(encoded.tobytes())
            )
            
            # ส่งไป plate_recognizer (เรียก /from-plate-crop endpoint)
            print(f"   📤 Sending to plate_recognizer...")
            try:
                response = await self.plate_recognizer.process_plate_crop(image_file)
                result = response.json()
                
                plate_id = result.get('plate_id', 'N/A')
                province = result.get('province', 'N/A')
                full_plate = result.get('full_plate', 'N/A')
                format_flag = result.get('format_flag', 'unknown')
                
                print(f"   📥 Response: {format_flag}")
                
                if format_flag == 'complete':
                    self.plates_recognized += 1
                    print(f"   🎯 Result: {full_plate}")
                    print(f"      - Plate: {plate_id}")
                    print(f"      - Province: {province}")
                else:
                    print(f"   ⚠️  Recognition failed or incomplete")
                    print(f"      - Message: {result.get('message', 'Unknown error')}")
                
                # บันทึกลง database
                await self.database_service.save_detection(
                    camera_id=camera_id,
                    image_filename=plate_filename,
                    plate_data=result,
                    bbox=result.get('plate_bbox')
                )
                
                return {
                    'frame': frame_count,
                    'timestamp': timestamp,
                    'plate_id': plate_id,
                    'province': province,
                    'full_plate': full_plate,
                    'format_flag': format_flag,
                    'saved_path': str(plate_path)
                }
                
            except ValueError as e:
                print(f"   ❌ plate_recognizer error: {e}")
                return None
            except Exception as e:
                print(f"   ❌ Unexpected error: {e}")
                return None
        
        except Exception as e:
            logger.error(f"Detection processing error: {e}")
            return None
    
    def _print_summary(self, elapsed_time: float):
        """แสดงสรุปผลการทดสอบ"""
        print("\n" + "="*70)
        print("📊 สรุปผลการทดสอบ RTSP Service Integration")
        print("="*70)
        print(f"⏱️  เวลาที่ใช้: {elapsed_time:.2f} วินาที")
        print(f"📹 Frame ที่ประมวลผล: {self.processed_frames}/{self.total_frames}")
        
        # แสดง corrupted frames (ถ้ามี)
        if self.corrupted_frames > 0:
            print(f"⚠️  Corrupted frames: {self.corrupted_frames} (HEVC decoder issues)")
        
        print(f"🎯 Plate ที่ detect ได้: {self.plates_detected}")
        print(f"✅ Plate ที่อ่านได้: {self.plates_recognized}")
        
        if self.plates_detected > 0:
            success_rate = (self.plates_recognized / self.plates_detected) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if elapsed_time > 0:
            print(f"⚡ ความเร็วประมวลผล: {self.processed_frames/elapsed_time:.2f} fps")
        
        if self.results:
            print(f"\n📋 รายการป้ายที่อ่านได้ ({len(self.results)} รายการ):")
            print("-"*70)
            for i, r in enumerate(self.results, 1):
                print(f"{i:3d}. Frame {r['frame']:6d} ({r['timestamp']:7.2f}s): {r['full_plate']}")
            
            # บันทึก JSON
            output_json = Path("tests/rtsp_integration_results.json")
            import json
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump({
                    'test_time': datetime.now().isoformat(),
                    'video_file': str(self.video_path),
                    'summary': {
                        'total_frames': self.total_frames,
                        'processed_frames': self.processed_frames,
                        'corrupted_frames': self.corrupted_frames,
                        'plates_detected': self.plates_detected,
                        'plates_recognized': self.plates_recognized,
                        'success_rate': (self.plates_recognized / self.plates_detected * 100) if self.plates_detected > 0 else 0,
                        'processing_time': elapsed_time,
                        'fps': self.processed_frames/elapsed_time if elapsed_time > 0 else 0
                    },
                    'results': self.results
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 บันทึกผลลัพธ์ที่: {output_json}")
        else:
            print(f"\n⚠️  ไม่พบป้ายทะเบียนที่อ่านได้")
        
        # Database log location
        if not self.database_service.enabled:
            print(f"📝 Log file: {self.database_service.log_file}")
        else:
            print(f"💾 บันทึกลง database: video_logs table")
        
        print("="*70 + "\n")
    
    async def cleanup(self):
        """ปิด connections"""
        await self.plate_recognizer.close()


async def main():
    """Main test function"""
    print("\n" + "="*70)
    print("🧪 RTSP Service Integration Test")
    print("="*70 + "\n")
    
    # กำหนด path วิดีโอ
    video_path = r"tests/TC2ML_L 192.168.40.226_001_2025-08-12-07-00-00_2025-08-12-07-21-03.mp4"
    
    # สร้าง test instance
    test = RTSPIntegrationTest(video_path)
    
    try:
        # 1. ทดสอบการเชื่อมต่อ services
        connected = await test.test_service_connection()
        if not connected:
            print("❌ ไม่สามารถเชื่อมต่อกับ services ได้")
            print("💡 กรุณาเปิด plate_recognizer service ก่อน:")
            print("   cd alpr_service/plate_recognizer")
            print("   python main.py")
            return
        
        # 2. ประมวลผลวิดีโอ
        await test.process_video(
            max_frames=1000,    # ประมวลผลทั้งหมด (หรือกำหนดเลข เช่น 300)
            skip_frames=1       # ข้าม 1 เฟรม (ลดจาก 2 เพื่อลด decoder error)
        )
        
    finally:
        # 3. Cleanup
        await test.cleanup()
    
    print("✅ Test Complete\n")


if __name__ == "__main__":
    # รัน async main
    asyncio.run(main())
