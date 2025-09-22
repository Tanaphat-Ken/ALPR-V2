import { message } from 'antd'

import { base64ToImage } from './file'
import type { ProcessedImage } from '../types/image'
import type { FileType } from '../types/file'

export const validateImage = (file: FileType) => {
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png' || file.type === 'image/jpg'
  if (!isJpgOrPng) {
    message.error('You can only upload JPEG/JPG/PNG files!')
    return false
  }

  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    message.error('Image must be smaller than 50MB!')
    return false
  }

  return true
}

export const cropImage = (img: HTMLImageElement, bbox: number[][] | null): Promise<HTMLImageElement> => {
  return new Promise((resolve) => {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    if (!ctx || !bbox || bbox.length !== 4) {
      resolve(img)
      return
    }

    const [tl, tr, bl, _] = bbox
    const [x1, y1] = tl
    const [x2] = tr

    const width = Math.abs(x2 - x1)
    const height = Math.abs(bl[1] - tl[1])

    canvas.width = width
    canvas.height = height

    ctx.drawImage(img, x1, y1, width, height, 0, 0, width, height)

    const croppedImageUrl = canvas.toDataURL()
    const croppedImage = new Image()
    croppedImage.src = croppedImageUrl

    resolve(croppedImage)
  })
}

export const convertImageListToTableDataType = async (item: ProcessedImage, index: number) => {
  try {
    const imageObject = await base64ToImage(item.image || '')
    const carImage = await cropImage(imageObject, item.carBbox)
    const plateImage = await cropImage(carImage, item.plateBbox)

    return {
      key: index,
      carImage: carImage.src,
      plateImage: plateImage.src,
      plateId: item.plateId || 'Not Found',
      province: item.province || 'Not Found',
      timeStamp: item.timeStamp,
    }
  } catch (error) {
    console.error('Error processing image item:', error)
    return null
  }
}

export const convertImageListToTableDataTypeSkipCar = async (item: ProcessedImage, index: number) => {
  try {
    const carImage = await base64ToImage(item.image || '')
    const plateImage = await cropImage(carImage, item.plateBbox)

    return {
      key: index,
      carImage: carImage.src,
      plateImage: plateImage.src,
      plateId: item.plateId || 'Not Found',
      province: item.province || 'Not Found',
      timeStamp: item.timeStamp,
    }
  } catch (error) {
    console.error('Error processing image item:', error)
    return null
  }
}