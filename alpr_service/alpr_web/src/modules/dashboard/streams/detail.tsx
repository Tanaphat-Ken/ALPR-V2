'use client'

import { useParams, useRouter } from 'next/navigation'
import { Button, Space, Typography, Tag, Breadcrumb, Card, Row, Col, Spin } from 'antd'
import { HomeOutlined, VideoCameraOutlined, EditOutlined, DeleteOutlined, ArrowLeftOutlined, PlayCircleOutlined, StopOutlined } from '@ant-design/icons'
import { useDispatch } from 'react-redux'
import { AppDispatch } from '@/shared/store'
import { setStreamToEdit, setStreamToDelete } from '@/shared/store/dashboard/streams-page-slice'
import { useStream, useStreams, useStartStream, useStopStream } from '@/api/dashboard/streams/hooks'
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
  const { mutate: startStream, isPending: isStarting } = useStartStream()
  const { mutate: stopStream, isPending: isStopping } = useStopStream()

  const handleBack = () => {
    router.push('/dashboard/streams')
  }

  const handleEdit = () => {
    dispatch(setStreamToEdit(cameraId))
  }

  const handleDelete = () => {
    dispatch(setStreamToDelete(cameraId))
  }

  const handleToggle = () => {
    if (stream?.running) {
      stopStream(cameraId)
    } else {
      startStream(cameraId)
    }
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

      {/* Top Row: Stream Viewer + Camera Info (ซ้าย-ขวา) */}
      <Row gutter={[24, 24]} style={{ marginBottom: '24px' }}>
        {/* Left: Stream Viewer - ใหญ่กว่า */}
        <Col xs={24} lg={16}>
          <StreamViewer
            cameraId={cameraId}
            streamUrl={stream.rtsp_url}
            cameraName={stream.name}
          />
        </Col>

        {/* Right: Camera Info - เล็กกว่า */}
        <Col xs={24} lg={8}>
          <Card style={{ height: '100%' }}>
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <div>
                <Title level={3} style={{ margin: 0, marginBottom: '16px' }}>
                  {stream.name}
                </Title>
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <div>
                    <Text type="secondary" strong>URL:</Text>
                    <br />
                    <Text>{stream.rtsp_url}</Text>
                  </div>
                  {stream.location && (
                    <div>
                      <Text type="secondary" strong>Location:</Text>
                      <br />
                      <Text>{stream.location}</Text>
                    </div>
                  )}
                  <div>
                    <Text type="secondary" strong>Status:</Text>
                    <br />
                    {getStatusTag()}
                  </div>
                </Space>
              </div>
              <Space style={{ width: '100%' }} wrap>
                <Button
                  type={stream.running ? 'default' : 'primary'}
                  icon={stream.running ? <StopOutlined /> : <PlayCircleOutlined />}
                  onClick={handleToggle}
                  loading={isStarting || isStopping}
                  style={{ flex: 1 }}
                >
                  {stream.running ? 'Stop' : 'Start'}
                </Button>
                <Button
                  icon={<EditOutlined />}
                  onClick={handleEdit}
                  style={{ flex: 1 }}
                >
                  Edit
                </Button>
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  onClick={handleDelete}
                  style={{ flex: 1 }}
                >
                  Delete
                </Button>
              </Space>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Detection Results - Full Width */}
      <Card>
        <Title level={4}>Process Result</Title>
        <DetectionTable cameraId={cameraId} />
      </Card>
    </div>
  )
}

export default StreamDetailPage
