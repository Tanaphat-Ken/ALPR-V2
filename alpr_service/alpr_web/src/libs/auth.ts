import apiClient from '@/libs/apiClient'

export type LoginRequest = {
  email: string
  password: string
}

export type LoginResponse = {
  access_token: string
  token_type: string
  user_id: number
  email: string
  message: string
}

export type RegisterRequest = {
  email: string
  password: string
}

export type RegisterResponse = {
  user_id: number
  email: string
  message: string
}

export type UserInfoResponse = {
  user_id: number
  email: string
  created_at: string
  updated_at: string
}

/**
 * Login user with email and password
 */
export const login = async (data: LoginRequest): Promise<LoginResponse> => {
  return await apiClient.post<LoginResponse>('/auth/login', data)
}

/**
 * Register new user
 */
export const register = async (data: RegisterRequest): Promise<RegisterResponse> => {
  return await apiClient.post<RegisterResponse>('/auth/register', data)
}

/**
 * Get current user information (requires authentication)
 */
export const getCurrentUser = async (): Promise<UserInfoResponse> => {
  const token = getToken()
  return await apiClient.get<UserInfoResponse>('/auth/me', {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
}

/**
 * Logout user (API call + clear local storage)
 */
export const logoutAPI = async (): Promise<{ message: string; user_id: number }> => {
  const token = getToken()
  const result = await apiClient.post<{ message: string; user_id: number }>('/auth/logout', {}, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
  logout() // Clear local storage
  return result
}

/**
 * Logout user (clear local storage)
 */
export const logout = (): void => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('token')
    localStorage.removeItem('userId')
  }
}

/**
 * Get stored auth token
 */
export const getToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token')
  }
  return null
}

/**
 * Get stored user ID
 */
export const getUserId = (): number | null => {
  if (typeof window !== 'undefined') {
    const userId = localStorage.getItem('userId')
    return userId ? parseInt(userId, 10) : null
  }
  return null
}

/**
 * Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  return !!getToken()
}
