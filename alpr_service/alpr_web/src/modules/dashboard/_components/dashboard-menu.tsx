'use client'

import { useRouter, usePathname } from 'next/navigation'

import type { MenuProps } from 'antd'
import { Menu } from 'antd'
import Sider from 'antd/es/layout/Sider'
import {
  HomeOutlined,
  KeyOutlined,
  CloudUploadOutlined,
  VideoCameraOutlined,
  ReadOutlined,
  SettingOutlined
} from '@ant-design/icons'

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
    key: '/dashboard/streams',
    icon: <VideoCameraOutlined />,
    label: 'Streams',
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
    children: [
      { key: '/dashboard/settings/subscription', label: 'Subscription' },
      { key: 'logout', label: 'Logout', danger: true },
    ],
  },
]

const DashboardMenu = () => {
  const router = useRouter()
  const pathname = usePathname()

  const handleOnClick: MenuProps['onClick'] = ({ key }) => {
    if (key === 'logout') {
      // Clear local storage
      localStorage.removeItem('token')
      localStorage.removeItem('userId')

      // Clear cookies if any
      document.cookie = 'token=; Max-Age=0; path=/;'
      document.cookie = 'userId=; Max-Age=0; path=/;'

      // Redirect to login
      router.push('/login')
      return
    }

    router.push(key)
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