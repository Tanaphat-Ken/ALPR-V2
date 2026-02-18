// Redux Store สำหรับ Streams Page
import { createSlice } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

type StreamsPageState = {
  isCreateModalOpen: boolean
  streamToEdit: string | undefined
  streamToDelete: string | undefined
  selectedStreamId: string | null
}

const initialState: StreamsPageState = { 
  isCreateModalOpen: false,
  streamToEdit: undefined,
  streamToDelete: undefined,
  selectedStreamId: null
}

const streamsPageSlice = createSlice({
  name: 'streams-page',
  initialState,
  reducers: {
    setIsCreateModalOpen: (state, action: PayloadAction<boolean>) => {
      state.isCreateModalOpen = action.payload
    },
    setStreamToEdit: (state, action: PayloadAction<StreamsPageState['streamToEdit']>) => {
      state.streamToEdit = action.payload
    },
    setStreamToDelete: (state, action: PayloadAction<StreamsPageState['streamToDelete']>) => {
      state.streamToDelete = action.payload
    },
    setSelectedStreamId: (state, action: PayloadAction<string | null>) => {
      state.selectedStreamId = action.payload
    }
  }
})

export const { 
  setIsCreateModalOpen, 
  setStreamToEdit,
  setStreamToDelete,
  setSelectedStreamId
} = streamsPageSlice.actions

export default streamsPageSlice
