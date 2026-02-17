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
  full_image_url?: string
  car_image_url?: string
  plate_image_url?: string
  plate_id?: string
  province?: string
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
