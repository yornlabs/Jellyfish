import { useEffect, useState } from 'react'
import { Card, Table, Tag, message } from 'antd'
import type { TableColumnsType } from 'antd'
import { fetchDemoList, type DemoItem } from '../services/exampleApi'
import { useTranslation } from 'react-i18next'

const ListPage: React.FC = () => {
  const { t } = useTranslation(['list', 'common'])
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<DemoItem[]>([])

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        // 这里调用示例接口，占位为本地假数据
        const res = await fetchDemoList()
        setData(res)
      } catch (error) {
        // 真正项目里替换为你的错误处理逻辑
        message.error(t('list.messageError'))
      } finally {
        setLoading(false)
      }
    }

    // 实际项目中可以按需触发
    void load()
  }, [])

  const columns: TableColumnsType<DemoItem> = [
    {
      title: t('list.columns.id'),
      dataIndex: 'id',
      key: 'id',
      width: 120,
    },
    {
      title: t('list.columns.name'),
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: t('list.columns.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: DemoItem['status']) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? t('list.status.active') : t('list.status.inactive')}
        </Tag>
      ),
    },
    {
      title: t('list.columns.createdAt'),
      dataIndex: 'createdAt',
      key: 'createdAt',
    },
  ]

  return (
    <Card title={t('list.title')}>
      <p className="text-gray-600 mb-4">
        {t('list.description')}
      </p>
      <Table<DemoItem>
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={data}
      />
    </Card>
  )
}

export default ListPage

