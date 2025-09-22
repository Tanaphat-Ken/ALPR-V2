import { createSlice } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'
import type { ServiceType } from '@/shared/types/subscription'

type HomePageState = {
  activeService: ServiceType
}

const initialState: HomePageState = { 
  activeService: 'API'
}

const homePageSlice = createSlice({
  name: 'dashboard-home',
  initialState,
  reducers: {
    setActiveService: (state, action: PayloadAction<ServiceType>) => {
      state.activeService = action.payload
    }
  }
})

export const { setActiveService } = homePageSlice.actions
export default homePageSlice