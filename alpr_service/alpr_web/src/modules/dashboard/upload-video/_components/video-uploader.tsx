'use client'

import { useDispatch, useSelector } from 'react-redux'
import type { UploadProps } from 'antd'
import { Flex, message, Upload, Spin, Progress } from 'antd'
import { LoadingOutlined } from '@ant-design/icons'
import { CloudUploadOutlined } from '@ant-design/icons'
import { fileToBase64 } from '@/shared/libs/file'

import type { AppDispatch, RootState } from '@/shared/store'
import type { FileType } from '@/shared/types/file'
import { setUploadedVideo, setVideoName, setVideoFrameCount } from '@/shared/store/dashboard/upload-video-slice'

const { Dragger } = Upload

const getVideoFrameCount = (file: File): Promise<number | null> => {
  return new Promise((resolve) => {
    const video = document.createElement('video')
    video.preload = 'auto'
    video.src = URL.createObjectURL(file)
    video.muted = true
    video.playsInline = true

    let frameCount = 0
    let startTime = 0

    const onFrame = (_now: number, _metadata: VideoFrameCallbackMetadata) => {
      frameCount++
      if (performance.now() - startTime < 1000) {
        video.requestVideoFrameCallback(onFrame)
      } else {
        video.pause()
        const estimatedFPS = frameCount / ((performance.now() - startTime) / 1000)
        const totalFrames = estimatedFPS * video.duration
        URL.revokeObjectURL(video.src)
        resolve(Math.round(totalFrames))
      }
    }

    video.onloadedmetadata = () => {
      if (!video.duration || isNaN(video.duration)) {
        resolve(null)
        return
      }

      startTime = performance.now()
      video.play().then(() => {
        if ('requestVideoFrameCallback' in HTMLVideoElement.prototype) {
          video.requestVideoFrameCallback(onFrame)
        } else {
          console.warn('requestVideoFrameCallback not supported in this browser.')
          resolve(null)
        }
      }).catch(() => resolve(null))
    }

    video.onerror = () => resolve(null)
  })
}

const getProcessingProgress = (processedFrames: number, totalFrames: number): number => {
  if (totalFrames === 0) return 0
  return Math.min(100, Math.round((processedFrames / totalFrames) * 100))
}

const VideoUploader = () => {
  const dispatch = useDispatch<AppDispatch>()
  const isSending = useSelector((state: RootState) => state.uploadVideoPage.isSending)
  const videoFrameCount = useSelector((state: RootState) => state.uploadVideoPage.videoFramesCount)
  const processedFrame = useSelector((state: RootState) => state.uploadVideoPage.processedFrames)
  const handleOnChange: UploadProps['onChange'] = async ({ file, fileList }) => {
    if (file && fileList.length) {
      const frameCount = await getVideoFrameCount(file as FileType)
      const base64Video = await fileToBase64(file as FileType)
      dispatch(setUploadedVideo(base64Video))
      dispatch(setVideoName(file.name))
      dispatch(setVideoFrameCount(frameCount ? frameCount : 0))
    }
  }

  const beforeUpload: UploadProps['beforeUpload'] = (file) => {
    const isVideo = file.type.startsWith('video/')
    if (!isVideo) {
      message.error('You can only upload video files!')
      return Upload.LIST_IGNORE
    }
    return false
  }

  return (
    <Flex vertical align='center' style={{ height: 300 }}>
      <div style={{ height: 270 }}>
        {isSending ? 
          (
            <div>
              <Flex vertical align='center' justify='center' style={{ marginTop: 92 }}>
                <Spin indicator={<LoadingOutlined style={{ fontSize: 64 }} />} />
                <p>Processing Video Frames...</p>
              </Flex>

              <Progress percent={getProcessingProgress(processedFrame, videoFrameCount)} status="active" />
            </div>

          ) :
          (
            <Dragger 
              style={{ width: 460 }} 
              maxCount={1} 
              onChange={handleOnChange} 
              beforeUpload={beforeUpload}
            >
              <p className='ant-upload-drag-icon'>
                <CloudUploadOutlined />
              </p>
              <p className="ant-upload-text">Click or drag video file to upload</p>
              <p className="ant-upload-hint">MP4, AVI, MKV</p>
            </Dragger>
          )
        }
      </div>
    </Flex>
  )
}

export default VideoUploader