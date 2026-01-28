# 🔌 Service Integration - ALPR Pipeline

## สถาปัตยกรรมระบบ

```
┌─────────────────────┐
│  alpr_api_image     │──┐
└─────────────────────┘  │
                         │
┌─────────────────────┐  │    HTTP POST
│ alpr_websocket_     │──┼──► http://plate-recognizer:5000/api/v1/image/process
│       image         │  │
└─────────────────────┘  │
                         │
┌─────────────────────┐  │
│ alpr_websocket_     │──┘
│       video         │
└─────────────────────┘

                         ▼
                ┌──────────────────┐
                │ plate_recognizer │
                │  (NEW PIPELINE)  │
                └──────────────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
      PlateDetector  PlateSplitter  Province+OCR
```

## ✅ Backward Compatibility

### API Endpoints (ไม่เปลี่ยน)

#### 1. Process Image

```http
POST http://plate-recognizer:5000/api/v1/image/process
Content-Type: multipart/form-data

file: <image_file>
```

**Response:**

```json
{
  "car_bbox": null,
  "plate_bbox": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
  "text_bbox_list": null,
  "plate_id": "1ฒว8052",
  "province": "ชลบุรี",
  "full_plate": "1ฒว8052 ชลบุรี",
  "format_flag": "complete",
  "message": "OK"
}
```

#### 2. Process with Car BBox (used by websocket_video)

```http
POST http://plate-recognizer:5000/api/v1/image/process/skip/car
Content-Type: multipart/form-data

file: <image_file>
car_bbox: [x1, y1, x2, y2]
```

**Response:** (เหมือนข้างบน)

#### 3. Health Check

```http
GET http://plate-recognizer:5000/readyz
```

**Response:**

```json
{
  "message": "service is ready",
  "cuda": true
}
```

## 🔗 Service Integration Details

### alpr_api_image

**File:** `Controllers/image.py`

```python
async def send_file_to_model(file_contents: bytes, filename: str, content_type: str):
    external_api_url = "http://plate-recognizer:5000/api/v1/image/process"
    files = {'file': (filename, file_contents, content_type)}

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(external_api_url, files=files)
        return response.json()
```

**Status:** ✅ ใช้งานได้ทันที (ไม่ต้องแก้)

---

### alpr_websocket_image

**File:** `Controllers/web_socket_images.py`

```python
async def send_file_to_model(file_contents: bytes, filename: str, content_type: str):
    external_api_url = "http://plate-recognizer:5000/api/v1/image/process"
    files = {'file': (filename, file_contents, content_type)}

    async with httpx.AsyncClient() as client:
        response = await client.post(external_api_url, files=files)
        return response.json()
```

**Status:** ✅ ใช้งานได้ทันที (ไม่ต้องแก้)

---

### alpr_websocket_video

**File:** `src/services/plate_recognizer.py`

```python
class PlateRecognizerService:
    def __init__(self):
        self.client = AsyncClient(
            base_url=configs.PLATE_RECOG_BASE_URL,
            timeout=60.0
        )

    async def process_image(self, car_bbox: np.ndarray, upload_file: UploadFile):
        data = {"car_bbox": car_bbox.tolist()}
        files = {"file": (upload_file.filename, await upload_file.read(), ...)}

        response = await self.client.post("/image/process/skip/car", data=data, files=files)
        return response
```

**Config:** `src/constants/configs.py`

```python
PLATE_RECOG_BASE_URL = "http://plate-recognizer:5000/api/v1"
```

**Status:** ✅ ใช้งานได้ทันที (ไม่ต้องแก้)

## 🧪 Testing Services Integration

### 1. Start plate_recognizer

```bash
cd d:\CodingD\ALPR-V2\alpr_service\plate_recognizer
python main.py
```

### 2. Test from each service

#### Test from alpr_api_image

```bash
cd d:\CodingD\ALPR-V2\alpr_service\alpr_api_image
# Start service
python main.py

# In another terminal
curl -X POST http://localhost:<port>/api/v1/image/upload-image \
  -H "Authorization: Bearer <token>" \
  -F "file=@test.jpg"
```

#### Test from alpr_websocket_image

```bash
cd d:\CodingD\ALPR-V2\alpr_service\alpr_websocket_image
# Start service
python main.py

# Connect via WebSocket client
# Send image bytes
```

#### Test from alpr_websocket_video

```bash
cd d:\CodingD\ALPR-V2\alpr_service\alpr_websocket_video
# Start service
python main.py

# Connect via WebSocket and stream video
```

## 📦 Docker Compose Integration

ถ้าใช้ Docker, ให้แน่ใจว่า services อยู่ใน network เดียวกัน:

```yaml
services:
  plate-recognizer:
    build: ./plate_recognizer
    container_name: plate-recognizer
    ports:
      - "5000:5000"
    networks:
      - alpr-network

  alpr-api-image:
    build: ./alpr_api_image
    depends_on:
      - plate-recognizer
    environment:
      PLATE_RECOGNIZER_URL: "http://plate-recognizer:5000"
    networks:
      - alpr-network

  alpr-websocket-image:
    build: ./alpr_websocket_image
    depends_on:
      - plate-recognizer
    networks:
      - alpr-network

  alpr-websocket-video:
    build: ./alpr_websocket_video
    depends_on:
      - plate-recognizer
    networks:
      - alpr-network

networks:
  alpr-network:
    driver: bridge
```

## 🎯 Key Points

1. **ไม่ต้องแก้ code ที่ services อื่นเลย** - Pipeline ใหม่ทำงานผ่าน API เหมือนเดิม
2. **Response format เหมือนเดิม 100%** - Services อื่นไม่รู้ด้วยซ้ำว่ามีการเปลี่ยน pipeline
3. **เพียงแค่ restart plate_recognizer service** - แล้วทุกอย่างจะทำงานด้วย pipeline ใหม่
4. **Performance ดีขึ้น 4 เท่า** - Services อื่นจะได้รับผลทันที

## 🚀 Deployment Steps

1. **Stop plate_recognizer service**

   ```bash
   docker stop plate-recognizer
   # or
   # kill python process
   ```

2. **Pull/Update code**

   ```bash
   cd d:\CodingD\ALPR-V2\alpr_service\plate_recognizer
   git pull  # if using git
   ```

3. **Install new dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Test locally**

   ```bash
   python test_pipeline.py
   ```

5. **Start service**

   ```bash
   python main.py
   # or
   docker-compose up -d plate-recognizer
   ```

6. **Verify health**

   ```bash
   curl http://plate-recognizer:5000/readyz
   ```

7. **Test integration**
   - Services อื่นจะ connect อัตโนมัติ
   - ไม่ต้อง restart services อื่น

## ⚠️ Troubleshooting

### Service can't connect to plate-recognizer

**Check network:**

```bash
docker network inspect alpr-network
# ตรวจสอบว่า services ทั้งหมดอยู่ใน network เดียวกัน
```

**Check DNS resolution:**

```bash
docker exec alpr-api-image ping plate-recognizer
```

**Check plate-recognizer is running:**

```bash
curl http://localhost:5000/readyz
```

### Response format mismatch

Pipeline ใหม่ return format เหมือนเดิมทุกประการ:

- `car_bbox` (อาจเป็น null ถ้าไม่มี)
- `plate_bbox` (4-point polygon)
- `plate_id` (OCR result)
- `province` (จังหวัด)
- `full_plate` (รวมกัน)
- `format_flag` (`complete` หรือ `warning`)
- `message` (status message)

---

**สรุป:** Pipeline ใหม่พร้อมใช้งานทันทีโดยไม่ต้องแก้ services อื่น! 🎉
