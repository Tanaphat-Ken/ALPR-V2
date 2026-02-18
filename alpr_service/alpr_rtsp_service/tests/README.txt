===========================================
ALPR RTSP Service - Test Suite
===========================================

📁 ไฟล์ทดสอบทั้งหมด:

1. test_rtsp_integration.py ⭐ (แนะนำ)
   ✅ ทดสอบการทำงานแบบ end-to-end
   - จำลองการทำงานของ RTSP Service
   - ทดสอบการเชื่อมต่อกับ plate_recognizer
   - ทดสอบการ detect และอ่านป้ายทะเบียน
   - ทดสอบการบันทึกข้อมูล

2. test_video_processing.py
   ✅ ทดสอบการประมวลผลวิดีโอ + plate recognition
   - ใช้ VideoPlateTracker
   - ส่งไป plate_recognizer API
   - บันทึกผลลัพธ์

3. test_plate_detection.py
   ✅ ทดสอบการ detect plate จากรูปภาพ

4. test_camera_config.py
   ✅ ทดสอบการโหลด camera config

===========================================
🚀 วิธีรันทดสอบ
===========================================

STEP 1: เปิด plate_recognizer service ก่อน
----------------------------------------
Terminal 1:
  cd C:\Users\Txxrz\Documents\GitHub\ALPR-V2\alpr_service\plate_recognizer
  python main.py

  รอจนเห็น: "Application startup complete"


STEP 2: รันไฟล์ทดสอบ
----------------------------------------
Terminal 2:
  cd C:\Users\Txxrz\Documents\GitHub\ALPR-V2\alpr_service\alpr_rtsp_service

  # ทดสอบแบบ Integration (แนะนำ)
  python tests/test_rtsp_integration.py

  # หรือ ทดสอบแบบ Simple
  python tests/test_video_processing.py


===========================================
📊 ผลลัพธ์ที่คาดหวัง
===========================================

✅ เชื่อมต่อกับ plate_recognizer ได้
✅ Detect plate จากวิดีโอได้
✅ ส่งไปอ่านป้ายทะเบียนได้
✅ แสดงผลลัพธ์: plate_id, province, full_plate
✅ บันทึก log/database ได้

Output:
- รูปป้ายที่ detect: tests/output_plates/
- Log file: images_logs/detections.log
- JSON results: tests/rtsp_integration_results.json


===========================================
⚙️ Configuration
===========================================

แก้ไขไฟล์ .env ใน alpr_rtsp_service:

# Database (ปิดอยู่ตอนนี้)
DATABASE_ENABLED=false

# Plate Recognizer Service
PLATE_RECOG_BASE_URL=http://localhost:5000/api/v1


===========================================
🐛 Troubleshooting
===========================================

❌ Error: ไม่สามารถเชื่อมต่อไปที่ http://localhost:5000
→ เปิด plate_recognizer service ก่อน

❌ Error: ไม่พบไฟล์วิดีโอ
→ ตรวจสอบว่า video file อยู่ที่ tests/ folder

❌ Error: No plate detected
→ ลดค่า skip_frames หรือเพิ่ม max_frames

❌ Error: Database connection failed
→ ตั้งค่า DATABASE_ENABLED=false ใน .env

⚠️  Warning: [hevc @ ...] Could not find ref with POC
→ ปกติ! ไม่ใช่ bug แต่เป็น HEVC decoder warning
→ วิดีโอ RTSP มี corrupted frames (เป็นเรื่องปกติ)
→ โปรแกรมยังทำงานได้และอ่านป้ายได้
→ ดู TROUBLESHOOTING.md สำหรับรายละเอียด


===========================================
📹 ไฟล์วิดีโอทดสอบ
===========================================

วางไฟล์วิดีโอไว้ที่ tests/ folder
ตัวอย่าง: TC2ML_L 192.168.40.226_001_2025-08-12-07-00-00_2025-08-12-07-21-03.mp4
