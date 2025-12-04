import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  Card, Table, Tag, Space, Button, Select, Modal,
  Descriptions, Timeline, Spin
} from 'antd'
import { 
  WarningOutlined, EyeOutlined, ReloadOutlined,
  UserOutlined, ClockCircleOutlined
} from '@ant-design/icons'
import { securityApi } from '../utils/api'
import dayjs from 'dayjs'

const { Option } = Select

const riskColors: Record<string, string> = {
  low: 'green',
  medium: 'orange',
  high: 'red',
  critical: 'magenta'
}

const riskLabels: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
  critical: '嚴重'
}

export default function RiskMonitor() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [riskLevel, setRiskLevel] = useState<string | undefined>()
  const [selectedUser, setSelectedUser] = useState<any>(null)
  const [detailModalVisible, setDetailModalVisible] = useState(false)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['risk-users', page, pageSize, riskLevel],
    queryFn: async () => {
      const response = await securityApi.getRiskUsers({ 
        page, 
        page_size: pageSize,
        risk_level: riskLevel 
      })
      return response.data.data
    },
  })

  const { data: userAlerts, isLoading: alertsLoading } = useQuery({
    queryKey: ['user-alerts', selectedUser?.user_id],
    queryFn: async () => {
      if (!selectedUser?.user_id) return null
      const response = await securityApi.getAlerts({ 
        user_id: selectedUser.user_id,
        page: 1, 
        page_size: 20 
      })
      return response.data.data
    },
    enabled: !!selectedUser?.user_id,
  })

  const handleViewDetail = (record: any) => {
    setSelectedUser(record)
    setDetailModalVisible(true)
  }

  const columns = [
    {
      title: '用戶 ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 80,
    },
    {
      title: 'Telegram',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: any) => (
        <Space>
          <UserOutlined />
          <span>@{text || record.telegram_id}</span>
        </Space>
      ),
    },
    {
      title: '警報次數',
      dataIndex: 'alert_count',
      key: 'alert_count',
      sorter: true,
      render: (count: number) => (
        <Tag color={count > 10 ? 'red' : count > 5 ? 'orange' : 'default'}>
          {count} 次
        </Tag>
      ),
    },
    {
      title: '風險等級',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (level: string) => (
        <Tag color={riskColors[level]} icon={<WarningOutlined />}>
          {riskLabels[level] || level}
        </Tag>
      ),
    },
    {
      title: '餘額 (USDT)',
      dataIndex: 'balance',
      key: 'balance',
      render: (balance: number) => `$${balance?.toFixed(2) || '0.00'}`,
    },
    {
      title: '最後警報',
      dataIndex: 'last_alert',
      key: 'last_alert',
      render: (date: string) => (
        <Space>
          <ClockCircleOutlined />
          {date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '-'}
        </Space>
      ),
    },
    {
      title: '註冊時間',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD') : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button 
            type="link" 
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            詳情
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>
          <WarningOutlined style={{ marginRight: 8, color: '#faad14' }} />
          風險監控
        </h1>
        <Space>
          <Select
            placeholder="風險等級"
            value={riskLevel}
            onChange={setRiskLevel}
            allowClear
            style={{ width: 120 }}
          >
            <Option value="low">低風險</Option>
            <Option value="medium">中風險</Option>
            <Option value="high">高風險</Option>
            <Option value="critical">嚴重</Option>
          </Select>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            刷新
          </Button>
        </Space>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={data?.users || []}
          rowKey="user_id"
          loading={isLoading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: data?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 個風險用戶`,
            onChange: (p, ps) => {
              setPage(p)
              setPageSize(ps)
            },
          }}
        />
      </Card>

      {/* 用戶詳情彈窗 */}
      <Modal
        title={`用戶風險詳情 - ${selectedUser?.username || selectedUser?.telegram_id}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedUser && (
          <>
            <Descriptions bordered column={2} style={{ marginBottom: 24 }}>
              <Descriptions.Item label="用戶 ID">{selectedUser.user_id}</Descriptions.Item>
              <Descriptions.Item label="Telegram ID">{selectedUser.telegram_id}</Descriptions.Item>
              <Descriptions.Item label="用戶名">@{selectedUser.username || '-'}</Descriptions.Item>
              <Descriptions.Item label="餘額">${selectedUser.balance?.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="風險等級">
                <Tag color={riskColors[selectedUser.risk_level]}>
                  {riskLabels[selectedUser.risk_level]}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="警報次數">
                <Tag color="red">{selectedUser.alert_count} 次</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="註冊時間" span={2}>
                {dayjs(selectedUser.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            </Descriptions>

            <Card title="警報歷史" size="small">
              {alertsLoading ? (
                <Spin />
              ) : userAlerts?.alerts?.length > 0 ? (
                <Timeline
                  items={userAlerts.alerts.map((alert: any) => ({
                    color: riskColors[alert.risk_level],
                    children: (
                      <div>
                        <div>
                          <Tag color={riskColors[alert.risk_level]}>{alert.alert_type}</Tag>
                          <span style={{ marginLeft: 8, color: '#999' }}>
                            {dayjs(alert.created_at).format('YYYY-MM-DD HH:mm')}
                          </span>
                        </div>
                        <div style={{ marginTop: 4, color: '#666' }}>
                          IP: {alert.ip_address || '-'}
                        </div>
                        {alert.details && (
                          <div style={{ marginTop: 4, fontSize: 12, color: '#999' }}>
                            {JSON.stringify(alert.details)}
                          </div>
                        )}
                      </div>
                    ),
                  }))}
                />
              ) : (
                <div style={{ textAlign: 'center', color: '#999' }}>暫無警報記錄</div>
              )}
            </Card>
          </>
        )}
      </Modal>
    </div>
  )
}
