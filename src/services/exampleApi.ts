import { get } from './http'

export interface DemoItem {
  id: string
  name: string
  status: 'active' | 'inactive'
  createdAt: string
}

export const fetchDemoList = () => {
  // 实际项目中这里请求后端接口，这里先给出占位路径
  return get<DemoItem[]>('/demo/list')
}

