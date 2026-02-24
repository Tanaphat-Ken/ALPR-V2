'use client'

import { useRouter, usePathname } from 'next/navigation'

import type { MenuProps } from 'antd'
import { Menu } from 'antd'
import Sider from 'antd/es/layout/Sider'
import {
  HomeOutlined,
  SearchOutlined,
  CloudUploadOutlined,
  VideoCameraOutlined,
  ReadOutlined,
  SettingOutlined,
  PictureOutlined,
  StarOutlined,
  PlayCircleOutlined,
  ProfileOutlined,
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
    icon: <SearchOutlined />,
    label: 'Tokens',
  },
  {
    key: '/dashboard/upload',
    icon: <CloudUploadOutlined />,
    label: 'Upload',
    children: [
      { key: '/dashboard/upload/image', icon: <PictureOutlined />, label: 'Image' },
      { key: '/dashboard/upload/video', icon: <VideoCameraOutlined />, label: 'Video' },
    ],
  },
  {
    key: '/dashboard/streams',
    icon: <PlayCircleOutlined />,
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
      { key: '/dashboard/settings/subscription', icon: <ProfileOutlined />, label: 'Subscription' },
      { key: 'logout', label: 'Logout', danger: true },
    ],
  },
]

const DashboardMenu = () => {
  const router = useRouter()
  const pathname = usePathname()

  const handleOnClick: MenuProps['onClick'] = ({ key }) => {
    if (key === 'logout') {
      localStorage.removeItem('token')
      localStorage.removeItem('userId')
      document.cookie = 'token=; Max-Age=0; path=/;'
      document.cookie = 'userId=; Max-Age=0; path=/;'
      router.push('/login')
      return
    }

    router.push(key)
  }

  return (
      <Sider theme='light' style={{ overflow: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '16px 24px 8px' }}>
        <span style={{ fontWeight: 600, fontSize: 15 }}>Quick Access</span>
        <StarOutlined style={{ fontSize: 14 }} />
      </div>
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