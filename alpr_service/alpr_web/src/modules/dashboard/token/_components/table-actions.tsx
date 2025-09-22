'use client'

import { useDispatch } from 'react-redux'
import { Button, Flex } from 'antd'
import { EditOutlined, DeleteOutlined } from '@ant-design/icons'

import { AppDispatch } from '@/shared/store'
import { setTokenToEdit, setTokenToDelete } from '@/shared/store/dashboard/tokens-page-slice'

type TableActionsProps = {
  tokenKey: string
}

const TableActions = ({ tokenKey }: TableActionsProps) => {
  const dispatch = useDispatch<AppDispatch>()

  const handleOpenEditModal = (tokenKey: string) => dispatch(setTokenToEdit(tokenKey))
  const handleOpenDeleteModal = (tokenKey: string) => dispatch(setTokenToDelete(tokenKey))

  return (
    <Flex gap={16}>
      <Button icon={<EditOutlined />} onClick={() => handleOpenEditModal(tokenKey)}>Edit</Button>
      <Button icon={<DeleteOutlined />} onClick={() => handleOpenDeleteModal(tokenKey)}>Delete</Button>
    </Flex>
  )
}

export default TableActions