'use client'

import { useSelector, useDispatch } from 'react-redux'
import { Row, Col } from 'antd'

import { RootState, AppDispatch } from '@/shared/store'
import { setActiveService } from '@/shared/store/dashboard/home-page-slice'
import SectionTitle from '../../../../shared/components/section-title'
import SubscriptionCard from './subscription-card'
import useSubscription from '@/api/dashboard/subscription'
import type { ServiceType } from '@/shared/types/subscription'

const serviceOrder: ServiceType[] = ['API', 'WEBSOCKET', 'VIDEO_WEBSOCKET', 'RTSP']

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

  const serviceItems: {
    serviceType: ServiceType,
    limit: number | null,
    quota: number | null,
    isActive: boolean | undefined,
    expireDate: string | undefined,
    key: string
  }[] = []

  subscriptionList?.subscriptions.forEach((sub) => {
    // Skip inactive subscriptions
    if (!sub.is_activate) {
      return
    }

    const details = sub.subscription_details
    const baseKey = `${sub.user_sub_id}`

    // API — limit = api_request_limit (null = unlimited), quota = remaining request_quota
    if (details.has_api_access) {
      serviceItems.push({
        serviceType: 'API',
        limit: details.api_request_limit ?? null,
        quota: sub.request_quota ?? null,
        isActive: sub.is_activate,
        expireDate: sub.end_date || undefined,
        key: `${baseKey}-API`
      })
    }

    // WEBSOCKET — limit = api_request_limit (null = unlimited), quota = remaining request_quota
    if (details.has_websocket_access) {
      serviceItems.push({
        serviceType: 'WEBSOCKET',
        limit: details.api_request_limit ?? null,
        quota: sub.request_quota ?? null,
        isActive: sub.is_activate,
        expireDate: sub.end_date || undefined,
        key: `${baseKey}-WS`
      })
    }

    // VIDEO_WEBSOCKET — limit = video_upload_limit (null = unlimited)
    if (details.has_video_upload) {
      serviceItems.push({
        serviceType: 'VIDEO_WEBSOCKET',
        limit: details.video_upload_limit ?? null,
        quota: details.video_upload_limit ?? null,
        isActive: sub.is_activate,
        expireDate: sub.end_date || undefined,
        key: `${baseKey}-VID`
      })
    }

    // RTSP
    if (details.has_rtsp_stream) {
      serviceItems.push({
        serviceType: 'RTSP',
        limit: null,
        quota: null,
        isActive: sub.is_activate,
        expireDate: sub.end_date || undefined,
        key: `${baseKey}-RTSP`
      })
    }
  })

  const sortedSubscriptions = serviceItems.sort(
    (a, b) => serviceOrder.indexOf(a.serviceType) - serviceOrder.indexOf(b.serviceType)
  )

  return (
    <div style={{ marginTop: 16 }}>
      <SectionTitle>Service Usage</SectionTitle>
      <Row gutter={16}>
        {sortedSubscriptions.map((item) => {
          const subScriptionCardProps = {
            serviceType: item.serviceType,
            isServiceActive: !!item.isActive,
            expireDate: item.expireDate || 'N/A',
            requestLimit: item.limit,
            requestQuota: item.quota,
            onClick: () => handleCardOnClick(item.serviceType)
          }

          return (
            <Col span={8} key={item.key}>
              <SubscriptionCard {...subScriptionCardProps} />
            </Col>
          )
        })}
      </Row>
    </div>
  )
}

export default SubscriptionList