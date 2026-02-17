'use client'

import { useState } from 'react'
import {
  Card,
  Breadcrumb,
  Row,
  Col,
  Typography,
  Button,
  Spin,
  Modal,
  Badge,
  message,
  List,
  Tag,
  Divider,
  Space
} from 'antd'
import {
  HomeOutlined,
  CheckCircleFilled,
  CloseCircleFilled,
  CheckOutlined
} from '@ant-design/icons'
import { useSelector } from 'react-redux'
import moment from 'moment'

import { useServices, useSubscription, useChangeSubscription, useCancelSubscription } from '@/api/dashboard/subscription'
import { RootState } from '@/shared/store'
import type { SubscriptionType, SubscriptionDetailsType } from '@/shared/types/subscription'

const { Title, Text, Paragraph } = Typography

const SubscriptionPage = () => {
  const user = useSelector((state: RootState) => state.user)
  const { data: allServices, isLoading: isLoadingServices } = useServices()
  const { data: userSubscriptionsData, isLoading: isLoadingUserSubs, refetch } = useSubscription(user?.userId || 0)

  // Mutation hooks
  const changeSubscriptionMutation = useChangeSubscription()
  const cancelSubscriptionMutation = useCancelSubscription()

  const userSubscriptions = userSubscriptionsData?.subscriptions || []

  // Since we now have bundled plans, we likely have one main active subscription
  // But for safety, we'll take the first active one or handle multiples if needed.
  const activeSubscription = userSubscriptions.find(sub => sub.is_activate)

  const handleChangePlan = (subId: number) => {
    Modal.confirm({
      title: 'Confirm Plan Change',
      content: 'Are you sure you want to switch to this plan? Changes will apply immediately.',
      onOk: async () => {
        try {
          await changeSubscriptionMutation.mutateAsync({ user_id: user.userId, sub_id: subId })
          message.success('Subscription plan updated successfully')
          refetch()
        } catch (error) {
          message.error('Failed to change subscription plan')
        }
      }
    })
  }

  const handleCancelSubscription = (userSubId: number) => {
    Modal.confirm({
      title: 'Cancel Subscription?',
      content: 'Are you sure you want to cancel? You will lose access to premium features.',
      okText: 'Yes, Cancel',
      okType: 'danger',
      cancelText: 'No, Keep It',
      onOk: async () => {
        try {
          await cancelSubscriptionMutation.mutateAsync(userSubId)
          message.success('Subscription cancelled successfully')
          refetch()
        } catch (error) {
          message.error('Failed to cancel subscription')
        }
      }
    })
  }

  const renderFeatureItem = (text: string, included: boolean = true) => (
    <List.Item style={{ padding: '8px 0', border: 'none' }}>
      <Space>
        {included ? <CheckCircleFilled style={{ color: '#52c41a' }} /> : <CloseCircleFilled style={{ color: '#ff4d4f' }} />}
        <Text type={included ? undefined : 'secondary'} delete={!included}>{text}</Text>
      </Space>
    </List.Item>
  )

  const renderPlanCard = (plan: SubscriptionDetailsType, isCurrent: boolean) => {
    return (
      <Col xs={24} md={12} lg={8} key={plan.sub_id}>
        <Card
          hoverable
          style={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            borderColor: isCurrent ? '#1890ff' : undefined,
            borderWidth: isCurrent ? 2 : 1,
            position: 'relative',
            boxShadow: isCurrent ? '0 4px 12px rgba(24, 144, 255, 0.2)' : undefined
          }}
          bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        >
          {isCurrent && (
            <div style={{ position: 'absolute', top: 0, right: 0 }}>
              <Tag color="blue" style={{ margin: 0, borderTopRightRadius: 8, borderBottomLeftRadius: 8, padding: '4px 12px' }}>
                CURRENT PLAN
              </Tag>
            </div>
          )}

          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <Title level={3} style={{ marginBottom: 0 }}>{plan.service_type.replace(/_/g, ' ')}</Title>
            <Text type="secondary">{plan.description}</Text>
            <div style={{ marginTop: 16 }}>
              <Title level={2} style={{ marginBottom: 0 }}>
                ฿{plan.price.toLocaleString()}
                <Text type="secondary" style={{ fontSize: 16, fontWeight: 'normal' }}> / {plan.billing_period.toLowerCase()}</Text>
              </Title>
            </div>
          </div>

          <Divider dashed />

          <List size="small" split={false} style={{ flex: 1 }}>
            <List.Item style={{ padding: '8px 0', border: 'none' }}>
              <Text strong>Features & Limits</Text>
            </List.Item>

            {/* API Access */}
            {renderFeatureItem(
              `${(plan.api_request_limit || 0).toLocaleString()} API Requests/day`,
              !!plan.has_api_access
            )}

            {/* WebSocket */}
            {renderFeatureItem('WebSocket Support', !!plan.has_websocket_access)}

            {/* Video */}
            {renderFeatureItem(
              plan.has_video_upload ? `${(plan.video_upload_limit || 0).toLocaleString()} Video Uploads/day` : 'Video Analysis',
              !!plan.has_video_upload
            )}

            {/* RTSP */}
            {renderFeatureItem(
              plan.has_rtsp_stream ? 'RTSP Stream Processing' : 'RTSP Stream Processing',
              !!plan.has_rtsp_stream
            )}
          </List>

          <div style={{ marginTop: 24 }}>
            <Button
              block
              type={isCurrent ? 'default' : 'primary'}
              size="large"
              disabled={isCurrent}
              onClick={() => !isCurrent && handleChangePlan(plan.sub_id)}
              loading={changeSubscriptionMutation.isPending}
            >
              {isCurrent ? 'Current Plan' : 'Choose Plan'}
            </Button>
          </div>
        </Card>
      </Col>
    )
  }

  if (isLoadingServices || isLoadingUserSubs) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <Spin size="large" tip="Loading plans..." />
      </div>
    )
  }

  return (
    <div style={{ padding: 24, paddingBottom: 48 }}>
      <Breadcrumb
        style={{ marginBottom: 24 }}
        items={[
          { href: '/dashboard', title: <HomeOutlined /> },
          { title: 'Settings' },
          { title: 'Subscription' }
        ]}
      />

      <div style={{ marginBottom: 40 }}>
        <Title level={2}>Subscription Plans</Title>
        <Paragraph type="secondary" style={{ fontSize: 16 }}>
          Choose the plan that fits your needs. Upgrade or downgrade at any time.
        </Paragraph>
      </div>

      {/* Current Subscription Status (if user is subscribed) */}
      {activeSubscription && (
        <Card
          style={{ marginBottom: 32, borderColor: '#b7eb8f' }}
          title={
            <Space>
              <CheckCircleFilled style={{ color: '#52c41a' }} />
              <span>Active Subscription</span>
            </Space>
          }
          extra={
            <Button
              danger
              type="text"
              onClick={() => handleCancelSubscription(activeSubscription.user_sub_id)}
            >
              Cancel Subscription
            </Button>
          }
        >
          <Row gutter={[24, 24]}>
            <Col xs={24} md={6}>
              <Text type="secondary">Current Plan</Text>
              <div style={{ fontSize: 18, fontWeight: 600 }}>
                {activeSubscription.subscription_details.service_type}
              </div>
            </Col>
            <Col xs={24} md={6}>
              <Text type="secondary">Renewal Date</Text>
              <div style={{ fontSize: 18, fontWeight: 600 }}>
                {moment(activeSubscription.end_date).format('MMM D, YYYY')}
              </div>
            </Col>
            <Col xs={24} md={6}>
              <Text type="secondary">Cost</Text>
              <div style={{ fontSize: 18, fontWeight: 600 }}>
                ฿{activeSubscription.subscription_details.price.toLocaleString()} / {activeSubscription.subscription_details.billing_period.toLowerCase()}
              </div>
            </Col>
            <Col xs={24} md={6}>
              <Text type="secondary">Status</Text>
              <div>
                <Badge status="success" text="Active" />
              </div>
            </Col>
          </Row>
        </Card>
      )}

      {/* Plans Grid */}
      <Row gutter={[24, 24]} align="stretch">
        {allServices?.map(plan => renderPlanCard(
          plan,
          activeSubscription?.subscription_details.sub_id === plan.sub_id
        ))}
      </Row>
    </div>
  )
}

export default SubscriptionPage
