// Types สำหรับ RTSP Streams

export type StreamStatus = 'connected' | 'disconnected' | 'error'

export interface Stream {
  id: string
  name: string
  rtsp_url: string
  location?: string
  enabled: boolean
  running?: boolean
  fps?: number
  frame_skip?: number
}

export interface StreamDetection {
  id: string
  camera_id: string
  timestamp: string
  full_image?: string // Base64 encoded full frame (resized to 480px width)
  car_image_url?: string
  plate_image_url?: string
  plate_image?: string // Base64 encoded plate crop
  plate_id?: string
  full_plate?: string // ป้ายทะเบียนเต็ม เช่น "กก-1234"
  province?: string
  format_flag?: string // รูปแบบป้าย เช่น "new", "old"
  confidence?: number
}

export interface StreamResponse {
  id: string
  name: string
  location?: string
  enabled: boolean
  running: boolean
}

export interface DetectionsResponse {
  camera_id: string
  total: number
  detections: StreamDetection[]
}

export interface CreateStreamRequest {
  name: string
  rtsp_url: string
  location?: string
  enabled?: boolean
  fps?: number
  frame_skip?: number
}

export interface UpdateStreamRequest {
  name?: string
  rtsp_url?: string
  location?: string
  enabled?: boolean
  fps?: number
  frame_skip?: number
}
