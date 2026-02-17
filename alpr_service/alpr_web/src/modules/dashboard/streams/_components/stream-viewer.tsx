'use client'

import { Card, Typography, Empty } from 'antd'
import { VideoCameraOutlined } from '@ant-design/icons'

const { Text } = Typography

interface StreamViewerProps {
  cameraId: string
  streamUrl?: string
  cameraName?: string
}

const StreamViewer = ({ cameraId, streamUrl, cameraName }: StreamViewerProps) => {
  // TODO: Implement WebSocket or HLS stream viewer
  // สำหรับตอนนี้แสดงแค่ placeholder

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
        position: 'relative'
      }}>
        <Empty
          image={<VideoCameraOutlined style={{ fontSize: '64px', color: '#666' }} />}
          description={
            <div>
              <Text style={{ color: '#fff' }}>Live Stream Viewer</Text>
              <br />
              <Text style={{ color: '#999', fontSize: '12px' }}>
                Camera: {cameraName || cameraId}
              </Text>
              <br />
              <Text style={{ color: '#999', fontSize: '12px' }}>
                Stream URL: {streamUrl || 'Not available'}
              </Text>
            </div>
          }
        />
        
        {/* Timestamp overlay */}
        <div style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          background: 'rgba(0,0,0,0.7)',
          padding: '8px 12px',
          borderRadius: '4px'
        }}>
          <Text style={{ color: '#fff', fontSize: '12px' }}>
            {new Date().toLocaleString()}
          </Text>
        </div>
      </div>
    </Card>
  )
}

export default StreamViewer
