import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  Card, Row, Col, Statistic, Spin, Button, Select, Empty, Tag, Progress,
  Table, Alert
} from 'antd'
import { 
  SafetyOutlined, StopOutlined, WarningOutlined, ReloadOutlined,
  MobileOutlined, GlobalOutlined, BellOutlined, DollarOutlined,
  ArrowUpOutlined, ArrowDownOutlined
} from '@ant-design/icons'
import { 
  LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts'
import { securityApi } from '../utils/api'
import dayjs from 'dayjs'

const { Option } = Select

const COLORS = ['#ff4d4f', '#faad14', '#52c41a', '#1890ff', '#722ed1', '#13c2c2']

const riskColors: Record<string, string> = {
  low: '#52c41a',
  medium: '#faad14',
  high: '#ff4d4f',
  critical: '#a61d24'
}

export default function SecurityDashboard() {
  const [days, setDays] = useState(7)

  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['security-stats'],
    queryFn: async () => {
      const response = await securityApi.getStats()
      return response.data.data
    },
  })

  const { data: trends, isLoading: trendsLoading, refetch: refetchTrends } = useQuery({
    queryKey: ['security-trends', days],
    queryFn: async () => {
      const response = await securityApi.getTrends({ days })
      return response.data.data
    },
  })

  const { data: riskUsers, isLoading: riskLoading } = useQuery({
    queryKey: ['risk-users'],
    queryFn: async () => {
      const response = await securityApi.getRiskUsers({ page: 1, page_size: 5 })
      return response.data.data
    },
  })

  const { data: alerts, isLoading: alertsLoading } = useQuery({
    queryKey: ['recent-alerts'],
    queryFn: async () => {
      const response = await securityApi.getAlerts({ resolved: false, page: 1, page_size: 5 })
      return response.data.data
    },
  })

  const handleRefresh = () => {
    refetchStats()
    refetchTrends()
  }

  if (statsLoading) {
    return <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: 50 }} />
  }

  const riskColumns = [
    {
      title: '用戶',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: any) => (
        <span>@{text || record.telegram_id}</span>
      ),
    },
    {
      title: '警報次數',
      dataIndex: 'alert_count',
      key: 'alert_count',
      render: (count: number) => (
        <Tag color={count > 5 ? 'red' : count > 2 ? 'orange' : 'default'}>{count}</Tag>
      ),
    },
    {
      title: '風險等級',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (level: string) => (
        <Tag color={riskColors[level]}>{level?.toUpperCase()}</Tag>
      ),
    },
    {
      title: '最後警報',
      dataIndex: 'last_alert',
      key: 'last_alert',
      render: (date: string) => date ? dayjs(date).format('MM-DD HH:mm') : '-',
    },
  ]

  const alertColumns = [
    {
      title: '類型',
      dataIndex: 'alert_type',
      key: 'alert_type',
      render: (type: string) => {
        const typeLabels: Record<string, string> = {
          new_account_claim: '新帳號搶包',
          same_ip_sessions: '同IP多會話',
          high_ip_claim_rate: 'IP高頻請求',
          device_mismatch: '設備異常',
        }
        return typeLabels[type] || type
      },
    },
    {
      title: '風險',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (level: string) => (
        <Tag color={riskColors[level]}>{level}</Tag>
      ),
    },
    {
      title: 'IP',
      dataIndex: 'ip_address',
      key: 'ip_address',
      ellipsis: true,
    },
    {
      title: '時間',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('MM-DD HH:mm'),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>
          <SafetyOutlined style={{ marginRight: 8 }} />
          安全中心
        </h1>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <Select value={days} onChange={setDays} style={{ width: 120 }}>
            <Option value={7}>最近7天</Option>
            <Option value={14}>最近14天</Option>
            <Option value={30}>最近30天</Option>
          </Select>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
        </div>
      </div>

      {/* 統計卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="今日攔截"
              value={stats?.today_blocked || 0}
              prefix={<StopOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
              suffix={
                stats?.blocked_change !== 0 && (
                  <span style={{ fontSize: 14, marginLeft: 8 }}>
                    {stats?.blocked_change > 0 ? (
                      <><ArrowUpOutlined style={{ color: '#ff4d4f' }} /> {stats.blocked_change}</>
                    ) : (
                      <><ArrowDownOutlined style={{ color: '#52c41a' }} /> {Math.abs(stats.blocked_change)}</>
                    )}
                  </span>
                )
              }
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="可疑帳號"
              value={stats?.suspicious_users || 0}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活躍設備"
              value={stats?.active_devices || 0}
              prefix={<MobileOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="可疑 IP"
              value={stats?.suspicious_ips || 0}
              prefix={<GlobalOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card>
            <Statistic
              title="待解鎖 Stars"
              value={stats?.pending_stars || 0}
              prefix={<DollarOutlined />}
              precision={2}
              valueStyle={{ color: '#faad14' }}
              suffix="USDT"
            />
            <Progress 
              percent={70} 
              status="active" 
              strokeColor="#faad14"
              format={() => '冷卻期'}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Statistic
              title="未處理警報"
              value={stats?.pending_alerts || 0}
              prefix={<BellOutlined />}
              valueStyle={{ color: stats?.pending_alerts > 10 ? '#ff4d4f' : '#1890ff' }}
            />
            {stats?.pending_alerts > 10 && (
              <Alert 
                message="警報堆積，請盡快處理" 
                type="warning" 
                showIcon 
                style={{ marginTop: 8 }}
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* 趨勢圖表 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Card title="攔截趨勢" loading={trendsLoading}>
            {trends?.block_trends && trends.block_trends.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trends.block_trends.map((item: any) => ({
                  date: dayjs(item.date).format('MM-DD'),
                  count: item.count
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="count" 
                    stroke="#ff4d4f" 
                    name="攔截次數"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="暫無數據" />
            )}
          </Card>
        </Col>
        <Col span={8}>
          <Card title="攔截類型分布" loading={trendsLoading}>
            {trends?.type_stats && trends.type_stats.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={trends.type_stats.map((item: any) => ({
                      name: item.type === 'new_account_claim' ? '新帳號搶包' :
                            item.type === 'same_ip_sessions' ? '同IP多會話' :
                            item.type === 'high_ip_claim_rate' ? 'IP高頻' :
                            item.type === 'device_mismatch' ? '設備異常' : item.type,
                      value: item.count
                    }))}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={(entry: any) => `${entry.name}: ${entry.value}`}
                  >
                    {trends.type_stats.map((_: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="暫無數據" />
            )}
          </Card>
        </Col>
      </Row>

      {/* 風險用戶和最近警報 */}
      <Row gutter={16}>
        <Col span={12}>
          <Card 
            title="風險用戶 TOP 5" 
            loading={riskLoading}
            extra={<a href="/security/risk">查看全部</a>}
          >
            <Table
              columns={riskColumns}
              dataSource={riskUsers?.users || []}
              rowKey="user_id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card 
            title="最近警報" 
            loading={alertsLoading}
            extra={<a href="/security/alerts">查看全部</a>}
          >
            <Table
              columns={alertColumns}
              dataSource={alerts?.alerts || []}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
