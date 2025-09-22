import { Flex, Avatar } from 'antd'
import Text from 'antd/lib/typography'

type UserProfileProps = {
  userEmail: string
}

const UserProfile = ({ userEmail }: UserProfileProps) => {
  const userName = userEmail.split('@')[0]
  return (
    <Flex gap={4}>
      <Avatar size={24} src="https://api.dicebear.com/7.x/miniavs/svg?seed=1" />
      <Text style={{ color: 'white' }}>{userName}</Text>
    </Flex>
  )
}

export default UserProfile