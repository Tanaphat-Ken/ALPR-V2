# ALPRS V2 — คู่มือการรันสคริปต์ทดสอบ (4.5.1 & 4.5.2)

---

## 4.5.1 การทดสอบระดับหน่วย (Unit Testing)

> ไม่จำเป็นต้องเปิดระบบ — ทดสอบโดยตรงภายใน Docker container

### 1) ทดสอบโมดูล AI (YOLOv11 + OCR)

```bash
# ติดตั้ง pytest (ครั้งแรกเท่านั้น) แล้วรัน
docker exec alpr_service-plate-recognizer-1 bash -c \
  "pip install pytest -q && cd /usr/src/app && python -m pytest testing/test_ai_unit.py -v"
```

**หมายเหตุ:** ไฟล์ภาพ `test.jpg` ถูก mount เข้า container โดยอัตโนมัติผ่าน volume
เนื่องจาก `plate_recognizer/` ถูก mount ไว้ที่ `/usr/src/app` — ไม่ต้อง copy หรือ rebuild ใดๆ

---

### 2) ทดสอบตรรกะการจัดการโควตา (Quota Management)

```bash
# ติดตั้ง dependencies แล้วรัน (ครั้งแรกเท่านั้น)
docker exec alpr_api_image bash -c \
  "pip install pytest pytest-asyncio twisted -q && \
   cd /app && python -m pytest tests/test_quota_unit.py -v -p no:twisted"
```

---

### 3) ทดสอบระบบ JWT Authentication

```bash
# ติดตั้ง twisted ครั้งแรก (แก้ broken plugin)
docker exec alpr_general_api bash -c "pip install twisted -q"

# รันทดสอบ
docker exec alpr_general_api bash -c \
  "cd /app && python -m pytest Test/test_jwt_unit.py -v -p no:twisted"
```

---

## 4.5.2 การทดสอบการผสานระบบ (Integration Testing)

> ต้องมีระบบทำงานอยู่ก่อน: `docker compose up -d`
> รันคำสั่งทั้งหมดจาก directory `alpr_service/`

```bash
# 1. คัดลอก script และภาพทดสอบเข้า container
docker exec alpr_general_api mkdir -p /tmp/plate_recognizer/testing
docker cp plate_recognizer/testing/test.jpg alpr_general_api:/tmp/plate_recognizer/testing/test.jpg
docker cp test_integration_main.py alpr_general_api:/tmp/test_integration_main.py

# 2. ติดตั้ง psycopg2 (ครั้งแรกเท่านั้น)
docker exec alpr_general_api bash -c "pip install psycopg2-binary -q"

# 3. รันทดสอบทั้งหมด
docker exec alpr_general_api bash -c "
  NGINX_BASE=http://alpr_nginx \
  DB_HOST=alpr_postgres \
  DB_USER=postgres \
  DB_PASSWORD=postgres \
  DB_NAME=alpr_db \
  python /tmp/test_integration_main.py
"
```

### ทดสอบแยกหัวข้อ

```bash
# เฉพาะ API Gateway & Routing
docker exec alpr_general_api bash -c "
  NGINX_BASE=http://alpr_nginx DB_HOST=alpr_postgres DB_USER=postgres DB_PASSWORD=postgres DB_NAME=alpr_db \
  python /tmp/test_integration_main.py gateway
"

# เฉพาะ Load Balancing
docker exec alpr_general_api bash -c "
  NGINX_BASE=http://alpr_nginx \
  python /tmp/test_integration_main.py loadbalance
"

# เฉพาะ Database Persistence
docker exec alpr_general_api bash -c "
  NGINX_BASE=http://alpr_nginx DB_HOST=alpr_postgres DB_USER=postgres DB_PASSWORD=postgres DB_NAME=alpr_db \
  python /tmp/test_integration_main.py database
"
```

---

## ตำแหน่งไฟล์ทดสอบ

| หัวข้อ | ไฟล์ |
|--------|------|
| AI Inference Unit Test | `plate_recognizer/testing/test_ai_unit.py` |
| Quota Management Unit Test | `alpr_api_image/tests/test_quota_unit.py` |
| JWT Auth Unit Test | `alpr_general_api/Test/test_jwt_unit.py` |
| Integration Tests (ทั้งหมด) | `test_integration_main.py` |

---

## ทดสอบ Load Balancing ด้วย Docker Logs (วิธีการมือ)

หลังจากส่งภาพหลายครั้งผ่าน Postman หรือ curl:

```bash
# ดู log ของ replica ทั้งสองชุด
docker logs alpr_service-plate-recognizer-1 --tail 20
docker logs alpr_service-plate-recognizer-2 --tail 20
```

ควรเห็น POST request สลับกันระหว่าง replica-1 และ replica-2

---

## ตรวจสอบ Database ด้วย psql

```bash
docker exec alpr_postgres psql -U postgres -d alpr_db -c \
  "SELECT log_id, plate_id, province, created_at FROM image_logs ORDER BY created_at DESC LIMIT 10;"
```
