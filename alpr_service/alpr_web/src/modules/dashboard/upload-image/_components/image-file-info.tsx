'use client'

import { useSelector } from 'react-redux'
import styled from 'styled-components'
import { Flex } from 'antd'

import type { RootState } from '@/shared/store'

const P = styled.p`
  margin: 0;
`

const ImageFileInfo = () => {
  const imageName = useSelector((state: RootState) => state.uploadImagePage.imageName)
  const imageSize = useSelector((state: RootState) => state.uploadImagePage.imageSize)
  return (
    <Flex vertical align='center' justify='center' gap={16} style={{ marginTop: 16 }}>
      <P>{imageName ? imageName : 'JPG, JPEG, PNG'}</P>
      <P>File Size: {imageSize.toFixed(2)} / 50 MB</P>
    </Flex>
  )
}

export default ImageFileInfo