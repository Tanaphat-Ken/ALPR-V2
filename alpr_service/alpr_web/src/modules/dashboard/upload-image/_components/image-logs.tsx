'use client'

import { useState, useEffect } from 'react'

import { useSelector } from 'react-redux'
import { Table, Image as AntdImage } from 'antd'
import type { TableColumnsType } from 'antd'

import SectionTitle from '@/shared/components/section-title'
import { convertImageListToTableDataType } from '@/shared/libs/image'
import type { RootState } from '@/shared/store'
import { convertToReadableTimeStamp } from '@/shared/libs/times'

type ImageDataType = {
  key: React.Key
  carImage: string,
  plateImage: string,
  plateId: string,
  province: string,
  timeStamp: string
}

const columns: TableColumnsType<ImageDataType> = [
  { 
    title: 'Car Image', 
    dataIndex: 'carImage', 
    key: 'carImage',
    render: (carImage: string) => <AntdImage width={100} src={carImage} alt='car-image' />
  },
  { 
    title: 'Plate Image', 
    dataIndex: 'plateImage', 
    key: 'plateImage',
    render: (plateImage: string) => <AntdImage width={100} src={plateImage} alt='plate-image' />
  },
  { title: 'Plate ID', dataIndex: 'plateId', key: 'plateId' },
  { title: 'Province', dataIndex: 'province', key: 'province' },
  { 
    title: 'Time Stamp', 
    dataIndex: 'timeStamp', 
    key: 'timeStamp', 
    render: (timeStamp: string) => convertToReadableTimeStamp(timeStamp)
  },
]

const ImageLogs = () => {
  const imageList = useSelector((state: RootState) => state.uploadImagePage.processedImageList)
  const [imageListConverted, setImageListConverted] = useState<ImageDataType[]>([])

  useEffect(() => {
    const processAllImages = async () => {
      const processedList = await Promise.all(imageList.map(convertImageListToTableDataType))
      setImageListConverted(processedList.filter(Boolean) as ImageDataType[])
    }
    processAllImages()
  }, [imageList])

  return (
    <div>
      <SectionTitle>Process Result</SectionTitle>      
      <div>
        <Table<ImageDataType> 
          columns={columns}
          dataSource={imageListConverted.reverse()}
          pagination={false}
        />
      </div>
    </div>
  )
}

export default ImageLogs