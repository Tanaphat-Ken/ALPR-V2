// API Requests สำหรับ RTSP Streams
import apiClient from '@/shared/libs/apiClient'
import type { 
  Stream, 
  StreamResponse, 
  DetectionsResponse,
  CreateStreamRequest,
  UpdateStreamRequest 
} from './types'

const RTSP_BASE_URL = process.env.NEXT_PUBLIC_RTSP_SERVICE_URL || 'http://localhost:5003/api/v1'

// ✅ API ที่มีอยู่แล้ว (Read-Only)
export const streamsAPI = {
  // ดูรายการกล้องทั้งหมด
  getAll: async (): Promise<Stream[]> => {
    const response = await fetch(`${RTSP_BASE_URL}/cameras`)
    if (!response.ok) throw new Error('Failed to fetch cameras')
    return response.json()
  },

  // ดูข้อมูลกล้อง 1 ตัว
  getById: async (cameraId: string): Promise<StreamResponse> => {
    const response = await fetch(`${RTSP_BASE_URL}/cameras/${cameraId}`)
    if (!response.ok) throw new Error('Failed to fetch camera')
    return response.json()
  },

  // ดูผลการจับภาพของกล้อง
  getDetections: async (cameraId: string, limit: number = 20): Promise<DetectionsResponse> => {
    const response = await fetch(`${RTSP_BASE_URL}/cameras/${cameraId}/detections?limit=${limit}`)
    if (!response.ok) throw new Error('Failed to fetch detections')
    return response.json()
  },

  // เปิดกล้อง
  start: async (cameraId: string): Promise<void> => {
    const response = await fetch(`${RTSP_BASE_URL}/cameras/${cameraId}/start`, {
      method: 'POST'
    })
    if (!response.ok) throw new Error('Failed to start camera')
  },

  // ปิดกล้อง
  stop: async (cameraId: string): Promise<void> => {
    const response = await fetch(`${RTSP_BASE_URL}/cameras/${cameraId}/stop`, {
      method: 'POST'
    })
    if (!response.ok) throw new Error('Failed to stop camera')
  },

  // ⏭️ API เหล่านี้ยังไม่มีใน Backend (ต้องเพิ่มทีหลัง)
  create: async (data: CreateStreamRequest): Promise<Stream> => {
    // TODO: รอ Backend เพิ่ม API
    throw new Error('Not implemented yet')
  },

  update: async (cameraId: string, data: UpdateStreamRequest): Promise<Stream> => {
    // TODO: รอ Backend เพิ่ม API
    throw new Error('Not implemented yet')
  },

  delete: async (cameraId: string): Promise<void> => {
    // TODO: รอ Backend เพิ่ม API
    throw new Error('Not implemented yet')
  }
}
