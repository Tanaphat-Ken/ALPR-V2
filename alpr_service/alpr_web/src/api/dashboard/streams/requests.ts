// API Requests สำหรับ RTSP Streams
import type {
  Stream,
  StreamResponse,
  DetectionsResponse,
  CreateStreamRequest,
  UpdateStreamRequest
} from './types'

const RTSP_BASE_URL = process.env.NEXT_PUBLIC_RTSP_SERVICE_URL || 'http://localhost:5003/api/rtsp'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options)
  if (!res.ok) {
    const err = await res.text().catch(() => res.statusText)
    throw new Error(err || `Request failed: ${res.status}`)
  }
  return res.json()
}

export const streamsAPI = {
  // ดูรายการกล้องทั้งหมด
  getAll: async (): Promise<Stream[]> => {
    const data = await request<{ cameras: Stream[] }>(`${RTSP_BASE_URL}/cameras`)
    return data.cameras || []
  },

  // ดูข้อมูลกล้อง 1 ตัว
  getById: async (cameraId: string): Promise<StreamResponse> =>
    request<StreamResponse>(`${RTSP_BASE_URL}/cameras/${cameraId}`),

  // ดูผลการจับภาพของกล้อง
  getDetections: async (cameraId: string, limit = 20): Promise<DetectionsResponse> =>
    request<DetectionsResponse>(`${RTSP_BASE_URL}/cameras/${cameraId}/detections?limit=${limit}`),

  // เปิดกล้อง
  start: async (cameraId: string): Promise<void> =>
    request<void>(`${RTSP_BASE_URL}/cameras/${cameraId}/start`, { method: 'POST' }),

  // ปิดกล้อง
  stop: async (cameraId: string): Promise<void> =>
    request<void>(`${RTSP_BASE_URL}/cameras/${cameraId}/stop`, { method: 'POST' }),

  // สร้างกล้องใหม่
  create: async (data: CreateStreamRequest): Promise<Stream> =>
    request<Stream>(`${RTSP_BASE_URL}/cameras`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  // แก้ไขข้อมูลกล้อง
  update: async (cameraId: string, data: UpdateStreamRequest): Promise<Stream> =>
    request<Stream>(`${RTSP_BASE_URL}/cameras/${cameraId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  // ลบกล้อง
  delete: async (cameraId: string): Promise<void> =>
    request<void>(`${RTSP_BASE_URL}/cameras/${cameraId}`, { method: 'DELETE' }),
}
