import { ServiceType } from '@/shared/types/subscription'

type GetServiceTokenParams = {
  userId: number
  serviceType: ServiceType
}

type ServiceTokenUsage = {
  token_key: string
  usage_per_hour: number[]
}

type ServiceToken = {
  key: string
  user_id: number
  name: string
  service_type: string,
  expire_time: string
}

type CreateServiceTokenBody = {
  user_id: number
  service_type: ServiceType
  expire_time: string | null
  token_name: string
}

type EditServiceTokenBody = {
  key: string
  token_name: string
}

type DeleteServiceTokenBody = {
  key: string
}

export type {
  GetServiceTokenParams,
  ServiceTokenUsage,
  ServiceToken,
  CreateServiceTokenBody,
  EditServiceTokenBody,
  DeleteServiceTokenBody
}