'use client'

import { useParams, useRouter } from 'next/navigation'
import { Button, Space, Typography, Tag, Breadcrumb, Card, Row, Col, Spin } from 'antd'
import { HomeOutlined, VideoCameraOutlined, EditOutlined, DeleteOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import { useDispatch } from 'react-redux'
import { AppDispatch } from '@/shared/store'
import { setStreamToEdit, setStreamToDelete } from '@/shared/store/dashboard/streams-page-slice'
import { useStream, useStreams } from '@/api/dashboard/streams/hooks'
import StreamViewer from './_components/stream-viewer'
import DetectionTable from './_components/detection-table'
import StreamModals from './_components/stream-modals'

const { Title, Text } = Typography

const StreamDetailPage = () => {
  const params = useParams()
  const router = useRouter()
  const dispatch = useDispatch<AppDispatch>()
  const cameraId = params?.id as string

  const { data: streams, isLoading: isLoadingStreams } = useStreams()
  const stream = streams?.find(s => s.id === cameraId)

  const handleBack = () => {
    router.push('/dashboard/streams')
  }

  const handleEdit = () => {
    dispatch(setStreamToEdit(cameraId))
  }

  const handleDelete = () => {
    dispatch(setStreamToDelete(cameraId))
  }

  if (isLoadingStreams) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '400px' 
      }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!stream) {
    return (
      <div style={{ padding: '24px' }}>
        <Text>Camera not found</Text>
        <br />
        <Button onClick={handleBack} style={{ marginTop: '16px' }}>
          Back to Streams
        </Button>
      </div>
    )
  }

  const getStatusTag = () => {
    if (!stream.enabled) {
      return <Tag color="default">Disabled</Tag>
    }
    if (stream.running) {
      return <Tag color="success">Connected</Tag>
    }
    return <Tag color="error">Disconnected</Tag>
  }

  return (
    <div style={{ padding: '24px' }}>
      <StreamModals />

      {/* Breadcrumb */}
      <Breadcrumb style={{ marginBottom: '24px' }}>
        <Breadcrumb.Item href="/dashboard">
          <HomeOutlined />
        </Breadcrumb.Item>
        <Breadcrumb.Item href="/dashboard/streams">
          <VideoCameraOutlined />
          <span>Streams</span>
        </Breadcrumb.Item>
        <Breadcrumb.Item>{stream.name}</Breadcrumb.Item>
      </Breadcrumb>

      {/* Back Button */}
      <Button 
        icon={<ArrowLeftOutlined />} 
        onClick={handleBack}
        style={{ marginBottom: '16px' }}
      >
        Back to Streams
      </Button>

      {/* Stream Viewer */}
      <StreamViewer 
        cameraId={cameraId}
        streamUrl={stream.rtsp_url}
        cameraName={stream.name}
      />

      {/* Camera Info Card */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col flex="auto">
            <Space direction="vertical" size="small">
              <Title level={3} style={{ margin: 0 }}>
                {stream.name}
              </Title>
              <Space size="middle">
                <Text type="secondary">
                  <strong>URL:</strong> {stream.rtsp_url}
                </Text>
                {stream.location && (
                  <Text type="secondary">
                    <strong>Location:</strong> {stream.location}
                  </Text>
                )}
              </Space>
              <div>
                <Text type="secondary" style={{ marginRight: '8px' }}>
                  <strong>Status:</strong>
                </Text>
                {getStatusTag()}
              </div>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button 
                icon={<EditOutlined />}
                onClick={handleEdit}
              >
                Edit
              </Button>
              <Button 
                danger
                icon={<DeleteOutlined />}
                onClick={handleDelete}
              >
                Delete
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Detection Results */}
      <Card>
        <Title level={4}>Process Result</Title>
        <DetectionTable cameraId={cameraId} />
      </Card>
    </div>
  )
}

export default StreamDetailPage
