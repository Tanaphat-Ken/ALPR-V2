import axios, { AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_BASE_API_GATE_WAY_URL || 'http://localhost:8092/api/v1'
})

const handleResponse = <T>(response: AxiosResponse<T>) => response.data

const handleError = (error: AxiosError) => {
  console.error(error)
  throw error
}

const apiClient = {
  get: <T>(url: string, config?: AxiosRequestConfig): Promise<T> =>
    api.get<T>(url, config).then(handleResponse).catch(handleError),

  post: <T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> =>
    api.post<T>(url, data, config).then(handleResponse).catch(handleError),

  put: <T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> =>
    api.put<T>(url, data, config).then(handleResponse).catch(handleError),

  delete: <T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> =>
    api.delete<T>(url, { ...config, data }).then(handleResponse).catch(handleError),
}

export default apiClient
