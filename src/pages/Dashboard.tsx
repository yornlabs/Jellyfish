import { Card, Col, Row, Statistic, Table, Tag } from 'antd'
import type { TableColumnsType } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'
import { useCounter } from '../hooks/useCounter'
import { useTranslation } from 'react-i18next'

interface DataType {
  key: string
  name: string
  status: 'active' | 'inactive'
  createdAt: string
}

const dataSource: DataType[] = [
  {
    key: '1',
    name: '示例任务一',
    status: 'active',
    createdAt: '2024-01-15',
  },
  {
    key: '2',
    name: '示例任务二',
    status: 'inactive',
    createdAt: '2024-01-20',
  },
]

const Dashboard: React.FC = () => {
  const { t } = useTranslation(['dashboard', 'common'])
  const { count, increment, decrement, reset } = useCounter(10)

  const columns: TableColumnsType<DataType> = [
    {
      title: t('dashboard.columns.name'),
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: t('dashboard.columns.status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: DataType['status']) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? t('dashboard.status.active') : t('dashboard.status.inactive')}
        </Tag>
      ),
    },
    {
      title: t('dashboard.columns.createdAt'),
      dataIndex: 'createdAt',
      key: 'createdAt',
    },
  ]

  return (
    <div className="space-y-4">
      <Row gutter={16}>
        <Col xs={24} md={8}>
          <Card bordered={false}>
            <Statistic
              title={t('dashboard.todayVisits')}
              value={1128}
              prefix={<ArrowUpOutlined />}
              valueStyle={{ color: '#3f8600' }}
              suffix={t('dashboard.visitsUnit')}
            />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card bordered={false}>
            <Statistic
              title={t('dashboard.newUsers')}
              value={32}
              prefix={<ArrowUpOutlined />}
              valueStyle={{ color: '#3f8600' }}
              suffix={t('dashboard.usersUnit')}
            />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card bordered={false}>
            <Statistic
              title={t('dashboard.systemLoad')}
              value={73}
              prefix={<ArrowDownOutlined />}
              valueStyle={{ color: '#cf1322' }}
              suffix="%"
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Card title={t('dashboard.counterTitle')} bordered={false}>
            <div className="flex items-center gap-4">
              <span className="text-4xl font-bold text-blue-600">{count}</span>
              <div className="space-x-2">
                <button
                  className="px-3 py-1 rounded bg-blue-600 text-white text-sm"
                  onClick={increment}
                >
                  {t('dashboard.counter.inc')}
                </button>
                <button
                  className="px-3 py-1 rounded bg-gray-200 text-sm"
                  onClick={decrement}
                >
                  {t('dashboard.counter.dec')}
                </button>
                <button
                  className="px-3 py-1 rounded bg-red-500 text-white text-sm"
                  onClick={reset}
                >
                  {t('common:reset')}
                </button>
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card title={t('dashboard.tableTitle')} bordered={false}>
            <Table<DataType>
              rowKey="key"
              columns={columns}
              dataSource={dataSource}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard

