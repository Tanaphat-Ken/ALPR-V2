import { createSlice } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

import type { ServiceType } from '@/shared/types/subscription'

type TokensPageState = {
  isCreateModalOpen: boolean
  tokenToEdit: string | undefined
  tokenToDelete: string | undefined
  activeTab: ServiceType
}

const initialState: TokensPageState = { 
  isCreateModalOpen: false,
  tokenToEdit: undefined,
  tokenToDelete: undefined,
  activeTab: 'API'
}

const tokensPageSlice = createSlice({
  name: 'dashboard-tokens',
  initialState,
  reducers: {
    setIsCreateModalOpen: (state, action: PayloadAction<boolean>) => {
      state.isCreateModalOpen = action.payload
    },
    setTokenToEdit: (state, action: PayloadAction<TokensPageState['tokenToEdit']>) => {
      state.tokenToEdit = action.payload
    },
    setTokenToDelete: (state, action: PayloadAction<TokensPageState['tokenToDelete']>) => {
      state.tokenToDelete = action.payload
    },
    setActiveTab: (state, action: PayloadAction<ServiceType>) => {
      state.activeTab = action.payload
    }
  }
})

export const { 
  setIsCreateModalOpen, 
  setTokenToEdit,
  setTokenToDelete,
  setActiveTab 
} = tokensPageSlice.actions
export default tokensPageSlice