import { createSlice } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

type UserState = {
  userId: number,
  email: string,
  createdAt: string,
  updatedAt: string
}

const initialState: UserState = { 
  userId: 0,
  email: '',
  createdAt: '',
  updatedAt: ''
}

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setUser: (_, action: PayloadAction<UserState>) => {
      return action.payload
    }
  }
})

export type { UserState }
export const { setUser } = userSlice.actions
export default userSlice