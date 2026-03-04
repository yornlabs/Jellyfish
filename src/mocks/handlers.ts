import { http, HttpResponse } from 'msw'
import type { DemoItem } from '../services/exampleApi'

const demoList: DemoItem[] = [
  {
    id: '1',
    name: 'Mock 任务一',
    status: 'active',
    createdAt: '2024-01-15',
  },
  {
    id: '2',
    name: 'Mock 任务二',
    status: 'inactive',
    createdAt: '2024-01-20',
  },
  {
    id: '3',
    name: 'Mock 任务三',
    status: 'active',
    createdAt: '2024-02-01',
  },
]

export const handlers = [
  // 示例列表接口
  http.get('/api/demo/list', () => {
    return HttpResponse.json(demoList, { status: 200 })
  }),
]

