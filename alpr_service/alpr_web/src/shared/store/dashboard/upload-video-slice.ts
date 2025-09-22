import { createSlice } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

import type { ProcessedImage } from '@/shared/types/image'

type UploadVideoState = {
  video: string | null
  videoName: string 
  videoFramesCount: number
  processedFrames: number
  selectedTokenKey: string | null
  processedImageList: ProcessedImage[]
  isSending: boolean
}

const initialState: UploadVideoState = { 
  video: null,
  videoName: '',
  videoFramesCount: 0,
  processedFrames: 0,
  selectedTokenKey: null,
  processedImageList: [],
  isSending: false
}

const uploadVideoSlice = createSlice({
  name: 'dashboard-upload-video',
  initialState,
  reducers: {
    resetVideoUploadState: (state) => {
      return {
        ...initialState,
        processedImageList: state.processedImageList
      }
    },
    setUploadedVideo: (state, action: PayloadAction<string>) => {
      state.video = action.payload
    },
    setSelectedTokenKey: (state, action: PayloadAction<string>) => {
      state.selectedTokenKey = action.payload
    },
    appendProcessedImageList: (state, action: PayloadAction<ProcessedImage>) => {
      const newImageList = state.processedImageList
      newImageList.push(action.payload)
      state.processedImageList = newImageList
    },
    setVideoName: (state, action: PayloadAction<string>) => {
      state.videoName = action.payload
    },
    toggleIsPending: (state) => {
      state.isSending = !state.isSending
    },
    setVideoFrameCount: (state, action: PayloadAction<number>) => {
      state.videoFramesCount = action.payload
    },
    setProcessedFrames: (state, action: PayloadAction<number>) => {
      state.processedFrames = action.payload
    }
  }
})

export const { 
  setUploadedVideo, 
  setSelectedTokenKey, 
  appendProcessedImageList,
  setVideoName,
  toggleIsPending,
  resetVideoUploadState,
  setVideoFrameCount,
  setProcessedFrames
} = uploadVideoSlice.actions

export default uploadVideoSlice