import { Flex, Avatar, Dropdown, MenuProps } from 'antd' // Added Dropdown, MenuProps
import Text from 'antd/lib/typography'
import { LogoutOutlined, UserOutlined } from '@ant-design/icons' // Added icons
import { useRouter } from 'next/navigation' // Added useRouter

type UserProfileProps = {
  userEmail: string
}

const UserProfile = ({ userEmail }: UserProfileProps) => {
  const userName = userEmail.split('@')[0]
  const router = useRouter()

  const handleLogout = () => {
    // Clear local storage
    localStorage.removeItem('token')
    localStorage.removeItem('userId')

    // Clear cookies if any (optional but good practice)
    document.cookie = 'token=; Max-Age=0; path=/;'
    document.cookie = 'userId=; Max-Age=0; path=/;'

    // Redirect to login
    router.push('/login')
  }

  const items: MenuProps['items'] = [
    {
      key: 'logout',
      label: 'Logout',
      icon: <LogoutOutlined />,
      onClick: handleLogout,
      danger: true
    }
  ]

  return (
    <Dropdown menu={{ items }} placement="bottomRight" arrow>
      <Flex gap={8} align="center" style={{ cursor: 'pointer' }}>
        <Avatar size={32} icon={<UserOutlined />} src="https://api.dicebear.com/7.x/miniavs/svg?seed=1" />
        <Text style={{ color: 'white', fontWeight: 500 }}>{userName}</Text>
      </Flex>
    </Dropdown>
  )
}

export default UserProfile