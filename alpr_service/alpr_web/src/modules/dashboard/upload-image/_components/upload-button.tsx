'use client'

import { CloudUploadOutlined } from '@ant-design/icons'

const UploadImageButton = () => {
  return (
    <button style={{ border: 0, background: 'none' }} type="button">
      <CloudUploadOutlined style={{ fontSize: 24, color: '#1677FF' }} />
      <div style={{ marginTop: 8 }}>Upload Image</div>
    </button>
  )
}

export default UploadImageButton