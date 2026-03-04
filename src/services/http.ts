import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'

const baseURL = '/api'

const http: AxiosInstance = axios.create({
  baseURL,
  timeout: 10000,
})

http.interceptors.request.use(
  (config) => {
    // 这里可以注入 token 等信息
    return config
  },
  (error) => Promise.reject(error),
)

http.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  (error) => {
    // 这里可以统一处理错误提示、跳转登录等
    return Promise.reject(error)
  },
)

export const get = <T = unknown>(url: string, config?: AxiosRequestConfig) =>
  http.get<T>(url, config)

export const post = <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
  http.post<T>(url, data, config)

export const put = <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
  http.put<T>(url, data, config)

export const del = <T = unknown>(url: string, config?: AxiosRequestConfig) =>
  http.delete<T>(url, config)

export default http

