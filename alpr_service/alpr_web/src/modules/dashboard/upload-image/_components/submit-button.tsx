'use client'

import { useState } from 'react'

import { useSelector } from 'react-redux'
import { Flex, Select, Button } from 'antd'

import type { RootState } from '@/shared/store'
import { useTokens } from '@/api/dashboard/token/hooks'
import { useProcessImage } from '@/api/dashboard/upload-image/hook'
import { base64ToFile } from '@/shared/libs/file'
import { isExpired } from '@/shared/libs/times'

const SubmitButton = () => {
  const userId = useSelector((state: RootState) => state.user.userId)
  const uploadedImage = useSelector((state: RootState) => state.uploadImagePage.image)
  const imageName = useSelector((state: RootState) => state.uploadImagePage.imageName)
  const [selectedToken, setSelectedToken] = useState<string>()
  const { data: tokenList } = useTokens(userId, 'WEBSOCKET')
  const { mutate: processImage, isPending } = useProcessImage()

  const tokenOptionList = tokenList
    ?.map(item => {
      if (!isExpired(item.expireDate)) {
        return { value: item.tokenKey, label: item.tokenName }
      }
      return undefined
    })
    .filter((option) => option !== undefined)

  const handleOnClick = () => {
    if (uploadedImage && imageName && selectedToken) {
      processImage({ file: base64ToFile(uploadedImage, imageName, 'image'), token: selectedToken })
    }
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
        disabled={uploadedImage && selectedToken ? false : true}
        onClick={handleOnClick}
        loading={isPending}
        iconPosition='end'
      >
        Submit
      </Button>
    </Flex>
  )
}

export default SubmitButton