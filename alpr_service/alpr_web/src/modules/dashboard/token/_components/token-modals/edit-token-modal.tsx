'use client'

import { ChangeEvent, useState } from 'react'

import { useSelector, useDispatch } from 'react-redux'
import { Modal, Input, Flex, Button } from 'antd'

import { AppDispatch, RootState } from '@/shared/store'
import { setTokenToEdit } from '@/shared/store/dashboard/tokens-page-slice'
import { useEditToken } from '@/api/dashboard/token/hooks'

const EditTokenModal = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { mutate: editToken } = useEditToken()
  const tokenToEdit = useSelector((state: RootState) => state.tokensPage.tokenToEdit)
  const [newTokenName, setNewTokenName] = useState<string>('')
  const [confirmLoading, setConfirmLoading] = useState(false)

  const handleOk = (tokenKey: string | undefined) => {
    setConfirmLoading(true)
    if (tokenKey) editToken({ key: tokenKey, token_name: newTokenName })
    dispatch(setTokenToEdit(undefined))
    setConfirmLoading(false)
  }

  const handleCancel = () => dispatch(setTokenToEdit(undefined))
  const handleOnChange = (e: ChangeEvent<HTMLInputElement>) => setNewTokenName(e.target.value)

  return (
    <Modal
      title="Edit Token" 
      open={tokenToEdit ? true : false}
      onOk={() => handleOk(tokenToEdit)}
      onCancel={handleCancel}
      footer={[
        <Button key="back" onClick={handleCancel}>Cancle</Button>,
        <Button key="submit" type="primary" loading={confirmLoading} onClick={() => handleOk(tokenToEdit)}>Submit</Button>
      ]}
    >
      <Flex gap={16} vertical style={{ marginTop: 16 }}>
        <Input placeholder='Token Name' value={newTokenName} onChange={handleOnChange} />
      </Flex>
    </Modal>
  )
}

export default EditTokenModal