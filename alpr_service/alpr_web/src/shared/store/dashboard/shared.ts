import { createSlice } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

type SharedState = {
  modalErrorMsg: string
}

const initialState: SharedState = { 
  modalErrorMsg: ''
}

const sharedStateSlice = createSlice({
  name: 'shared',
  initialState,
  reducers: {
    setModalErrorMsg: (state, action: PayloadAction<string>) => {
      state.modalErrorMsg = action.payload
    }
  }
})

export const { setModalErrorMsg } = sharedStateSlice.actions
export default sharedStateSlice