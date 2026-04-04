# CE68-XX PROJECT_NAME - Installation

## 1) วัตถุประสงค์

เอกสารนี้อธิบายวิธีติดตั้งระบบ ALPR-V2 แบบครบถ้วน ตั้งแต่การเตรียมเครื่อง ติดตั้งซอฟต์แวร์ ตั้งค่าระบบ นำซอร์สโค้ดเข้าระบบ (Clone/Pull หรือ Upload Source Code) กำหนดค่า Environment Variables ไปจนถึงการตรวจสอบว่าใช้งานได้จริง

## 2) ขอบเขตระบบ

ระบบประกอบด้วยบริการหลักดังนี้

1. Web Frontend (Next.js)
2. General API (FastAPI)
3. Image Upload API (FastAPI)
4. WebSocket Video Service
5. RTSP Service
6. Plate Recognizer (AI Inference)
7. PostgreSQL
8. Nginx Reverse Proxy

## 3) ความต้องการระบบ (Prerequisites)

### 3.1 ความต้องการด้านฮาร์ดแวร์

ขั้นต่ำ (CPU Mode)

1. CPU 4 Cores ขึ้นไป
2. RAM 8 GB ขึ้นไป
3. Disk ว่างอย่างน้อย 30 GB
4. Network เสถียรสำหรับดึง Docker Images

แนะนำ (Production)

1. CPU 8 Cores ขึ้นไป
2. RAM 16 GB ขึ้นไป
3. SSD/NVMe
4. GPU NVIDIA (ทางเลือก) สำหรับเร่ง AI Inference

กรณีใช้งาน GPU

1. NVIDIA GPU ที่รองรับ CUDA 11.8+
2. ติดตั้ง NVIDIA Driver และ NVIDIA Container Toolkit เรียบร้อย

### 3.2 ความต้องการด้านซอฟต์แวร์

1. OS: Linux / macOS / Windows (แนะนำ Windows + WSL2 หากรันด้วย Docker Desktop)
2. Docker Engine 24+ หรือ Docker Desktop เวอร์ชันเทียบเท่า
3. Docker Compose 2+
4. Git เวอร์ชันล่าสุด
5. (Windows) เปิดใช้งาน WSL2

### 3.3 พอร์ตที่ควรเปิดใช้งาน

1. 80 (Nginx)
2. 5432 (PostgreSQL ภายในระบบ)
3. พอร์ตภายในของแต่ละบริการตาม Docker Compose

---

## 4) การเตรียมระบบก่อนติดตั้ง

### 4.1 ตรวจสอบ Docker และ Compose

```bash
docker --version
docker compose version
```

### 4.2 ตรวจสอบ GPU (ถ้าใช้งาน)

```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

หากคำสั่งนี้แสดงข้อมูล GPU แสดงว่าพร้อมใช้งาน GPU Mode

---

## 5) วิธีนำซอร์สโค้ดเข้าระบบ

### วิธีที่ 1: Clone จาก Git (แนะนำสำหรับติดตั้งใหม่)

```bash
git clone https://github.com/Tanaphat-Ken/ALPR-V2.git
cd ALPR-V2/alpr_service
```

### วิธีที่ 2: Pull อัปเดตโค้ด (กรณีเคยติดตั้งแล้ว)

```bash
cd ALPR-V2
git pull origin main
cd alpr_service
```

### วิธีที่ 3: Upload Source Code

กรณีไม่ได้ใช้ Git ให้ Upload โฟลเดอร์โปรเจกต์ทั้งหมดขึ้นเครื่องเซิร์ฟเวอร์ แล้วเข้าโฟลเดอร์

```bash
cd ALPR-V2/alpr_service
```

ต้องตรวจสอบให้มีไฟล์สำคัญครบ เช่น docker-compose.yml และโฟลเดอร์บริการย่อยทั้งหมด

---

## 6) ขั้นตอนการติดตั้ง (Installation Steps)

### 6.1 สร้างไฟล์ Environment หลัก

ภายในโฟลเดอร์ alpr_service

```bash
cp .env.example .env
```

แก้ไขค่าอย่างน้อย

1. SERVER_URL เช่น http://your-server-ip
2. WS_URL เช่น ws://your-server-ip

### 6.2 สร้างไฟล์ Environment รายบริการ

```bash
cp alpr_general_api/.env.example  alpr_general_api/.env
cp alpr_api_image/.env.example     alpr_api_image/.env
cp alpr_rtsp_service/.env.example  alpr_rtsp_service/.env
```

### 6.3 กำหนดค่าที่จำเป็น

ใน alpr_general_api/.env

1. DB_PASSWORD
2. SECRET_KEY (สุ่มคีย์ใหม่)
3. APP_ENV (production หรือ development)

ตัวอย่างการสุ่ม SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

ใน alpr_api_image/.env และ alpr_rtsp_service/.env

1. DB_PASSWORD ให้ตรงกับฐานข้อมูล
2. APP_ENV ตามโหมดใช้งาน

### 6.4 ติดตั้งและรันระบบโหมด Production (CPU)

```bash
docker compose --env-file .env up -d --build
```

### 6.5 ติดตั้งและรันระบบโหมด Development

```bash
cp .env.dev.example .env.dev
docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

