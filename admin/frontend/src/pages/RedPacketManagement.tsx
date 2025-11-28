import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Table,
  Card,
  Button,
  Input,
  Select,
  DatePicker,
  Space,
  Tag,
  Modal,
  message,
  Statistic,
  Row,
  Col,
  Tooltip,
  Popconfirm,
  Spin,
} from 'antd'
import {
  SearchOutlined,
  EyeOutlined,
  ReloadOutlined,
  DeleteOutlined,
  DollarOutlined,
  GiftOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import dayjs, { Dayjs } from 'dayjs'
import type { ColumnsType } from 'antd/es/table'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts'
import { Typography } from 'antd'
import { redpacketApi } from '../utils/api'

const { Text } = Typography

const { RangePicker } = DatePicker

interface RedPacket {
  id: number
  uuid: string
  sender_id: number
  sender_tg_id?: number
  sender_username?: string
  sender_name?: string
  chat_id?: number
  chat_title?: string
  currency: string
  packet_type: string
  total_amount: number
  total_count: number
  claimed_amount: number
  claimed_count: number
  status: string
  message?: string
  expires_at?: string
  created_at: string
  completed_at?: string
}

export default function RedPacketManagement() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [filters, setFilters] = useState({
    status: undefined as string | undefined,
    currency: undefined as string | undefined,
    packet_type: undefined as string | undefined,
    uuid: undefined as string | undefined,
    dateRange: undefined as [Dayjs, Dayjs] | undefined,
  })
  const [trendDays, setTrendDays] = useState(30)

  // 获取红包列表
  const { data: listData, isLoading } = useQuery({
    queryKey: ['redpackets', page, pageSize, filters],
    queryFn: async () => {
      const response = await redpacketApi.list({
        page,
        page_size: pageSize,
        status: filters.status,
        currency: filters.currency,
        packet_type: filters.packet_type,
        uuid: filters.uuid,
        start_date: filters.dateRange?.[0]?.toISOString(),
        end_date: filters.dateRange?.[1]?.toISOString(),
      })
      return response.data
    },
  })

  // 获取统计信息
  const { data: statsData } = useQuery({
    queryKey: ['redpackets-stats'],
    queryFn: async () => {
      const response = await redpacketApi.getStats()
      return response.data
    },
  })

  // 获取趋势数据
  const { data: trendData, isLoading: trendLoading } = useQuery({
    queryKey: ['redpackets-trend', trendDays],
    queryFn: async () => {
      const response = await redpacketApi.getTrend({ days: trendDays })
      return response.data
    },
  })

  // 删除红包
  const deleteMutation = useMutation({
    mutationFn: (id: number) => redpacketApi.delete(id),
    onSuccess: () => {
      message.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['redpackets'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '删除失败')
    },
  })

  // 退款
  const refundMutation = useMutation({
    mutationFn: (id: number) => redpacketApi.refund(id),
    onSuccess: () => {
      message.success('退款成功')
      queryClient.invalidateQueries({ queryKey: ['redpackets'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '退款失败')
    },
  })

  // 延长过期时间
  const extendMutation = useMutation({
    mutationFn: ({ id, hours }: { id: number; hours: number }) => redpacketApi.extend(id, hours),
    onSuccess: () => {
      message.success('延长成功')
      queryClient.invalidateQueries({ queryKey: ['redpackets'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '延长失败')
    },
  })

  // 强制完成
  const completeMutation = useMutation({
    mutationFn: (id: number) => redpacketApi.complete(id),
    onSuccess: () => {
      message.success('完成成功')
      queryClient.invalidateQueries({ queryKey: ['redpackets'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '完成失败')
    },
  })

  const handleExtend = (id: number) => {
    Modal.confirm({
      title: '延长过期时间',
      content: '请选择延长的小时数',
      okText: '确定',
      cancelText: '取消',
      onOk: () => {
        extendMutation.mutate({ id, hours: 24 })
      },
    })
  }

  const columns: ColumnsType<RedPacket> = [
    {
      title: 'UUID',
      dataIndex: 'uuid',
      key: 'uuid',
      width: 200,
      ellipsis: true,
    },
    {
      title: '发送者',
      key: 'sender',
      width: 150,
      render: (_, record) => (
        <div>
          <div>{record.sender_name || record.sender_username || `ID: ${record.sender_id}`}</div>
          {record.sender_tg_id && (
            <div style={{ fontSize: 12, color: '#999' }}>TG: {record.sender_tg_id}</div>
          )}
        </div>
      ),
    },
    {
      title: '群组',
      dataIndex: 'chat_title',
      key: 'chat_title',
      width: 150,
      render: (text, record) => (
        <div>
          <div>{text || '未指定'}</div>
          {record.chat_id && (
            <div style={{ fontSize: 12, color: '#999' }}>ID: {record.chat_id}</div>
          )}
        </div>
      ),
    },
    {
      title: '币种',
      dataIndex: 'currency',
      key: 'currency',
      width: 80,
      render: (currency) => <Tag color="blue">{currency.toUpperCase()}</Tag>,
    },
    {
      title: '类型',
      dataIndex: 'packet_type',
      key: 'packet_type',
      width: 100,
      render: (type) => {
        const typeMap: Record<string, string> = {
          random: '拼手气',
          equal: '平分',
          exclusive: '专属',
        }
        return <Tag>{typeMap[type] || type}</Tag>
      },
    },
    {
      title: '总金额',
      dataIndex: 'total_amount',
      key: 'total_amount',
      width: 120,
      render: (amount, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{Number(amount).toFixed(4)}</div>
          <div style={{ fontSize: 12, color: '#999' }}>
            已领: {Number(record.claimed_amount).toFixed(4)}
          </div>
        </div>
      ),
    },
    {
      title: '数量',
      key: 'count',
      width: 100,
      render: (_, record) => (
        <div>
          <div>{record.claimed_count} / {record.total_count}</div>
          <div style={{ fontSize: 12, color: '#999' }}>
            {record.total_count > 0
              ? ((record.claimed_count / record.total_count) * 100).toFixed(1)
              : 0}%
          </div>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const statusMap: Record<string, { text: string; color: string }> = {
          active: { text: '进行中', color: 'green' },
          completed: { text: '已完成', color: 'blue' },
          expired: { text: '已过期', color: 'orange' },
          refunded: { text: '已退款', color: 'red' },
        }
        const config = statusMap[status] || { text: status, color: 'default' }
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/redpackets/${record.id}`)}
            />
          </Tooltip>
          {record.status === 'active' && (
            <>
              <Tooltip title="延长24小时">
                <Button
                  type="link"
                  onClick={() => handleExtend(record.id)}
                  loading={extendMutation.isPending}
                >
                  延长
                </Button>
              </Tooltip>
              <Tooltip title="强制完成">
                <Popconfirm
                  title="确定要强制完成这个红包吗？"
                  onConfirm={() => completeMutation.mutate(record.id)}
                >
                  <Button type="link" loading={completeMutation.isPending}>
                    完成
                  </Button>
                </Popconfirm>
              </Tooltip>
            </>
          )}
          {record.status !== 'refunded' && record.claimed_count === 0 && (
            <Tooltip title="退款">
              <Popconfirm
                title="确定要退款这个红包吗？"
                onConfirm={() => refundMutation.mutate(record.id)}
              >
                <Button type="link" danger loading={refundMutation.isPending}>
                  退款
                </Button>
              </Popconfirm>
            </Tooltip>
          )}
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个红包吗？此操作不可恢复！"
              onConfirm={() => deleteMutation.mutate(record.id)}
            >
              <Button
                type="link"
                danger
                icon={<DeleteOutlined />}
                loading={deleteMutation.isPending}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>红包管理</h1>

      {/* 统计卡片 */}
      {statsData && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总红包数"
                value={statsData.total_count}
                prefix={<GiftOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总金额"
                value={Number(statsData.total_amount).toFixed(2)}
                prefix={<DollarOutlined />}
                suffix={statsData.total_amount ? 'USDT' : ''}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="平均金额"
                value={Number(statsData.average_amount).toFixed(2)}
                prefix={<DollarOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="领取率"
                value={statsData.claim_rate}
                suffix="%"
                precision={2}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 筛选栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input
            placeholder="搜索 UUID"
            prefix={<SearchOutlined />}
            style={{ width: 200 }}
            value={filters.uuid}
            onChange={(e) => setFilters({ ...filters, uuid: e.target.value || undefined })}
            allowClear
          />
          <Select
            placeholder="状态"
            style={{ width: 120 }}
            value={filters.status}
            onChange={(value) => setFilters({ ...filters, status: value })}
            allowClear
          >
            <Select.Option value="active">进行中</Select.Option>
            <Select.Option value="completed">已完成</Select.Option>
            <Select.Option value="expired">已过期</Select.Option>
            <Select.Option value="refunded">已退款</Select.Option>
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
          <Select
            placeholder="类型"
            style={{ width: 120 }}
            value={filters.packet_type}
            onChange={(value) => setFilters({ ...filters, packet_type: value })}
            allowClear
          >
            <Select.Option value="random">拼手气</Select.Option>
            <Select.Option value="equal">平分</Select.Option>
            <Select.Option value="exclusive">专属</Select.Option>
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
                status: undefined,
                currency: undefined,
                packet_type: undefined,
                uuid: undefined,
                dateRange: undefined,
              })
              queryClient.invalidateQueries({ queryKey: ['redpackets'] })
            }}
          >
            重置
          </Button>
        </Space>
      </Card>

      {/* 统计图表 */}
      <Card
        title={
          <Space>
            <BarChartOutlined />
            <span>红包趋势分析</span>
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
              <Card size="small" title="红包数量趋势">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trendData.dates?.map((date: string, index: number) => ({
                    date: dayjs(date).format('MM-DD'),
                    count: trendData.counts?.[index] || 0,
                  })) || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="count" stroke="#8884d8" name="红包数量" />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col span={12}>
              <Card size="small" title="红包金额趋势">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={trendData.dates?.map((date: string, index: number) => ({
                    date: dayjs(date).format('MM-DD'),
                    总金额: Number(trendData.amounts?.[index] || 0).toFixed(2),
                    已领取: Number(trendData.claimed_amounts?.[index] || 0).toFixed(2),
                  })) || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Bar dataKey="总金额" fill="#8884d8" />
                    <Bar dataKey="已领取" fill="#82ca9d" />
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

