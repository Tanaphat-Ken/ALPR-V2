'use client'

import { useEffect, useState } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { Modal, Input, Form, Button, InputNumber, Switch, message } from 'antd'
import { AppDispatch, RootState } from '@/shared/store'
import { setStreamToEdit } from '@/shared/store/dashboard/streams-page-slice'
import { useStreams } from '@/api/dashboard/streams/hooks'

const EditStreamModal = () => {
  const dispatch = useDispatch<AppDispatch>()
  const streamToEdit = useSelector((state: RootState) => state.streamsPage.streamToEdit)
  const { data: streams } = useStreams()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (streamToEdit && streams) {
      const stream = streams.find(s => s.id === streamToEdit)
      if (stream) {
        form.setFieldsValue(stream)
      }
    }
  }, [streamToEdit, streams, form])

  const handleOk = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      
      // TODO: เชื่อม API เมื่อ Backend พร้อม
      // await updateStream(streamToEdit, values)
      
      message.info('This feature requires backend API implementation')
      console.log('Updated values:', values)
      
      dispatch(setStreamToEdit(undefined))
    } catch (error) {
      console.error('Validation failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    dispatch(setStreamToEdit(undefined))
  }

  return (
    <Modal
      title="Edit Camera"
      open={!!streamToEdit}
      onCancel={handleCancel}
      footer={[
        <Button key="cancel" onClick={handleCancel}>
          Cancel
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleOk}>
          Update Camera
        </Button>
      ]}
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
      >
        <Form.Item
          label="Camera Name"
          name="name"
          rules={[{ required: true, message: 'Please enter camera name' }]}
        >
          <Input placeholder="Main Entrance" />
        </Form.Item>

        <Form.Item
          label="RTSP URL"
          name="rtsp_url"
          rules={[
            { required: true, message: 'Please enter RTSP URL' },
            { 
              pattern: /^rtsp:\/\/.+/,
              message: 'URL must start with rtsp://' 
            }
          ]}
        >
          <Input placeholder="rtsp://admin:password@192.168.1.100:554/stream1" />
        </Form.Item>

        <Form.Item
          label="Location"
          name="location"
        >
          <Input placeholder="Building A - Floor 1" />
        </Form.Item>

        <Form.Item
          label="FPS (Frames Per Second)"
          name="fps"
        >
          <InputNumber min={1} max={30} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          label="Frame Skip"
          name="frame_skip"
          tooltip="Process every Nth frame to reduce CPU usage"
        >
          <InputNumber min={1} max={10} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          label="Enabled"
          name="enabled"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default EditStreamModal
