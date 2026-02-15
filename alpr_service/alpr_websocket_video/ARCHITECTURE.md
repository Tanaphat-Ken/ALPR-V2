# ALPR WebSocket Video - Architecture & Flow

## Overview
ALPR WebSocket Video service รับ video stream จาก client ผ่าน WebSocket แล้วตรวจจับป้ายทะเบียนโดยตรงโดยใช้ PlateDetector (YOLO ที่เทรนเฉพาะป้ายทะเบียน) จากนั้น crop plate และส่งไปให้ plate_recognizer service อ่านป้ายทะเบียน

## Architecture Flow

```
┌─────────────┐
│   Client    │
│  (WebSocket)│
└──────┬──────┘
       │ Video Frames (JPEG)
       ▼
┌──────────────────────────────────────────┐
│   WebSocket Video Service (Port 8091)    │
│  ┌────────────────────────────────────┐  │
│  │  1. Token Validation               │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  2. VideoPlateTracker              │  │
│  │     (plate_detector_best.pt)       │  │
│  │     - Detect license plate bbox    │  │
│  │     - Track plate with ByteTrack   │  │
│  │     - Crop plate region            │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  3. Send plate crop to             │  │
│  │     plate_recognizer service       │  │
│  └────────────────────────────────────┘  │
└──────────┬───────────────────────────────┘
           │ Cropped Plate Image (~50-200KB)
           ▼
┌──────────────────────────────────────────┐
│   Plate Recognizer Service (Port 5000)   │
│  ┌────────────────────────────────────┐  │
│  │  /api/v1/image/process/            │  │
│  │       from-plate-crop              │  │
│  │  1. PlateSplitter (Skip detector)  │  │
│  │  2. ProvinceClassifier             │  │
│  │  3. CTCOCRReader (OCR)             │  │
│  └────────────────────────────────────┘  │
└──────────┬───────────────────────────────┘
           │ JSON Result
           ▼
┌──────────────────────────────────────────┐
│   WebSocket Video Service                │
│  ┌────────────────────────────────────┐  │
│  │  4. Save plate crop to disk        │  │
│  │  5. Save to database               │  │
│  │  6. Send JSON result to client     │  │
│  │     (NO base64 image)              │  │
│  └────────────────────────────────────┘  │
└──────────┬───────────────────────────────┘
           │ JSON Response
           ▼
┌──────────────────┐
│   Client         │
│  (WebSocket)     │
└──────────────────┘
```

## Detailed Flow

### 1. Client Connection
- Client connects to `ws://host:8091/video/{TOKEN}`
- Server validates token against database
- WebSocket connection established

### 2. Frame Processing Loop
For each frame received from client:

#### 2.1 Frame Validation
- Check frame size (< 50MB limit)
- Verify image format

#### 2.2 Plate Detection (ALPR-Specific YOLO)
```python
VideoPlateTracker.process_frame(frame):
  1. Run PlateDetector (plate_detector_best.pt) - trained for license plates
  2. Update ByteTrack tracker
  3. Track plates across frames
  4. When plate tracking changes (new plate OR plate leaves):
     - Crop plate region from frame
     - Return plate_crop + detected=True flag
  5. Otherwise:
     - Return None, None (skip frame)
```

**Key Point:** Uses ALPR-specific trained model (plate_detector_best.pt) for better accuracy on grayscale/dark images. Returns cropped plate, not full frame.

#### 2.3 Send to Plate Recognizer
When plate is detected:
```python
PlateRecognizerService.process_plate_crop(plate_crop):
  1. Create multipart form data with cropped plate
  2. POST to /api/v1/image/process/from-plate-crop
  3. plate_recognizer skips PlateDetector step
  4. Runs PlateSplitter → ProvinceClassifier + OCR directly
  5. Returns JSON result with license plate info
```

#### 2.4 Save Results
```python
1. Save plate crop to ./images_logs/{uuid}_{timestamp}.jpg
2. Save to database:
   - image_log table
   - license_plate table
   - province_plate table
   - websocket_log table
3. Send JSON response to client (NO base64 image)
```

### 3. Response Format
```json
{
  "plate_id": "1กข1234",
  "province": "กรุงเทพมหานคร",
  "full_plate": "1กข1234 กรุงเทพมหานคร",
  "format_flag": "COMPLETE",
  "filename": "8a9057b4-ef80-4cd8-b933-9696293144fd_2026-02-08_01-52-58.jpg"
}
```

**Important:** Response does NOT include base64 encoded image to keep WebSocket message size small.

## Key Changes from V2 to V3 (Current)

