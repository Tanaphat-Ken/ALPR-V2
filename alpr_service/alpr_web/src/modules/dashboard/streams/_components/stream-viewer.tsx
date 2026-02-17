'use client'

import { Card, Typography, Empty, Button, Tag } from 'antd'
import { VideoCameraOutlined, ReloadOutlined, CheckCircleOutlined, LoadingOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { useStreamWebSocket } from '@/api/dashboard/streams/useStreamWebSocket'

const { Text } = Typography

interface StreamViewerProps {
  cameraId: string
  streamUrl?: string
  cameraName?: string
}

const StreamViewer = ({ cameraId, streamUrl, cameraName }: StreamViewerProps) => {
  const { isConnected, isConnecting, error, lastFrame, reconnect } = useStreamWebSocket({
    cameraId,
    enabled: true,
    onDetection: (detection) => {
      console.log('Detection received:', detection.plate_id)
    }
  })

  const getStatusIcon = () => {
    if (isConnecting) {
      return <LoadingOutlined style={{ fontSize: '16px', color: '#1890ff' }} spin />
    }
    if (isConnected) {
      return <CheckCircleOutlined style={{ fontSize: '16px', color: '#52c41a' }} />
    }
    return <CloseCircleOutlined style={{ fontSize: '16px', color: '#ff4d4f' }} />
  }

  const getStatusText = () => {
    if (isConnecting) return 'Connecting...'
    if (isConnected) return 'Live'
    if (error) return error
    return 'Disconnected'
  }

  const getStatusColor = () => {
    if (isConnecting) return 'processing'
    if (isConnected) return 'success'
    return 'error'
  }

  return (
    <Card
      style={{ 
        width: '100%',
        height: '100%'
      }}
    >
      <div style={{
        width: '100%',
        height: '360px',
        background: '#000',
        borderRadius: '8px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Live Video Frame */}
        {lastFrame ? (
          <img 
            src={lastFrame} 
            alt="Live Stream"
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              objectFit: 'contain'
            }}
          />
        ) : (
          <Empty
            image={<VideoCameraOutlined style={{ fontSize: '64px', color: '#666' }} />}
            description={
              <div>
                <Text style={{ color: '#fff' }}>
                  {isConnecting ? 'Connecting to stream...' : 'Waiting for frames...'}
                </Text>
                <br />
                <Text style={{ color: '#999', fontSize: '12px' }}>
                  Camera: {cameraName || cameraId}
                </Text>
              </div>
            }
          />
        )}
        
        {/* Status Badge - Top Left */}
        <div style={{
          position: 'absolute',
          top: '12px',
          left: '12px',
        }}>
          <Tag 
            icon={getStatusIcon()} 
            color={getStatusColor()}
            style={{ margin: 0 }}
          >
            {getStatusText()}
          </Tag>
        </div>

        {/* Reconnect Button - Show when disconnected */}
        {!isConnected && !isConnecting && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 10
          }}>
            <Button 
              type="primary" 
              icon={<ReloadOutlined />}
              onClick={reconnect}
              size="large"
            >
              Reconnect
            </Button>
          </div>
        )}
        
        {/* Camera Name - Bottom Left */}
        <div style={{
          position: 'absolute',
          bottom: '12px',
          left: '12px',
          background: 'rgba(0,0,0,0.7)',
          padding: '6px 12px',
          borderRadius: '4px'
        }}>
          <Text style={{ color: '#fff', fontSize: '12px' }}>
            {cameraName || cameraId}
          </Text>
        </div>

        {/* Timestamp - Bottom Right */}
        <div style={{
          position: 'absolute',
          bottom: '12px',
          right: '12px',
          background: 'rgba(0,0,0,0.7)',
          padding: '6px 12px',
          borderRadius: '4px'
        }}>
          <Text style={{ color: '#fff', fontSize: '12px' }}>
            {new Date().toLocaleTimeString()}
          </Text>
        </div>
      </div>
    </Card>
  )
}

export default StreamViewer
