# ALPR-V2 — System Diagrams & Test Cases

> Auto-generated system analysis for the ALPR-V2 Automatic License Plate Recognition System

---

## Table of Contents

1. [Use Case Diagram](#1-use-case-diagram)
2. [Sequence Diagrams](#2-sequence-diagrams)
   - [2.1 User Registration & Login](#21-user-registration--login)
   - [2.2 Image Upload & Plate Recognition (HTTP)](#22-image-upload--plate-recognition-http)
   - [2.3 Real-time Video via WebSocket](#23-real-time-video-via-websocket)
   - [2.4 RTSP Stream Management](#24-rtsp-stream-management)
   - [2.5 Token Management (Create / Delete)](#25-token-management-create--delete)
   - [2.6 Subscription Purchase](#26-subscription-purchase)
3. [Test Cases — System Testing](#3-test-cases--system-testing)
   - [TC-AUTH — Authentication](#tc-auth--authentication)
   - [TC-TOKEN — Token Management](#tc-token--token-management)
   - [TC-IMAGE — Image Upload & Recognition](#tc-image--image-upload--recognition)
   - [TC-VIDEO — WebSocket Video Streaming](#tc-video--websocket-video-streaming)
   - [TC-RTSP — RTSP Stream Management](#tc-rtsp--rtsp-stream-management)
   - [TC-SUB — Subscription Management](#tc-sub--subscription-management)
   - [TC-AI — AI Plate Recognizer](#tc-ai--ai-plate-recognizer)

---

## 1. Use Case Diagram

```mermaid
---
title: ALPR-V2 Use Case Diagram
---
flowchart TD
    %% Actors
    Guest(["👤 Guest\n(Unauthenticated)"])
    User(["👤 Registered User"])
    Admin(["👤 Admin"])
    ExtSystem(["🖥️ External System\n(API Client)"])
    Camera(["📷 IP Camera\n(RTSP Source)"])

    %% ── Auth Subsystem ──
    subgraph AUTH ["🔐 Authentication"]
        UC1([Register Account])
        UC2([Login & Get JWT])
        UC3([View My Profile])
    end

    %% ── Subscription Subsystem ──
    subgraph SUB ["💳 Subscription & Quota"]
        UC4([Browse Subscription Plans])
        UC5([Purchase Subscription])
        UC6([View Current Subscription])
        UC7([Check Quota Usage])
    end

    %% ── Token Subsystem ──
    subgraph TOK ["🔑 Token Management"]
        UC8([Create API Token])
        UC9([Create Video-WS Token])
        UC10([Create RTSP Token])
        UC11([List Tokens])
        UC12([Update Token])
        UC13([Delete Token])
        UC14([View Token Usage per Hour])
    end

    %% ── Image Recognition Subsystem ──
    subgraph IMG ["🖼️ Image Recognition"]
        UC15([Upload Image via HTTP])
        UC16([Recognize Plate – Direct API])
        UC17([Recognize Plate – Skip Car Detection])
        UC18([Recognize Plate – From Plate Crop])
        UC19([View Image Logs])
    end

    %% ── WebSocket Video Subsystem ──
    subgraph WSV ["🎥 WebSocket Video Streaming"]
        UC20([Connect via WS with Token])
        UC21([Stream Video Frames])
        UC22([Receive Recognition Results])
    end

    %% ── RTSP Subsystem ──
    subgraph RTSP ["📡 RTSP Camera Streams"]
        UC23([Add RTSP Stream])
        UC24([Start / Stop Stream])
        UC25([View Live Stream – Web Viewer])
        UC26([View Detection Events])
    end

    %% ── AI Engine (internal) ──
    subgraph AI ["🤖 AI Plate Recognizer – Internal Only"]
        UC27([Detect Car & Plate – YOLOv11s])
        UC28([Split Plate Characters – YOLOv11n])
        UC29([Classify Province – MobileNetV3])
        UC30([Read Characters – CTC/CRNN OCR])
    end

    %% Actor → Use Case relationships
    Guest --> UC1
    Guest --> UC2

    User --> UC3
    User --> UC4
    User --> UC5
    User --> UC6
    User --> UC7
    User --> UC8
    User --> UC9
    User --> UC10
    User --> UC11
    User --> UC12
    User --> UC13
    User --> UC14
    User --> UC15
    User --> UC19
    User --> UC23
    User --> UC24
    User --> UC25
    User --> UC26

    ExtSystem --> UC16
    ExtSystem --> UC17
    ExtSystem --> UC18
    ExtSystem --> UC20
    ExtSystem --> UC21
    ExtSystem --> UC22

    Camera --> UC24

    Admin --> UC4
    Admin --> UC5

    %% Include / Extend
    UC15 -.->|«include»| UC16
    UC21 -.->|«include»| UC22
    UC24 -.->|«include»| UC26
    UC16 -.->|«include»| UC27
    UC27 -.->|«include»| UC28
    UC28 -.->|«include»| UC29
    UC28 -.->|«include»| UC30
```

---

## 2. Sequence Diagrams

### 2.1 User Registration & Login

```mermaid
sequenceDiagram
    actor User
    participant FE as Next.js Frontend
    participant Nginx
    participant GenAPI as General API :8092
    participant DB as PostgreSQL

    Note over User,DB: ── Registration ──
    User->>FE: Fill register form (email, password)
    FE->>Nginx: POST /api/general/api/v1/auth/register
    Nginx->>GenAPI: POST /api/v1/auth/register
    GenAPI->>GenAPI: Validate email format & password length
    GenAPI->>DB: INSERT INTO users (email, hashed_password)
    DB-->>GenAPI: user_id, email
    GenAPI-->>Nginx: 201 { user_id, email, message }
    Nginx-->>FE: 201 Created
    FE-->>User: "Registration successful"

    Note over User,DB: ── Login ──
    User->>FE: Enter email & password
    FE->>Nginx: POST /api/general/api/v1/auth/login
    Nginx->>GenAPI: POST /api/v1/auth/login
    GenAPI->>DB: SELECT user WHERE email=?
    DB-->>GenAPI: user record
    GenAPI->>GenAPI: bcrypt.verify(password, hash)
    alt Credentials valid
        GenAPI->>GenAPI: create_access_token(user_id, email, exp=7days)
        GenAPI-->>FE: 200 { access_token, token_type, user_id, email }
        FE->>FE: Store JWT in localStorage / Redux
        FE-->>User: Redirect to Dashboard
    else Invalid credentials
        GenAPI-->>FE: 401 Unauthorized
        FE-->>User: "Incorrect email or password"
    end
```

---

### 2.2 Image Upload & Plate Recognition (HTTP)

```mermaid
sequenceDiagram
    actor Client
    participant Nginx
    participant ImgAPI as Image API :8089
    participant DB as PostgreSQL
    participant PR as Plate Recognizer ×2

    Client->>Nginx: POST /api/image/api/v1/images/upload-image\nHeaders: X-API-Token: <token>\nBody: multipart/form-data image
    Nginx->>ImgAPI: Forward request

    Note over ImgAPI: TokenAuthMiddleware
    ImgAPI->>DB: SELECT token WHERE key=<token> AND service_type='API'
    DB-->>ImgAPI: token record (quota, expiry, user_id)

    alt Token invalid / expired
        ImgAPI-->>Client: 401 Unauthorized
    else Quota exhausted
        ImgAPI-->>Client: 403 Quota exceeded
    else Token valid
        ImgAPI->>ImgAPI: Decode image bytes
        ImgAPI->>PR: POST /api/v1/image/process (load balanced)
        PR->>PR: YOLOv11s — detect car + plate bbox
        PR->>PR: YOLOv11n — split plate into character segments
        PR->>PR: MobileNetV3 — classify province
        PR->>PR: CTC/CRNN OCR — read plate digits/chars
        PR-->>ImgAPI: { plate_id, province, full_plate, format_flag, plate_bbox }
        ImgAPI->>DB: INSERT image_logs (token_id, plate_id, province, timestamp, …)
        ImgAPI->>DB: UPDATE token SET request_quota = request_quota - 1
        DB-->>ImgAPI: OK
        ImgAPI-->>Client: 200 { plate_id, province, full_plate, format_flag }
    end
```

---

### 2.3 Real-time Video via WebSocket

```mermaid
sequenceDiagram
    actor Client
    participant Nginx
    participant WSVid as WebSocket Video :5000
    participant PR as Plate Recognizer

    Client->>Nginx: WS Upgrade: ws://host/ws/video/<token>
    Nginx->>WSVid: WS /{token}

    WSVid->>WSVid: Validate token (service_type=VIDEO_WEBSOCKET)
    alt Token invalid
        WSVid-->>Client: WS Close 4001 Unauthorized
    else Token valid
        WSVid-->>Client: WS Open (connection accepted)

        loop For each video frame
            Client->>WSVid: Binary frame data (≤5 MB)
            WSVid->>WSVid: Decode frame bytes → image
            WSVid->>PR: POST /api/v1/image/process (image bytes)
            PR-->>WSVid: { plate_id, province, full_plate, format_flag }
            WSVid-->>Client: JSON { plate_id, province, full_plate, format_flag }
        end

        Client->>WSVid: WS Close
        WSVid->>WSVid: Cleanup task & resources
    end
```

---

### 2.4 RTSP Stream Management

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant Nginx
    participant RTSP as RTSP Service :5003
    participant Camera as IP Camera
    participant PR as Plate Recognizer
    participant DB as PostgreSQL

    Note over User,DB: ── Add & Start Stream ──
    User->>FE: Enter RTSP URL + stream name
    FE->>Nginx: POST /api/rtsp/api/v1/streams\n{ name, rtsp_url, token_id }
    Nginx->>RTSP: POST /api/v1/streams
    RTSP->>DB: INSERT INTO rtsp_streams
    DB-->>RTSP: stream_id
    RTSP-->>FE: 201 { stream_id, name, status: "stopped" }

    User->>FE: Click "Start Stream"
    FE->>Nginx: POST /api/rtsp/api/v1/streams/{id}/start
    Nginx->>RTSP: POST /api/v1/streams/{id}/start
    RTSP->>RTSP: Spawn async capture task

    loop Continuous frame capture
        RTSP->>Camera: OpenCV VideoCapture (RTSP)
        Camera-->>RTSP: Raw frame
        RTSP->>PR: POST /api/v1/image/process
        PR-->>RTSP: { plate_id, province, full_plate }
        RTSP->>DB: INSERT detection_logs
    end

    Note over User,DB: ── Live Web Viewer ──
    User->>FE: Open Web Viewer
    FE->>Nginx: WS ws://host/api/rtsp/stream/{id}
    Nginx->>RTSP: WS /api/v1/stream/{id}
    loop Broadcast frames
        RTSP-->>FE: JPEG frame + detection overlay
    end

    Note over User,DB: ── Stop Stream ──
    User->>FE: Click "Stop Stream"
    FE->>Nginx: POST /api/rtsp/api/v1/streams/{id}/stop
    Nginx->>RTSP: POST /api/v1/streams/{id}/stop
    RTSP->>RTSP: Cancel capture task
    RTSP->>DB: UPDATE stream SET status='stopped'
    RTSP-->>FE: 200 { status: "stopped" }
```

---

### 2.5 Token Management (Create / Delete)

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant Nginx
    participant GenAPI as General API
    participant DB as PostgreSQL

    Note over User,DB: ── Create Token ──
    User->>FE: Click "New Token" (service_type, name, expiry)
    FE->>Nginx: POST /api/general/api/v1/tokens\nAuthorization: Bearer <JWT>
    Nginx->>GenAPI: POST /api/v1/tokens
    GenAPI->>GenAPI: Verify JWT
    GenAPI->>DB: SELECT user_subscription WHERE user_id=?
    DB-->>GenAPI: subscription + token_limit
    GenAPI->>DB: SELECT COUNT(*) FROM tokens WHERE user_id=?
    alt Limit reached
        GenAPI-->>FE: 403 Token limit reached
    else Under limit
        GenAPI->>GenAPI: Generate unique token key (UUID)
        GenAPI->>DB: INSERT INTO tokens\n(user_id, key, service_type, name, expire_time)
        DB-->>GenAPI: token record
        GenAPI-->>FE: 200 TokenResponse { key, name, service_type, expire_time }
        FE-->>User: Display new token key
    end

    Note over User,DB: ── Delete Token ──
    User->>FE: Click "Delete" on token
    FE->>Nginx: DELETE /api/general/api/v1/tokens\nBody: { key: "<token_key>" }
    Nginx->>GenAPI: DELETE /api/v1/tokens
    GenAPI->>DB: DELETE FROM tokens WHERE key=?
    DB-->>GenAPI: rows_affected
    GenAPI-->>FE: 200 { message: "Token deleted" }
    FE-->>User: Token removed from list
```

---

### 2.6 Subscription Purchase

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant GenAPI as General API
    participant DB as PostgreSQL

    User->>FE: Open Subscription page
    FE->>GenAPI: GET /api/v1/subscription/get_all_service
    GenAPI->>DB: SELECT subscriptions WHERE service_type ILIKE 'tier%'
    DB-->>GenAPI: [Tier1, Tier2, Tier3, …]
    GenAPI-->>FE: List of plans

    User->>FE: Select plan & confirm purchase
    FE->>GenAPI: POST /api/v1/subscription/create_user_subscription\n{ user_id, sub_id }
    GenAPI->>DB: SELECT subscription WHERE sub_id=?
    GenAPI->>DB: SELECT user WHERE user_id=?
    GenAPI->>DB: INSERT INTO user_subscriptions\n(user_id, sub_id, start_date, end_date, …)
    DB-->>GenAPI: user_subscription record
    GenAPI-->>FE: 200 { message: "Subscription activated" }
    FE-->>User: Show active plan + quota

    User->>FE: View subscription details
    FE->>GenAPI: GET /api/v1/info/subscribe/{user_id}
    GenAPI->>DB: SELECT user_subscription JOIN subscription
    DB-->>GenAPI: quota, expiry, limits
    GenAPI-->>FE: Subscription info
    FE-->>User: Display quota dashboard
```

---

## 3. Test Cases — System Testing

### TC-AUTH — Authentication

| ID         | Test Case                          | Precondition                 | Steps                                                        | Expected Result                                          | Priority |
| ---------- | ---------------------------------- | ---------------------------- | ------------------------------------------------------------ | -------------------------------------------------------- | -------- |
| TC-AUTH-01 | Register with valid data           | No existing account          | POST `/auth/register` with valid email & password (≥6 chars) | 201, `user_id` returned, password stored as bcrypt hash  | High     |
| TC-AUTH-02 | Register with duplicate email      | Email already exists in DB   | POST `/auth/register` with same email                        | 400 / 409 / 500 error                                    | High     |
| TC-AUTH-03 | Register with invalid email format | —                            | POST with `"email": "not-an-email"`                          | 422 Unprocessable Entity                                 | Medium   |
| TC-AUTH-04 | Register with short password       | —                            | POST with password < 6 chars                                 | 422 Validation Error                                     | Medium   |
| TC-AUTH-05 | Login with correct credentials     | User registered (TC-AUTH-01) | POST `/auth/login` with correct email/password               | 200, JWT `access_token` returned, `token_type: "bearer"` | High     |
| TC-AUTH-06 | Login with wrong password          | User registered              | POST with wrong password                                     | 401 Unauthorized                                         | High     |
| TC-AUTH-07 | Login with non-existent email      | —                            | POST with unknown email                                      | 401 Unauthorized                                         | High     |
| TC-AUTH-08 | Access `/auth/me` with valid JWT   | User logged in               | GET `/auth/me` with `Authorization: Bearer <token>`          | 200, user info returned                                  | High     |
| TC-AUTH-09 | Access `/auth/me` without JWT      | —                            | GET `/auth/me` (no header)                                   | 401 / 403 Unauthorized                                   | High     |
| TC-AUTH-10 | Access `/auth/me` with expired JWT | JWT past expiry              | GET `/auth/me` with expired token                            | 401 Unauthorized                                         | Medium   |
| TC-AUTH-11 | JWT contains correct claims        | User logged in               | Decode JWT from login response                               | Payload has `user_id`, `email`, `exp` (~7 days)          | Medium   |

---

### TC-TOKEN — Token Management

| ID        | Test Case                           | Precondition                     | Steps                                                                     | Expected Result                                    | Priority |
| --------- | ----------------------------------- | -------------------------------- | ------------------------------------------------------------------------- | -------------------------------------------------- | -------- |
| TC-TOK-01 | Create API token                    | User with active subscription    | POST `/tokens` `{ user_id, service_type:"API", token_name, expire_time }` | 200, `key` (UUID) returned, `service_type = "API"` | High     |
| TC-TOK-02 | Create VIDEO_WEBSOCKET token        | User with subscription           | POST `/tokens` with `service_type: "VIDEO_WEBSOCKET"`                     | 200, token with correct service_type               | High     |
| TC-TOK-03 | Create RTSP token                   | User with subscription           | POST `/tokens` with `service_type: "RTSP"`                                | 200, token with correct service_type               | High     |
| TC-TOK-04 | Default expiry = 30 days            | —                                | POST `/tokens` with `expire_time: null`                                   | 200, `expire_time` ≈ now + 30 days                 | Medium   |
| TC-TOK-05 | Get tokens filtered by service_type | Tokens of multiple types exist   | GET `/tokens/{user_id}?service_type=API`                                  | 200, array only contains `service_type = "API"`    | High     |
| TC-TOK-06 | Delete token                        | Token exists                     | DELETE `/tokens` `{ key: "<token_key>" }`                                 | 200, token no longer retrievable via GET           | High     |
| TC-TOK-07 | Update token name/expiry            | Token exists                     | PUT `/tokens` `{ key, token_name, expire_time }`                          | 200, updated token data returned                   | Medium   |
| TC-TOK-08 | Token limit enforcement             | User at subscription token limit | POST `/tokens` beyond limit                                               | 403 / 400 error                                    | High     |
| TC-TOK-09 | Token usage per hour                | Tokens used for requests         | POST `/tokens_usage_per_hour` `{ user_id, service_type }`                 | 200, list of `{ hour, count }`                     | Medium   |
| TC-TOK-10 | Get tokens for wrong user           | Tokens belong to user A          | GET `/tokens/{userB_id}?service_type=API`                                 | 200, empty array                                   | Medium   |

---

### TC-IMAGE — Image Upload & Recognition

| ID        | Test Case                            | Precondition                  | Steps                                                          | Expected Result                                                                   | Priority |
| --------- | ------------------------------------ | ----------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------------- | -------- |
| TC-IMG-01 | Upload image with valid API token    | Active API token, quota > 0   | POST `/images/upload-image` multipart with valid `X-API-Token` | 200, `{ plate_id, province, full_plate, format_flag }`                            | High     |
| TC-IMG-02 | Upload without token                 | —                             | POST without `X-API-Token` header                              | 401 Unauthorized                                                                  | High     |
| TC-IMG-03 | Upload with invalid token            | —                             | POST with random string as token                               | 401 Unauthorized                                                                  | High     |
| TC-IMG-04 | Upload with wrong service_type token | VIDEO_WEBSOCKET token used    | POST with `service_type=VIDEO_WEBSOCKET` token                 | 401 / 403 Unauthorized                                                            | High     |
| TC-IMG-05 | Quota deducted after successful call | Token quota = N               | POST successful image upload                                   | Token quota becomes N-1 in DB                                                     | High     |
| TC-IMG-06 | Upload when quota = 0                | Token quota exhausted         | POST image                                                     | 403 Quota exceeded                                                                | High     |
| TC-IMG-07 | Upload expired token                 | Token expiry date in the past | POST image                                                     | 401 Token expired                                                                 | High     |
| TC-IMG-08 | Upload file > 10 MB                  | —                             | POST with 11 MB image                                          | 413 Request Entity Too Large                                                      | Medium   |
| TC-IMG-09 | Upload non-image file                | —                             | POST with `.txt` or `.pdf` file                                | 400 / 422 Bad Request                                                             | Medium   |
| TC-IMG-10 | Valid response structure             | Valid upload                  | Check response JSON                                            | Contains all required fields: `plate_id`, `province`, `full_plate`, `format_flag` | High     |
| TC-IMG-11 | Log stored after recognition         | Valid upload                  | Query `image_logs` in DB                                       | New row with correct `token_id`, `plate_id`, `timestamp`                          | High     |

---

### TC-VIDEO — WebSocket Video Streaming

| ID        | Test Case                                | Precondition                 | Steps                                      | Expected Result                                                 | Priority |
| --------- | ---------------------------------------- | ---------------------------- | ------------------------------------------ | --------------------------------------------------------------- | -------- |
| TC-VID-01 | Connect with valid VIDEO_WEBSOCKET token | Active VIDEO_WEBSOCKET token | WS connect to `ws://host/ws/video/<token>` | WebSocket connection established (101 Switching Protocols)      | High     |
| TC-VID-02 | Connect with invalid token               | —                            | WS connect with unknown token              | Connection rejected (close code 4001)                           | High     |
| TC-VID-03 | Connect with API-type token              | API token (wrong type)       | WS connect using API token in path         | Connection rejected                                             | High     |
| TC-VID-04 | Send frame and receive result            | WS connected                 | Send JPEG binary frame (≤5 MB)             | JSON response `{ plate_id, province, full_plate, format_flag }` | High     |
| TC-VID-05 | Frame too large                          | WS connected                 | Send frame > 5 MB                          | Connection closed with appropriate error code                   | Medium   |
| TC-VID-06 | Multiple frames in sequence              | WS connected                 | Send 10 frames at 1 fps                    | 10 independent JSON results received without error              | High     |
| TC-VID-07 | Graceful disconnect                      | WS connected                 | Client closes connection                   | Server cleans up task, no memory leak                           | Medium   |
| TC-VID-08 | Concurrent connections                   | Multiple tokens active       | 10 clients simultaneously stream           | All 10 connections receive independent results                  | Medium   |

---

### TC-RTSP — RTSP Stream Management

| ID         | Test Case                       | Precondition                       | Steps                                       | Expected Result                                        | Priority |
| ---------- | ------------------------------- | ---------------------------------- | ------------------------------------------- | ------------------------------------------------------ | -------- |
| TC-RTSP-01 | Add RTSP stream                 | User authenticated                 | POST `/streams` `{ name, rtsp_url }`        | 201, `{ stream_id, name, status:"stopped" }`           | High     |
| TC-RTSP-02 | Get all streams                 | Streams exist                      | GET `/streams`                              | 200, array of stream objects                           | High     |
| TC-RTSP-03 | Start stream                    | Stream in "stopped" state          | POST `/streams/{id}/start`                  | 200, status changes to "running"; capture task spawned | High     |
| TC-RTSP-04 | start already-running stream    | Stream already "running"           | POST `/streams/{id}/start` again            | 400 / 409 already running                              | Medium   |
| TC-RTSP-05 | Stop stream                     | Stream "running"                   | POST `/streams/{id}/stop`                   | 200, status changes to "stopped"; task cancelled       | High     |
| TC-RTSP-06 | Detection event logged          | Stream running, camera shows plate | Wait for detection cycle                    | Row inserted into detection_logs with plate data       | High     |
| TC-RTSP-07 | Web Viewer WebSocket            | Stream running                     | WS connect `ws://host/api/rtsp/stream/{id}` | Receives JPEG frames + overlay                         | Medium   |
| TC-RTSP-08 | Delete stream                   | Stream stopped                     | DELETE `/streams/{id}`                      | 200, stream removed from DB                            | High     |
| TC-RTSP-09 | Invalid RTSP URL                | —                                  | POST `/streams` with bad URL                | Stream created but fails gracefully on start           | Medium   |
| TC-RTSP-10 | Service restart resumes streams | DB has active streams              | Restart RTSP service                        | `startup_rtsp()` re-attaches active stream tasks       | Medium   |

---

### TC-SUB — Subscription Management

| ID        | Test Case                                | Precondition                 | Steps                                                               | Expected Result                                                       | Priority |
| --------- | ---------------------------------------- | ---------------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------- | -------- |
| TC-SUB-01 | Get all subscription plans               | Plans seeded in DB           | GET `/subscription/get_all_service`                                 | 200, list of Tier plans with `api_request_limit`, `token_limit`, etc. | High     |
| TC-SUB-02 | Purchase valid subscription              | User registered, plan exists | POST `/subscription/create_user_subscription` `{ user_id, sub_id }` | 200, subscription activated with `start_date` and `end_date`          | High     |
| TC-SUB-03 | Purchase invalid plan                    | —                            | POST with non-existent `sub_id`                                     | 404 Plan not found                                                    | Medium   |
| TC-SUB-04 | Purchase for non-existent user           | —                            | POST with invalid `user_id`                                         | 404 User not found                                                    | Medium   |
| TC-SUB-05 | View active subscription                 | User has subscription        | GET `/info/subscribe/{user_id}`                                     | 200, subscription details including quota and expiry                  | High     |
| TC-SUB-06 | Subscription quota limits token creation | Token limit = 3              | Create 4th token                                                    | 400 / 403 error                                                       | High     |
| TC-SUB-07 | Subscription quota limits API calls      | `api_request_limit` = 100    | Make 101st API call                                                 | 403 Quota exceeded                                                    | High     |
| TC-SUB-08 | Subscription with API access flag        | `has_api_access = false`     | Attempt image upload                                                | 403 Forbidden                                                         | Medium   |

---

### TC-AI — AI Plate Recognizer

| ID       | Test Case                      | Precondition       | Steps                                                        | Expected Result                                                                                   | Priority |
| -------- | ------------------------------ | ------------------ | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- | -------- |
| TC-AI-01 | Health check endpoint          | Service running    | GET `/readyz`                                                | 200, `{ message:"service is ready", cuda:<bool> }`                                                | High     |
| TC-AI-02 | Process clear Thai plate image | Service running    | POST `/api/v1/image/process` with clear plate image          | `format_flag = "complete"`, `plate_id` non-empty, `province` non-empty                            | High     |
| TC-AI-03 | Process image with no plate    | Service running    | POST with plain car photo (no visible plate)                 | `plate_id = null` or `format_flag = "no_plate"`                                                   | High     |
| TC-AI-04 | Skip car detection endpoint    | Service running    | POST `/api/v1/image/process/skip/car` with plate-region crop | Skips YOLOv11s step, still returns plate_id/province                                              | Medium   |
| TC-AI-05 | From-plate-crop endpoint       | Service running    | POST `/api/v1/image/process/from-plate-crop`                 | Returns plate_id/province from pre-cropped plate                                                  | Medium   |
| TC-AI-06 | Inference time performance     | Service running    | POST 10 sequential requests                                  | Average response ≤ 200 ms per request                                                             | Medium   |
| TC-AI-07 | Load balanced requests         | 2 replicas running | POST 20 concurrent requests                                  | Requests distributed across both replicas; all succeed                                            | Medium   |
| TC-AI-08 | Response structure validation  | Service running    | Inspect JSON response                                        | Contains `car_bbox`, `plate_bbox`, `plate_id`, `province`, `full_plate`, `format_flag`, `message` | High     |
| TC-AI-09 | Blurry / low-res image         | Service running    | POST with 50×30 px image                                     | Graceful response (no crash), `format_flag` reflects partial/fail                                 | Medium   |
| TC-AI-10 | Large image (10 MB)            | Service running    | POST with 10 MB JPEG                                         | Successful processing or 413 if over limit, no service crash                                      | Low      |

---

## Summary

| Category                   | Use Cases    | Sequence Diagrams | Test Cases |
| -------------------------- | ------------ | ----------------- | ---------- |
| Authentication             | 3            | 1                 | 11         |
| Token Management           | 7            | 1                 | 10         |
| Image Upload & Recognition | 5            | 1                 | 11         |
| WebSocket Video            | 3            | 1                 | 8          |
| RTSP Stream                | 4            | 1                 | 10         |
| Subscription               | 4            | 1                 | 8          |
| AI Engine                  | — (internal) | —                 | 10         |
| **Total**                  | **26**       | **6**             | **68**     |
