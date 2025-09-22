type ServiceType = 'API' | 'WEBSOCKET' | 'VIDEO' | 'VIDEO_WEBSOCKET'

type BillingPeriodType = 'ANNUALLY' | 'MONTHLY' | 'YEARLY'

type SubscriptionDetailsType = {
  sub_id: number
  billing_period: BillingPeriodType
  service_type: ServiceType
  price: number
  request_limit: number
  description: string
}

type SubscriptionType = {
  user_sub_id: number
  is_activate: boolean
  start_date: string
  end_date: string
  request_quota: number | null
  subscription_details: SubscriptionDetailsType
}

export type { 
  ServiceType,
  BillingPeriodType,
  SubscriptionDetailsType,
  SubscriptionType,
}