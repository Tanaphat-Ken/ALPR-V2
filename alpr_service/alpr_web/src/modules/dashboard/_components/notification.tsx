
import { Badge } from 'antd'
import { BellOutlined } from '@ant-design/icons'

const Notification = () => {
  return (
    <Badge count={11} size='small' offset={[10, -8]}>
      <BellOutlined style={{ color: 'white' }} />
    </Badge>
  )
}

export default Notification