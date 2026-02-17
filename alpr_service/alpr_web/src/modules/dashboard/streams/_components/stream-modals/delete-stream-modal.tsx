'use client'

import { useSelector, useDispatch } from 'react-redux'
import { Modal, Typography, message } from 'antd'
import { ExclamationCircleOutlined } from '@ant-design/icons'
import { AppDispatch, RootState } from '@/shared/store'
import { setStreamToDelete } from '@/shared/store/dashboard/streams-page-slice'
import { useStreams } from '@/api/dashboard/streams/hooks'

const { Text } = Typography

const DeleteStreamModal = () => {
  const dispatch = useDispatch<AppDispatch>()
  const streamToDelete = useSelector((state: RootState) => state.streamsPage.streamToDelete)
  const { data: streams } = useStreams()

  const stream = streams?.find(s => s.id === streamToDelete)

  const handleOk = () => {
    // TODO: เชื่อม API เมื่อ Backend พร้อม
    // await deleteStream(streamToDelete)
    
    message.info('This feature requires backend API implementation')
    console.log('Delete camera:', streamToDelete)
    
    dispatch(setStreamToDelete(undefined))
  }

  const handleCancel = () => {
    dispatch(setStreamToDelete(undefined))
  }

  return (
    <Modal
      title={
        <span>
          <ExclamationCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
          Delete Camera
        </span>
      }
      open={!!streamToDelete}
      onOk={handleOk}
      onCancel={handleCancel}
      okText="Delete"
      okButtonProps={{ danger: true }}
      cancelText="Cancel"
    >
      <p>Are you sure you want to delete this camera?</p>
      {stream && (
        <div style={{ padding: '12px', background: '#f5f5f5', borderRadius: '8px' }}>
          <Text strong>{stream.name}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {stream.rtsp_url}
          </Text>
        </div>
      )}
      <p style={{ marginTop: '16px', color: '#ff4d4f' }}>
        This action cannot be undone.
      </p>
    </Modal>
  )
}

export default DeleteStreamModal
