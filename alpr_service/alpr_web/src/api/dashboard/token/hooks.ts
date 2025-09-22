import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDispatch } from 'react-redux'

import { setModalErrorMsg } from '@/shared/store/dashboard/shared'
import type { AppDispatch } from '@/shared/store'
import type { ServiceType } from '@/shared/types/subscription'
import { 
  getServiceTokenList, 
  getServiceTokenUsageList,
  createServiceToken,
  editServiceToken,
  deleteServiceToken
} from './requests'

const useTokenUsage = (userId: number, serviceType: ServiceType) => {
  return useQuery({ 
    queryKey: ['token-usage', { userId, serviceType }], 
    queryFn: getServiceTokenUsageList, 
    enabled: userId !== 0
  })
}

const useTokens = (userId: number, serviceType: ServiceType) => {
  return useQuery({
    queryKey: ['tokens', { userId, serviceType }], 
    queryFn: getServiceTokenList, 
    enabled: userId !== 0
  })
}

const useNewToken = () => {
  const queryClient = useQueryClient()
  const dispatch = useDispatch<AppDispatch>()

  return useMutation({
    mutationFn: createServiceToken,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tokens'] }),
    onError: (error) => dispatch(setModalErrorMsg(error.message)),
  })
}

const useDeleteToken = () => {
  const queryClient = useQueryClient()
  const dispatch = useDispatch<AppDispatch>()

  return useMutation({
    mutationFn: deleteServiceToken,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tokens'] }),
    onError: (error) => dispatch(setModalErrorMsg(error.message))
  })
}

const useEditToken = () => {
  const queryClient = useQueryClient()
  const dispatch = useDispatch<AppDispatch>()

  return useMutation({
    mutationFn: editServiceToken,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tokens'] }),
    onError: (error) => dispatch(setModalErrorMsg(error.message))
  })
}

export { useTokenUsage, useTokens, useNewToken, useDeleteToken, useEditToken }