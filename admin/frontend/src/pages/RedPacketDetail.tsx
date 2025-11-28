import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Descriptions,
  Tag,
  Table,
  Button,
  Space,
  Statistic,
  Row,
  Col,
  Spin,
  Typography,
} from 'antd'
import {
  ArrowLeftOutlined,
  UserOutlined,
  GiftOutlined,
  DollarOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type { ColumnsType } from 'antd/es/table'
import { redpacketApi } from '../utils/api'

const { Title, Text } = Typography

interface Claim {
  id: number
  user_id: number
  user_tg_id?: number
  user_username?: string
  user_name?: string
  amount: number
  is_luckiest: boolean
  created_at?: string
}

export default function RedPacketDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: redpacket, isLoading } = useQuery({
    queryKey: ['redpacket-detail', id],
    queryFn: async () => {
      const response = await redpacketApi.detail(Number(id))
      return response.data
    },
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!redpacket) {
    return (
      <div>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/redpackets')}>
          返回列表
        </Button>
        <Card style={{ marginTop: 16 }}>
          <div style={{ textAlign: 'center', padding: 50 }}>
            <Text type="secondary">红包不存在</Text>
          </div>
        </Card>
      </div>
    )
  }

  const statusMap: Record<string, { text: string; color: string }> = {
    active: { text: '进行中', color: 'green' },
    completed: { text: '已完成', color: 'blue' },
    expired: { text: '已过期', color: 'orange' },
    refunded: { text: '已退款', color: 'red' },
  }

  const typeMap: Record<string, string> = {
    random: '拼手气',
    equal: '平分',
    exclusive: '专属',
  }

  const currencyMap: Record<string, string> = {
    usdt: 'USDT',
    ton: 'TON',
    stars: 'Stars',
    points: 'Points',
  }

  const claimColumns: ColumnsType<Claim> = [
    {
      title: '排名',
      key: 'rank',
      width: 80,
      render: (_, __, index) => {
        if (index === 0) return <Tag color="gold">🥇</Tag>
        if (index === 1) return <Tag color="default">🥈</Tag>
        if (index === 2) return <Tag color="orange">🥉</Tag>
        return `#${index + 1}`
      },
    },
    {
      title: '用户',
      key: 'user',
      width: 200,
      render: (_, record) => (
        <div>
          <div>{record.user_name || record.user_username || `ID: ${record.user_id}`}</div>
          {record.user_tg_id && (
            <div style={{ fontSize: 12, color: '#999' }}>TG: {record.user_tg_id}</div>
          )}
        </div>
      ),
    },
    {
      title: '领取金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 150,
      render: (amount, record) => (
        <Space>
          <Text strong>{Number(amount).toFixed(4)} {currencyMap[redpacket.currency]}</Text>
          {record.is_luckiest && <Tag color="red">手气最佳</Tag>}
        </Space>
      ),
    },
    {
      title: '领取时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time) => (time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-'),
    },
  ]

  const claimRate = redpacket.total_count > 0
    ? ((redpacket.claimed_count / redpacket.total_count) * 100).toFixed(1)
    : '0'

  const amountRate = redpacket.total_amount > 0
    ? ((Number(redpacket.claimed_amount) / Number(redpacket.total_amount)) * 100).toFixed(1)
    : '0'

  return (
    <div>
      <Space style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/redpackets')}>
          返回列表
        </Button>
        <Title level={2} style={{ margin: 0 }}>
          红包详情
        </Title>
      </Space>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总金额"
              value={Number(redpacket.total_amount).toFixed(4)}
              prefix={<DollarOutlined />}
              suffix={currencyMap[redpacket.currency]}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已领取"
              value={Number(redpacket.claimed_amount).toFixed(4)}
              prefix={<GiftOutlined />}
              suffix={currencyMap[redpacket.currency]}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="领取进度"
              value={claimRate}
              suffix="%"
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="金额进度"
              value={amountRate}
              suffix="%"
              prefix={<DollarOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 基本信息 */}
      <Card title="基本信息" style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered>
          <Descriptions.Item label="UUID">
            <Text copyable>{redpacket.uuid}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusMap[redpacket.status]?.color}>
              {statusMap[redpacket.status]?.text}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="发送者">
            <div>
              <div>{redpacket.sender_name || redpacket.sender_username || `ID: ${redpacket.sender_id}`}</div>
              {redpacket.sender_tg_id && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  TG ID: {redpacket.sender_tg_id}
                </Text>
              )}
            </div>
          </Descriptions.Item>
          <Descriptions.Item label="群组">
            <div>
              <div>{redpacket.chat_title || '未指定'}</div>
              {redpacket.chat_id && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  群组 ID: {redpacket.chat_id}
                </Text>
              )}
            </div>
          </Descriptions.Item>
          <Descriptions.Item label="币种">
            <Tag color="blue">{currencyMap[redpacket.currency]}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="类型">
            <Tag>{typeMap[redpacket.packet_type]}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="总金额">
            <Text strong>{Number(redpacket.total_amount).toFixed(4)} {currencyMap[redpacket.currency]}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="总数量">
            {redpacket.total_count} 个
          </Descriptions.Item>
          <Descriptions.Item label="已领取金额">
            <Text strong>{Number(redpacket.claimed_amount).toFixed(4)} {currencyMap[redpacket.currency]}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="已领取数量">
            {redpacket.claimed_count} / {redpacket.total_count}
          </Descriptions.Item>
          <Descriptions.Item label="祝福语" span={2}>
            {redpacket.message || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dayjs(redpacket.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="过期时间">
            {redpacket.expires_at
              ? dayjs(redpacket.expires_at).format('YYYY-MM-DD HH:mm:ss')
              : '-'}
          </Descriptions.Item>
          {redpacket.completed_at && (
            <Descriptions.Item label="完成时间">
              {dayjs(redpacket.completed_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      {/* 领取记录 */}
      <Card
        title={
          <Space>
            <GiftOutlined />
            <span>领取记录 ({redpacket.claims?.length || 0})</span>
          </Space>
        }
      >
        {redpacket.claims && redpacket.claims.length > 0 ? (
          <Table
            columns={claimColumns}
            dataSource={redpacket.claims}
            rowKey="id"
            pagination={false}
            size="small"
          />
        ) : (
          <div style={{ textAlign: 'center', padding: 50 }}>
            <Text type="secondary">暂无领取记录</Text>
          </div>
        )}
      </Card>
    </div>
  )
}

