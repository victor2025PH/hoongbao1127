import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Tabs, Table, Input, Button, Space, Tag, Modal, Form, message } from 'antd'
import { SearchOutlined, SendOutlined, CopyOutlined, EyeOutlined } from '@ant-design/icons'
import { telegramApi } from '../utils/api'
import MessageTemplateManagement from './MessageTemplateManagement'
import type { ColumnsType } from 'antd/es/table'

const { TabPane } = Tabs

export default function TelegramManagement() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('groups')
  const [searchText, setSearchText] = useState('')
  const [sendMessageModalVisible, setSendMessageModalVisible] = useState(false)
  const [resolveIdModalVisible, setResolveIdModalVisible] = useState(false)
  const [form] = Form.useForm()

  const { data: groupsData, isLoading: groupsLoading } = useQuery({
    queryKey: ['telegram-groups', searchText],
    queryFn: () => telegramApi.getGroups({ search: searchText || undefined }).then(res => res.data),
    enabled: activeTab === 'groups',
  })

  const { data: messagesData, isLoading: messagesLoading } = useQuery({
    queryKey: ['telegram-messages'],
    queryFn: () => telegramApi.getMessages().then(res => res.data),
    enabled: activeTab === 'messages',
  })

  const sendMessageMutation = useMutation({
    mutationFn: (data: any) => telegramApi.sendMessage(data),
    onSuccess: () => {
      message.success('消息發送成功')
      setSendMessageModalVisible(false)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.error || '發送失敗')
    },
  })

  const resolveIdMutation = useMutation({
    mutationFn: (data: any) => telegramApi.resolveId(data),
    onSuccess: (response) => {
      const data = response.data.data
      message.success(`Telegram ID: ${data.telegram_id || data.id}`)
      form.setFieldsValue({ resolved_id: data.telegram_id || data.id })
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '解析失敗')
    },
  })

  const copyId = (id: number) => {
    navigator.clipboard.writeText(id.toString())
    message.success('ID 已複製')
  }

  const groupColumns: ColumnsType<any> = [
    {
      title: '群組 ID',
      dataIndex: 'chat_id',
      key: 'chat_id',
      width: 150,
      render: (chatId: number) => (
        <Space>
          <span style={{ fontFamily: 'monospace' }}>#{chatId}</span>
          <Button
            type="link"
            size="small"
            icon={<CopyOutlined />}
            onClick={() => copyId(chatId)}
          />
        </Space>
      ),
    },
    {
      title: '群組名稱',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: '類型',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: 'Bot 狀態',
      dataIndex: 'bot_status',
      key: 'bot_status',
      render: (status) => (
        <Tag color={status === 'administrator' || status === 'creator' ? 'green' : 'default'}>
          {status || 'unknown'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/telegram/groups/${record.chat_id}`)}
          >
            詳情
          </Button>
          <Button
            type="link"
            size="small"
            icon={<SendOutlined />}
            onClick={() => {
              form.setFieldsValue({ chat_id: record.chat_id })
              setSendMessageModalVisible(true)
            }}
          >
            發送消息
          </Button>
        </Space>
      ),
    },
  ]

  const messageColumns: ColumnsType<any> = [
    {
      title: '消息 ID',
      dataIndex: 'message_id',
      key: 'message_id',
    },
    {
      title: '接收者 ID',
      dataIndex: 'to_user_id',
      key: 'to_user_id',
      render: (id) => id ? `#${id}` : '-',
    },
    {
      title: '內容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'sent' ? 'green' : 'red'}>
          {status === 'sent' ? '已發送' : '失敗'}
        </Tag>
      ),
    },
    {
      title: '發送時間',
      dataIndex: 'sent_at',
      key: 'sent_at',
      render: (time) => time ? new Date(time).toLocaleString('zh-TW') : '-',
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Telegram 管理</h1>
        <Space>
          <Button onClick={() => setResolveIdModalVisible(true)}>ID 解析工具</Button>
        </Space>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="群組管理" key="groups">
          <div style={{ marginBottom: 16 }}>
            <Input
              placeholder="搜索群組"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 300 }}
              allowClear
            />
          </div>
          <Table
            columns={groupColumns}
            dataSource={groupsData?.data?.groups || []}
            loading={groupsLoading}
            rowKey="id"
            pagination={{
              total: groupsData?.data?.total || 0,
              pageSize: groupsData?.data?.limit || 20,
            }}
          />
        </TabPane>
        <TabPane tab="消息記錄" key="messages">
          <Table
            columns={messageColumns}
            dataSource={messagesData?.data?.messages || []}
            loading={messagesLoading}
            rowKey="id"
            pagination={{
              total: messagesData?.data?.total || 0,
              pageSize: messagesData?.data?.limit || 20,
            }}
          />
        </TabPane>
        <TabPane tab="消息模板" key="templates">
          <MessageTemplateManagement />
        </TabPane>
      </Tabs>

      {/* 發送消息模態框 */}
      <Modal
        title="發送 Telegram 消息"
        open={sendMessageModalVisible}
        onCancel={() => {
          setSendMessageModalVisible(false)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        confirmLoading={sendMessageMutation.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => {
            sendMessageMutation.mutate(values)
          }}
        >
          <Form.Item
            name="chat_id"
            label="Chat ID"
            rules={[{ required: true, message: '請輸入 Chat ID' }]}
          >
            <Input placeholder="輸入群組或用戶 ID" />
          </Form.Item>
          <Form.Item
            name="text"
            label="消息內容"
            rules={[{ required: true, message: '請輸入消息內容' }]}
          >
            <Input.TextArea rows={5} placeholder="輸入要發送的消息..." />
          </Form.Item>
        </Form>
      </Modal>

      {/* ID 解析模態框 */}
      <Modal
        title="Telegram ID 解析工具"
        open={resolveIdModalVisible}
        onCancel={() => {
          setResolveIdModalVisible(false)
          form.resetFields()
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => {
            resolveIdMutation.mutate(values)
          }}
        >
          <Form.Item
            name="username"
            label="用戶名（不含 @）"
          >
            <Input placeholder="例如：username" />
          </Form.Item>
          <Form.Item
            name="link"
            label="或輸入鏈接"
          >
            <Input placeholder="例如：https://t.me/username" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={resolveIdMutation.isPending} block>
              解析
            </Button>
          </Form.Item>
          <Form.Item name="resolved_id" label="解析結果">
            <Input disabled />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

