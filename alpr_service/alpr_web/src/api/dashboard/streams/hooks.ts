// React Query Hooks สำหรับ Streams
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { message } from 'antd'
import { streamsAPI } from './requests'
import type { CreateStreamRequest, UpdateStreamRequest } from './types'

// ดูรายการกล้องทั้งหมด
export const useStreams = () => {
  return useQuery({
    queryKey: ['streams'],
    queryFn: streamsAPI.getAll,
    refetchInterval: 5000, // รีเฟรชทุก 5 วินาที เพื่อดู status
  })
}

// ดูข้อมูลกล้อง 1 ตัว
export const useStream = (cameraId: string) => {
  return useQuery({
    queryKey: ['stream', cameraId],
    queryFn: () => streamsAPI.getById(cameraId),
    enabled: !!cameraId,
  })
}

// ดูผลการจับภาพ
export const useDetections = (cameraId: string, limit: number = 20) => {
  return useQuery({
    queryKey: ['detections', cameraId, limit],
    queryFn: () => streamsAPI.getDetections(cameraId, limit),
    enabled: !!cameraId,
    refetchInterval: 3000, // รีเฟรชทุก 3 วินาที เพื่อดูผลล่าสุด
  })
}

// เปิดกล้อง
export const useStartStream = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (cameraId: string) => streamsAPI.start(cameraId),
    onSuccess: () => {
      message.success('Camera started successfully')
      queryClient.invalidateQueries({ queryKey: ['streams'] })
    },
    onError: (error: Error) => {
      message.error(`Failed to start camera: ${error.message}`)
    }
  })
}

// ปิดกล้อง
export const useStopStream = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (cameraId: string) => streamsAPI.stop(cameraId),
    onSuccess: () => {
      message.success('Camera stopped successfully')
      queryClient.invalidateQueries({ queryKey: ['streams'] })
    },
    onError: (error: Error) => {
      message.error(`Failed to stop camera: ${error.message}`)
    }
  })
}

// สร้างกล้องใหม่ (ยังไม่ทำงาน - รอ Backend)
export const useCreateStream = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateStreamRequest) => streamsAPI.create(data),
    onSuccess: () => {
      message.success('Camera created successfully')
      queryClient.invalidateQueries({ queryKey: ['streams'] })
    },
    onError: (error: Error) => {
      message.error(`Failed to create camera: ${error.message}`)
    }
  })
}

// อัปเดตกล้อง (ยังไม่ทำงาน - รอ Backend)
export const useUpdateStream = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ cameraId, data }: { cameraId: string, data: UpdateStreamRequest }) => 
      streamsAPI.update(cameraId, data),
    onSuccess: () => {
      message.success('Camera updated successfully')
      queryClient.invalidateQueries({ queryKey: ['streams'] })
    },
    onError: (error: Error) => {
      message.error(`Failed to update camera: ${error.message}`)
    }
  })
}

// ลบกล้อง (ยังไม่ทำงาน - รอ Backend)
export const useDeleteStream = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (cameraId: string) => streamsAPI.delete(cameraId),
    onSuccess: () => {
      message.success('Camera deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['streams'] })
    },
    onError: (error: Error) => {
      message.error(`Failed to delete camera: ${error.message}`)
    }
  })
}
