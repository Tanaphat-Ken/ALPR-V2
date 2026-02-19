type ServiceType = 'API' | 'WEBSOCKET' | 'VIDEO_WEBSOCKET' | 'RTSP'

type BillingPeriodType = 'ANNUALLY' | 'MONTHLY' | 'YEARLY' | 'QUARTERLY' | 'SEMI ANNUALLY'

type SubscriptionDetailsType = {
  sub_id: number
  billing_period: BillingPeriodType
  service_type: string        // e.g. "Tier 1", "Tier 2", "Tier 3"
  price: number
  description: string
  // Quotas & Features
  api_request_limit?: number | null
  video_upload_limit?: number | null
  has_api_access?: boolean | number
  has_websocket_access?: boolean | number
  has_video_upload?: boolean | number
  has_rtsp_stream?: boolean | number
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