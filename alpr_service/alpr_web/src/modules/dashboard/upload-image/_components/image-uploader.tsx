'use client'

import { useState, useEffect } from 'react'

import { useDispatch, useSelector } from 'react-redux'
import styled from 'styled-components'
import { Flex, Upload } from 'antd'
import type { UploadFile, UploadProps } from 'antd'

import ImagePreview from './image-preview'
import UploadImageButton from './upload-button'
import { validateImage } from '@/shared/libs/image'
import { fileToBase64 } from '@/shared/libs/file'
import type { FileType } from '../_types'
import type { AppDispatch, RootState } from '@/shared/store'
import { 
  setImageSize, 
  setImage, 
  setImageName,
  resetUploadImageState
} from '@/shared/store/dashboard/upload-image-slice'

const StyledUpload = styled(Upload)`
  .ant-upload-wrapper, .ant-upload-list, .ant-upload {
    width: 200px !important;
    height: 200px !important;
  }

  .ant-upload-list-item-thumbnail {
    line-height: 150px !important;
  }

  .ant-upload-list-item-progress {
    bottom: 80px !important;
  }
`

const ImageUploader = () => {
  const dispatch = useDispatch<AppDispatch>()
  const processImageList = useSelector((state: RootState) => state.uploadImagePage.processedImageList)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewImage, setPreviewImage] = useState('')
  const [fileList, setFileList] = useState<UploadFile[]>([])

  const handlePreview = async (file: UploadFile) => {
    if (!file.url && !file.preview) {
      file.preview = await fileToBase64(file.originFileObj as FileType)
    }

    setPreviewImage(file.url || (file.preview as string))
    setPreviewOpen(true)
  }

  const handleChange: UploadProps['onChange'] = async ({ file, fileList: newFileList }) => {
    if (newFileList.length && !validateImage(file.originFileObj as FileType)) {
      return
    }

    if (newFileList.length && file.size) {
      dispatch(setImageSize(file.size / 1024 / 1024))
      dispatch(setImageName(file.name))
      const imageBase64 = await fileToBase64(file.originFileObj as FileType)
      dispatch(setImage(imageBase64))
    } else {
      dispatch(resetUploadImageState())
    }

    setFileList(newFileList)
  }

  useEffect(() => {
    setFileList([])
  }, [processImageList])

  return (
    <Flex align='center' justify='center'>
      <StyledUpload
        listType="picture-circle"
        fileList={fileList}
        onPreview={handlePreview}
        onChange={handleChange}
        maxCount={1}
        itemRender={(originNode, _) => <div {...originNode.props} style={{ width: 200, height: 200 }} />}
      >
        {fileList.length > 0 ? null : <UploadImageButton />}
      </StyledUpload>
      {previewImage && 
        <ImagePreview 
          isPreviewOpen={previewOpen} 
          previewImage={previewImage}
          setPreviewImage={setPreviewImage} 
          setPreviewOpen={setPreviewOpen} 
        />
      }
    </Flex>
  )
}

export default ImageUploader