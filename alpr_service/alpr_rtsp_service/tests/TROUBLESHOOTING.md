# Troubleshooting Guide - RTSP Service Tests

## 🐛 Common Errors และวิธีแก้ไข

---

### 1. HEVC Decoder Warnings (ปกติ - ไม่ใช่ Bug)

```
[hevc @ 0000027b08475240] Could not find ref with POC 0
[hevc @ 0000027b084b91c0] Could not find ref with POC 0
[hevc @ 0000027b5bafd9c0] Could not find ref with POC 35
[hevc @ 0000027b08475800] Duplicate POC in a sequence: 1
```

#### 🔍 สาเหตุ:
- วิดีโอ HEVC (H.265) จาก RTSP stream มี **corrupted frames**
- เกิดจากการ encode/stream แบบ real-time ที่ไม่สมบูรณ์
- POC (Picture Order Count) หาย หรือ ซ้ำกัน → decoder ไม่สามารถ reconstruct frame ได้

#### ✅ ผลกระทบ:
- ⚠️ **บาง frame อาจเพี้ยน/blur** → tracker detect ไม่ได้
- ✅ **โปรแกรมไม่ crash** และยังทำงานได้ปกติ
- ✅ **ส่วนใหญ่ยังอ่านป้ายได้**

#### 🔧 วิธีแก้:

**Option 1: Suppress Warnings (แนะนำ)** ✅
```python
# เพิ่มใน test script
import os
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'loglevel;quiet'
```

**Option 2: ตรวจสอบ Corrupted Frames**
```python
ret, frame = cap.read()
if frame is None or frame.size == 0:
    corrupted_frames += 1
    continue
```

**Option 3: ลดการข้าม Frame**
```python
# ลดจาก skip_frames=2 เป็น skip_frames=1
# เพิ่มโอกาสได้ frame ที่ดี
await test.process_video(skip_frames=1)
```

**Option 4: Re-encode Video (แก้ที่ต้นทาง)**
```bash
# แปลงเป็น H.264 ที่ stable กว่า
ffmpeg -i input.mp4 \
       -c:v libx264 -crf 23 -preset medium \
       -c:a copy output.mp4
```

---

### 2. Connection Error - plate_recognizer

```
❌ plate_recognizer service: Connection failed
❌ ไม่สามารถเชื่อมต่อไปที่ http://localhost:5000
```

#### 🔍 สาเหตุ:
- plate_recognizer service ยังไม่เปิด

#### ✅ วิธีแก้:
```bash
# Terminal 1: เปิด plate_recognizer
cd alpr_service/plate_recognizer
python main.py

# รอจนเห็น: "Application startup complete"

# Terminal 2: รัน test
cd alpr_service/alpr_rtsp_service
python tests/test_rtsp_integration.py
```

---

### 3. ไม่พบไฟล์วิดีโอ

```
❌ ไม่พบไฟล์: tests/TC2ML_L...mp4
```

#### ✅ วิธีแก้:
1. ตรวจสอบว่าไฟล์อยู่ใน `tests/` folder
2. ตรวจสอบชื่อไฟล์ว่าถูกต้อง
3. ใช้ absolute path แทน:
```python
video_path = r"C:\full\path\to\video.mp4"
```

---

### 4. No Plate Detected

```
📊 Progress: 300/300 frames, 12.5 fps, 0 plates detected
```

#### 🔍 สาเหตุ:
- วิดีโอไม่มีป้ายทะเบียน หรือ มีแต่เล็กเกินไป
- ข้าม frame มากเกินไป พลาดช่วงที่มีป้าย

#### ✅ วิธีแก้:
1. ลดการข้าม frame:
```python
skip_frames=0  # ประมวลผลทุก frame
```

2. เพิ่ม max_frames เพื่อประมวลผลนานขึ้น:
```python
max_frames=1000  # หรือ None = ทั้งหมด
```

3. ตรวจสอบ video ว่ามีป้ายจริง:
```bash
# เปิดดูด้วย VLC หรือ media player
```

---

### 5. Database Connection Error

```
Failed to save to video_logs: connection refused
```

#### 🔍 สาเหตุ:
- Database ยังไม่เปิด แต่ตั้งค่า `DATABASE_ENABLED=true`

#### ✅ วิธีแก้:

**Option 1: ปิด Database (แนะนำสำหรับ testing)**
```bash
# แก้ .env
DATABASE_ENABLED=false
```

**Option 2: เปิด Database**
```bash
# เปิด PostgreSQL
# แก้ .env ให้ถูกต้อง
DB_HOST=localhost
DB_PORT=5432
DB_NAME=alpr_service
DB_USER=alpr
DB_PASSWORD=your_password
```

---

### 6. Recognition Failed

```
⚠️  Recognition failed or incomplete
   - Message: Plate detected but OCR/Province failed
```

#### 🔍 สาเหตุ:
- ภาพป้ายเบลอ, มืด, หรือ มุมกล้องไม่ดี
- Model ไม่สามารถอ่านได้

#### ✅ ผลกระทบ:
- ไม่ใช่ error ของระบบ
- เป็นข้อจำกัดของ AI model

#### 📊 ยอมรับได้:
- Success rate 60-80% ถือว่าปกติ
- ถ้า < 50% → ตรวจสอบคุณภาพวิดีโอ

---

## 📊 Success Metrics

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| **Detection Rate** | > 5 plates/min | 2-5 plates/min | < 2 plates/min |
| **Success Rate** | > 80% | 60-80% | < 60% |
| **Processing Speed** | > 20 fps | 10-20 fps | < 10 fps |
| **Corrupted Frames** | < 5% | 5-10% | > 10% |

---

## 💡 Performance Tips

### เพิ่มความเร็ว:
```python
skip_frames=2    # ข้าม 2 frame (fast)
max_frames=300   # จำกัด 300 frame
```

### เพิ่มความแม่นยำ:
```python
skip_frames=0    # ไม่ข้าม frame (slow แต่แม่น)
max_frames=None  # ประมวลผลทั้งหมด
```

---

## 🔍 Debug Mode

เปิด debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

ดู response จาก API:
```python
print(f"Response: {json.dumps(result, indent=2)}")
```

---

## 📞 ติดต่อ Support

ถ้ายังแก้ไม่ได้:
1. Capture screenshot ของ error
2. แนบ log file: `images_logs/detections.log`
3. แนบ JSON results: `tests/rtsp_integration_results.json`
4. ระบุ environment:
   - OS version
   - Python version
   - OpenCV version

---

## ✅ Quick Fix Checklist

- [ ] plate_recognizer service เปิดอยู่
- [ ] ไฟล์วิดีโออยู่ใน tests/ folder
- [ ] DATABASE_ENABLED=false (สำหรับ testing)
- [ ] skip_frames ไม่สูงเกินไป (แนะนำ 1-2)
- [ ] HEVC warnings ถูก suppress แล้ว
- [ ] มี output_plates/ folder สำหรับบันทึกรูป

---

**หมายเหตุ:** HEVC decoder warnings ไม่ใช่ bug ของระบบ แต่เป็นข้อจำกัดของไฟล์วิดีโอ RTSP ที่ record มาจาก network stream ซึ่งเป็นเรื่องปกติในการใช้งานจริง
