import { QueryFunctionContext } from '@tanstack/react-query'

import apiClient from '@/shared/libs/apiClient'
import { convertToDateString } from '@/shared/libs/times'
import type { 
  GetServiceTokenParams, 
  ServiceTokenUsage, 
  ServiceToken,
  CreateServiceTokenBody,
  EditServiceTokenBody,
  DeleteServiceTokenBody,
} from './type'

const transformData = (data: ServiceToken[]) => {
  return data.map((item, index) => ({
    key: index,
    tokenName: item.name,
    expireDate: convertToDateString(item.expire_time),
    tokenKey: item.key, 
  }))
}

export const getServiceTokenUsageList = async ({ queryKey }: QueryFunctionContext<[string, GetServiceTokenParams]>) => {
  const [_key, params] = queryKey
  const data = await apiClient.post<ServiceTokenUsage[]>(
    '/tokens_usage_per_hour', { 
      user_id: params.userId, 
      service_type: params.serviceType
    })

  return data.map(item => {
    return {
      ...item,
      usage_per_hour: item.usage_per_hour.reverse()
    }
  })
}

export const getServiceTokenList = async ({ queryKey }: QueryFunctionContext<[string, GetServiceTokenParams]>) => {
  const [_key, params] = queryKey
  const data = await apiClient.get<ServiceToken[]>(`/tokens/${params.userId}?service_type=${params.serviceType}`)
  return transformData(data)
}

export const createServiceToken = async (data: CreateServiceTokenBody) => await apiClient.post('/tokens', data)   
export const deleteServiceToken = async (data: DeleteServiceTokenBody) => await apiClient.delete('/tokens', data)   
export const editServiceToken = async (data: EditServiceTokenBody) => await apiClient.put('/tokens', data)   