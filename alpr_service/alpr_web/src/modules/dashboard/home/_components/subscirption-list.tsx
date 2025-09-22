'use client'

import { useSelector, useDispatch } from 'react-redux'
import { Row, Col } from 'antd'

import { RootState, AppDispatch } from '@/shared/store'
import { setActiveService } from '@/shared/store/dashboard/home-page-slice'
import SectionTitle from '../../../../shared/components/section-title'
import SubscriptionCard from './subscription-card'
import useSubscription from '@/api/dashboard/subscription'
import type { ServiceType } from '@/shared/types/subscription'

const serviceOrder: ServiceType[] = ['API', 'WEBSOCKET', 'VIDEO', 'VIDEO_WEBSOCKET']

const SubscriptionList = () => {
  const dispatch = useDispatch<AppDispatch>()
  const userId = useSelector((state: RootState) => state.user.userId)
  const { data: subscriptionList, isError } = useSubscription(userId) // temporary handle undefine userId

  if (isError) {
    return <div>error</div>
  }

  const handleCardOnClick = (serviceType: ServiceType) => {
    dispatch(setActiveService(serviceType))
  }

  const sortedSubscriptions = subscriptionList?.subscriptions.sort(
    (a, b) => serviceOrder.indexOf(a.subscription_details.service_type) - serviceOrder.indexOf(b.subscription_details.service_type)
  )

  return (
    <div style={{ marginTop: 16 }}>
      <SectionTitle>Service Usage</SectionTitle>
      <Row gutter={16}>
        {sortedSubscriptions?.map((item, index) => {
          const subScriptionCardProps = {
            serviceType: item.subscription_details.service_type,
            isServiceActive: item.is_activate,
            expireDate: item.end_date,
            requestLimit: item.subscription_details.request_limit,
            requestQuota: item.request_quota,
            onClick: () => handleCardOnClick(item.subscription_details.service_type)
          }

          return (
            <Col span={8} key={index+item.user_sub_id}>
              <SubscriptionCard {...subScriptionCardProps} />
            </Col>
          )
        })}
      </Row>
    </div>
  )
}

export default SubscriptionList