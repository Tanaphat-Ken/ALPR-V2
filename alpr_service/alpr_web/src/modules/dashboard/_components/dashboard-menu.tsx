'use client'

import { useRouter, usePathname } from 'next/navigation'

import { useDispatch } from 'react-redux'
import type { MenuProps } from 'antd'
import { Menu } from 'antd'
import Sider from 'antd/es/layout/Sider'
import { 
  HomeOutlined,
  KeyOutlined,
  CloudUploadOutlined, 
  ReadOutlined, 
  SettingOutlined 
} from '@ant-design/icons'

import { AppDispatch } from '@/shared/store'
import { setActiveTab } from '@/shared/store/dashboard/tokens-page-slice'
import type { ServiceType } from '@/shared/types/subscription'

type MenuItem = Required<MenuProps>['items'][number];

const items: MenuItem[] = [
  {
    key: '/dashboard',
    icon: <HomeOutlined />,
    label: 'Home',
  },
  {
    key: '/dashboard/tokens',
    icon: <KeyOutlined />,
    label: 'Tokens',
    children: [
      { key: '/dashboard/tokens/api', label: 'API' },
      { key: '/dashboard/tokens/websocket', label: 'WebSocket' },
      { key: '/dashboard/tokens/video', label: 'Video' },
    ],
  },
  {
    key: '/dashboard/upload',
    icon: <CloudUploadOutlined />,
    label: 'Upload',
    children: [
      { key: '/dashboard/upload/image', label: 'Image' },
      { key: '/dashboard/upload/video', label: 'Video' },
    ],
  },
  {
    key: '/dashboard/documentation',
    icon: <ReadOutlined />,
    label: 'Documentation',
  },
  {
    key: '/dashboard/settings',
    icon: <SettingOutlined />,
    label: 'Settings',
  },
]

const DashboardMenu = () => {
  const router = useRouter()
  const pathname = usePathname()
  const dispatch = useDispatch<AppDispatch>()

  const handleOnClick: MenuProps['onClick'] = ({ key }) => {
    if (key.startsWith('/dashboard/tokens')) {
      const activeTab = key.split('/')[3].toUpperCase() as ServiceType
      dispatch(setActiveTab(activeTab))
    }
    router.replace(key)
  }

  return (
    <Sider theme='light'>
      <Menu 
        onClick={handleOnClick}
        defaultSelectedKeys={['/dashboard']}
        selectedKeys={[pathname]}
        mode='inline' 
        items={items}
      />
    </Sider>
  )
}

export default DashboardMenu