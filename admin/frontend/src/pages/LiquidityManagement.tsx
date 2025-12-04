import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Card, Table, Tag, Space, Button, Select, Input, Modal, message,
  Row, Col, Statistic, Progress, Form, Radio
} from 'antd'
import { 
  LockOutlined, UnlockOutlined,
  ClockCircleOutlined, ReloadOutlined, EditOutlined,
  WalletOutlined
} from '@ant-design/icons'
import { securityApi } from '../utils/api'
import dayjs from 'dayjs'

const { Option } = Select
const { Search } = Input

const statusColors: Record<string, string> = {
  locked: 'red',
  cooldown: 'orange',
  withdrawable: 'green'
}

const statusLabels: Record<string, string> = {
  locked: '鎖定',
  cooldown: '冷卻期',
  withdrawable: '可提現'
}

const statusIcons: Record<string, React.ReactNode> = {
  locked: <LockOutlined />,
  cooldown: <ClockCircleOutlined />,
  withdrawable: <UnlockOutlined />
}

const sourceLabels: Record<string, string> = {
  real_crypto: '實際加密貨幣',
  stars_credit: 'Stars 信用',
  bonus: '獎勵',
  referral: '推薦獎勵'
}

const categoryLabels: Record<string, string> = {
  deposit: '充值',
  withdraw: '提現',
  send_packet: '發紅包',
  claim_packet: '搶紅包',
  refund: '退款',
  stars_conversion: 'Stars轉換',
  fiat_deposit: '法幣充值',
  referral_bonus: '推薦獎勵',
  game_win: '遊戲贏',
  game_loss: '遊戲輸',
  fee: '手續費'
}

