import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Descriptions,
  Tag,
  Button,
  Space,
  Table,
  Tabs,
  Statistic,
  Row,
  Col,
  Spin,
  message,
  Empty,
} from 'antd'
import {
  ArrowLeftOutlined,
  CopyOutlined,
  DollarOutlined,
  GiftOutlined,
  CheckCircleOutlined,
  SendOutlined,
} from '@ant-design/icons'
import { userApi } from '../utils/api'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'

export default function UserDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data, isLoading } = useQuery({
    queryKey: ['user-detail', id],
    queryFn: () => userApi.detailFull(Number(id)).then(res => res.data),
    enabled: !!id,
  })

  const copyTelegramId = () => {
    if (data?.user?.telegram_id) {
      navigator.clipboard.writeText(data.user.telegram_id.toString())
      message.success('Telegram ID 已複製')
    }
  }

  const copyToTelegram = () => {
    if (data?.user?.telegram_id) {
      window.open(`https://t.me/${data.user.username || data.user.telegram_id}`, '_blank')
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
    return <Empty description="用戶不存在" />
  }

  const { user, statistics, transactions, sent_packets, claimed_packets, checkins } = data

  // 交易记录表格列
  const transactionColumns: ColumnsType<any> = [
    {
      title: '時間',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '類型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => {
        const typeMap: Record<string, { color: string; text: string }> = {
          deposit: { color: 'green', text: '充值' },
          withdraw: { color: 'red', text: '提現' },
          red_packet_send: { color: 'orange', text: '發送紅包' },
          red_packet_claim: { color: 'blue', text: '領取紅包' },
          admin_adjust: { color: 'purple', text: '管理員調整' },
        }
        const typeInfo = typeMap[type] || { color: 'default', text: type }
        return <Tag color={typeInfo.color}>{typeInfo.text}</Tag>
      },
    },
    {
      title: '金額',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount, record) => {
        const sign = amount >= 0 ? '+' : ''
        const color = amount >= 0 ? '#52c41a' : '#ff4d4f'
        return <span style={{ color }}>{sign}{amount} {record.currency}</span>
      },
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'completed' ? 'green' : 'orange'}>{status}</Tag>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
  ]

  // 发送的红包表格列
  const sentPacketColumns: ColumnsType<any> = [
    {
      title: '時間',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: 'UUID',
      dataIndex: 'uuid',
      key: 'uuid',
      render: (text) => <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{text}</span>,
    },
    {
      title: '金額',
      dataIndex: 'total_amount',
      key: 'total_amount',
      render: (amount, record) => `${amount} ${record.currency.toUpperCase()}`,
    },
    {
      title: '數量',
      dataIndex: 'total_count',
      key: 'total_count',
    },
    {
      title: '已領取',
      dataIndex: 'claimed_count',
      key: 'claimed_count',
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusMap: Record<string, { color: string; text: string }> = {
          active: { color: 'green', text: '進行中' },
          completed: { color: 'blue', text: '已完成' },
          expired: { color: 'red', text: '已過期' },
          refunded: { color: 'orange', text: '已退款' },
        }
        const statusInfo = statusMap[status] || { color: 'default', text: status }
        return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
      },
    },
  ]

  // 领取的红包表格列
  const claimedPacketColumns: ColumnsType<any> = [
    {
      title: '時間',
      dataIndex: 'claimed_at',
      key: 'claimed_at',
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '金額',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount) => <span style={{ color: '#52c41a' }}>+{amount}</span>,
    },
    {
      title: '手氣最佳',
      dataIndex: 'is_luckiest',
      key: 'is_luckiest',
      render: (isLuckiest) => isLuckiest ? <Tag color="gold">🏆 手氣最佳</Tag> : '-',
    },
  ]

  // 签到记录表格列
  const checkinColumns: ColumnsType<any> = [
    {
      title: '日期',
      dataIndex: 'checkin_date',
      key: 'checkin_date',
      render: (text) => text ? dayjs(text).format('YYYY-MM-DD') : '-',
    },
    {
      title: '連續天數',
      dataIndex: 'day_of_streak',
      key: 'day_of_streak',
    },
    {
      title: '獎勵',
      dataIndex: 'reward_points',
      key: 'reward_points',
      render: (points) => <span style={{ color: '#52c41a' }}>+{points} Points</span>,
    },
  ]

  const tabItems = [
    {
      key: 'transactions',
      label: '交易記錄',
      children: (
        <Table
          columns={transactionColumns}
          dataSource={transactions || []}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: '暫無交易記錄' }}
        />
      ),
    },
    {
      key: 'sent_packets',
      label: '發送的紅包',
      children: (
        <Table
          columns={sentPacketColumns}
          dataSource={sent_packets || []}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: '暫無發送的紅包' }}
        />
      ),
    },
    {
      key: 'claimed_packets',
      label: '領取的紅包',
      children: (
        <Table
          columns={claimedPacketColumns}
          dataSource={claimed_packets || []}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: '暫無領取的紅包' }}
        />
      ),
    },
    {
      key: 'checkins',
      label: '簽到記錄',
      children: (
        <Table
          columns={checkinColumns}
          dataSource={checkins || []}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: '暫無簽到記錄' }}
        />
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/users')}
        >
          返回用戶列表
        </Button>
      </div>

      <Card title="用戶基本信息" style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered>
          <Descriptions.Item label="用戶 ID">{user.id}</Descriptions.Item>
          <Descriptions.Item label="Telegram ID">
            <Space>
              <span style={{ fontFamily: 'monospace', fontSize: 16, fontWeight: 'bold' }}>
                #{user.telegram_id}
              </span>
              <Button
                type="link"
                size="small"
                icon={<CopyOutlined />}
                onClick={copyTelegramId}
              >
                複製
              </Button>
              <Button
                type="link"
                size="small"
                icon={<SendOutlined />}
                onClick={copyToTelegram}
              >
                打開 Telegram
              </Button>
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="用戶名">{user.username || '-'}</Descriptions.Item>
          <Descriptions.Item label="姓名">
            {user.first_name || ''} {user.last_name || ''}
          </Descriptions.Item>
          <Descriptions.Item label="等級">{user.level}</Descriptions.Item>
          <Descriptions.Item label="經驗值">{user.xp.toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="邀請碼">{user.invite_code || '-'}</Descriptions.Item>
          <Descriptions.Item label="邀請人數">{user.invite_count}</Descriptions.Item>
          <Descriptions.Item label="連續簽到">{user.checkin_streak} 天</Descriptions.Item>
          <Descriptions.Item label="最後簽到">
            {user.last_checkin ? dayjs(user.last_checkin).format('YYYY-MM-DD HH:mm:ss') : '從未簽到'}
          </Descriptions.Item>
          <Descriptions.Item label="狀態">
            <Space>
              <Tag color={user.is_banned ? 'red' : 'green'}>
                {user.is_banned ? '已封禁' : '正常'}
              </Tag>
              {user.is_admin && <Tag color="purple">管理員</Tag>}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="註冊時間">
            {user.created_at ? dayjs(user.created_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="財務信息" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title="USDT 餘額"
              value={user.balance_usdt}
              prefix={<DollarOutlined />}
              precision={2}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="TON 餘額"
              value={user.balance_ton}
              prefix={<DollarOutlined />}
              precision={2}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Stars 餘額"
              value={user.balance_stars}
              prefix={<GiftOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Points 餘額"
              value={user.balance_points}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Col>
        </Row>
      </Card>

      <Card title="統計信息" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="發送的紅包"
              value={statistics.sent_packets_count}
              prefix={<GiftOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="領取的紅包"
              value={statistics.claimed_packets_count}
              prefix={<GiftOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="交易次數"
              value={statistics.total_transactions}
              prefix={<DollarOutlined />}
            />
          </Col>
        </Row>
      </Card>

      <Card title="詳細記錄">
        <Tabs items={tabItems} />
      </Card>
    </div>
  )
}