### 6.6 ติดตั้งและรันระบบโหมด GPU

```bash
docker compose --env-file .env -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

### 6.7 ตรวจสอบสถานะบริการ

```bash
docker compose ps
docker compose logs -f plate-recognizer
```

ทุกบริการควรอยู่สถานะ Up และไม่มี Error ต่อเนื่องใน Logs

---

## 7) การตั้งค่าหลังติดตั้ง

### 7.1 ตรวจสอบการเข้าถึงระบบ

1. Dashboard: http://localhost
2. General API docs: http://localhost/api/general/docs (dev mode)
3. Image API docs: http://localhost/api/image/docs (dev mode)
4. RTSP API docs: http://localhost/api/rtsp/docs (dev mode)
5. Health check: http://localhost/readyz

### 7.2 การตั้งค่าโดเมน/Reverse Proxy

หากใช้โดเมนจริง ให้แก้ค่าที่ไฟล์ nginx.conf และปรับ SERVER_URL, WS_URL ให้ตรงกับโดเมนจริง

### 7.3 การกำหนด Token และสิทธิ์ใช้งาน

หลังระบบขึ้นครบ ให้สร้างผู้ใช้และ Token ผ่าน General API เพื่อใช้งานบริการ API, VIDEO_WEBSOCKET และ RTSP ตามนโยบายระบบ

---

## 8) การอัปเดตเวอร์ชันโปรแกรม

```bash
cd ALPR-V2
git pull
cd alpr_service
docker compose --env-file .env up -d --build
```

หากมีการเปลี่ยนแปลงตัวแปรแวดล้อม ให้ตรวจสอบไฟล์ .env ของทุกบริการก่อนสั่ง Build ใหม่

---

## 9) การถอนการติดตั้ง / หยุดระบบ

หยุดบริการ

```bash
docker compose down
```

หยุดพร้อมลบ Volume (ข้อมูลฐานข้อมูลจะถูกลบ)

```bash
docker compose down -v
```

---

## 10) Troubleshooting เบื้องต้น

1. เข้าเว็บไม่ได้  
   ตรวจสอบ docker compose ps, พอร์ต 80, Firewall และค่า SERVER_URL

2. เชื่อมต่อฐานข้อมูลไม่ได้  
   ตรวจสอบ DB_PASSWORD, DB_HOST, DB_PORT และ container postgres ว่าทำงานอยู่

3. Swagger ไม่แสดง  
   ตรวจสอบ APP_ENV ต้องเป็น development

4. GPU ใช้ไม่ได้  
   ตรวจสอบผล nvidia-smi ในโฮสต์ และคำสั่งทดสอบ Docker GPU

5. AI Service ช้า  
   ตรวจสอบทรัพยากร RAM/CPU, ลดจำนวนงานพร้อมกัน หรือเปิดใช้ GPU Mode

---

## 11) เอกสารอ้างอิงภายในโปรเจกต์

1. README.md
2. alpr_service/DEV_MODE_GUIDE.md
3. alpr_service/TESTING_GUIDE.md
4. alpr_service/SERVICE_INTEGRATION.md
5. alpr_service/SYSTEM_SUMMARY.md