export default function LiquidityManagement() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [userId, setUserId] = useState<number | undefined>()
  const [currencySource, setCurrencySource] = useState<string | undefined>()
  const [withdrawableStatus, setWithdrawableStatus] = useState<string | undefined>()
  const [adjustModalVisible, setAdjustModalVisible] = useState(false)
  const [selectedEntry, setSelectedEntry] = useState<any>(null)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['liquidity-stats'],
    queryFn: async () => {
      const response = await securityApi.getLiquidityStats()
      return response.data.data
    },
  })

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['liquidity-entries', page, pageSize, userId, currencySource, withdrawableStatus],
    queryFn: async () => {
      const response = await securityApi.getLiquidityEntries({ 
        page, 
        page_size: pageSize,
        user_id: userId,
        currency_source: currencySource,
        withdrawable_status: withdrawableStatus
      })
      return response.data.data
    },
  })

  const adjustMutation = useMutation({
    mutationFn: async (data: any) => {
      return securityApi.adjustLiquidity(data)
    },
    onSuccess: () => {
      message.success('狀態已更新')
      setAdjustModalVisible(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['liquidity-entries'] })
      queryClient.invalidateQueries({ queryKey: ['liquidity-stats'] })
    },
    onError: () => {
      message.error('更新失敗')
    },
  })

  const handleAdjust = (record: any) => {
    setSelectedEntry(record)
    form.setFieldsValue({
      new_status: record.withdrawable_status,
      reason: ''
    })
    setAdjustModalVisible(true)
  }

  const handleSubmitAdjust = async () => {
    const values = await form.validateFields()
    adjustMutation.mutate({
      user_id: selectedEntry.user_id,
      entry_id: selectedEntry.id,
      new_status: values.new_status,
      reason: values.reason
    })
  }

  const totalAmount = (stats?.total_locked || 0) + (stats?.total_cooldown || 0) + (stats?.total_withdrawable || 0)

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '用戶 ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 80,
    },
    {
      title: '類別',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag>{categoryLabels[category] || category}</Tag>
      ),
    },
    {
      title: '來源',
      dataIndex: 'currency_source',
      key: 'currency_source',
      render: (source: string) => (
        <Tag color={source === 'real_crypto' ? 'blue' : source === 'stars_credit' ? 'gold' : 'default'}>
          {sourceLabels[source] || source}
        </Tag>
      ),
    },
    {
      title: '金額',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => (
        <span style={{ fontWeight: 'bold' }}>${amount?.toFixed(2) || '0.00'}</span>
      ),
    },
    {
      title: '狀態',
      dataIndex: 'withdrawable_status',
      key: 'withdrawable_status',
      render: (status: string) => (
        <Tag color={statusColors[status]} icon={statusIcons[status]}>
          {statusLabels[status] || status}
        </Tag>
      ),
    },
    {
      title: '解鎖時間',
      dataIndex: 'unlock_at',
      key: 'unlock_at',
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '流水要求/已完成',
      key: 'turnover',
      render: (_: any, record: any) => (
        <div style={{ fontSize: 12 }}>
          <div>要求: ${record.turnover_required?.toFixed(2) || '0.00'}</div>
          <div>完成: ${record.turnover_completed?.toFixed(2) || '0.00'}</div>
          {record.turnover_required > 0 && (
            <Progress 
              percent={Math.min(100, (record.turnover_completed / record.turnover_required) * 100)} 
              size="small"
              status={record.turnover_completed >= record.turnover_required ? 'success' : 'active'}
            />
          )}
        </div>
      ),
    },
    {
      title: '創建時間',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: any) => (
        <Button 
          type="link" 
          icon={<EditOutlined />} 
          size="small"
          onClick={() => handleAdjust(record)}
        >
          調整
        </Button>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>
          <WalletOutlined style={{ marginRight: 8 }} />
          流動性管理
        </h1>
        <Space>
          <Search
            placeholder="用戶 ID"
            onSearch={(value) => setUserId(value ? parseInt(value) : undefined)}
            style={{ width: 120 }}
            allowClear
          />
          <Select
            placeholder="資金來源"
            value={currencySource}
            onChange={setCurrencySource}
            allowClear
            style={{ width: 140 }}
          >
            {Object.entries(sourceLabels).map(([key, label]) => (
              <Option key={key} value={key}>{label}</Option>
            ))}
          </Select>
          <Select
            placeholder="狀態"
            value={withdrawableStatus}
            onChange={setWithdrawableStatus}
            allowClear
            style={{ width: 120 }}
          >
            {Object.entries(statusLabels).map(([key, label]) => (
              <Option key={key} value={key}>{label}</Option>
            ))}
          </Select>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            刷新
          </Button>
        </Space>
      </div>

      {/* 統計卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card loading={statsLoading}>
            <Statistic
              title="鎖定金額"
              value={stats?.total_locked || 0}
              prefix={<LockOutlined />}
              precision={2}
              valueStyle={{ color: '#ff4d4f' }}
              suffix="USDT"
            />
            {totalAmount > 0 && (
              <Progress 
                percent={(stats?.total_locked / totalAmount) * 100} 
                showInfo={false}
                strokeColor="#ff4d4f"
                size="small"
              />
            )}
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={statsLoading}>
            <Statistic
              title="冷卻期金額"
              value={stats?.total_cooldown || 0}
              prefix={<ClockCircleOutlined />}
              precision={2}
              valueStyle={{ color: '#faad14' }}
              suffix="USDT"
            />
            {totalAmount > 0 && (
              <Progress 
                percent={(stats?.total_cooldown / totalAmount) * 100} 
                showInfo={false}
                strokeColor="#faad14"
                size="small"
              />
            )}
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={statsLoading}>
            <Statistic
              title="可提現金額"
              value={stats?.total_withdrawable || 0}
              prefix={<UnlockOutlined />}
              precision={2}
              valueStyle={{ color: '#52c41a' }}
              suffix="USDT"
            />
            {totalAmount > 0 && (
              <Progress 
                percent={(stats?.total_withdrawable / totalAmount) * 100} 
                showInfo={false}
                strokeColor="#52c41a"
                size="small"
              />
            )}
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={statsLoading} title="資金來源分布">
            {stats?.by_source?.map((item: any) => (
              <div key={item.source} style={{ marginBottom: 8 }}>
                <span>{sourceLabels[item.source] || item.source}: </span>
                <span style={{ fontWeight: 'bold' }}>${item.amount?.toFixed(2)}</span>
              </div>
            ))}
          </Card>
        </Col>
      </Row>

      {/* 帳本條目列表 */}
      <Card title="帳本條目">
        <Table
          columns={columns}
          dataSource={data?.entries || []}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: data?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 條記錄`,
            onChange: (p, ps) => {
              setPage(p)
              setPageSize(ps)
            },
          }}
        />
      </Card>

      {/* 調整狀態彈窗 */}
      <Modal
        title="調整流動性狀態"
        open={adjustModalVisible}
        onCancel={() => setAdjustModalVisible(false)}
        onOk={handleSubmitAdjust}
        confirmLoading={adjustMutation.isPending}
      >
        {selectedEntry && (
          <>
            <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
              <div>帳本 ID: {selectedEntry.id}</div>
              <div>用戶 ID: {selectedEntry.user_id}</div>
              <div>金額: ${selectedEntry.amount?.toFixed(2)}</div>
              <div>
                當前狀態: 
                <Tag color={statusColors[selectedEntry.withdrawable_status]} style={{ marginLeft: 8 }}>
                  {statusLabels[selectedEntry.withdrawable_status]}
                </Tag>
              </div>
            </div>
            
            <Form form={form} layout="vertical">
              <Form.Item
                name="new_status"
                label="新狀態"
                rules={[{ required: true, message: '請選擇新狀態' }]}
              >
                <Radio.Group>
                  <Radio.Button value="locked">
                    <LockOutlined /> 鎖定
                  </Radio.Button>
                  <Radio.Button value="cooldown">
                    <ClockCircleOutlined /> 冷卻期
                  </Radio.Button>
                  <Radio.Button value="withdrawable">
                    <UnlockOutlined /> 可提現
                  </Radio.Button>
                </Radio.Group>
              </Form.Item>
              
              <Form.Item
                name="reason"
                label="原因"
                rules={[{ required: true, message: '請輸入調整原因' }]}
              >
                <Input.TextArea rows={3} placeholder="請輸入調整原因..." />
              </Form.Item>
            </Form>
          </>
        )}
      </Modal>
    </div>
  )
}
