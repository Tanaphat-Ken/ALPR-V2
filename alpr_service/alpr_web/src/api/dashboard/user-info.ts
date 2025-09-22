import { useQuery, QueryFunctionContext } from '@tanstack/react-query'

import apiClient from '@/shared/libs/apiClient'

type FetchUserInfoType = {
  userId: number
}

type QueryResultUserInfoType = {
  user_id: number
  email: string
  created_at: string
  updated_at: string
}

const fetchUserInfoById = async ({ queryKey }: QueryFunctionContext<[string, FetchUserInfoType]>) => {
  const [_key, params] = queryKey
  return await apiClient.get<QueryResultUserInfoType[]>(`/info/user/${params.userId}`)
}

const useUserInfo = (userId: number) => {
  return useQuery({ 
    queryKey: ['userInfo', { userId }], 
    queryFn: fetchUserInfoById 
  })
}

export default useUserInfo