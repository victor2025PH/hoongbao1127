import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Table, Input, Button, Space, Tag, Modal, Form, InputNumber, Select, message, DatePicker } from 'antd'
import { SearchOutlined, CopyOutlined, SendOutlined, EyeOutlined, FilterOutlined, ExportOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { userApi, telegramApi } from '../utils/api'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'

interface User {
  id: number
  telegram_id: number
  username?: string
  first_name?: string
  last_name?: string
  balance_usdt: number
  balance_ton: number
  balance_stars: number
  balance_points: number
  level: number
  is_banned: boolean
  is_admin?: boolean
  created_at: string
}

export default function UserManagement() {
  const navigate = useNavigate()
  const [searchText, setSearchText] = useState('')
  const [adjustModalVisible, setAdjustModalVisible] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [sendMessageModalVisible, setSendMessageModalVisible] = useState(false)
  const [batchModalVisible, setBatchModalVisible] = useState(false)
  const [filterModalVisible, setFilterModalVisible] = useState(false)
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [filters, setFilters] = useState<any>({})
  const [form] = Form.useForm()
  const [batchForm] = Form.useForm()
  const [filterForm] = Form.useForm()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['users', searchText, filters],
    queryFn: async () => {
      const params: any = { search: searchText || undefined }
      if (filters.level !== undefined) params.level = filters.level
      if (filters.is_banned !== undefined) params.is_banned = filters.is_banned
      if (filters.min_balance_usdt !== undefined) params.min_balance_usdt = filters.min_balance_usdt
      if (filters.max_balance_usdt !== undefined) params.max_balance_usdt = filters.max_balance_usdt
      if (filters.created_from) params.created_from = filters.created_from
      if (filters.created_to) params.created_to = filters.created_to
      const response = await userApi.list(params)
      console.log('User list API response:', response.data)
      // 确保返回的数据结构正确
      if (response.data && response.data.data) {
        // 如果响应是 { success: true, data: [...], total: ... }
        return {
          data: response.data.data,
          total: response.data.total || response.data.data.length,
          page: response.data.page || 1,
          limit: response.data.limit || 10
        }
      }
      return response.data
    },
  })

  const adjustBalanceMutation = useMutation({
    mutationFn: (values: any) => userApi.adjustBalance(values),
    onSuccess: () => {
      message.success('餘額調整成功')
      setAdjustModalVisible(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.error || '調整失敗')
    },
  })

  const sendMessageMutation = useMutation({
    mutationFn: (data: any) => telegramApi.sendMessage(data),
    onSuccess: () => {
      message.success('消息發送成功')
      setSendMessageModalVisible(false)
    },
    onError: (error: any) => {
      message.error(error.response?.data?.error || '發送失敗')
    },
  })

  const copyTelegramId = (tgId: number) => {
    navigator.clipboard.writeText(tgId.toString())
    message.success('Telegram ID 已複製')
  }

  const handleAdjustBalance = (user: User) => {
    setSelectedUser(user)
    setAdjustModalVisible(true)
  }

  const handleSendMessage = (user: User) => {
    setSelectedUser(user)
    setSendMessageModalVisible(true)
  }

  const handleViewDetail = (user: User) => {
    navigate(`/users/${user.id}`)
  }

  const handleBatchOperation = async (operation: string) => {
    if (selectedRowKeys.length === 0) {
      message.warning('請選擇要操作的用戶')
      return
    }

    if (operation === 'send_message') {
      setBatchModalVisible(true)
      batchForm.setFieldsValue({ operation: 'send_message' })
    } else {
      try {
        await userApi.batchOperation({
          user_ids: selectedRowKeys,
          operation: operation,
        })
        message.success('批量操作成功')
        setSelectedRowKeys([])
        queryClient.invalidateQueries({ queryKey: ['users'] })
      } catch (error: any) {
        message.error(error.response?.data?.detail || '操作失敗')
      }
    }
  }

  const handleApplyFilters = () => {
    const values = filterForm.getFieldsValue()
    const newFilters: any = {}
    if (values.level) newFilters.level = values.level
    if (values.is_banned !== undefined) newFilters.is_banned = values.is_banned
    if (values.min_balance_usdt) newFilters.min_balance_usdt = values.min_balance_usdt
    if (values.max_balance_usdt) newFilters.max_balance_usdt = values.max_balance_usdt
    if (values.created_from) newFilters.created_from = values.created_from.format('YYYY-MM-DD')
    if (values.created_to) newFilters.created_to = values.created_to.format('YYYY-MM-DD')
    setFilters(newFilters)
    setFilterModalVisible(false)
  }

  const handleClearFilters = () => {
    filterForm.resetFields()
    setFilters({})
    setFilterModalVisible(false)
  }

  const handleExport = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('請選擇要導出的用戶')
      return
    }

    try {
      const response = await userApi.batchOperation({
        user_ids: selectedRowKeys,
        operation: 'export',
      })
      
      // 导出为 CSV
      const users = response.data.data || []
      const headers = ['ID', 'Telegram ID', '用戶名', '姓名', 'USDT餘額', 'TON餘額', 'Stars餘額', 'Points餘額', '等級', '狀態', '註冊時間']
      const rows = users.map((u: any) => [
        u.id,
        u.telegram_id,
        u.username || '',
        `${u.first_name || ''} ${u.last_name || ''}`.trim(),
        u.balance_usdt,
        u.balance_ton,
        u.balance_stars,
        u.balance_points,
        u.level,
        u.is_banned ? '已封禁' : '正常',
        u.created_at ? dayjs(u.created_at).format('YYYY-MM-DD HH:mm:ss') : '',
      ])
      
      const csvContent = [
        headers.join(','),
        ...rows.map((row: any[]) => row.map(cell => `"${cell}"`).join(','))
      ].join('\n')
      
      const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `users_export_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
      link.click()
      
      message.success('導出成功')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '導出失敗')
    }
  }

  const columns: ColumnsType<User> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'Telegram ID',
      dataIndex: 'telegram_id',
      key: 'telegram_id',
      width: 150,
      render: (tgId: number) => (
        <Space>
          <span style={{ fontFamily: 'monospace' }}>#{tgId}</span>
          <Button
            type="link"
            size="small"
            icon={<CopyOutlined />}
            onClick={() => copyTelegramId(tgId)}
          />
        </Space>
      ),
    },
    {
      title: '用戶名',
      dataIndex: 'username',
      key: 'username',
      render: (text) => text || '-',
    },
    {
      title: '餘額',
      dataIndex: 'balance',
      key: 'balance',
      render: (balance, record: any) => {
        const balanceValue = balance || record.balance_usdt || 0
        return `$${Number(balanceValue).toFixed(2)}`
      },
    },
    {
      title: '等級',
      dataIndex: 'level',
      key: 'level',
    },
    {
      title: '狀態',
      key: 'status',
      render: (_, record) => (
        <Tag color={record.is_banned ? 'red' : 'green'}>
          {record.is_banned ? '已封禁' : '正常'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 250,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            詳情
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => handleAdjustBalance(record)}
          >
            充值
          </Button>
          <Button
            type="link"
            size="small"
            icon={<SendOutlined />}
            onClick={() => handleSendMessage(record)}
          >
            發送消息
          </Button>
        </Space>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (selectedKeys: React.Key[]) => {
      setSelectedRowKeys(selectedKeys)
    },
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>用戶管理</h1>
        <Space>
          <Input
            placeholder="搜索用戶（ID/用戶名）"
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
            allowClear
          />
          <Button
            icon={<FilterOutlined />}
            onClick={() => setFilterModalVisible(true)}
          >
            高級篩選
          </Button>
          {selectedRowKeys.length > 0 && (
            <>
              <Button
                onClick={() => handleBatchOperation('ban')}
                danger
              >
                批量封禁 ({selectedRowKeys.length})
              </Button>
              <Button
                onClick={() => handleBatchOperation('unban')}
              >
                批量解封 ({selectedRowKeys.length})
              </Button>
              <Button
                icon={<SendOutlined />}
                onClick={() => handleBatchOperation('send_message')}
              >
                批量發送 ({selectedRowKeys.length})
              </Button>
              <Button
                icon={<ExportOutlined />}
                onClick={handleExport}
              >
                導出 ({selectedRowKeys.length})
              </Button>
            </>
          )}
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={data?.data || []}
        loading={isLoading}
        rowKey="id"
        rowSelection={rowSelection}
        pagination={{
          total: data?.data?.total || 0,
          pageSize: data?.data?.limit || 20,
          current: (data?.data?.offset || 0) / (data?.data?.limit || 20) + 1,
          showTotal: (total) => `共 ${total} 條記錄`,
        }}
      />

      {/* 充值模態框 */}
      <Modal
        title="調整餘額"
        open={adjustModalVisible}
        onCancel={() => {
          setAdjustModalVisible(false)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        confirmLoading={adjustBalanceMutation.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => {
            adjustBalanceMutation.mutate({
              user_id: selectedUser?.id,
              amount: values.amount,
              currency: values.currency,
              reason: values.reason,
            })
          }}
        >
          <Form.Item label="用戶">
            <Input value={selectedUser?.username || selectedUser?.telegram_id} disabled />
          </Form.Item>
          <Form.Item
            name="currency"
            label="貨幣類型"
            initialValue="usdt"
            rules={[{ required: true }]}
          >
            <Select>
              <Select.Option value="usdt">USDT</Select.Option>
              <Select.Option value="ton">TON</Select.Option>
              <Select.Option value="stars">Stars</Select.Option>
              <Select.Option value="points">Points</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="amount"
            label="金額（正數充值，負數扣款）"
            rules={[{ required: true, message: '請輸入金額' }]}
          >
            <InputNumber style={{ width: '100%' }} step={0.01} />
          </Form.Item>
          <Form.Item name="reason" label="備註">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 發送消息模態框 */}
      <Modal
        title="發送 Telegram 消息"
        open={sendMessageModalVisible}
        onCancel={() => {
          setSendMessageModalVisible(false)
        }}
        onOk={() => {
          const message = form.getFieldValue('message')
          if (message) {
            sendMessageMutation.mutate({
              chat_id: selectedUser?.telegram_id,
              text: message,
            })
          }
        }}
        confirmLoading={sendMessageMutation.isPending}
      >
        <Form layout="vertical">
          <Form.Item label="接收者">
            <Input value={selectedUser?.username || selectedUser?.telegram_id} disabled />
          </Form.Item>
          <Form.Item
            name="message"
            label="消息內容"
            rules={[{ required: true, message: '請輸入消息內容' }]}
          >
            <Input.TextArea rows={5} placeholder="輸入要發送的消息..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* 批量操作模態框 */}
      <Modal
        title="批量發送消息"
        open={batchModalVisible}
        onCancel={() => {
          setBatchModalVisible(false)
          batchForm.resetFields()
        }}
        onOk={() => batchForm.submit()}
      >
        <Form
          form={batchForm}
          layout="vertical"
          onFinish={async (values) => {
            try {
              await userApi.batchOperation({
                user_ids: selectedRowKeys,
                operation: 'send_message',
                data: { message: values.message },
              })
              message.success('批量發送成功')
              setBatchModalVisible(false)
              setSelectedRowKeys([])
              batchForm.resetFields()
              queryClient.invalidateQueries({ queryKey: ['users'] })
            } catch (error: any) {
              message.error(error.response?.data?.detail || '發送失敗')
            }
          }}
        >
          <Form.Item label={`將發送給 ${selectedRowKeys.length} 個用戶`}>
            <span style={{ color: '#999' }}>已選擇 {selectedRowKeys.length} 個用戶</span>
          </Form.Item>
          <Form.Item
            name="message"
            label="消息內容"
            rules={[{ required: true, message: '請輸入消息內容' }]}
          >
            <Input.TextArea rows={5} placeholder="輸入要發送的消息..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* 高級篩選模態框 */}
      <Modal
        title="高級篩選"
        open={filterModalVisible}
        onCancel={() => setFilterModalVisible(false)}
        footer={[
          <Button key="clear" onClick={handleClearFilters}>
            清除
          </Button>,
          <Button key="cancel" onClick={() => setFilterModalVisible(false)}>
            取消
          </Button>,
          <Button key="apply" type="primary" onClick={handleApplyFilters}>
            應用
          </Button>,
        ]}
      >
        <Form form={filterForm} layout="vertical">
          <Form.Item name="level" label="等級">
            <InputNumber min={1} style={{ width: '100%' }} placeholder="篩選等級" />
          </Form.Item>
          <Form.Item name="is_banned" label="狀態">
            <Select placeholder="選擇狀態" allowClear>
              <Select.Option value={false}>正常</Select.Option>
              <Select.Option value={true}>已封禁</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="USDT 餘額範圍">
            <Space>
              <Form.Item name="min_balance_usdt" noStyle>
                <InputNumber min={0} placeholder="最小值" style={{ width: 150 }} />
              </Form.Item>
              <span>至</span>
              <Form.Item name="max_balance_usdt" noStyle>
                <InputNumber min={0} placeholder="最大值" style={{ width: 150 }} />
              </Form.Item>
            </Space>
          </Form.Item>
          <Form.Item label="註冊時間範圍">
            <Space>
              <Form.Item name="created_from" noStyle>
                <DatePicker placeholder="開始日期" style={{ width: 150 }} />
              </Form.Item>
              <span>至</span>
              <Form.Item name="created_to" noStyle>
                <DatePicker placeholder="結束日期" style={{ width: 150 }} />
              </Form.Item>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

