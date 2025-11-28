import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Table,
  Card,
  Button,
  Input,
  DatePicker,
  Space,
  Tag,
  Statistic,
  Row,
  Col,
  Spin,
  Typography,
  Select,
} from 'antd'
import {
  ReloadOutlined,
  CalendarOutlined,
  TrophyOutlined,
  UserOutlined,
} from '@ant-design/icons'
import dayjs, { Dayjs } from 'dayjs'
import type { ColumnsType } from 'antd/es/table'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { checkinApi } from '../utils/api'

const { RangePicker } = DatePicker
const { Text } = Typography

interface CheckinRecord {
  id: number
  user_id: number
  user_tg_id?: number
  user_username?: string
  user_name?: string
  checkin_date: string
  day_of_streak: number
  reward_points: number
  created_at: string
}

export default function CheckinManagement() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [filters, setFilters] = useState({
    user_id: undefined as number | undefined,
    start_date: undefined as Dayjs | undefined,
    end_date: undefined as Dayjs | undefined,
  })
  const [trendDays, setTrendDays] = useState(30)

  // 获取签到列表
  const { data: listData, isLoading } = useQuery({
    queryKey: ['checkins', page, pageSize, filters],
    queryFn: async () => {
      const response = await checkinApi.list({
        page,
        page_size: pageSize,
        user_id: filters.user_id,
        start_date: filters.start_date?.toISOString(),
        end_date: filters.end_date?.toISOString(),
      })
      return response.data
    },
  })

  // 获取统计信息
  const { data: statsData } = useQuery({
    queryKey: ['checkins-stats'],
    queryFn: async () => {
      const response = await checkinApi.getStats()
      return response.data
    },
  })

  // 获取趋势数据
  const { data: trendData, isLoading: trendLoading } = useQuery({
    queryKey: ['checkins-trend', trendDays],
    queryFn: async () => {
      const response = await checkinApi.getTrend({ days: trendDays })
      return response.data
    },
  })

  const columns: ColumnsType<CheckinRecord> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '用户',
      key: 'user',
      width: 200,
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
      title: '签到日期',
      dataIndex: 'checkin_date',
      key: 'checkin_date',
      width: 150,
      render: (date) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '连续天数',
      dataIndex: 'day_of_streak',
      key: 'day_of_streak',
      width: 100,
      render: (day) => (
        <Tag color={day === 7 ? 'gold' : day >= 3 ? 'orange' : 'blue'}>
          第 {day} 天
        </Tag>
      ),
    },
    {
      title: '奖励积分',
      dataIndex: 'reward_points',
      key: 'reward_points',
      width: 120,
      render: (points) => (
        <Text strong style={{ color: '#52c41a' }}>
          +{points} Points
        </Text>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
  ]

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>签到管理</h1>

      {/* 统计卡片 */}
      {statsData && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总签到数"
                value={statsData.total_checkins}
                prefix={<CalendarOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="今日签到"
                value={statsData.today_checkins}
                prefix={<CalendarOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总奖励积分"
                value={statsData.total_rewards}
                prefix={<TrophyOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="平均连续签到"
                value={statsData.average_streak}
                prefix={<UserOutlined />}
                suffix="天"
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 统计图表 */}
      <Card
        title={
          <Space>
            <CalendarOutlined />
            <span>签到趋势分析</span>
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
        ) : trendData?.data ? (
          <Row gutter={16}>
            <Col span={12}>
              <Card size="small" title="签到数量趋势">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trendData.data.dates.map((date: string, index: number) => ({
                    date: dayjs(date).format('MM-DD'),
                    count: trendData.data.counts[index],
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="count" stroke="#8884d8" name="签到数量" />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col span={12}>
              <Card size="small" title="奖励积分趋势">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={trendData.data.dates.map((date: string, index: number) => ({
                    date: dayjs(date).format('MM-DD'),
                    奖励: trendData.data.rewards[index],
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="奖励" fill="#52c41a" />
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
          <RangePicker
            value={filters.start_date && filters.end_date ? [filters.start_date, filters.end_date] : null}
            onChange={(dates) => {
              if (dates && dates[0] && dates[1]) {
                setFilters({
                  ...filters,
                  start_date: dates[0],
                  end_date: dates[1],
                })
              } else {
                setFilters({
                  ...filters,
                  start_date: undefined,
                  end_date: undefined,
                })
              }
            }}
            allowClear
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              setFilters({
                user_id: undefined,
                start_date: undefined,
                end_date: undefined,
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

