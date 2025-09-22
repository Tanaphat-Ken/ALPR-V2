import { useMutation } from '@tanstack/react-query'
import { message } from 'antd'
import { useDispatch, useSelector } from 'react-redux'

import plateRecognizerService from '@/shared/libs/plateRegcognizer'
import type { AppDispatch, RootState } from '@/shared/store'
import { appendProcessedImageList, resetUploadImageState } from '@/shared/store/dashboard/upload-image-slice'
import type { ProcessImageBody, ProcessImageResponse } from './type'

const requestProcessImage = async (data: ProcessImageBody) => {
  const formData = new FormData()
  formData.append('file', data.file)
  return await plateRecognizerService.post<ProcessImageResponse>(
    '/images/upload-image', 
    formData, 
    { 
      headers: {
        'Authorization': `Bearer ${data.token}`,
        'Content-Type': 'multipart/form-data'
      }, 
      timeout: 60000
    }
  )
}

const useProcessImage = () => {
  const dispatch = useDispatch<AppDispatch>()
  const uploadedImage = useSelector((state: RootState) => state.uploadImagePage.image)
  return useMutation({
    mutationFn: requestProcessImage,
    onError: (error) => message.error(error.message),
    onSuccess: (data) => {
      const result = data.model_response
      const timeStamp = new Date()
      const newImageItem = {
        image: uploadedImage,
        carBbox: result.car_bbox,
        plateBbox: result.plate_bbox,
        plateId: result.plate_id,
        province: result.province,
        timeStamp: timeStamp.toISOString()
      }
      dispatch(appendProcessedImageList(newImageItem))
      dispatch(resetUploadImageState())
    }
  })
}

export { useProcessImage }
