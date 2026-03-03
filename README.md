# 🚗 ALPR-V2 — Automatic License Plate Recognition System

> AI-powered License Plate Recognition System with Real-time Processing, WebSocket Support, and Microservices Architecture

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-000000?logo=nextdotjs)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://www.python.org/)
[![YOLOv11](https://img.shields.io/badge/YOLO-v11-00FFFF)](https://github.com/ultralytics/ultralytics)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Services](#-services)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Environment Variables](#-environment-variables)
- [API Documentation](#-api-documentation)
- [Performance](#-performance)

---

## 🎯 Overview

ALPR-V2 is an Automatic License Plate Recognition system built with AI and Deep Learning, supporting:

- 🖼️ **Real-time image processing** via HTTP upload and WebSocket
- 🎥 **Video frame streaming** via WebSocket
- 📡 **RTSP stream processing** from IP cameras
- 🔌 **RESTful API** for system integration
- 💳 **Subscription & quota management**
- 🔐 **JWT-based authentication**

---

## 🏛️ Architecture

```mermaid
graph TB
    Client[Client / Browser] -->|HTTP / WebSocket| Nginx[Nginx Reverse Proxy :80]

    Nginx -->|/| Web[Next.js Frontend]
    Nginx -->|/api/v1/image/| PR["Plate Recognizer × 2 (Load Balanced)"]
    Nginx -->|/api/general/| GeneralAPI[General API :8092]
    Nginx -->|/api/image/| ImageAPI[Image Upload API :8089]
    Nginx -->|/ws/image/| WSImage[WebSocket Image :8090]
    Nginx -->|/ws/video/| WSVideo[WebSocket Video :5000]
    Nginx -->|/api/rtsp/| RTSP[RTSP Service :5003]

    GeneralAPI -->|SQL| DB[(PostgreSQL :5432)]
    ImageAPI -->|SQL| DB
    WSImage -->|SQL| DB
    RTSP -->|SQL| DB

    ImageAPI -->|HTTP| PR
    WSImage -->|HTTP| PR
    WSVideo -->|HTTP| PR
    RTSP -->|HTTP| PR

    PR --> Detector["PlateDetector (YOLOv11s)"]
    Detector --> Splitter["PlateSplitter (YOLOv11n)"]
    Splitter --> Province["Province Classifier (MobileNetV3)"]
    Splitter --> OCR["OCR Reader (CTC/CRNN)"]
```

### Processing Pipeline

```
Image Input
    ↓
PlateDetector (YOLOv11s)      ← detects car + plate regions
    ↓
PlateSplitter (YOLOv11n)      ← splits plate into character segments
    ↓
    ├── Province Classifier (MobileNetV3) → province name
    └── CTC OCR Reader (CRNN)            → plate digits / letters
    ↓
Result: { plate_id, province, full_plate, format_flag }
```

---

## 🔧 Services

| # | Service | Container | Internal Port | Public Path |
|---|---------|-----------|--------------|-------------|
| 1 | **Nginx** | `alpr_nginx` | 80 | — |
| 2 | **Next.js Frontend** | `alpr_nextjs` | 3000 | `/` |
| 3 | **General API** | `alpr_general_api` | 8092 | `/api/general/` |
| 4 | **Image Upload API** | `alpr_api_image` | 8089 | `/api/image/` |
| 5 | **WebSocket Video** | `alpr_websocket_video` | 5000 | `/ws/video/` |
| 6 | **RTSP Service** | `alpr_rtsp_service` | 5003 | `/api/rtsp/` |
| 7 | **Plate Recognizer** | *(2 replicas)* | 5000 | `/api/v1/image/` |
| 8 | **PostgreSQL** | `alpr_postgres` | 5432 | — |

### Service Descriptions

**plate_recognizer** — AI core engine running 4 models (YOLOv11s detector, YOLOv11n splitter, MobileNetV3 province classifier, CTC/CRNN OCR). Deployed as 2 load-balanced replicas, each limited to 2 GB RAM.

**alpr_web** — Next.js 14 dashboard for managing tokens, subscriptions, RTSP streams, image/video upload, and viewing detection logs.

**alpr_general_api** — FastAPI gateway handling authentication (JWT), token CRUD, subscription info, payment, and user management.

**alpr_api_image** — FastAPI service for authenticated one-shot image uploads. Validates **API-type** service tokens, deducts quota (`request_quota`), calls the plate recognizer, and persists structured logs to PostgreSQL.

**alpr_websocket_video** — WebSocket endpoint for video frame streaming. Token is embedded in the URL path. Optimised for high-throughput frame delivery (up to 5 MB/frame).

**alpr_rtsp_service** — Manages RTSP camera streams, performs continuous license plate detection, and supports a live Web Viewer. Stores detection events to the database.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Ant Design, Redux Toolkit |
| Backend APIs | FastAPI (Python 3.11+), SQLAlchemy, Pydantic |
| AI Models | PyTorch, YOLOv11 (Ultralytics), MobileNetV3, CTC/CRNN |
| Image Processing | OpenCV, Pillow |
| Database | PostgreSQL 15 |
| Reverse Proxy | Nginx Alpine |
| Containerisation | Docker & Docker Compose |
| Auth | JWT (python-jose / PyJWT) |

---

## 🚀 Quick Start

### Prerequisites

- Docker ≥ 24 and Docker Compose ≥ 2
- 8 GB RAM minimum (16 GB recommended for 2 AI replicas)
- Linux / macOS / Windows (WSL2)

### 1 — Clone

```bash
git clone https://github.com/Tanaphat-Ken/ALPR-V2.git
cd ALPR-V2/alpr_service
```

### 2 — Configure environment variables

Copy the root env template and fill in your server IP:

```bash
cd alpr_service
cp .env.example .env
# edit SERVER_URL and WS_URL
```

Copy per-service env templates:

```bash
cp alpr_general_api/.env.example  alpr_general_api/.env
cp alpr_api_image/.env.example     alpr_api_image/.env
cp alpr_rtsp_service/.env.example  alpr_rtsp_service/.env
```

Key variables to set before first run:

```env
# alpr_service/.env  (controls Next.js public URLs)
SERVER_URL=http://your-server-ip
WS_URL=ws://your-server-ip

# alpr_general_api/.env
DB_PASSWORD=your_db_password
SECRET_KEY=<random_secret>   # python3 -c "import secrets; print(secrets.token_hex(32))"

# alpr_api_image/.env / alpr_rtsp_service/.env
DB_PASSWORD=your_db_password
```

### 3 — Start all services

```bash
docker compose --env-file .env up -d --build
```

### 4 — Check status

```bash
docker compose ps
docker compose logs -f plate-recognizer
```

### 5 — Access

| Interface | URL |
|-----------|-----|
| Dashboard | http://localhost |
| General API docs | http://localhost/api/general/docs *(dev mode only)* |
| Image API docs | http://localhost/api/image/docs *(dev mode only)* |
| RTSP Service docs | http://localhost/api/rtsp/docs *(dev mode only)* |
| Plate Recognizer health | http://localhost/api/v1/image/readyz |

> **Note:** Swagger UI (`/docs`) is disabled in production (`APP_ENV=production`). It is only available when running dev mode.

### Development mode

Copy the dev env template, then run with both compose files:

```bash
cp .env.dev.example .env.dev
# edit SERVER_URL and WS_URL in .env.dev

docker compose --env-file .env.dev -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Dev mode enables:
- Next.js hot reload (volume-mounted `src/`)
- Swagger UI on all FastAPI services (`APP_ENV=development`)

---

## 🔐 Environment Variables

### Root (`alpr_service/.env` and `.env.dev`)

| Variable | Description |
|----------|-------------|
| `SERVER_URL` | HTTP base URL of the server, e.g. `http://your-domain.com` |
| `WS_URL` | WebSocket base URL of the server, e.g. `ws://your-domain.com` |

### alpr_general_api

| Variable | Description |
|----------|-------------|
| `DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT` | PostgreSQL connection |
| `SECRET_KEY` | Secret key for signing JWTs — generate with `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `APP_ENV` | `production` disables Swagger UI; `development` enables it |

### alpr_api_image

| Variable | Description |
|----------|-------------|
| `DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT` | PostgreSQL connection |
| `APP_ENV` | `production` disables Swagger UI; `development` enables it |

### alpr_rtsp_service

| Variable | Description |
|----------|-------------|
| `PLATE_RECOG_BASE_URL` | Plate recognizer endpoint (internal: `http://plate-recognizer:5000/api/v1`) |
| `DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD` | PostgreSQL connection |
| `DATABASE_ENABLED` | `true` / `false` |
| `APP_ENV` | `production` disables Swagger UI; `development` enables it |
| `FPS_LIMIT / FRAME_SKIP` | Stream processing tuning |

### alpr_web (Next.js build args — set via root `.env`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_BASE_API_GATE_WAY_URL` | General API base URL |
| `NEXT_PUBLIC_API_UPLOAD_IMAGE` | Image Upload API base URL |
| `NEXT_PUBLIC_WEBSOCKET_VIDEO_HANLER` | WebSocket video base URL |
| `NEXT_PUBLIC_RTSP_SERVICE_URL` | RTSP HTTP API base URL |
| `NEXT_PUBLIC_RTSP_WEBSOCKET_URL` | RTSP WebSocket base URL |

---

## 📚 API Documentation

Full interactive documentation is available in the dashboard at **Dashboard → Documentation**, or via the auto-generated Swagger UIs:

| Service | Swagger UI |
|---------|-----------|
| General API | `/api/general/docs` *(dev only)* |
| Image API | `/api/image/docs` *(dev only)* |
| RTSP Service | `/api/rtsp/docs` *(dev only)* |

### Key endpoints at a glance

```
# Auth
POST   /api/general/auth/register
POST   /api/general/auth/login
GET    /api/general/auth/me

# Plate Recognition (direct, no token required)
POST   /api/v1/image/process
POST   /api/v1/image/process/skip/car
POST   /api/v1/image/process/from-plate-crop
GET    /readyz

# Image Upload (API token required — service_type: API)
POST   /api/image/upload-image

# WebSocket — Video (VIDEO_WEBSOCKET token in path)
WS     ws://host/ws/video/{token}

# RTSP Streams
GET    /api/rtsp/streams
POST   /api/rtsp/streams
POST   /api/rtsp/streams/{id}/start
POST   /api/rtsp/streams/{id}/stop
WS     ws://host/api/rtsp/stream/{id}

# Token Management
GET    /api/general/tokens/{user_id}?service_type=API
POST   /api/general/tokens
PUT    /api/general/tokens
DELETE /api/general/tokens
# service_type values: API | VIDEO_WEBSOCKET | RTSP

# Subscription
GET    /api/general/info/subscribe/{user_id}
```

### Plate recognizer response

```json
{
  "car_bbox": null,
  "plate_bbox": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]],
  "plate_id": "1ฒว8052",
  "province": "ชลบุรี",
  "full_plate": "1ฒว8052 ชลบุรี",
  "format_flag": "complete",
  "message": "OK"
}
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Inference time (single image) | ~200 ms |
| OCR accuracy | ~96% |
| Province classification accuracy | ~97% |
| Concurrent users (load balanced) | 100+ |
| Max upload size (HTTP) | 10 MB |
| Max WebSocket frame (video) | 5 MB |
| Max WebSocket frame (image) | 50 MB |

---

## 🗂️ Project Structure

```
alpr_service/
├── .env.example                # Root env template (SERVER_URL, WS_URL)
├── .env.dev.example            # Dev env template
├── nginx.conf                  # Nginx reverse proxy + routing rules
├── docker-compose.yml          # Production compose
├── docker-compose.dev.yml      # Development compose (hot reload + Swagger UI)
├── dump.sql                    # Initial DB schema + seed data
├── plate_recognizer/           # AI inference engine (YOLOv11 + OCR)
├── alpr_web/                   # Next.js 14 frontend dashboard
├── alpr_general_api/           # Auth, tokens, subscriptions, users
├── alpr_api_image/             # Authenticated image upload + logging (service_type: API)
├── alpr_websocket_image/       # WS image service (not exposed in dashboard)
├── alpr_websocket_video/       # WebSocket real-time video processing (service_type: VIDEO_WEBSOCKET)
├── alpr_rtsp_service/          # RTSP camera stream management (service_type: RTSP)
└── videos/                     # Shared video storage (read-only mount)
```

---

<div align="center">
  <strong>Built with FastAPI · Next.js · PyTorch · YOLOv11</strong>
</div>
