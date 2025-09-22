'use client'

import styled from 'styled-components'
import { Card, Tag, Flex } from 'antd'
import Text from 'antd/es/typography/Text'
import { CheckCircleOutlined, SwapOutlined, ApiOutlined, VideoCameraOutlined, CloseCircleOutlined } from '@ant-design/icons'

import { useSelector } from 'react-redux'
import { RootState } from '@/shared/store'
import type { ServiceType } from '@/shared/types/subscription'

const serviceIcons = {
  API: SwapOutlined,
  WEBSOCKET: ApiOutlined,
  VIDEO: VideoCameraOutlined
}

const colorMap = {
  API: '#67E8F9',
  WEBSOCKET: '#FCD34D',
  VIDEO: '#D946EF'
}

type SubscriptionCardProps = {
  serviceType: ServiceType
  isServiceActive: boolean
  expireDate: string
  requestLimit: number | null
  requestQuota: number | null
  onClick: () => void
}

type StyledCardProps = {
  borderColor: string
  isCardActive: boolean
}

const StyledCard = styled(Card).withConfig({
  shouldForwardProp: (prop) => prop !== 'isCardActive' && prop !== 'borderColor'
})<StyledCardProps>`
  .ant-card-body {
    padding-top: 12px;
  }

  border: ${({ isCardActive, borderColor }) => (isCardActive ? `1px solid ${borderColor}` : 'none')};

  &:hover {
    border: ${({ borderColor }) => `1px solid ${borderColor}`};
  }
`

const CardTitle = ({ title }: { title: keyof typeof serviceIcons }) => {
  const DisplayIcon = serviceIcons[title]
  return (
    <Flex align="center" gap={8}>
      {title} <DisplayIcon style={{ color: `${colorMap[title]}` }} />
    </Flex>
  )
}

const SubscriptionCard = ({ 
  serviceType, 
  expireDate, 
  isServiceActive, 
  requestLimit, 
  requestQuota, 
  onClick
}: SubscriptionCardProps) => {

  serviceType = serviceType == 'VIDEO_WEBSOCKET' ? 'VIDEO' : serviceType // temporary handle video type

  const activeSubscription = useSelector((state: RootState) => state.homePageSlice.activeService)
  const isCardActive = activeSubscription == serviceType

  return (
    <StyledCard 
      title={<CardTitle title={serviceType} />} 
      borderColor={colorMap[serviceType]} 
      isCardActive={isCardActive}
      onClick={onClick}
      hoverable 
    >
      <div style={{ marginBottom: 12 }}>
        <Text style={{ fontSize: '2rem', fontWeight: 'bold' }}>{serviceType == 'VIDEO' ? '️-': requestQuota}</Text>
        <Text> / {serviceType == 'VIDEO' ? '♾️': requestLimit} </Text>
        <Text type="secondary">Remaining</Text>
      </div>

      {isServiceActive 
        ? <Tag icon={<CheckCircleOutlined />} color="success">Active</Tag> 
        : <Tag icon={<CloseCircleOutlined />} color="error">Inactive</Tag>
      }
      
      <Tag color="warning">Expire: {expireDate}</Tag>
    </StyledCard>
  )
}

export default SubscriptionCard