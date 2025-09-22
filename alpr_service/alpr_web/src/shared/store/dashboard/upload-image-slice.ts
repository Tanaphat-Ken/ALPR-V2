import { createSlice } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

import type { ProcessedImage } from '@/shared/types/image'

const MAX_IMAGE_SIZE_MB = 50

type UploadImageState = {
  image: string | null
  imageSize: number
  imageName: string | null
  selectedTokenKey: string | null
  processedImageList: ProcessedImage[]
}

const initialState: UploadImageState = { 
  image: null,
  imageSize: 0,
  imageName: null,
  selectedTokenKey: null,
  processedImageList: []
}

const uploadImageSlice = createSlice({
  name: 'dashboard-upload-image',
  initialState,
  reducers: {
    resetUploadImageState: (state) => {
      return {
        ...initialState,
        processedImageList: state.processedImageList
      }
    },
    setSelectedTokenKey: (state, action: PayloadAction<string>) => {
      state.selectedTokenKey = action.payload
    },
    setImage: (state, action: PayloadAction<string>) => {
      state.image = action.payload
    },
    setImageSize: (state, action: PayloadAction<number>) => {
      if (action.payload <= MAX_IMAGE_SIZE_MB) {
        state.imageSize = action.payload
      }
    },
    setImageName: (state, action: PayloadAction<string>) => {
      state.imageName = action.payload
    },
    appendProcessedImageList: (state, action: PayloadAction<ProcessedImage>) => {
      const newImageList = state.processedImageList
      newImageList.push(action.payload)
      state.processedImageList = newImageList
    },
  }
})

export const { 
  setSelectedTokenKey, 
  setImage, 
  setImageSize, 
  setImageName, 
  appendProcessedImageList,
  resetUploadImageState
} = uploadImageSlice.actions

export default uploadImageSlice