'use client'

import { useDispatch } from 'react-redux'
import { Button, Space, Typography } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { AppDispatch } from '@/shared/store'
import { setIsCreateModalOpen } from '@/shared/store/dashboard/streams-page-slice'
import StreamTable from './_components/stream-table'
import StreamModals from './_components/stream-modals'

const { Title, Text } = Typography

const DashboardStreams = () => {
  const dispatch = useDispatch<AppDispatch>()

  const handleAddCamera = () => {
    dispatch(setIsCreateModalOpen(true))
  }

  return (
    <div>
      <StreamModals />
      
      <Space 
        direction="vertical" 
        size="large" 
        style={{ width: '100%', padding: '24px' }}
      >
        {/* Header */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center' 
        }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>Streams</Title>
            <Text type="secondary">Manage your RTSP camera streams</Text>
          </div>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={handleAddCamera}
            size="large"
          >
            Add Camera
          </Button>
        </div>

        {/* Section Header */}
        <div style={{ marginTop: '16px' }}>
          <Title level={4} style={{ margin: 0 }}>My Streams</Title>
        </div>

        {/* Table */}
        <StreamTable />
      </Space>
    </div>
  )
}

export default DashboardStreams