### V1 (Original - Deprecated)
- YOLO detects car
- Crop car bbox from frame
- Send cropped car image to plate_recognizer
- plate_recognizer runs full pipeline: PlateDetector → PlateSplitter → OCR

### V2 (Previous)
- YOLO detects IF car exists (trigger only)
- Send FULL frame (1920x1080) to plate_recognizer
- plate_recognizer runs full pipeline
- **Problem:** Large bandwidth usage, poor accuracy on grayscale/dark images

### V3 (Current - Optimized)
- **PlateDetector** (plate_detector_best.pt) detects license plate directly
- Crop ONLY the plate region
- Send small plate crop (~50-200KB) to plate_recognizer
- plate_recognizer skips PlateDetector step → faster processing
- **Benefits:**
  - Better accuracy on grayscale/dark images (ALPR-specific training data)
  - Lower bandwidth usage (plate crop vs full frame)
  - Faster processing (skip PlateDetector at plate_recognizer)

## File Structure Changes

### Modified Files:

1. **src/models/tracker.py**
   - Added `VideoPlateTracker` class (NEW)
     - Uses `plate_detector_best.pt` instead of yolov8n.pt
     - Detects class 0 (license plate) instead of car classes
     - Returns cropped plate instead of full frame
   - Kept `VideoCarTracker` for backward compatibility (DEPRECATED)

2. **src/services/plate_recognizer.py**
   - Added `process_plate_crop()` method
   - Calls `/image/process/from-plate-crop` endpoint
   - Keeps `process_image()` for backward compatibility

3. **src/utils/consumer.py**
   - Changed tracker type from `VideoCarTracker` → `VideoPlateTracker`
   - Calls `process_plate_crop()` instead of `process_image()`
   - Saves plate crop instead of full frame
   - Updated logging messages

4. **src/handlers/video.py**
   - Changed `VideoCarTracker()` → `VideoPlateTracker()`

5. **src/constants/configs.py**
   - Added `PLATE_DETECTOR_WEIGHT` config
   - Kept `TRACKER_WEIGHT` for backward compatibility

6. **requirements.txt**
   - Updated `ultralytics==8.2.98` → `ultralytics==8.4.11` (for C3k2 support)

7. **.env**
   - PORT changed to 8091 for local testing
   - Added comments for Docker deployment configuration

### New Files:

**plate_recognizer service:**
- `models/image_processor.py::read_from_plate_crop()` - Process pre-cropped plate
- `handlers/image.py::/process/from-plate-crop` - New endpoint for plate crops

## Configuration

### Local Testing
```env
PORT=8091
PLATE_RECOG_BASE_URL=http://localhost:5000/api/v1
DB_HOST=localhost
```

### Docker Deployment
```env
PORT=5000
PLATE_RECOG_BASE_URL=http://plate-recognizer:5000/api/v1
DB_HOST=host.docker.internal
```

## Model Weights

- **PLATE_DETECTOR_WEIGHT**: `./src/models/weights/plate_detector_best.pt` (ALPR-specific YOLO)
- **TRACKER_WEIGHT**: `./src/models/weights/yolov8n.pt` (Deprecated - car detection)

## Performance Comparison

| Metric | V2 (Full Frame) | V3 (Plate Crop) |
|--------|----------------|-----------------|
| Upload size per detection | ~1MB | ~50-200KB |
| Bandwidth savings | - | ~80-95% |
| Processing speed | Baseline | ~1.5x faster |
| Grayscale accuracy | Poor | Good |
| Dark image accuracy | Poor | Good |

## Database Schema

Same as V1/V2 - no changes required to database schema.

## Dependencies

- FastAPI
- Uvicorn (with ws_max_size support)
- OpenCV (cv2)
- Ultralytics YOLO==8.4.11 (upgraded for C3k2 support)
- Supervision (ByteTrack)
- httpx (AsyncClient)
- PostgreSQL + asyncpg

## API Endpoints

### WebSocket
- `ws://host:8091/video/{TOKEN}` - Main video streaming endpoint

### Health Check
- `GET /readyz` - Service health check

## Troubleshooting

### AttributeError: Can't get attribute 'C3k2'
- **Cause:** ultralytics version mismatch - model trained with newer version
- **Fix:** Upgrade ultralytics to 8.4.11+ in requirements.txt
  ```bash
  pip install ultralytics==8.4.11
  ```

### No plate detected on dark/grayscale images
- **Cause:** Using VideoCarTracker (car detection) instead of VideoPlateTracker
- **Fix:** Ensure VideoPlateTracker is being used in handlers/video.py
