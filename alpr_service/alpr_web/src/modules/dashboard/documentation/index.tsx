'use client'

import { Tag, Typography, Table, Card, Flex, Divider } from 'antd'
import {
    ApiOutlined,
    KeyOutlined,
    VideoCameraOutlined,
    CloudServerOutlined,
    SwapOutlined,
    SafetyCertificateOutlined,
    InfoCircleOutlined,
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography

// ─── Helpers ──────────────────────────────────────────────────────────────────

const METHOD_COLORS: Record<string, string> = {
    GET: '#1677ff',
    POST: '#52c41a',
    PUT: '#fa8c16',
    DELETE: '#ff4d4f',
    WS: '#722ed1',
}

const MethodBadge = ({ method }: { method: string }) => (
    <Tag
        style={{
            fontFamily: 'monospace',
            fontWeight: 700,
            fontSize: 12,
            borderRadius: 4,
            color: '#fff',
            backgroundColor: METHOD_COLORS[method] ?? '#666',
            border: 'none',
            padding: '2px 8px',
            lineHeight: '20px',
            minWidth: 60,
            textAlign: 'center',
        }}
    >
        {method}
    </Tag>
)

const EndpointRow = ({ method, path, description }: { method: string; path: string; description: string }) => (
    <Flex
        align="center"
        gap={12}
        style={{
            padding: '10px 16px',
            background: '#fafafa',
            border: '1px solid #e8e8e8',
            borderRadius: 8,
            marginBottom: 8,
        }}
    >
        <MethodBadge method={method} />
        <Text code style={{ fontSize: 13, flex: 1, marginInline: 0 }}>
            {path}
        </Text>
        <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'nowrap' }}>
            {description}
        </Text>
    </Flex>
)

const CodeBlock = ({ children }: { children: string }) => (
    <pre
        style={{
            background: '#1e1e2e',
            color: '#cdd6f4',
            borderRadius: 8,
            padding: '16px 20px',
            fontSize: 13,
            lineHeight: 1.6,
            overflowX: 'auto',
            margin: '12px 0',
            fontFamily: '"Fira Code", "Cascadia Code", monospace',
        }}
    >
        {children}
    </pre>
)

const SectionHeader = ({
    id,
    icon,
    title,
    subtitle,
}: {
    id: string
    icon: React.ReactNode
    title: string
    subtitle: string
}) => (
    <div id={id} style={{ paddingTop: 8, marginBottom: 24 }}>
        <Flex align="center" gap={10} style={{ marginBottom: 6 }}>
            <span style={{ fontSize: 22, color: '#1677ff' }}>{icon}</span>
            <Title level={3} style={{ margin: 0 }}>
                {title}
            </Title>
        </Flex>
        <Text type="secondary">{subtitle}</Text>
        <Divider style={{ marginTop: 14 }} />
    </div>
)

const paramsColumns = [
    { title: 'Name', dataIndex: 'name', key: 'name', render: (v: string) => <Text code>{v}</Text>, width: 160 },
    { title: 'Type', dataIndex: 'type', key: 'type', width: 100 },
    { title: 'Required', dataIndex: 'required', key: 'required', width: 90, render: (v: boolean) => v ? <Tag color="red">required</Tag> : <Tag>optional</Tag> },
    { title: 'Description', dataIndex: 'description', key: 'description' },
]

// ── Nav sidebar ───────────────────────────────────────────────────────────────

const NAV_ITEMS = [
    { id: 'overview', label: 'Overview', icon: <InfoCircleOutlined /> },
    { id: 'auth', label: 'Authentication', icon: <SafetyCertificateOutlined /> },
    { id: 'plate', label: 'Plate Recognition', icon: <SwapOutlined /> },
    { id: 'image-upload', label: 'Image Upload API', icon: <ApiOutlined /> },
    { id: 'ws-video', label: 'WebSocket — Video', icon: <VideoCameraOutlined /> },
    { id: 'rtsp', label: 'RTSP Streams', icon: <CloudServerOutlined /> },
    { id: 'tokens', label: 'Token Management', icon: <KeyOutlined /> },
    { id: 'subscription', label: 'Subscription', icon: <InfoCircleOutlined /> },
]

