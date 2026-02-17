'use client'

import { useDispatch } from 'react-redux'
import { Button, Space, Popconfirm } from 'antd'
import { EyeOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined, StopOutlined } from '@ant-design/icons'
import { useRouter } from 'next/navigation'
import { AppDispatch } from '@/shared/store'
import { setStreamToEdit, setStreamToDelete } from '@/shared/store/dashboard/streams-page-slice'
import { useStartStream, useStopStream } from '@/api/dashboard/streams/hooks'

interface TableActionsProps {
  cameraId: string
  isRunning?: boolean
}

const TableActions = ({ cameraId, isRunning }: TableActionsProps) => {
  const dispatch = useDispatch<AppDispatch>()
  const router = useRouter()
  const { mutate: startStream } = useStartStream()
  const { mutate: stopStream } = useStopStream()

  const handleView = () => {
    router.push(`/dashboard/streams/${cameraId}`)
  }

  const handleEdit = () => {
    dispatch(setStreamToEdit(cameraId))
  }

  const handleDelete = () => {
    dispatch(setStreamToDelete(cameraId))
  }

  const handleToggleStream = () => {
    if (isRunning) {
      stopStream(cameraId)
    } else {
      startStream(cameraId)
    }
  }

  return (
    <Space size="small">
      <Button 
        icon={<EyeOutlined />} 
        onClick={handleView}
        size="small"
        title="View Details"
      />
      
      <Button 
        icon={isRunning ? <StopOutlined /> : <PlayCircleOutlined />}
        onClick={handleToggleStream}
        size="small"
        type={isRunning ? "default" : "primary"}
        title={isRunning ? "Stop Camera" : "Start Camera"}
      />

      <Button
        icon={<EditOutlined />}
        onClick={handleEdit}
        size="small"
        title="Edit Camera"
      />

      <Popconfirm
        title="Delete Camera"
        description="Are you sure you want to delete this camera?"
        onConfirm={handleDelete}
        okText="Yes"
        cancelText="No"
      >
        <Button
          icon={<DeleteOutlined />}
          danger
          size="small"
          title="Delete Camera"
        />
      </Popconfirm>
    </Space>
  )
}

export default TableActions
