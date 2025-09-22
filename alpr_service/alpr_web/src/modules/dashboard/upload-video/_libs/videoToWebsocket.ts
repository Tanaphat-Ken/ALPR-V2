import { message } from 'antd'
import type { AppDispatch } from '@/shared/store'
import { appendProcessedImageList, setProcessedFrames } from '@/shared/store/dashboard/upload-video-slice'

let webSocketInstance: WebSocket | null = null

const initialWebSocketConnection = async (token: string): Promise<WebSocket> => {
  return new Promise((resolve, reject) => {
    const baseUrl = process.env.NEXT_PUBLIC_WEBSOCKET_VIDEO_HANLER || 'ws://localhost:5002/video'
    const ws = new WebSocket(`${baseUrl}/${token}`)
    ws.onopen = () => {
      message.info('Connected to Server')
      resolve(ws)
    }
    ws.onclose = () => { 
      message.error('Disconnected from Server')
    }
    ws.onerror = (error) => {
      message.error(`WebSocket Error: ${error}`)
      reject(error)
    }
  })
}

const closeWebSocketConnection = () => {
  if (webSocketInstance) {
    webSocketInstance.close()
    webSocketInstance = null
  }
}

const sendFramesOverWebSocket = async (video: HTMLVideoElement, ws: WebSocket) => {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')

  video.addEventListener('loadeddata', () => {
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    video.play()

    const captureFrame = async () => {
      if (video.currentTime >= video.duration) return
      if (ws.readyState !== WebSocket.OPEN) return

      ctx?.drawImage(video, 0, 0, canvas.width, canvas.height)
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.95))

      if (blob instanceof Blob) {
        const arrayBuffer = await blob.arrayBuffer()
        if (ws.readyState === WebSocket.OPEN) ws.send(new Uint8Array(arrayBuffer))
      }

      video.currentTime += 1 / 30
    }

    video.addEventListener('seeked', captureFrame)
    captureFrame()
  })

  video.load()
}

const videoToWebsocket = async (videoFile: File, token: string, dispatch: AppDispatch) => {
  try {
    webSocketInstance = await initialWebSocketConnection(token) 
    const video = document.createElement('video')
    video.src = URL.createObjectURL(videoFile)
    video.crossOrigin = 'anonymous'
    video.muted = true
    video.autoplay = false
    video.loop = false
    video.preload = 'auto'

    webSocketInstance.onmessage = async (data) => {
      const res = JSON.parse(data.data)
      if (res.frame_no) {
        dispatch(setProcessedFrames(parseInt(res.frame_no)))
      } else if (res.image) {
        dispatch(appendProcessedImageList({
          image: res.image,
          carBbox: res.car_bbox,
          plateBbox: res.plate_bbox,
          plateId: res.plate_id,
          province: res.province,
          timeStamp: new Date().toISOString()
        }))
      }
    }

    sendFramesOverWebSocket(video, webSocketInstance)
  } catch (error) {
    message.error(`WebSocket failed to connect: ${error}`)
  }
}

export { closeWebSocketConnection }
export default videoToWebsocket