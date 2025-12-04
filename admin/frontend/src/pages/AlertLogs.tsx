import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Card, Table, Tag, Space, Button, Select, Modal, message,
  Descriptions, Tooltip, Badge
} from 'antd'
import { 
  BellOutlined, CheckOutlined, CloseOutlined,
  ExclamationCircleOutlined, ReloadOutlined, EyeOutlined,
  ArrowUpOutlined
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

const typeLabels: Record<string, string> = {
  new_account_claim: '新帳號搶包',
  same_ip_sessions: '同IP多會話',
  high_ip_claim_rate: 'IP高頻請求',
  device_mismatch: '設備異常',
  suspicious_behavior: '可疑行為',
  multiple_devices: '多設備登入',
}

export default function AlertLogs() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [resolved, setResolved] = useState<boolean | undefined>(false)
  const [riskLevel, setRiskLevel] = useState<string | undefined>()
  const [alertType, setAlertType] = useState<string | undefined>()
  const [selectedAlert, setSelectedAlert] = useState<any>(null)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const queryClient = useQueryClient()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['alerts', page, pageSize, resolved, riskLevel, alertType],
    queryFn: async () => {
      const response = await securityApi.getAlerts({ 
        page, 
        page_size: pageSize,
        resolved,
        risk_level: riskLevel,
        alert_type: alertType
      })
      return response.data.data
    },
  })

  const actionMutation = useMutation({
    mutationFn: async ({ alertId, action, note }: { alertId: number, action: string, note?: string }) => {
      return securityApi.alertAction(alertId, { action, note })
    },
    onSuccess: (_, variables) => {
      const actionLabels: Record<string, string> = {
        resolve: '已解決',
        dismiss: '已忽略',
        escalate: '已升級'
      }
      message.success(`警報${actionLabels[variables.action]}`)
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
    onError: () => {
      message.error('操作失敗')
    },
  })

  const handleAction = (alertId: number, action: string) => {
    actionMutation.mutate({ alertId, action })
  }

  const handleViewDetail = (record: any) => {
    setSelectedAlert(record)
    setDetailModalVisible(true)
  }

  const columns = [
    {
      title: '時間',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => dayjs(date).format('MM-DD HH:mm:ss'),
    },
    {
      title: '類型',
      dataIndex: 'alert_type',
      key: 'alert_type',
      render: (type: string) => (
        <Tag>{typeLabels[type] || type}</Tag>
      ),
    },
    {
      title: '風險等級',
      dataIndex: 'risk_level',
      key: 'risk_level',
      width: 100,
      render: (level: string) => (
        <Tag color={riskColors[level]} icon={<ExclamationCircleOutlined />}>
          {riskLabels[level] || level}
        </Tag>
      ),
    },
    {
      title: '用戶 ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 80,
    },
    {
      title: 'IP 地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      ellipsis: true,
      render: (ip: string) => <code>{ip || '-'}</code>,
    },
    {
      title: '狀態',
      dataIndex: 'resolved',
      key: 'resolved',
      width: 100,
      render: (resolved: boolean) => (
        resolved ? (
          <Badge status="success" text="已處理" />
        ) : (
          <Badge status="processing" text="待處理" />
        )
      ),
    },
    {
      title: '處理信息',
      key: 'resolve_info',
      render: (_: any, record: any) => (
        record.resolved ? (
          <div style={{ fontSize: 12 }}>
            <div>處理人: {record.resolved_by || '-'}</div>
            <div>時間: {record.resolved_at ? dayjs(record.resolved_at).format('MM-DD HH:mm') : '-'}</div>
          </div>
        ) : '-'
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: any) => (
        <Space>
          <Tooltip title="查看詳情">
            <Button 
              type="link" 
              icon={<EyeOutlined />} 
              size="small"
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          {!record.resolved && (
            <>
              <Tooltip title="標記已解決">
                <Button 
                  type="link" 
                  icon={<CheckOutlined />} 
                  size="small"
                  style={{ color: '#52c41a' }}
                  onClick={() => handleAction(record.id, 'resolve')}
                />
              </Tooltip>
              <Tooltip title="忽略">
                <Button 
                  type="link" 
                  icon={<CloseOutlined />} 
                  size="small"
                  onClick={() => handleAction(record.id, 'dismiss')}
                />
              </Tooltip>
              {record.risk_level !== 'critical' && (
                <Tooltip title="升級為嚴重">
                  <Button 
                    type="link" 
                    icon={<ArrowUpOutlined />} 
                    size="small"
                    danger
                    onClick={() => handleAction(record.id, 'escalate')}
                  />
                </Tooltip>
              )}
            </>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>
          <BellOutlined style={{ marginRight: 8 }} />
          警報日誌
          {data?.total > 0 && !resolved && (
            <Badge count={data.total} style={{ marginLeft: 8 }} />
          )}
        </h1>
        <Space>
          <Select
            placeholder="處理狀態"
            value={resolved}
            onChange={setResolved}
            allowClear
            style={{ width: 120 }}
          >
            <Option value={false}>待處理</Option>
            <Option value={true}>已處理</Option>
          </Select>
          <Select
            placeholder="風險等級"
            value={riskLevel}
            onChange={setRiskLevel}
            allowClear
            style={{ width: 120 }}
          >
            <Option value="low">低</Option>
            <Option value="medium">中</Option>
            <Option value="high">高</Option>
            <Option value="critical">嚴重</Option>
          </Select>
          <Select
            placeholder="警報類型"
            value={alertType}
            onChange={setAlertType}
            allowClear
            style={{ width: 140 }}
          >
            {Object.entries(typeLabels).map(([key, label]) => (
              <Option key={key} value={key}>{label}</Option>
            ))}
          </Select>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            刷新
          </Button>
        </Space>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={data?.alerts || []}
          rowKey="id"
          loading={isLoading}
          rowClassName={(record) => record.risk_level === 'critical' ? 'ant-table-row-critical' : ''}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: data?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 條警報`,
            onChange: (p, ps) => {
              setPage(p)
              setPageSize(ps)
            },
          }}
        />
      </Card>

      {/* 警報詳情彈窗 */}
      <Modal
        title="警報詳情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={
          selectedAlert && !selectedAlert.resolved ? [
            <Button key="dismiss" onClick={() => {
              handleAction(selectedAlert.id, 'dismiss')
              setDetailModalVisible(false)
            }}>
              忽略
            </Button>,
            <Button key="resolve" type="primary" onClick={() => {
              handleAction(selectedAlert.id, 'resolve')
              setDetailModalVisible(false)
            }}>
              標記已解決
            </Button>,
          ] : null
        }
        width={600}
      >
        {selectedAlert && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="警報 ID">{selectedAlert.id}</Descriptions.Item>
            <Descriptions.Item label="用戶 ID">{selectedAlert.user_id}</Descriptions.Item>
            <Descriptions.Item label="類型">
              <Tag>{typeLabels[selectedAlert.alert_type] || selectedAlert.alert_type}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="風險等級">
              <Tag color={riskColors[selectedAlert.risk_level]}>
                {riskLabels[selectedAlert.risk_level]}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="IP 地址" span={2}>
              <code>{selectedAlert.ip_address || '-'}</code>
            </Descriptions.Item>
            <Descriptions.Item label="創建時間" span={2}>
              {dayjs(selectedAlert.created_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
            <Descriptions.Item label="狀態" span={2}>
              {selectedAlert.resolved ? (
                <Badge status="success" text="已處理" />
              ) : (
                <Badge status="processing" text="待處理" />
              )}
            </Descriptions.Item>
            {selectedAlert.resolved && (
              <>
                <Descriptions.Item label="處理人">{selectedAlert.resolved_by || '-'}</Descriptions.Item>
                <Descriptions.Item label="處理時間">
                  {selectedAlert.resolved_at ? dayjs(selectedAlert.resolved_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
                </Descriptions.Item>
              </>
            )}
            <Descriptions.Item label="詳情" span={2}>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 12 }}>
                {selectedAlert.details ? JSON.stringify(selectedAlert.details, null, 2) : '-'}
              </pre>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      <style>{`
        .ant-table-row-critical {
          background-color: #fff1f0 !important;
        }
        .ant-table-row-critical:hover > td {
          background-color: #ffccc7 !important;
        }
      `}</style>
    </div>
  )
}
