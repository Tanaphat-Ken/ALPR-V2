import { useQuery, QueryFunctionContext } from '@tanstack/react-query'

import apiClient from '@/shared/libs/apiClient'
import type { SubscriptionType } from '@/shared/types/subscription'

type FetchSubscriptionListType = {
  userId: number
}

type QueryResultSubscriptionListType = {
  user_id: number
  subscriptions: SubscriptionType[]
}

const fetchSubscriptionListByUserId = async ({ queryKey }: QueryFunctionContext<[string, FetchSubscriptionListType]>) => {
  const [_key, params] = queryKey
  return await apiClient.get<QueryResultSubscriptionListType>(`/info/subscribe/${params.userId}`)
}

const useSubscription = (userId: number) => {
  return useQuery({ 
    queryKey: ['subscription', { userId }], 
    queryFn: fetchSubscriptionListByUserId, 
    enabled: userId !== 0
  })
}

export default useSubscription