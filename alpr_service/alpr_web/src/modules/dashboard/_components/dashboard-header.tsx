'use client'
import { useEffect, useState } from 'react'

import { Flex } from 'antd'
import { Header } from 'antd/lib/layout/layout'
import { SearchOutlined, QuestionCircleOutlined } from '@ant-design/icons'
import { useDispatch } from 'react-redux'

import Notification from './notification'
import UserProfile from './user-profile'
import LocaleSwapper from './locale-swapper'
import useUserInfo from '@/api/dashboard/user-info'
import { AppDispatch } from '@/shared/store'
import { setUser } from '@/shared/store/dashboard/user-slice'

const DashboardHeader = () => {
  const [userId, setUserId] = useState<number | null>(null)

  // Get userId from localStorage on component mount
  useEffect(() => {
    const storedUserId = localStorage.getItem('userId')
    if (storedUserId) {
      setUserId(parseInt(storedUserId, 10))
    }
  }, [])

  const { data: userInfo, isSuccess, error } = useUserInfo(userId || 0)
  const dispatch = useDispatch<AppDispatch>()

  useEffect(() => { // temporary fetch user by header
    if (isSuccess && userInfo) {
      dispatch(setUser({
        userId: userInfo[0].user_id,
        email: userInfo[0].email,
        createdAt: userInfo[0].created_at,
        updatedAt: userInfo[0].updated_at
      }))
    }
  }, [isSuccess, userInfo, dispatch])

  if (error && userId) {
    return <div>Error</div>
  }

  return (
    <Header style={{ color: 'white', background: '#150E4B', flexShrink: 0 }}>
      <Flex justify='space-between' align='center'>
        <h1 style={{ margin: 0, padding: 0, color: 'white', fontFamily: 'var(--font-unbounded), Unbounded, sans-serif', fontWeight: 400 }}>ALPR - Automatice License Plate Recognition</h1>
        <Flex align='center' justify='center' gap={24}>
          <SearchOutlined />
          <QuestionCircleOutlined />
          <Notification />
          <UserProfile userEmail={userInfo ? userInfo[0].email : ''} />
          <LocaleSwapper />
        </Flex>
      </Flex>
    </Header>
  )
}

export default DashboardHeader