import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, Row, Col, Statistic, Spin, Switch, Button, Select, Empty, Divider, Alert } from 'antd'
import { UserOutlined, GiftOutlined, DollarOutlined, ReloadOutlined, CalendarOutlined, UserAddOutlined, SafetyOutlined, StopOutlined, WarningOutlined, MobileOutlined } from '@ant-design/icons'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { dashboardApi, securityApi } from '../utils/api'
import dayjs from 'dayjs'

const { Option } = Select

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d']

export default function Dashboard() {
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [days, setDays] = useState(30)

  const { data: stats, isLoading, refetch: refetchStats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await dashboardApi.getStats()
      return response.data.data
    },
    refetchInterval: autoRefresh ? 30000 : false, // 30秒自动刷新
  })

  const { data: trends, isLoading: trendsLoading, refetch: refetchTrends } = useQuery({
    queryKey: ['dashboard-trends', days],
    queryFn: async () => {
      const response = await dashboardApi.getTrends({ days })
      return response.data.data
    },
  })

  const { data: distribution, isLoading: distributionLoading, refetch: refetchDistribution } = useQuery({
    queryKey: ['dashboard-distribution'],
    queryFn: async () => {
      const response = await dashboardApi.getDistribution()
      return response.data.data
    },
  })

  // 安全統計
  const { data: securityStats, refetch: refetchSecurity } = useQuery({
    queryKey: ['security-stats-overview'],
    queryFn: async () => {
      try {
        const response = await securityApi.getStats()
        return response.data.data
      } catch {
        return null
      }
    },
  })

  const handleRefresh = () => {
    refetchStats()
    refetchTrends()
    refetchDistribution()
    refetchSecurity()
  }

  if (isLoading) {
    return <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: 50 }} />
  }

  // 格式化图表数据
  const formatTrendData = (trends: any[]) => {
    return trends.map((item: any) => ({
      date: dayjs(item.date).format('MM-DD'),
      value: item.count || item.amount || 0,
    }))
  }

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>儀表盤</h1>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <Select value={days} onChange={setDays} style={{ width: 120 }}>
            <Option value={7}>最近7天</Option>
            <Option value={30}>最近30天</Option>
            <Option value={90}>最近90天</Option>
            <Option value={365}>最近1年</Option>
          </Select>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            刷新
          </Button>
          <span>
            自動刷新: <Switch checked={autoRefresh} onChange={setAutoRefresh} size="small" />
          </span>
        </div>
      </div>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="總用戶數"
              value={stats?.users?.total || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="今日新用戶"
              value={stats?.users?.new_today || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="今日簽到"
              value={stats?.checkin?.today || 0}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活躍邀請人"
              value={stats?.invite?.active_inviters || 0}
              prefix={<UserAddOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="總紅包數"
              value={stats?.red_packets?.total || 0}
              prefix={<GiftOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活躍紅包"
              value={stats?.red_packets?.active || 0}
              prefix={<GiftOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 安全統計 */}
      {securityStats && (
        <>
          <Divider orientation="left">
            <SafetyOutlined style={{ marginRight: 8 }} />
            安全監控
          </Divider>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="今日攔截"
                  value={securityStats.today_blocked || 0}
                  prefix={<StopOutlined />}
                  valueStyle={{ color: '#ff4d4f', fontSize: 20 }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="可疑帳號"
                  value={securityStats.suspicious_users || 0}
                  prefix={<WarningOutlined />}
                  valueStyle={{ color: '#faad14', fontSize: 20 }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="活躍設備"
                  value={securityStats.active_devices || 0}
                  prefix={<MobileOutlined />}
                  valueStyle={{ color: '#1890ff', fontSize: 20 }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="待處理警報"
                  value={securityStats.pending_alerts || 0}
                  prefix={<SafetyOutlined />}
                  valueStyle={{ color: securityStats.pending_alerts > 10 ? '#ff4d4f' : '#52c41a', fontSize: 20 }}
                />
              </Card>
            </Col>
          </Row>
          {securityStats.pending_alerts > 10 && (
            <Alert
              message="安全警報"
              description={`有 ${securityStats.pending_alerts} 條警報待處理，請前往安全中心查看。`}
              type="warning"
              showIcon
              action={
                <Button size="small" type="primary" href="/security/alerts">
                  查看警報
                </Button>
              }
              style={{ marginBottom: 16 }}
            />
          )}
        </>
      )}
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card>
            <Statistic
              title="總交易數"
              value={stats?.transactions?.total || 0}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Statistic
              title="總交易額 (USDT)"
              value={stats?.transactions?.volume || 0}
              prefix={<DollarOutlined />}
              precision={2}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Card>
        </Col>
      </Row>
      {/* 趨勢圖表 */}
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="用戶增長趨勢" loading={trendsLoading}>
            {trends?.user_trends && trends.user_trends.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={formatTrendData(trends.user_trends)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#1890ff" name="新用戶數" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="暫無數據" />
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="紅包創建趨勢" loading={trendsLoading}>
            {trends?.packet_trends && trends.packet_trends.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={formatTrendData(trends.packet_trends)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#ff4d4f" name="紅包數" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="暫無數據" />
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="交易趨勢" loading={trendsLoading}>
            {trends?.transaction_trends && trends.transaction_trends.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trends.transaction_trends.map((item: any) => ({
                  date: dayjs(item.date).format('MM-DD'),
                  amount: item.total_amount || 0,
                  count: item.count || 0,
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="amount" stroke="#52c41a" name="交易額" />
                  <Line yAxisId="right" type="monotone" dataKey="count" stroke="#722ed1" name="交易數" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="暫無數據" />
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="紅包領取趨勢" loading={trendsLoading}>
            {trends?.claim_trends && trends.claim_trends.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={trends.claim_trends.map((item: any) => ({
                  date: dayjs(item.date).format('MM-DD'),
                  count: item.count || 0,
                  amount: item.amount || 0,
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="count" fill="#faad14" name="領取次數" />
                  <Bar yAxisId="right" dataKey="amount" fill="#13c2c2" name="領取金額" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="暫無數據" />
            )}
          </Card>
        </Col>
      </Row>

      {/* 分布圖表 */}
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={8}>
          <Card title="用戶等級分布" loading={distributionLoading}>
            {distribution?.level_distribution && distribution.level_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={distribution.level_distribution}
                    dataKey="count"
                    nameKey="level"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={(item: any) => `Lv${item.level}: ${item.count}`}
                  >
                    {distribution.level_distribution.map((_item: any, index: number) => (
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
        <Col span={8}>
          <Card title="紅包狀態分布" loading={distributionLoading}>
            {distribution?.status_distribution && distribution.status_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={distribution.status_distribution}
                    dataKey="count"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={(entry: any) => `${entry.status}: ${entry.count}`}
                  >
                    {distribution.status_distribution.map((_entry: any, index: number) => (
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
        <Col span={8}>
          <Card title="餘額分布" loading={distributionLoading}>
            {distribution?.balance_distribution && distribution.balance_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={distribution.balance_distribution} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="range" type="category" />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#1890ff" name="用戶數" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="暫無數據" />
            )}
          </Card>
        </Col>
      </Row>

      {(!stats || (stats.users?.total === 0 && stats.red_packets?.total === 0)) && (
        <Card style={{ marginTop: 24, textAlign: 'center' }}>
          <p style={{ color: '#999', fontSize: 16 }}>
            📊 目前還沒有數據，系統運行正常！
          </p>
          <p style={{ color: '#999', marginTop: 8 }}>
            當有用戶註冊、創建紅包或進行交易時，統計數據會在這裡顯示。
          </p>
        </Card>
      )}
    </div>
  )
}

