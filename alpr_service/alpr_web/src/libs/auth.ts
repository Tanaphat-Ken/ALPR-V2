import apiClient from '@/libs/apiClient'

export type LoginRequest = {
  email: string
  password: string
}

export type LoginResponse = {
  token: string
  userId: number
  email: string
}

export type RegisterRequest = {
  name: string
  email: string
  password: string
}

export type RegisterResponse = {
  userId: number
  email: string
  message: string
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
