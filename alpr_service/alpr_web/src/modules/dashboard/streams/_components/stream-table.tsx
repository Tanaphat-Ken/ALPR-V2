'use client'

import { Table, Tag, Typography } from 'antd'
import type { TableColumnsType } from 'antd'
import TableActions from './table-actions'
import { useStreams } from '@/api/dashboard/streams/hooks'
import type { Stream } from '@/api/dashboard/streams/types'

const { Text } = Typography

type StreamDataType = {
  key: string
  id: string
  name: string
  rtsp_url: string
  location?: string
  enabled: boolean
  running?: boolean
}

const columns: TableColumnsType<StreamDataType> = [
  { 
    title: 'Name', 
    dataIndex: 'name', 
    key: 'name',
    width: 200
  },
  { 
    title: 'Stream URL', 
    dataIndex: 'rtsp_url', 
    key: 'rtsp_url',
    render: (url: string) => (
      <Text 
        ellipsis={{ tooltip: url }} 
        style={{ maxWidth: 300, display: 'block' }}
      >
        {url}
      </Text>
    )
  },
  {
    title: 'Location',
    dataIndex: 'location',
    key: 'location',
    width: 150,
    render: (location?: string) => location || '-'
  },
  {
    title: 'Status',
    key: 'status',
    width: 150,
    render: (_, record) => {
      if (!record.enabled) {
        return <Tag color="default">Disabled</Tag>
      }
      if (record.running) {
        return <Tag color="success">Connected</Tag>
      }
      return <Tag color="error">Disconnected</Tag>
    }
  },
  {
    title: 'Actions',
    key: 'actions',
    width: 200,
    render: (_, record) => (
      <TableActions 
        cameraId={record.id} 
        isRunning={record.running}
      />
    ),
  },
]

const StreamTable = () => {
  const { data: streams, isLoading } = useStreams()

  const dataSource: StreamDataType[] = (streams || []).map((stream: Stream) => ({
    key: stream.id,
    id: stream.id,
    name: stream.name,
    rtsp_url: stream.rtsp_url,
    location: stream.location,
    enabled: stream.enabled,
    running: stream.running
  }))

  return (
    <Table<StreamDataType>
      columns={columns}
      dataSource={dataSource}
      loading={isLoading}
      pagination={{
        pageSize: 10,
        showSizeChanger: true,
        showTotal: (total) => `Total ${total} cameras`
      }}
    />
  )
}

export default StreamTable
