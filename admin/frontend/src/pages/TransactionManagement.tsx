import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Table,
  Card,
  Button,
  Input,
  Select,
  DatePicker,
  Space,
  Tag,
  Statistic,
  Row,
  Col,
  Tooltip,
  Spin,
  Typography,
} from 'antd'
import {
  SearchOutlined,
  EyeOutlined,
  ReloadOutlined,
  DollarOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs, { Dayjs } from 'dayjs'
import type { ColumnsType } from 'antd/es/table'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts'
import { transactionApi } from '../utils/api'

const { RangePicker } = DatePicker
const { Text } = Typography

interface Transaction {
  id: number
  user_id: number
  user_tg_id?: number
  user_username?: string
  user_name?: string
  type: string
  currency: string
  amount: number
  balance_before?: number
  balance_after?: number
  ref_id?: string
  note?: string
  created_at: string
}

export default function TransactionManagement() {
  const navigate = useNavigate()
  
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [filters, setFilters] = useState({
    user_id: undefined as number | undefined,
    transaction_type: undefined as string | undefined,
    currency: undefined as string | undefined,
    ref_id: undefined as string | undefined,
    dateRange: undefined as [Dayjs, Dayjs] | undefined,
  })
  const [trendDays, setTrendDays] = useState(30)

  // 获取交易列表
  const { data: listData, isLoading } = useQuery({
    queryKey: ['transactions', page, pageSize, filters],
    queryFn: async () => {
      const response = await transactionApi.list({
        page,
        page_size: pageSize,
        user_id: filters.user_id,
        transaction_type: filters.transaction_type,
        currency: filters.currency,
        ref_id: filters.ref_id,
        start_date: filters.dateRange?.[0]?.toISOString(),
        end_date: filters.dateRange?.[1]?.toISOString(),
      })
      return response.data
    },
  })

  // 获取统计信息
  const { data: statsData } = useQuery({
    queryKey: ['transactions-stats'],
    queryFn: async () => {
      const response = await transactionApi.getStats()
      return response.data
    },
  })

  // 获取趋势数据
  const { data: trendData, isLoading: trendLoading } = useQuery({
    queryKey: ['transactions-trend', trendDays],
    queryFn: async () => {
      const response = await transactionApi.getTrend({ days: trendDays })
      return response.data
    },
  })

  const typeMap: Record<string, { text: string; color: string }> = {
    deposit: { text: '充值', color: 'green' },
    withdraw: { text: '提现', color: 'orange' },
    send: { text: '发送', color: 'blue' },
    receive: { text: '接收', color: 'cyan' },
    checkin: { text: '签到', color: 'purple' },
    invite: { text: '邀请', color: 'magenta' },
    admin_adjust: { text: '管理员调整', color: 'red' },
  }

  const currencyMap: Record<string, string> = {
    usdt: 'USDT',
    ton: 'TON',
    stars: 'Stars',
    points: 'Points',
  }

  const columns: ColumnsType<Transaction> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '用户',
      key: 'user',
      width: 150,
      render: (_, record) => (
        <div>
          <div>{record.user_name || record.user_username || `ID: ${record.user_id}`}</div>
          {record.user_tg_id && (
            <div style={{ fontSize: 12, color: '#999' }}>TG: {record.user_tg_id}</div>
          )}
        </div>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type) => {
        const config = typeMap[type] || { text: type, color: 'default' }
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '币种',
      dataIndex: 'currency',
      key: 'currency',
      width: 80,
      render: (currency) => <Tag color="blue">{currencyMap[currency] || currency}</Tag>,
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 150,
      render: (amount, record) => {
        const isPositive = Number(amount) >= 0
        return (
          <Space>
            {isPositive ? (
              <ArrowUpOutlined style={{ color: '#52c41a' }} />
            ) : (
              <ArrowDownOutlined style={{ color: '#ff4d4f' }} />
            )}
            <Text strong={true} style={{ color: isPositive ? '#52c41a' : '#ff4d4f' }}>
              {isPositive ? '+' : ''}{Number(amount).toFixed(4)}
            </Text>
            <Text type="secondary">{currencyMap[record.currency]}</Text>
          </Space>
        )
      },
    },
    {
      title: '余额变动',
      key: 'balance',
      width: 180,
      render: (_, record) => (
        <div>
          {record.balance_before !== null && record.balance_after !== null ? (
            <>
              <div style={{ fontSize: 12, color: '#999' }}>
                前: {Number(record.balance_before).toFixed(4)}
              </div>
              <div style={{ fontSize: 12, color: '#999' }}>
                后: {Number(record.balance_after).toFixed(4)}
              </div>
            </>
          ) : (
            <Text type="secondary">-</Text>
          )}
        </div>
      ),
    },
    {
      title: '关联ID',
      dataIndex: 'ref_id',
      key: 'ref_id',
      width: 150,
      ellipsis: true,
    },
    {
      title: '备注',
      dataIndex: 'note',
      key: 'note',
      width: 200,
      ellipsis: true,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right',
      render: (_, record) => (
        <Tooltip title="查看详情">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/transactions/${record.id}`)}
          />
        </Tooltip>
      ),
    },
  ]

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>交易管理</h1>

      {/* 统计卡片 */}
      {statsData && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总交易数"
                value={statsData.total_count}
                prefix={<DollarOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总收入"
                value={Number(statsData.total_income).toFixed(2)}
                prefix={<ArrowUpOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总支出"
                value={Number(statsData.total_expense).toFixed(2)}
                prefix={<ArrowDownOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="净额"
                value={Number(statsData.net_amount).toFixed(2)}
                prefix={<DollarOutlined />}
                valueStyle={{
                  color: Number(statsData.net_amount) >= 0 ? '#52c41a' : '#ff4d4f',
                }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 统计图表 */}
      <Card
        title={
          <Space>
            <BarChartOutlined />
            <span>交易趋势分析</span>
          </Space>
        }
        style={{ marginBottom: 16 }}
        extra={
          <Select
            value={trendDays}
            onChange={setTrendDays}
            style={{ width: 120 }}
          >
            <Select.Option value={7}>最近7天</Select.Option>
            <Select.Option value={30}>最近30天</Select.Option>
            <Select.Option value={90}>最近90天</Select.Option>
            <Select.Option value={365}>最近1年</Select.Option>
          </Select>
        }
      >
        {trendLoading ? (
          <div style={{ textAlign: 'center', padding: 50 }}>
            <Spin />
          </div>
        ) : trendData ? (
          <Row gutter={16}>
            <Col span={12}>
              <Card size="small" title="交易数量趋势">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trendData.dates?.map((date: string, index: number) => ({
                    date: dayjs(date).format('MM-DD'),
                    count: trendData.counts?.[index] || 0,
                  })) || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="count" stroke="#8884d8" name="交易数量" />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col span={12}>
              <Card size="small" title="收支趋势">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={trendData.dates?.map((date: string, index: number) => ({
                    date: dayjs(date).format('MM-DD'),
                    收入: Number(trendData.incomes?.[index] || 0).toFixed(2),
                    支出: Number(trendData.expenses?.[index] || 0).toFixed(2),
                  })) || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Bar dataKey="收入" fill="#52c41a" />
                    <Bar dataKey="支出" fill="#ff4d4f" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>
        ) : (
          <div style={{ textAlign: 'center', padding: 50 }}>
            <Text type="secondary">暂无数据</Text>
          </div>
        )}
      </Card>

      {/* 筛选栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input
            placeholder="用户ID"
            style={{ width: 120 }}
            type="number"
            value={filters.user_id}
            onChange={(e) => setFilters({ ...filters, user_id: e.target.value ? Number(e.target.value) : undefined })}
            allowClear
          />
          <Input
            placeholder="搜索关联ID"
            prefix={<SearchOutlined />}
            style={{ width: 200 }}
            value={filters.ref_id}
            onChange={(e) => setFilters({ ...filters, ref_id: e.target.value || undefined })}
            allowClear
          />
          <Select
            placeholder="交易类型"
            style={{ width: 120 }}
            value={filters.transaction_type}
            onChange={(value) => setFilters({ ...filters, transaction_type: value })}
            allowClear
          >
            <Select.Option value="deposit">充值</Select.Option>
            <Select.Option value="withdraw">提现</Select.Option>
            <Select.Option value="send">发送</Select.Option>
            <Select.Option value="receive">接收</Select.Option>
            <Select.Option value="checkin">签到</Select.Option>
            <Select.Option value="invite">邀请</Select.Option>
            <Select.Option value="admin_adjust">管理员调整</Select.Option>
          </Select>
          <Select
            placeholder="币种"
            style={{ width: 120 }}
            value={filters.currency}
            onChange={(value) => setFilters({ ...filters, currency: value })}
            allowClear
          >
            <Select.Option value="usdt">USDT</Select.Option>
            <Select.Option value="ton">TON</Select.Option>
            <Select.Option value="stars">Stars</Select.Option>
            <Select.Option value="points">Points</Select.Option>
          </Select>
          <RangePicker
            value={filters.dateRange}
            onChange={(dates) => setFilters({ ...filters, dateRange: dates as any })}
            allowClear
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              setFilters({
                user_id: undefined,
                transaction_type: undefined,
                currency: undefined,
                ref_id: undefined,
                dateRange: undefined,
              })
            }}
          >
            重置
          </Button>
        </Space>
      </Card>

      {/* 表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={listData?.items || []}
          loading={isLoading}
          rowKey="id"
          scroll={{ x: 1500 }}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: listData?.total || 0,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (newPage, newPageSize) => {
              setPage(newPage)
              setPageSize(newPageSize)
            },
          }}
        />
      </Card>
    </div>
  )
}

