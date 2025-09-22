import axios, { AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_UPLOAD_IMAGE || 'http://localhost:8089/api/v1'
})

const handleResponse = <T>(response: AxiosResponse<T>) => response.data

const handleError = (error: AxiosError) => {
  throw error
}

const plateRecognizerService = {
  post: <T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> =>
    api.post<T>(url, data, config).then(handleResponse).catch(handleError),
}

export default plateRecognizerService

