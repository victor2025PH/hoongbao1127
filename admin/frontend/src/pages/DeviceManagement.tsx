import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Card, Table, Tag, Space, Button, Select, Input, message,
  Tooltip, Popconfirm
} from 'antd'
import { 
  MobileOutlined, LaptopOutlined, TabletOutlined,
  StopOutlined, CheckOutlined, SafetyOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { securityApi } from '../utils/api'
import dayjs from 'dayjs'

const { Option } = Select
const { Search } = Input

const deviceIcons: Record<string, React.ReactNode> = {
  mobile: <MobileOutlined />,
  desktop: <LaptopOutlined />,
  tablet: <TabletOutlined />,
}

export default function DeviceManagement() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [userId, setUserId] = useState<number | undefined>()
  const [isBlocked, setIsBlocked] = useState<boolean | undefined>()
  const queryClient = useQueryClient()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['devices', page, pageSize, userId, isBlocked],
    queryFn: async () => {
      const response = await securityApi.getDevices({ 
        page, 
        page_size: pageSize,
        user_id: userId,
        is_blocked: isBlocked
      })
      return response.data.data
    },
  })

  const actionMutation = useMutation({
    mutationFn: async ({ deviceId, action, reason }: { deviceId: number, action: string, reason?: string }) => {
      return securityApi.deviceAction(deviceId, { action, reason })
    },
    onSuccess: () => {
      message.success('操作成功')
      queryClient.invalidateQueries({ queryKey: ['devices'] })
    },
    onError: () => {
      message.error('操作失敗')
    },
  })

  const handleAction = (deviceId: number, action: string) => {
    actionMutation.mutate({ deviceId, action })
  }

  const columns = [
    {
      title: '設備',
      dataIndex: 'device_type',
      key: 'device_type',
      width: 100,
      render: (type: string, _record: any) => (
        <Space>
          {deviceIcons[type] || <MobileOutlined />}
          <span>{type || 'unknown'}</span>
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
      title: '指紋',
      dataIndex: 'fingerprint',
      key: 'fingerprint',
      ellipsis: true,
      render: (fp: string) => (
        <Tooltip title={fp}>
          <code style={{ fontSize: 12 }}>{fp}</code>
        </Tooltip>
      ),
    },
    {
      title: '平台',
      dataIndex: 'platform',
      key: 'platform',
      render: (platform: string) => <Tag>{platform || '-'}</Tag>,
    },
    {
      title: '瀏覽器',
      dataIndex: 'browser',
      key: 'browser',
      render: (browser: string) => browser || '-',
    },
    {
      title: '風險分數',
      dataIndex: 'risk_score',
      key: 'risk_score',
      render: (score: number) => (
        <Tag color={score > 70 ? 'red' : score > 40 ? 'orange' : 'green'}>
          {score || 0}
        </Tag>
      ),
    },
    {
      title: '狀態',
      key: 'status',
      render: (_: any, record: any) => (
        <Space>
          {record.is_blocked && <Tag color="red">已封鎖</Tag>}
          {record.is_trusted && <Tag color="green">已信任</Tag>}
          {!record.is_blocked && !record.is_trusted && <Tag>正常</Tag>}
        </Space>
      ),
    },
    {
      title: '首次/最後登入',
      key: 'times',
      render: (_: any, record: any) => (
        <div style={{ fontSize: 12 }}>
          <div>首次: {record.first_seen ? dayjs(record.first_seen).format('MM-DD HH:mm') : '-'}</div>
          <div>最後: {record.last_seen ? dayjs(record.last_seen).format('MM-DD HH:mm') : '-'}</div>
        </div>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: any) => (
        <Space>
          {!record.is_blocked ? (
            <Popconfirm
              title="確定要封鎖此設備嗎？"
              onConfirm={() => handleAction(record.id, 'block')}
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
              onClick={() => handleAction(record.id, 'unblock')}
            >
              解封
            </Button>
          )}
          {!record.is_trusted && (
            <Popconfirm
              title="確定要信任此設備嗎？"
              description="信任後此設備將跳過安全檢查"
              onConfirm={() => handleAction(record.id, 'trust')}
              okText="確定"
              cancelText="取消"
            >
              <Button type="link" icon={<SafetyOutlined />} size="small">
                信任
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>
          <MobileOutlined style={{ marginRight: 8 }} />
          設備管理
        </h1>
        <Space>
          <Search
            placeholder="用戶 ID"
            onSearch={(value) => setUserId(value ? parseInt(value) : undefined)}
            style={{ width: 150 }}
            allowClear
          />
          <Select
            placeholder="狀態"
            value={isBlocked}
            onChange={setIsBlocked}
            allowClear
            style={{ width: 120 }}
          >
            <Option value={true}>已封鎖</Option>
            <Option value={false}>正常</Option>
          </Select>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            刷新
          </Button>
        </Space>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={data?.devices || []}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: data?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 台設備`,
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
