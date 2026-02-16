type ServiceType = 'API' | 'WEBSOCKET' | 'VIDEO_WEBSOCKET' | 'RTSP'

type BillingPeriodType = 'ANNUALLY' | 'MONTHLY' | 'YEARLY' | 'QUARTERLY' | 'SEMI ANNUALLY'

type SubscriptionDetailsType = {
  sub_id: number
  billing_period: BillingPeriodType
  service_type: ServiceType
  price: number
  description: string
  // Quotas & Features
  api_request_limit?: number
  video_upload_limit?: number
  has_api_access?: boolean
  has_websocket_access?: boolean
  has_video_upload?: boolean
  has_rtsp_stream?: boolean
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