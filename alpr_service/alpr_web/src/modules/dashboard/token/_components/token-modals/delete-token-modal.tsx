'use client'

import { useState } from 'react'

import { useSelector, useDispatch } from 'react-redux'
import { Modal, Button } from 'antd'
import { ExclamationCircleOutlined } from '@ant-design/icons'

import { AppDispatch, RootState } from '@/shared/store'
import { setTokenToDelete } from '@/shared/store/dashboard/tokens-page-slice'
import { useDeleteToken } from '@/api/dashboard/token/hooks'

const ModalTitle = () => {
  return (
    <p style={{ margin: 0 }}>
      <ExclamationCircleOutlined
        style={{ color: 'orange', marginRight: 8 }}
      />Delete Token
    </p>
  )
}

const DeleteTokenModal = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { mutate: deleteToken } = useDeleteToken()
  const tokenToDelete = useSelector((state: RootState) => state.tokensPage.tokenToDelete)
  const [confirmLoading, setConfirmLoading] = useState(false)

  const handleOk = (tokenKey: string | undefined) => {
    if (!tokenKey) return
    setConfirmLoading(true)
    deleteToken(
      { key: tokenKey },
      {
        onSuccess: () => dispatch(setTokenToDelete(undefined)),
        onSettled: () => setConfirmLoading(false),
      }
    )
  }

  const handleCancel = () => dispatch(setTokenToDelete(undefined))

  return (
    <Modal
      title={<ModalTitle />}
      open={tokenToDelete ? true : false}
      onOk={() => handleOk(tokenToDelete)}
      onCancel={handleCancel}
      footer={[
        <Button key="back" onClick={handleCancel}>Cancle</Button>,
        <Button key="submit" type="primary" loading={confirmLoading} onClick={() => handleOk(tokenToDelete)}>Submit</Button>
      ]}
    >
      <p>Are you sure you want to delete this token?</p>
    </Modal>
  )
}

export default DeleteTokenModal