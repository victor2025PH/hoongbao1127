import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  Card,
  Descriptions,
  Tag,
  Button,
  Space,
  Table,
  Statistic,
  Row,
  Col,
  Spin,
  message,
  Empty,
  Modal,
  Form,
  Input,
} from 'antd'
import {
  ArrowLeftOutlined,
  CopyOutlined,
  SendOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { telegramApi } from '../utils/api'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'

export default function GroupDetail() {
  const { chatId } = useParams<{ chatId: string }>()
  const navigate = useNavigate()
  const [sendMessageModalVisible, setSendMessageModalVisible] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['group-detail', chatId],
    queryFn: () => telegramApi.getGroupDetail(Number(chatId)).then(res => res.data),
    enabled: !!chatId,
  })

  const sendMessageMutation = useMutation({
    mutationFn: (data: any) => telegramApi.sendMessage(data),
    onSuccess: () => {
      message.success('消息發送成功')
      setSendMessageModalVisible(false)
      form.resetFields()
      refetch()
    },
    onError: (error: any) => {
      message.error(error.response?.data?.error || '發送失敗')
    },
  })

  const copyChatId = () => {
    if (data?.chat?.id) {
      navigator.clipboard.writeText(data.chat.id.toString())
      message.success('群組 ID 已複製')
    }
  }

  const copyInviteLink = () => {
    if (data?.db_record?.invite_link) {
      navigator.clipboard.writeText(data.db_record.invite_link)
      message.success('邀請鏈接已複製')
    }
  }

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!data) {
    return <Empty description="群組不存在" />
  }

  const { chat, db_record, statistics, bot_status, recent_messages } = data

  // 最近消息表格列
  const messageColumns: ColumnsType<any> = [
    {
      title: '消息 ID',
      dataIndex: 'message_id',
      key: 'message_id',
      width: 120,
    },
    {
      title: '內容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: '類型',
      dataIndex: 'message_type',
      key: 'message_type',
      width: 100,
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      width: 100,
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
      width: 180,
      render: (time) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/telegram')}
          >
            返回群組列表
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
          >
            刷新
          </Button>
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={() => {
              form.setFieldsValue({ chat_id: chat.id })
              setSendMessageModalVisible(true)
            }}
          >
            發送消息
          </Button>
        </Space>
      </div>

      <Card title="群組基本信息" style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered>
          <Descriptions.Item label="群組 ID">
            <Space>
              <span style={{ fontFamily: 'monospace', fontSize: 16, fontWeight: 'bold' }}>
                #{chat.id}
              </span>
              <Button
                type="link"
                size="small"
                icon={<CopyOutlined />}
                onClick={copyChatId}
              >
                複製
              </Button>
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="群組名稱">{chat.title || '-'}</Descriptions.Item>
          <Descriptions.Item label="類型">
            <Tag>{chat.type || '-'}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="用戶名">
            {chat.username ? `@${chat.username}` : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="描述" span={2}>
            {chat.description || db_record?.description || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="成員數量">
            {db_record?.member_count ? `${db_record.member_count} 人` : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Bot 狀態">
            <Space>
              <Tag color={
                bot_status?.status === 'administrator' || bot_status?.status === 'creator'
                  ? 'green'
                  : bot_status?.status === 'member'
                  ? 'blue'
                  : 'red'
              }>
                {bot_status?.status || db_record?.bot_status || 'unknown'}
              </Tag>
              {bot_status?.is_member && <Tag color="green">在群組中</Tag>}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="邀請鏈接">
            {db_record?.invite_link ? (
              <Space>
                <a href={db_record.invite_link} target="_blank" rel="noopener noreferrer">
                  {db_record.invite_link}
                </a>
                <Button
                  type="link"
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={copyInviteLink}
                >
                  複製
                </Button>
              </Space>
            ) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="狀態">
            <Tag color={db_record?.is_active ? 'green' : 'red'}>
              {db_record?.is_active ? '活躍' : '非活躍'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="最後更新">
            {db_record?.updated_at
              ? dayjs(db_record.updated_at).format('YYYY-MM-DD HH:mm:ss')
              : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="統計信息" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title="總消息數"
              value={statistics?.total_messages || 0}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="成功發送"
              value={statistics?.sent_messages || 0}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="發送失敗"
              value={statistics?.failed_messages || 0}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="最後消息時間"
              value={statistics?.last_message_at
                ? dayjs(statistics.last_message_at).format('MM-DD HH:mm')
                : '-'}
            />
          </Col>
        </Row>
      </Card>

      <Card title="最近消息">
        <Table
          columns={messageColumns}
          dataSource={recent_messages || []}
          rowKey="id"
          pagination={false}
          locale={{ emptyText: '暫無消息記錄' }}
        />
      </Card>

      {/* 發送消息模態框 */}
      <Modal
        title="發送消息到群組"
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
            label="群組 ID"
            rules={[{ required: true }]}
          >
            <Input disabled />
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
    </div>
  )
}

