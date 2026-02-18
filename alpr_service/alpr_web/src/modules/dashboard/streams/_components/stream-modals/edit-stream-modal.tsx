'use client'

import { useEffect } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { Modal, Input, Form, Button, InputNumber, Switch, Select } from 'antd'
import { AppDispatch, RootState } from '@/shared/store'
import { setStreamToEdit } from '@/shared/store/dashboard/streams-page-slice'
import { useStreams, useUpdateStream } from '@/api/dashboard/streams/hooks'
import { useTokens } from '@/api/dashboard/token/hooks'

const EditStreamModal = () => {
  const dispatch = useDispatch<AppDispatch>()
  const streamToEdit = useSelector((state: RootState) => state.streamsPage.streamToEdit)
  const userId = useSelector((state: RootState) => state.user.userId)
  const { data: streams } = useStreams()
  const [form] = Form.useForm()
  const { mutate: updateStream, isPending, isSuccess, reset } = useUpdateStream()

  // ดึง RTSP tokens ของ user คนนี้
  const { data: rtspTokens = [] } = useTokens(userId, 'RTSP')

  // โหลดค่าปัจจุบันเข้า form เมื่อ modal เปิด
  useEffect(() => {
    if (streamToEdit && streams) {
      const stream = streams.find(s => s.id === streamToEdit)
      if (stream) form.setFieldsValue(stream)
    }
  }, [streamToEdit, streams])

  // ปิด modal เมื่ออัปเดตสำเร็จ
  useEffect(() => {
    if (isSuccess) {
      form.resetFields()
      dispatch(setStreamToEdit(undefined))
      reset()
    }
  }, [isSuccess])

  const handleOk = async () => {
    try {
      const values = await form.validateFields()
      if (!streamToEdit) return
      updateStream({ cameraId: streamToEdit, data: values })
    } catch (_) { }
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
        <Button key="cancel" onClick={handleCancel}>Cancel</Button>,
        <Button key="submit" type="primary" loading={isPending} onClick={handleOk}>
          Update Camera
        </Button>
      ]}
      width={600}
    >
      <Form form={form} layout="vertical">
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
        >
          <Select
            placeholder="Select RTSP token (leave empty to keep current)"
            allowClear
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

export default EditStreamModal