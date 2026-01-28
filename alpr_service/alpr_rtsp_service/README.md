# ALPR RTSP Service

ระบบ RTSP สำหรับเชื่อมต่อกับกล้อง IP Camera และอ่านป้ายทะเบียนรถอัตโนมัติแบบ Real-time

## 🚀 Features

- ✅ เชื่อมต่อกับกล้อง IP Camera ผ่าน RTSP
- ✅ รองรับกล้องหลายตัวพร้อมกัน
- ✅ ตรวจจับและติดตามรถด้วย YOLO + ByteTrack
- ✅ อ่านป้ายทะเบียนอัตโนมัติ
- ✅ Web Viewer แสดงผล Live Stream
- ✅ แสดงผลลัพธ์แบบ Real-time
- ✅ Auto-reconnect เมื่อกล้องขาดการเชื่อมต่อ

## 📋 Requirements

- Python 3.10+
- OpenCV
- YOLO (Ultralytics)
- FastAPI
- PostgreSQL

## 🔧 Installation

### 1. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 2. ตั้งค่ากล้อง

แก้ไขไฟล์ `configs/cameras.json`:

```json
[
  {
    "id": "camera_001",
    "name": "Main Entrance",
    "rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream1",
    "location": "Building A - Floor 1",
    "enabled": true,
    "fps": 10,
    "frame_skip": 3
  }
]
```

### 3. ตั้งค่า Environment

แก้ไขไฟล์ `.env`:

```env
HOST=0.0.0.0
PORT=5003
PLATE_RECOGNIZER_URL=http://localhost:5000/api/v1/image/process
```

## 🎮 การใช้งาน

### เริ่มระบบ

```bash
python main.py
```

### เปิด Web Viewer

เปิดเบราว์เซอร์:
```
http://localhost:5003
```

### API Endpoints

#### ดูรายการกล้อง
```bash
GET http://localhost:5003/api/v1/cameras
```

#### เปิดกล้อง
```bash
POST http://localhost:5003/api/v1/cameras/{camera_id}/start
```

#### ปิดกล้อง
```bash
POST http://localhost:5003/api/v1/cameras/{camera_id}/stop
```

#### ดู Stream (WebSocket)
```
ws://localhost:5003/api/v1/stream/{camera_id}
```

## 🐳 Docker

### Build และ Run

```bash
docker-compose up --build
```

### Run Background

```bash
docker-compose up -d
```

### ดู Logs

```bash
docker-compose logs -f alpr_rtsp_service
```

### หยุดระบบ

```bash
docker-compose down
```

## 📁 โครงสร้างโปรเจค

```
alpr_rtsp_service/
├── main.py                 # Entry point
├── requirements.txt
├── Dockerfile
├── compose.yml
├── .env
├── configs/
│   └── cameras.json       # การตั้งค่ากล้อง
├── static/
│   └── viewer.html        # Web Viewer
├── src/
│   ├── constants/         # Config และ Error messages
│   ├── handlers/          # API endpoints
│   ├── models/            # Data models + Tracker
│   ├── services/          # Camera Manager, RTSP Reader, AI
│   └── utils/             # Utilities
├── images_logs/           # บันทึกรูปรถ
└── tests/                 # ไฟล์สำหรับทดสอบ
```

## 🎯 การทดสอบ

### ทดสอบด้วยไฟล์วิดีโอ

1. วางไฟล์ MP4 ไว้ใน `tests/sample-video.mp4`
2. ตั้งค่าใน `cameras.json`:
```json
{
  "id": "camera_test",
  "name": "Test Camera",
  "rtsp_url": "tests/sample-video.mp4",
  "enabled": true
}
```

### ทดสอบกับกล้อง IP จริง

1. หา RTSP URL ของกล้อง (ดูใน Manual หรือ ONVIF)
2. ตั้งค่าใน `cameras.json`:
```json
{
  "id": "camera_001",
  "name": "IP Camera",
  "rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream1",
  "enabled": true
}
```

## 🔍 Troubleshooting

### กล้องเชื่อมต่อไม่ได้

1. ตรวจสอบ RTSP URL ให้ถูกต้อง
2. ทดสอบด้วย VLC Player:
   ```
   vlc rtsp://admin:password@192.168.1.100:554/stream1
   ```
3. ตรวจสอบ Network (ping IP camera)
4. ตรวจสอบ Firewall

### ภาพกระตุก / FPS ต่ำ

1. เพิ่มค่า `frame_skip` ใน `cameras.json`
2. ลด `fps` ลงมา (แนะนำ 10 fps)
3. ลดจำนวนกล้องที่ทำงานพร้อมกัน

### AI ประมวลผลช้า

1. ใช้ GPU (CUDA) ถ้ามี
2. ลดขนาด `imgsz` ใน `tracker.py`
3. เพิ่ม `frame_skip` เพื่อประมวลผลน้อยลง

## 📝 หมายเหตุ

- กล้องที่มี `enabled: true` จะเริ่มทำงานอัตโนมัติ
- รูปรถจะถูกบันทึกใน `images_logs/`
- ระบบจะ reconnect อัตโนมัติเมื่อกล้องขาดการเชื่อมต่อ
- WebSocket จะส่ง frame ทุก frame แต่ประมวลผลเฉพาะบาง frames

## 🤝 การพัฒนาต่อ

- [ ] เพิ่ม database logging
- [ ] เพิ่ม authentication
- [ ] เพิ่ม motion detection
- [ ] เพิ่ม recording feature
- [ ] เพิ่ม notification (Line, Email)
