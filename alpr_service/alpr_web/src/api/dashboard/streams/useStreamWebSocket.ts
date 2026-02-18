import { useEffect, useRef, useState } from 'react'

interface StreamFrame {
  type: 'frame'
  camera_id: string
  frame_count: number
  image: string // Base64 data URL
}

interface StreamInfo {
  type: 'info'
  camera: {
    id: string
    name: string
    location?: string
  }
}

interface StreamDetection {
  type: 'detection'
  camera_id: string
  timestamp: string
  plate_id?: string
  province?: string
  full_plate?: string
  plate_image?: string
}

type StreamMessage = StreamFrame | StreamInfo | StreamDetection

interface UseStreamWebSocketOptions {
  cameraId: string
  onFrame?: (frame: StreamFrame) => void
  onDetection?: (detection: StreamDetection) => void
  onInfo?: (info: StreamInfo) => void
  enabled?: boolean
}

interface UseStreamWebSocketReturn {
  isConnected: boolean
  isConnecting: boolean
  error: string | null
  lastFrame: string | null
  reconnect: () => void
}

export const useStreamWebSocket = ({
  cameraId,
  onFrame,
  onDetection,
  onInfo,
  enabled = true
}: UseStreamWebSocketOptions): UseStreamWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastFrame, setLastFrame] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const reconnectAttemptsRef = useRef(0)
  
  const MAX_RECONNECT_ATTEMPTS = 5
  const RECONNECT_DELAY = 3000

  const connect = () => {
    if (!enabled || !cameraId) return
    
    // ปิด connection เดิม (ถ้ามี)
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    try {
      setIsConnecting(true)
      setError(null)
      
      const wsUrl = `ws://localhost:5003/api/v1/stream/${cameraId}`
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        console.log(`[WebSocket] Connected to camera: ${cameraId}`)
        setIsConnected(true)
        setIsConnecting(false)
        setError(null)
        reconnectAttemptsRef.current = 0
      }
      
      ws.onmessage = (event) => {
        try {
          const message: StreamMessage = JSON.parse(event.data)
          
          switch (message.type) {
          case 'frame':
            setLastFrame(message.image)
            onFrame?.(message)
            break
            
          case 'info':
            console.log('[WebSocket] Camera info:', message.camera)
            onInfo?.(message)
            break
            
          case 'detection':
            console.log('[WebSocket] Detection:', message.plate_id)
            onDetection?.(message)
            break
            
          default:
            console.warn('[WebSocket] Unknown message type:', message)
          }
        } catch (err) {
          console.error('[WebSocket] Failed to parse message:', err)
        }
      }
      
      ws.onerror = (event) => {
        console.error('[WebSocket] Error:', event)
        setError('WebSocket connection error')
        setIsConnecting(false)
      }
      
      ws.onclose = (event) => {
        console.log(`[WebSocket] Disconnected from camera: ${cameraId}`, event.code, event.reason)
        setIsConnected(false)
        setIsConnecting(false)
        wsRef.current = null
        
        // Auto reconnect ถ้ายังไม่เกินจำนวนครั้งที่กำหนด
        if (enabled && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current++
          console.log(`[WebSocket] Reconnecting... (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`)
          setError(`Reconnecting... (${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, RECONNECT_DELAY)
        } else if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
          setError('Failed to connect. Please check if the camera is running.')
        }
      }
      
      wsRef.current = ws
      
    } catch (err) {
      console.error('[WebSocket] Connection failed:', err)
      setError('Failed to create WebSocket connection')
      setIsConnecting(false)
    }
  }

  const reconnect = () => {
    reconnectAttemptsRef.current = 0
    connect()
  }

  useEffect(() => {
    if (enabled && cameraId) {
      connect()
    }
    
    return () => {
      // Cleanup
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [cameraId, enabled])

  return {
    isConnected,
    isConnecting,
    error,
    lastFrame,
    reconnect
  }
}
