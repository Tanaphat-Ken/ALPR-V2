import { configureStore } from '@reduxjs/toolkit'

import userSlice from './dashboard/user-slice'
import homePageSlice from './dashboard/home-page-slice'
import tokensPageSlice from './dashboard/tokens-page-slice'
import sharedStateSlice from './dashboard/shared'
import uploadImageSlice from './dashboard/upload-image-slice'
import uploadVideoSlice from './dashboard/upload-video-slice'
import streamsPageSlice from './dashboard/streams-page-slice'

export const store = () => {
  return configureStore({
    reducer: {
      sharedState: sharedStateSlice.reducer,
      user: userSlice.reducer,
      homePageSlice: homePageSlice.reducer,
      tokensPage: tokensPageSlice.reducer,
      uploadImagePage: uploadImageSlice.reducer,
      uploadVideoPage: uploadVideoSlice.reducer,
      streamsPage: streamsPageSlice.reducer
    }
  })
}

export type AppStore = ReturnType<typeof store>
export type RootState = ReturnType<AppStore['getState']>
export type AppDispatch = AppStore['dispatch']