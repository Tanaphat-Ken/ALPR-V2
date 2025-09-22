'use client'

import { useEffect } from 'react'

import { useSelector } from 'react-redux'
import { Table, Tag } from 'antd'
import type { TableColumnsType } from 'antd'

import TableActions from './table-actions'
import { isExpired} from '@/shared/libs/times'
import { useTokens } from '@/api/dashboard/token/hooks'
import { RootState } from '@/shared/store'

type TokenDataType = {
  key: React.Key
  tokenName: string
  expireDate: string
  tokenKey: string
}

const columns: TableColumnsType<TokenDataType> = [
  { title: 'Token Name', dataIndex: 'tokenName', key: 'tokenName' },
  { 
    title: 'Expire Date', 
    dataIndex: 'expireDate', 
    key: 'expireDate',
    render: (expireDate: string) => <TagExpire expireDate={expireDate} />
  },
  {
    title: 'Action',
    dataIndex: '',
    key: 'x',
    width: 200,
    render: (_, record) => <TableActions tokenKey={record.tokenKey} />,
  },
]

const TagExpire = ({ expireDate }: { expireDate: string }  ) => {
  return (
    <Tag color={isExpired(expireDate) ? 'error' : 'success'}>
      {expireDate}
    </Tag>
  ) 
}

const ExpandToken = ({ tokenKey }: { tokenKey: string }) => {
  return (
    <p style={{ margin: 0 }}>
      Key
      <Tag style={{ marginLeft: 16, opacity: 0.6 }}>{tokenKey}</Tag>
    </p>
  )
}

const TokenTable = () => {
  const activeTab = useSelector((state: RootState) => state.tokensPage.activeTab)
  const userId = useSelector((state: RootState) => state.user.userId)
  const { data: tokenList, refetch } = useTokens(userId, activeTab)

  useEffect(() => { 
    if (userId) refetch() 
  }, [userId])

  return (
    <Table<TokenDataType>
      columns={columns}
      dataSource={tokenList}
      pagination={false}
      expandable={{
        expandedRowRender: (record) => <ExpandToken tokenKey={record.tokenKey} />,
        rowExpandable: (_) => true,
      }}
    />
  )
}

export default TokenTable