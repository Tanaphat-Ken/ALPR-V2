'use client'

import { useSelector } from 'react-redux'
import { RootState } from '@/shared/store'
import { Flex } from 'antd'
import Title from 'antd/es/typography/Title'
import Text from 'antd/es/typography/Text'

const WelcomeBanner = () => {
  const userName = useSelector((state: RootState) => state.user.email).split('@')[0]
  return (
    <Flex style={{ backgroundColor: 'white', padding: '2rem' }} align='end' gap={16}>
      <Title style={{ fontSize: 20, margin: 0 }} level={2}>Welcome, {userName}</Title>
      <Text type='secondary'>Monitor and manage your license plate recognition services</Text>      
    </Flex>
  )
}

export default WelcomeBanner