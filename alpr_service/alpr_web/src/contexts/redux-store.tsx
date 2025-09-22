'use client'

import { useRef } from 'react'
import { store, AppStore } from '@/shared/store'
import { Provider } from 'react-redux'

const ReduxStoreProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const storeRef = useRef<AppStore>()
  if (!storeRef.current) {
    storeRef.current = store()
  }

  return <Provider store={storeRef.current}>{children}</Provider>
}

export default ReduxStoreProvider