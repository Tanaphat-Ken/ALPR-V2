'use client'

import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Modal, Input, Form, Button, InputNumber, Switch, Select } from 'antd'
import { AppDispatch, RootState } from '@/shared/store'
import { setIsCreateModalOpen } from '@/shared/store/dashboard/streams-page-slice'
import { useCreateStream } from '@/api/dashboard/streams/hooks'
import type { CreateStreamRequest } from '@/api/dashboard/streams/types'
import { useTokens } from '@/api/dashboard/token/hooks'

const CreateStreamModal = () => {
  const dispatch = useDispatch<AppDispatch>()
  const isOpen = useSelector((state: RootState) => state.streamsPage.isCreateModalOpen)
  const userId = useSelector((state: RootState) => state.user.userId)
  const [form] = Form.useForm()
  const { mutate: createStream, isPending, isSuccess, reset } = useCreateStream()

  // ดึง RTSP tokens ของ user คนนี้
  const { data: rtspTokens = [] } = useTokens(userId, 'RTSP')

  // ปิด modal เมื่อสร้างสำเร็จ (ใช้ isSuccess แทน inline callback ซึ่งไม่ reliable ใน RQ v5)
  useEffect(() => {
    if (isSuccess) {
      form.resetFields()
      dispatch(setIsCreateModalOpen(false))
      reset()
    }
  }, [isSuccess])

  const handleOk = async () => {
    try {
      const values: CreateStreamRequest = await form.validateFields()
      createStream(values)
    } catch (_) { }
  }

  const handleCancel = () => {
    form.resetFields()
    dispatch(setIsCreateModalOpen(false))
  }

  return (
    <Modal
      title="Add New Camera"
      open={isOpen}
      onCancel={handleCancel}
      footer={[
        <Button key="cancel" onClick={handleCancel}>Cancel</Button>,
        <Button key="submit" type="primary" loading={isPending} onClick={handleOk}>
          Add Camera
        </Button>
      ]}
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ enabled: true, fps: 10, frame_skip: 3 }}
      >
        <Form.Item
          label="Camera Name"
          name="name"
          rules={[{ required: true, message: 'Please enter camera name' }]}
        >
          <Input placeholder="Main Entrance" />
        </Form.Item>

        <Form.Item
          label="Stream URL"
          name="rtsp_url"
          tooltip="รองรับ RTSP URL (rtsp://...) หรือ path ไฟล์วิดีโอ เช่น /app/videos/demo.mp4 สำหรับ dev/demo"
          rules={[{ required: true, message: 'Please enter stream URL' }]}
        >
          <Input placeholder="rtsp://admin:password@192.168.1.100:554/stream1" />
        </Form.Item>

        <Form.Item
          label="RTSP Token"
          name="token_key"
          tooltip="เลือก Token ประเภท RTSP ที่สร้างไว้จากหน้า Tokens"
          rules={[{ required: true, message: 'Please select an RTSP token' }]}
        >
          <Select
            placeholder="Select RTSP token"
            options={rtspTokens.map(t => ({
              value: t.tokenKey,
              label: t.tokenName ? `${t.tokenName} (${t.tokenKey.slice(0, 8)}…)` : t.tokenKey,
            }))}
            notFoundContent="No RTSP tokens found — create one on the Tokens page first"
          />
        </Form.Item>

        <Form.Item label="Location" name="location">
          <Input placeholder="Building A - Floor 1" />
        </Form.Item>

        <Form.Item label="FPS (Frames Per Second)" name="fps">
          <InputNumber min={1} max={30} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          label="Frame Skip"
          name="frame_skip"
          tooltip="Process every Nth frame to reduce CPU usage"
        >
          <InputNumber min={1} max={10} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item label="Enabled" name="enabled" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default CreateStreamModal
