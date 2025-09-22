'use client'

import { useState } from 'react'

import { useSelector, useDispatch } from 'react-redux'
import { Flex, Select, Button } from 'antd'

import type { RootState, AppDispatch } from '@/shared/store'
import { useTokens } from '@/api/dashboard/token/hooks'
import { isExpired } from '@/shared/libs/times'
import { base64ToFile } from '@/shared/libs/file'
import videoToWebsocket, { closeWebSocketConnection } from '../_libs/videoToWebsocket'
import { toggleIsPending, resetVideoUploadState } from '@/shared/store/dashboard/upload-video-slice'

const SubmitButton = () => {
  const dispatch = useDispatch<AppDispatch>()
  const userId = useSelector((state: RootState) => state.user.userId)
  const uploadedVideo = useSelector((state: RootState) => state.uploadVideoPage.video)
  const isSending = useSelector((state: RootState) => state.uploadVideoPage.isSending)
  const videoName = useSelector((state: RootState) => state.uploadVideoPage.videoName)
  const [selectedToken, setSelectedToken] = useState<string>()
  const { data: tokenList } = useTokens(userId, 'VIDEO_WEBSOCKET') // temporary service name

  const tokenOptionList = tokenList
    ?.map(item => {
      if (!isExpired(item.expireDate)) {
        return { value: item.tokenKey, label: item.tokenName }
      }
      return undefined
    })
    .filter((option) => option !== undefined)

  const handleOnClick = () => {
    if (uploadedVideo && selectedToken && !isSending) {
      const videoFile = base64ToFile(uploadedVideo, videoName, 'video')
      videoToWebsocket(videoFile, selectedToken, dispatch)
    } else {
      closeWebSocketConnection()
      resetVideoUploadState()
    }
    dispatch(toggleIsPending())
  }

  return (
    <Flex align="center" justify="center" gap={16} style={{ marginTop: 16 }}>
      <Select 
        placeholder="Please Select Token" 
        style={{ width: 200 }} 
        options={tokenOptionList} 
        onChange={(value: string) => setSelectedToken(value)}
      />
      <Button 
        type='primary' 
        danger={isSending ? true : false}
        disabled={selectedToken && uploadedVideo ? false : true}
        onClick={handleOnClick}
      >
        {isSending ? 'Cancel': 'Submit'}
      </Button>
    </Flex>
  )
}

export default SubmitButton