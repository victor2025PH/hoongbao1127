import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Card, Table, Tag, Space, Button, Select, Input, message,
  Popconfirm, Row, Col, List
} from 'antd'
import { 
  GlobalOutlined, StopOutlined, CheckOutlined,
  ReloadOutlined, TeamOutlined,
  EnvironmentOutlined
} from '@ant-design/icons'
import { securityApi } from '../utils/api'
import dayjs from 'dayjs'

const { Option } = Select
const { Search } = Input

export default function IPMonitor() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [ipSearch, setIpSearch] = useState<string | undefined>()
  const [isActive, setIsActive] = useState<boolean | undefined>()
  const queryClient = useQueryClient()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['ip-sessions', page, pageSize, ipSearch, isActive],
    queryFn: async () => {
      const response = await securityApi.getIPSessions({ 
        page, 
        page_size: pageSize,
        ip_address: ipSearch,
        is_active: isActive
      })
      return response.data.data
    },
  })

  const { data: ipStats, isLoading: statsLoading } = useQuery({
    queryKey: ['ip-stats'],
    queryFn: async () => {
      const response = await securityApi.getIPStats()
      return response.data.data
    },
  })

  const actionMutation = useMutation({
    mutationFn: async ({ ipAddress, action, reason }: { ipAddress: string, action: string, reason?: string }) => {
      return securityApi.ipAction(ipAddress, { action, reason })
    },
    onSuccess: (_, variables) => {
      message.success(`IP ${variables.ipAddress} 已${variables.action === 'block' ? '封鎖' : '解封'}`)
      queryClient.invalidateQueries({ queryKey: ['ip-sessions'] })
    },
    onError: () => {
      message.error('操作失敗')
    },
  })

  const handleAction = (ipAddress: string, action: string) => {
    actionMutation.mutate({ ipAddress, action })
  }

  const columns = [
    {
      title: 'IP 地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      render: (ip: string) => (
        <Space>
          <GlobalOutlined />
          <code>{ip}</code>
        </Space>
      ),
    },
    {
      title: '用戶 ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 80,
    },
    {
      title: '地區',
      key: 'location',
      render: (_: any, record: any) => (
        <Space>
          <EnvironmentOutlined />
          <span>{record.country || '-'} / {record.city || '-'}</span>
        </Space>
      ),
    },
    {
      title: '搶包次數',
      dataIndex: 'claim_count',
      key: 'claim_count',
      render: (count: number) => (
        <Tag color={count > 50 ? 'red' : count > 20 ? 'orange' : 'default'}>
          {count || 0}
        </Tag>
      ),
    },
    {
      title: '狀態',
      key: 'status',
      render: (_: any, record: any) => (
        <Space>
          {record.is_blocked && <Tag color="red">已封鎖</Tag>}
          {record.is_active && !record.is_blocked && <Tag color="green">活躍</Tag>}
          {!record.is_active && !record.is_blocked && <Tag>不活躍</Tag>}
        </Space>
      ),
    },
    {
      title: '最後活動',
      dataIndex: 'last_activity',
      key: 'last_activity',
      render: (date: string) => date ? dayjs(date).format('MM-DD HH:mm') : '-',
    },
    {
      title: '最後搶包',
      dataIndex: 'last_claim_at',
      key: 'last_claim_at',
      render: (date: string) => date ? dayjs(date).format('MM-DD HH:mm') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: any) => (
        <Space>
          {!record.is_blocked ? (
            <Popconfirm
              title="確定要封鎖此 IP 嗎？"
              description="封鎖後該 IP 下所有會話都將受影響"
              onConfirm={() => handleAction(record.ip_address, 'block')}
              okText="確定"
              cancelText="取消"
            >
              <Button type="link" danger icon={<StopOutlined />} size="small">
                封鎖
              </Button>
            </Popconfirm>
          ) : (
            <Button 
              type="link" 
              icon={<CheckOutlined />} 
              size="small"
              onClick={() => handleAction(record.ip_address, 'unblock')}
            >
              解封
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>
          <GlobalOutlined style={{ marginRight: 8 }} />
          IP 監控
        </h1>
        <Space>
          <Search
            placeholder="搜索 IP"
            onSearch={(value) => setIpSearch(value || undefined)}
            style={{ width: 180 }}
            allowClear
          />
          <Select
            placeholder="狀態"
            value={isActive}
            onChange={setIsActive}
            allowClear
            style={{ width: 120 }}
          >
            <Option value={true}>活躍</Option>
            <Option value={false}>不活躍</Option>
          </Select>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            刷新
          </Button>
        </Space>
      </div>

      {/* IP 統計 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="同 IP 多用戶 (可疑)" loading={statsLoading}>
            <List
              size="small"
              dataSource={ipStats?.multi_user_ips || []}
              locale={{ emptyText: '暫無可疑 IP' }}
              renderItem={(item: any) => (
                <List.Item
                  actions={[
                    <Popconfirm
                      title="確定要封鎖此 IP 嗎？"
                      onConfirm={() => handleAction(item.ip_address, 'block')}
                      okText="確定"
                      cancelText="取消"
                    >
                      <Button type="link" danger size="small">封鎖</Button>
                    </Popconfirm>
                  ]}
                >
                  <List.Item.Meta
                    avatar={<GlobalOutlined style={{ fontSize: 20, color: item.user_count > 5 ? '#ff4d4f' : '#faad14' }} />}
                    title={<code>{item.ip_address}</code>}
                    description={
                      <Space>
                        <Tag icon={<TeamOutlined />} color={item.user_count > 5 ? 'red' : 'orange'}>
                          {item.user_count} 個用戶
                        </Tag>
                        <span>總搶包: {item.total_claims || 0}</span>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="用戶地區分布" loading={statsLoading}>
            <List
              size="small"
              dataSource={ipStats?.region_stats || []}
              locale={{ emptyText: '暫無數據' }}
              renderItem={(item: any) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<EnvironmentOutlined style={{ fontSize: 20 }} />}
                    title={item.country || '未知'}
                    description={`${item.user_count} 個用戶`}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* 會話列表 */}
      <Card title="IP 會話列表">
        <Table
          columns={columns}
          dataSource={data?.sessions || []}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: data?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 個會話`,
            onChange: (p, ps) => {
              setPage(p)
              setPageSize(ps)
            },
          }}
        />
      </Card>
    </div>
  )
}
