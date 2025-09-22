'use client'

import { usePathname } from 'next/navigation'

import { useDispatch } from 'react-redux'
import { Tabs, Button } from 'antd'
import { SwapOutlined, ApiOutlined, VideoCameraOutlined, PlusOutlined } from '@ant-design/icons'

import { AppDispatch } from '@/shared/store'
import { setIsCreateModalOpen, setActiveTab } from '@/shared/store/dashboard/tokens-page-slice'
import TokenTable from './token-table'
import type { ServiceType } from '@/shared/types/subscription'

const tokenTabItems = [
  { 
    key: 'API',
    label: 'API',
    children: <TokenTable />,
    icon: <SwapOutlined />
  },
  { 
    key: 'WEBSOCKET',
    label: 'WEBSOCKET',
    children: <TokenTable />,
    icon: <ApiOutlined />
  }, 
  {
    key: 'VIDEO',
    label: 'VIDEO',
    children: <TokenTable />,
    icon: <VideoCameraOutlined />
  }
]

const CreateNewModelButton = ({ onClick }: { onClick: () => void }) => {
  return <Button onClick={onClick} icon={<PlusOutlined />} type='primary' >Create Token</Button>
}

const TokenTabs = () => {
  const dispatch = useDispatch<AppDispatch>()
  const tokenType = usePathname().split('/')[3]

  const handleTabChange = (key: string) => dispatch(setActiveTab(key as ServiceType))
  const handleOpenCreateTokenModal = () => dispatch(setIsCreateModalOpen(true))

  return (
    <div style={{ backgroundColor: 'white', padding: 16 }}>
      <Tabs
        onChange={handleTabChange}
        defaultActiveKey={tokenType.toUpperCase()}
        tabBarExtraContent={<CreateNewModelButton onClick={() => handleOpenCreateTokenModal()} />}
        items={tokenTabItems}
      />
    </div>
  ) 
}

export default TokenTabs