const DocNav = ({ activeId }: { activeId: string }) => (
    <div
        style={{
            width: 220,
            flexShrink: 0,
            position: 'sticky',
            top: 24,
            alignSelf: 'flex-start',
            background: '#fff',
            borderRadius: 8,
            border: '1px solid #f0f0f0',
            padding: '8px 0',
        }}
    >
        <div style={{ padding: '10px 16px 6px' }}>
            <Text strong style={{ fontSize: 11, letterSpacing: 1, textTransform: 'uppercase', color: '#888' }}>
                Contents
            </Text>
        </div>
        {NAV_ITEMS.map((item) => (
            <a
                key={item.id}
                href={`#${item.id}`}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '7px 16px',
                    fontSize: 13,
                    color: activeId === item.id ? '#1677ff' : '#444',
                    background: activeId === item.id ? '#e6f4ff' : 'transparent',
                    borderLeft: activeId === item.id ? '3px solid #1677ff' : '3px solid transparent',
                    textDecoration: 'none',
                    transition: 'all .15s',
                }}
            >
                {item.icon}
                {item.label}
            </a>
        ))}
    </div>
)

// ─── Main Component ───────────────────────────────────────────────────────────

const DashboardDocumentation = () => {
    return (
        <div style={{ padding: '24px 24px 48px', background: '#f5f5f5', minHeight: '100vh' }}>
            {/* Page title */}
            <div style={{ marginBottom: 32 }}>
                <Title level={1} style={{ margin: 0, fontSize: 28 }}>
                    API Documentation
                </Title>
                <Text type="secondary" style={{ fontSize: 14 }}>
                    ALPR V2 · Automatic License Plate Recognition System
                </Text>
            </div>

            <Flex gap={24} align="flex-start">
                {/* ── Left nav ── */}
                <DocNav activeId="" />

                {/* ── Content ── */}
                <div style={{ flex: 1, minWidth: 0 }}>

                    {/* ── OVERVIEW ── */}
                    <Card id="overview" style={{ marginBottom: 24 }}>
                        <SectionHeader
                            id="overview-title"
                            icon={<InfoCircleOutlined />}
                            title="Overview"
                            subtitle="Base URL, authentication model, and response format"
                        />
                        <Paragraph>
                            ALPR V2 is a microservices-based Automatic License Plate Recognition platform.
                            All HTTP services are exposed through an Nginx reverse proxy on port <Text code>80</Text>.
                        </Paragraph>

                        <Title level={5}>Base URLs</Title>
                        <Table
                            size="small"
                            pagination={false}
                            dataSource={[
                                { key: '1', service: 'General API', base: '/api/general/', internal: 'alpr-api-web-gateway:8092' },
                                { key: '2', service: 'Plate Recognition', base: '/api/v1/image/', internal: 'plate-recognizer:5000' },
                                { key: '3', service: 'Image Upload API', base: '/api/image/', internal: 'fastapi_image_container:8089' },
                                { key: '4', service: 'WebSocket — Video', base: 'ws://host/ws/video/', internal: 'video-handler:5000' },
                                { key: '5', service: 'RTSP Service', base: '/api/rtsp/', internal: 'alpr_rtsp_service:5003' },
                            ]}
                            columns={[
                                { title: 'Service', dataIndex: 'service', key: 'service', width: 200 },
                                { title: 'Public Path', dataIndex: 'base', key: 'base', render: (v: string) => <Text code>{v}</Text> },
                                { title: 'Internal Host', dataIndex: 'internal', key: 'internal', render: (v: string) => <Text type="secondary">{v}</Text> },
                            ]}
                        />

                        <Title level={5} style={{ marginTop: 20 }}>Standard Response Format</Title>
                        <Paragraph type="secondary">
                            All endpoints return JSON. Errors follow the pattern below.
                        </Paragraph>
                        <CodeBlock>{`// Success
{ "message": "...", "data": { ... } }

// Error
{ "detail": "error description" }         // FastAPI default
{ "detail": { "message": "..." } }        // Custom error`}
                        </CodeBlock>
                    </Card>

                    {/* ── AUTHENTICATION ── */}
                    <Card id="auth" style={{ marginBottom: 24 }}>
                        <SectionHeader
                            id="auth-title"
                            icon={<SafetyCertificateOutlined />}
                            title="Authentication"
                            subtitle="JWT-based authentication. Include the token in the Authorization header for protected routes."
                        />

                        <Paragraph>
                            Protected endpoints require a <Text code>Bearer</Text> token in the{' '}
                            <Text code>Authorization</Text> header:
                        </Paragraph>
                        <CodeBlock>{`Authorization: Bearer <your_jwt_token>`}</CodeBlock>

                        {/* Register */}
                        <Title level={5} style={{ marginTop: 24 }}>Register</Title>
                        <EndpointRow method="POST" path="/api/general/auth/register" description="Create a new account" />
                        <Title level={5} style={{ marginTop: 16, fontSize: 13, fontWeight: 600, color: '#555' }}>Request Body</Title>
                        <Table size="small" pagination={false} dataSource={[
                            { key: '1', name: 'email', type: 'string', required: true, description: 'Valid email address (must be unique)' },
                            { key: '2', name: 'password', type: 'string', required: true, description: 'Minimum 6 characters' },
                        ]} columns={paramsColumns} />
                        <CodeBlock>{`POST /api/general/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secret123"
}

// 201 Created
{
  "user_id": 42,
  "email": "user@example.com",
  "message": "User registered successfully"
}`}</CodeBlock>

                        {/* Login */}
                        <Divider />
                        <Title level={5}>Login</Title>
                        <EndpointRow method="POST" path="/api/general/auth/login" description="Obtain a JWT token" />
                        <Table size="small" pagination={false} dataSource={[
                            { key: '1', name: 'email', type: 'string', required: true, description: 'Registered email address' },
                            { key: '2', name: 'password', type: 'string', required: true, description: 'User password' },
                        ]} columns={paramsColumns} style={{ marginTop: 12 }} />
                        <CodeBlock>{`POST /api/general/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secret123"
}

// 200 OK
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user_id": 42,
  "email": "user@example.com",
  "message": "Login successful"
}`}</CodeBlock>

                        {/* Get me */}
                        <Divider />
                        <Title level={5}>Get Current User</Title>
                        <EndpointRow method="GET" path="/api/general/auth/me" description="Returns authenticated user info" />
                        <Paragraph type="secondary" style={{ fontSize: 12, marginTop: 8 }}>
                            Requires: <Text code>Authorization: Bearer &lt;token&gt;</Text>
                        </Paragraph>
                        <CodeBlock>{`GET /api/general/auth/me
Authorization: Bearer <token>

// 200 OK
{
  "user_id": 42,
  "email": "user@example.com"
}`}</CodeBlock>
                    </Card>

                    {/* ── PLATE RECOGNITION ── */}
                    <Card id="plate" style={{ marginBottom: 24 }}>
                        <SectionHeader
                            id="plate-title"
                            icon={<SwapOutlined />}
                            title="Plate Recognition API"
                            subtitle="Direct access to the AI inference engine. No token required (internal/load-balanced)."
                        />
                        <Paragraph>
                            The plate recognizer runs two YOLOv11 models plus MobileNetV3 and a CTC/CRNN OCR reader.
                            Responses include bounding boxes, plate text, and province classification.
                        </Paragraph>

                        {/* /process */}
                        <Title level={5}>Process Image</Title>
                        <EndpointRow method="POST" path="/api/v1/image/process" description="Full pipeline — auto-detect car then plate" />
                        <Table size="small" pagination={false} dataSource={[
                            { key: '1', name: 'file', type: 'file (multipart)', required: true, description: 'Image file (JPEG / PNG / BMP / WEBP, max 10 MB)' },
                        ]} columns={paramsColumns} style={{ marginTop: 12 }} />
                        <CodeBlock>{`POST /api/v1/image/process
Content-Type: multipart/form-data

file: <image_file>

// 200 OK
{
  "car_bbox": null,
  "plate_bbox": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]],
  "plate_id": "1ฒว8052",
  "province": "ชลบุรี",
  "full_plate": "1ฒว8052 ชลบุรี",
  "format_flag": "complete",
  "message": "OK"
}`}</CodeBlock>

                        {/* /process/skip/car */}
                        <Divider />
                        <Title level={5}>Process — Skip Car Detection</Title>
                        <EndpointRow method="POST" path="/api/v1/image/process/skip/car" description="Skip car detector when bbox is already known" />
                        <Table size="small" pagination={false} dataSource={[
                            { key: '1', name: 'file', type: 'file (multipart)', required: true, description: 'Full image file' },
                            { key: '2', name: 'car_bbox', type: 'JSON array', required: true, description: '[x1, y1, x2, y2] bounding box of the car' },
                        ]} columns={paramsColumns} style={{ marginTop: 12 }} />
                        <CodeBlock>{`POST /api/v1/image/process/skip/car
Content-Type: multipart/form-data

file: <image_file>
car_bbox: [100, 80, 640, 480]`}</CodeBlock>

                        {/* /process/from-plate-crop */}
                        <Divider />
                        <Title level={5}>Process — From Plate Crop</Title>
                        <EndpointRow method="POST" path="/api/v1/image/process/from-plate-crop" description="Run OCR on a pre-cropped plate image" />
                        <Table size="small" pagination={false} dataSource={[
                            { key: '1', name: 'file', type: 'file (multipart)', required: true, description: 'Already-cropped plate image' },
                        ]} columns={paramsColumns} style={{ marginTop: 12 }} />
                        <CodeBlock>{`POST /api/v1/image/process/from-plate-crop
Content-Type: multipart/form-data

file: <cropped_plate_image>

// 200 OK
{
  "plate_id": "8052",
  "province": "ชลบุรี",
  "full_plate": "8052 ชลบุรี",
  "format_flag": "partial",
  "message": "OK"
}`}</CodeBlock>

                        {/* Health Check */}
                        <Divider />
                        <Title level={5}>Health Check</Title>
                        <EndpointRow method="GET" path="/api/v1/image/readyz" description="Service liveness probe" />
                        <CodeBlock>{`GET /readyz

// 200 OK
{ "message": "service is ready", "cuda": false }`}</CodeBlock>
                    </Card>

                    {/* ── IMAGE UPLOAD API ── */}
                    <Card id="image-upload" style={{ marginBottom: 24 }}>
                        <SectionHeader
                            id="image-upload-title"
                            icon={<ApiOutlined />}
                            title="Image Upload API"
                            subtitle="Authenticated image processing with quota management + persistent logging."
                        />
                        <Paragraph>
                            Requires a valid API token passed via the <Text code>Authorization</Text> header.
                            The service validates the token against the database, deducts quota, calls the plate
                            recognizer, and stores a structured log.
                        </Paragraph>

                        <EndpointRow method="POST" path="/api/image/upload-image" description="Process and log an image using an API token" />
                        <Table size="small" pagination={false} dataSource={[
                            { key: '1', name: 'file', type: 'file (multipart)', required: true, description: 'Image file (JPEG / PNG, max 10 MB)' },
                            { key: '2', name: 'Authorization', type: 'header', required: true, description: 'Bearer <api_token> (API service token from Token Management)' },
                        ]} columns={paramsColumns} style={{ marginTop: 12 }} />
                        <CodeBlock>{`POST /api/image/upload-image
Authorization: Bearer <api_token>
Content-Type: multipart/form-data

file: <image_file>

// 200 OK
{
  "plate_id": "1ฒว8052",
  "province": "ชลบุรี",
  "full_plate": "1ฒว8052 ชลบุรี",
  "format_flag": "complete",
  "message": "OK"
}`}</CodeBlock>
                    </Card>

                    {/* ── WEBSOCKET VIDEO ── */}
                    <Card id="ws-video" style={{ marginBottom: 24 }}>
                        <SectionHeader
                            id="ws-video-title"
                            icon={<VideoCameraOutlined />}
                            title="WebSocket — Video"
                            subtitle="Real-time video frame processing. Send individual frames, receive per-frame plate results."
                        />
                        <Paragraph>
                            The token is embedded directly in the WebSocket URL path.
                            Frames should be sent as browser <Text code>Blob</Text> / binary data.
                        </Paragraph>

                        <EndpointRow method="WS" path="ws://host/ws/video/{token}" description="Video frame streaming session" />
                        <Table size="small" pagination={false} dataSource={[
                            { key: '1', name: 'token', type: 'path param', required: true, description: 'VIDEO_WEBSOCKET-type service token' },
                        ]} columns={paramsColumns} style={{ marginTop: 12 }} />
                        <CodeBlock>{`// Connect — token in path
const token = "my_video_token"
const ws = new WebSocket(\`ws://host/ws/video/\${token}\`)

// Send a video frame as ArrayBuffer
ws.send(frameArrayBuffer)

// Receive detection result per frame
ws.onmessage = (event) => {
  const result = JSON.parse(event.data)
  /*
  {
    "plates": [
      { "plate_id": "กข1234", "province": "กรุงเทพมหานคร", "bbox": [...] }
    ],
    "frame_id": 42,
    "timestamp": "2026-02-19T10:00:00"
  }
  */
}`}</CodeBlock>
                        <Paragraph type="secondary" style={{ fontSize: 12 }}>
                            Max frame size: <Text code>5 MB</Text>.
                        </Paragraph>
                    </Card>

                    {/* ── RTSP ── */}
                    <Card id="rtsp" style={{ marginBottom: 24 }}>
                        <SectionHeader
                            id="rtsp-title"
                            icon={<CloudServerOutlined />}
                            title="RTSP Streams"
                            subtitle="Manage IP camera RTSP streams with automatic license plate detection and recording."
                        />
                        <Paragraph>
                            All RTSP endpoints are proxied through <Text code>/api/rtsp/</Text>.
                            Stream viewer WebSocket is on <Text code>/api/rtsp/stream/</Text> (upgraded by Nginx).
                        </Paragraph>

                        <EndpointRow method="GET" path="/api/rtsp/streams" description="List all registered RTSP streams" />
                        <EndpointRow method="POST" path="/api/rtsp/streams" description="Register a new RTSP stream" />
                        <EndpointRow method="GET" path="/api/rtsp/streams/{id}" description="Get detail of a single stream" />
                        <EndpointRow method="PUT" path="/api/rtsp/streams/{id}" description="Update stream configuration" />
                        <EndpointRow method="DELETE" path="/api/rtsp/streams/{id}" description="Remove a stream" />
                        <EndpointRow method="POST" path="/api/rtsp/streams/{id}/start" description="Start streaming / detection" />
                        <EndpointRow method="POST" path="/api/rtsp/streams/{id}/stop" description="Stop streaming" />
                        <EndpointRow method="WS" path="ws://host/api/rtsp/stream/{id}" description="Live viewer WebSocket" />

                        <CodeBlock>{`// Register a new stream
POST /api/rtsp/streams
Content-Type: application/json

{
  "name": "Parking Lot A",
  "rtsp_url": "rtsp://192.168.1.100:554/stream1",
  "description": "Main entrance camera"
}

// 201 Created
{
  "id": 1,
  "name": "Parking Lot A",
  "rtsp_url": "rtsp://192.168.1.100:554/stream1",
  "status": "stopped"
}`}</CodeBlock>
                    </Card>

                    {/* ── TOKENS ── */}
                    <Card id="tokens" style={{ marginBottom: 24 }}>
                        <SectionHeader
                            id="tokens-title"
                            icon={<KeyOutlined />}
                            title="Token Management"
                            subtitle="Create and manage service tokens used to authenticate API, WebSocket, and Video requests."
                        />
                        <Paragraph>
                            Tokens are scoped to a <Text code>service_type</Text>:{' '}
                            <Tag color="cyan">API</Tag>
                            <Tag color="purple">VIDEO_WEBSOCKET</Tag>
                            <Tag color="red">RTSP</Tag>
                        </Paragraph>

                        <EndpointRow method="GET" path="/api/general/tokens/{user_id}?service_type=API" description="List tokens for a user" />
                        <EndpointRow method="POST" path="/api/general/tokens" description="Create a new token" />
                        <EndpointRow method="PUT" path="/api/general/tokens" description="Rename or update expiry" />
                        <EndpointRow method="DELETE" path="/api/general/tokens" description="Delete a token by key" />

                        <CodeBlock>{`// Create API token
POST /api/general/tokens
Content-Type: application/json

{
  "user_id": 42,
  "service_type": "API",          // API | VIDEO_WEBSOCKET | RTSP
  "token_name": "My API Token",
  "expire_time": "2026-12-31T00:00:00"  // optional, defaults to +30 days
}

// 200 OK
{
  "key": "tk_abc123...",
  "token_name": "My API Token",
  "service_type": "API",
  "user_id": 42,
  "expire_time": "2026-12-31T00:00:00",
  "is_active": true
}

// Delete token
DELETE /api/general/tokens
Content-Type: application/json

{ "key": "tk_abc123..." }`}</CodeBlock>
                    </Card>

                    {/* ── SUBSCRIPTION ── */}
                    <Card id="subscription" style={{ marginBottom: 24 }}>
                        <SectionHeader
                            id="subscription-title"
                            icon={<InfoCircleOutlined />}
                            title="Subscription"
                            subtitle="Query active subscriptions, quotas, and service access flags for a user."
                        />

                        <EndpointRow method="GET" path="/api/general/info/subscribe/{user_id}" description="Get all subscriptions for a user" />
                        <EndpointRow method="GET" path="/api/general/info/user/{user_id}" description="Get user profile info" />
                        <EndpointRow method="GET" path="/api/general/subscription" description="List available subscription plans" />

                        <CodeBlock>{`GET /api/general/info/subscribe/42

// 200 OK
{
  "user_id": 42,
  "subscriptions": [
    {
      "user_sub_id": 5,
      "is_activate": true,
      "start_date": "2026-01-01",
      "end_date": "2026-12-31",
      "request_quota": 980,
      "subscription_details": {
        "sub_id": 2,
        "billing_period": "monthly",
        "service_type": "Tier 1",
        "price": 299.00,
        "api_request_limit": 1000,
        "video_upload_limit": null,
        "has_api_access": true,
        "has_websocket_access": false,
        "has_video_upload": false,
        "has_rtsp_stream": false
      }
    }
  ]
}`}</CodeBlock>
                    </Card>

                    {/* ── Error Codes ── */}
                    <Card style={{ marginBottom: 24 }}>
                        <Title level={4} style={{ marginBottom: 16 }}>Common HTTP Status Codes</Title>
                        <Table
                            size="small"
                            pagination={false}
                            dataSource={[
                                { key: '200', code: '200 OK', desc: 'Request succeeded' },
                                { key: '201', code: '201 Created', desc: 'Resource created successfully' },
                                { key: '400', code: '400 Bad Request', desc: 'Invalid parameters or file type' },
                                { key: '401', code: '401 Unauthorized', desc: 'Missing or invalid authentication token' },
                                { key: '403', code: '403 Forbidden', desc: 'Token exists but lacks permission (wrong service type)' },
                                { key: '404', code: '404 Not Found', desc: 'Resource not found' },
                                { key: '413', code: '413 Payload Too Large', desc: 'Image / frame exceeds size limit' },
                                { key: '429', code: '429 Too Many Requests', desc: 'API quota exhausted' },
                                { key: '500', code: '500 Internal Server Error', desc: 'Unexpected server error' },
                            ]}
                            columns={[
                                { title: 'Code', dataIndex: 'code', key: 'code', width: 200, render: (v: string) => <Text code>{v}</Text> },
                                { title: 'Description', dataIndex: 'desc', key: 'desc' },
                            ]}
                        />
                    </Card>

                </div>
            </Flex>
        </div>
    )
}

export default DashboardDocumentation
