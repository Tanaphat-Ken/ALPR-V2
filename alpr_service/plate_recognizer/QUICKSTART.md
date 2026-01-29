# Quick Start Guide - New ALPR Pipeline

## ติดตั้ง Dependencies

```bash
cd d:\CodingD\ALPR-V2\alpr_service\plate_recognizer
pip install -r requirements.txt
```

### Dependencies ที่สำคัญ:
- `ultralytics` - YOLO models (PlateDetector, PlateSplitter)
- `timm` - Province classifier
- `torch` + `torchvision` - Deep learning framework
- `opencv-python` - Image processing
- `fastapi[standard]` - API server (includes uvicorn)
- `pillow` - Image loading

## ทดสอบ Pipeline

### 1. ทดสอบว่า models โหลดได้
```bash
python test_pipeline.py
```

คาดหวังผลลัพธ์:
```
Testing New ALPR Pipeline
============================================================

1. Initializing ImageProcessor...
   ✓ PlateDetector loaded from models/weights/plate_detector_best.pt on cuda
   ✓ PlateSplitter loaded from models/weights/plate_splitter_best.pt on cuda
   ✓ ProvinceClassifier loaded from ... (mobilenetv3_small_100, 78 classes) on cuda
   ✓ CTCOCRReader loaded from models/weights/upper_ctc_special_best.pt on cuda
   ✓ ImageProcessor initialized successfully

2. Loading test image: ...
   ✓ Image loaded: (1920, 1200) (RGB)

3. Processing image through pipeline...
   ✓ Processing complete

4. Results:
   - Plate ID: 1ฒว8052
   - Province: ชลบุรี
   - Full Plate: 1ฒว8052 ชลบุรี
   - Plate BBox: [...]
   - Flag: complete
   - Message: OK

All tests passed! ✓
```

### 2. ทดสอบกับรูปของคุณ
```bash
python test_pipeline.py /path/to/your/image.jpg
```

## เริ่ม API Server

```bash
python main.py
```

Server จะรันที่ `http://localhost:5000`

### Endpoints:
- `GET /readyz` - Health check
- `POST /api/v1/image/process` - Process image
- `POST /api/v1/image/process/skip/car` - Process with car bbox

## ทดสอบ API

### Terminal 1: เริ่ม server
```bash
python main.py
```

### Terminal 2: ทดสอบ API
```bash
# ใช้ test script
python test_api.py

# หรือใช้ curl
curl -X POST http://localhost:5000/api/v1/image/process \
  -F "file=@test.jpg"

# หรือใช้ PowerShell
Invoke-WebRequest -Uri "http://localhost:5000/api/v1/image/process" `
  -Method POST `
  -Form @{file=Get-Item "test.jpg"}
```

## ตัวอย่าง Response

```json
{
  "car_bbox": null,
  "plate_bbox": [
    [409.92, 405.96],
    [520.15, 405.96],
    [520.15, 462.45],
    [409.92, 462.45]
  ],
  "text_bbox_list": null,
  "plate_id": "1ฒว8052",
  "province": "ชลบุรี",
  "full_plate": "1ฒว8052 ชลบุรี",
  "format_flag": "complete",
  "message": "OK"
}
```

## Troubleshooting

### ModuleNotFoundError: uvicorn
```bash
pip install "fastapi[standard]"
# หรือ
pip install uvicorn
```

### ModuleNotFoundError: timm
```bash
pip install timm
```

### CUDA out of memory
แก้ไข `models/image_processor.py` line 12:
```python
# เปลี่ยนจาก
processor = ImageProcessor()

# เป็น
processor = ImageProcessor(device="cpu")
```

### Weights not found
ตรวจสอบว่า weights อยู่ใน `models/weights/`:
```bash
ls models/weights/*.pt
```

ต้องมี 4 ไฟล์:
- plate_detector_best.pt
- plate_splitter_best.pt
- province_classifier_best_new_model.pt
- upper_ctc_special_best.pt

## Docker (Optional)

```bash
# Build
docker build -t alpr-plate-recognizer .

# Run
docker run -p 5000:5000 alpr-plate-recognizer
```

## Performance Tips

1. **ใช้ CUDA**: ถ้ามี GPU ความเร็วจะเพิ่มขึ้น ~4-5 เท่า
2. **Batch Processing**: ถ้าประมวลผลหลายรูป ใช้ batch API
3. **Image Size**: รูปที่เล็กกว่าจะเร็วกว่า (แนะนำ max 1920x1080)

## Next Steps

1. ติดตั้ง dependencies: `pip install -r requirements.txt`
2. ทดสอบ: `python test_pipeline.py`
3. เริ่ม server: `python main.py`
4. ทดสอบ API: `python test_api.py`
5. Deploy to production

---
สนุกกับการใช้งาน ALPR ใหม่! 🚀
