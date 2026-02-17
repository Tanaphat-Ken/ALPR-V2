import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import apiClient from '@/shared/libs/apiClient'
import type { SubscriptionType, SubscriptionDetailsType } from '@/shared/types/subscription'

type FetchSubscriptionListType = {
  userId: number
}

type QueryResultSubscriptionListType = {
  user_id: number
  subscriptions: SubscriptionType[]
}

const fetchSubscriptionListByUserId = async ({ queryKey }: { queryKey: [string, FetchSubscriptionListType] }) => {
  const [_key, params] = queryKey
  return await apiClient.get<QueryResultSubscriptionListType>(`/info/subscribe/${params.userId}`)
}

const fetchAllServices = async () => {
  return await apiClient.get<SubscriptionDetailsType[]>('/subscription/get_all_service')
}

export const useServices = () => {
  return useQuery({
    queryKey: ['services'],
    queryFn: fetchAllServices
  })
}

export const useSubscription = (userId: number) => {
  return useQuery({ 
    queryKey: ['subscription', { userId }], 
    queryFn: fetchSubscriptionListByUserId, 
    enabled: !!userId
  })
}

export const useChangeSubscription = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: { user_id: number, sub_id: number }) => {
      return await apiClient.put('/subscription/change_subscription', data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscription'] })
    }
  })
}

export const useCancelSubscription = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (user_sub_id: number) => {
      return await apiClient.delete(`/subscription/cancel_subscription/${user_sub_id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscription'] })
    }
  })
}

export default useSubscription
