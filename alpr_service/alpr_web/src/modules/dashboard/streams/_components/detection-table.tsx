'use client'

import { Table, Typography, Image } from 'antd'
import type { TableColumnsType } from 'antd'
import { useDetections } from '@/api/dashboard/streams/hooks'
import moment from 'moment'

const { Text } = Typography

interface DetectionTableProps {
  cameraId: string
}

type DetectionDataType = {
  key: string
  timestamp: string
  full_image_url?: string
  car_image_url?: string
  plate_image_url?: string
  plate_id?: string
  province?: string
}

const columns: TableColumnsType<DetectionDataType> = [
  {
    title: 'Full Image',
    dataIndex: 'full_image_url',
    key: 'full_image',
    width: 120,
    render: (url?: string, record?: DetectionDataType) => {
      const imageUrl = url || record?.car_image_url
      return imageUrl ? (
        <Image 
          src={imageUrl} 
          alt="Detection" 
          width={80} 
          height={60}
          style={{ objectFit: 'cover', borderRadius: '4px' }}
        />
      ) : (
        <div style={{ 
          width: 80, 
          height: 60, 
          background: '#f0f0f0', 
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>No Image</Text>
        </div>
      )
    }
  },
  {
    title: 'Plate Image',
    dataIndex: 'plate_image_url',
    key: 'plate_image',
    width: 120,
    render: (url?: string) => url ? (
      <Image 
        src={url} 
        alt="Plate" 
        width={80} 
        height={60}
        style={{ objectFit: 'cover', borderRadius: '4px' }}
      />
    ) : (
      <Text type="secondary">-</Text>
    )
  },
  {
    title: 'Plate ID',
    dataIndex: 'plate_id',
    key: 'plate_id',
    width: 120,
    render: (plate?: string) => plate ? (
      <Text strong style={{ fontSize: '16px' }}>{plate}</Text>
    ) : (
      <Text type="secondary">Not Found</Text>
    )
  },
  {
    title: 'Province',
    dataIndex: 'province',
    key: 'province',
    width: 120,
    render: (province?: string) => province || <Text type="secondary">-</Text>
  },
  {
    title: 'Time Stamp',
    dataIndex: 'timestamp',
    key: 'timestamp',
    width: 180,
    render: (timestamp: string) => moment(timestamp).format('YYYY-MM-DD HH:mm:ss')
  }
]

const DetectionTable = ({ cameraId }: DetectionTableProps) => {
  const { data: detectionsData, isLoading } = useDetections(cameraId, 50)

  const dataSource: DetectionDataType[] = (detectionsData?.detections || []).map((detection, index) => ({
    key: detection.id || `${cameraId}-${index}`,
    timestamp: detection.timestamp,
    full_image_url: detection.full_image_url,
    car_image_url: detection.car_image_url,
    plate_image_url: detection.plate_image_url,
    plate_id: detection.plate_id,
    province: detection.province
  }))

  return (
    <Table<DetectionDataType>
      columns={columns}
      dataSource={dataSource}
      loading={isLoading}
      pagination={{
        pageSize: 10,
        showSizeChanger: true,
        showTotal: (total) => `Total ${total} detections`
      }}
      scroll={{ x: 800 }}
    />
  )
}

export default DetectionTable
