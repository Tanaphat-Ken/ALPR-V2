'use client'

import { Image } from 'antd'

type ImagePreviewProps = {
  previewImage: string
  isPreviewOpen: boolean
  setPreviewOpen: (visible: boolean) => void
  setPreviewImage: (previewImage: string) => void
}

const ImagePreview = ({ previewImage, isPreviewOpen, setPreviewImage, setPreviewOpen }: ImagePreviewProps) => {
  return (
    <Image 
      wrapperStyle={{ display: 'none' }} 
      src={previewImage} 
      alt='uploaded'
      preview={{
        visible: isPreviewOpen,
        onVisibleChange: (visible) => setPreviewOpen(visible),
        afterOpenChange: (visible) => !visible && setPreviewImage(''),
      }}
          
    />
  )
}

export default ImagePreview