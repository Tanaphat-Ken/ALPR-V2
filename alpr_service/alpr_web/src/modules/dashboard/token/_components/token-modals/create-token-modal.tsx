'use client'

import { useState } from 'react'

import moment from 'moment'
import { useSelector, useDispatch } from 'react-redux'
import { Modal, Input, DatePicker, Flex, Button } from 'antd'

import { AppDispatch, RootState } from '@/shared/store'
import { setIsCreateModalOpen } from '@/shared/store/dashboard/tokens-page-slice'
import { useNewToken } from '@/api/dashboard/token/hooks'

type NewTokenDataType = {
  tokenName: string,
  expireDate: string | null
}

const CreateNewTokenModal = () => {
  const dispatch = useDispatch<AppDispatch>()
  const isCreateModalOpen = useSelector((state: RootState) => state.tokensPage.isCreateModalOpen)
  const userId = useSelector((state: RootState) => state.user.userId)
  const activeTab = useSelector((state: RootState) => state.tokensPage.activeTab)
  const [confirmLoading, setConfirmLoading] = useState(false)
  const [newTokenData, setNewTokenData] = useState<NewTokenDataType>({ tokenName: '', expireDate: null })
  const { mutate: createNewToken } = useNewToken()

  const resetTokenData = () => setNewTokenData({ tokenName: '', expireDate: null })

  const handleOk = () => {
    setConfirmLoading(true)
    createNewToken({
      user_id: userId,
      service_type: activeTab,
      token_name: newTokenData.tokenName,
      expire_time: newTokenData.expireDate
    })
    resetTokenData()
    dispatch(setIsCreateModalOpen(false))
    setConfirmLoading(false)
  }

  const handleCancel = () => {
    resetTokenData()
    dispatch(setIsCreateModalOpen(false))
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNewTokenData({ ...newTokenData, tokenName: e.target.value })
  }

  const handleDateChange = (date: moment.Moment | null) => {
    setNewTokenData({ ...newTokenData, expireDate: date ? date.toISOString() : null })
  }

  return (
    <Modal
      title="Create New Tokens"
      open={isCreateModalOpen}
      onOk={handleOk}
      onCancel={handleCancel}
      footer={[
        <Button key="back" onClick={handleCancel}>Cancle</Button>,
        <Button key="submit" type="primary" loading={confirmLoading} onClick={handleOk}>Submit</Button>
      ]}

    >
      <Flex gap={16} vertical style={{ marginTop: 16 }}>
        <Input placeholder='Token Name' onChange={handleInputChange} value={newTokenData.tokenName} />
        <DatePicker
          style={{ width: '100%' }}
          placeholder='Expire Date'
          onChange={handleDateChange}
          value={newTokenData.expireDate ? moment(newTokenData.expireDate) : null}
        />
      </Flex>
    </Modal>
  )
}

export default CreateNewTokenModal