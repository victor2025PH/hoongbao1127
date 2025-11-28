import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  Descriptions,
  Tag,
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
  DollarOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { transactionApi } from '../utils/api'

const { Title, Text } = Typography

export default function TransactionDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: transaction, isLoading } = useQuery({
    queryKey: ['transaction-detail', id],
    queryFn: async () => {
      const response = await transactionApi.detail(Number(id))
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

  if (!transaction) {
    return (
      <div>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/transactions')}>
          返回列表
        </Button>
        <Card style={{ marginTop: 16 }}>
          <div style={{ textAlign: 'center', padding: 50 }}>
            <Text type="secondary">交易不存在</Text>
          </div>
        </Card>
      </div>
    )
  }

  const typeMap: Record<string, { text: string; color: string }> = {
    deposit: { text: '充值', color: 'green' },
    withdraw: { text: '提现', color: 'orange' },
    send: { text: '发送', color: 'blue' },
    receive: { text: '接收', color: 'cyan' },
    checkin: { text: '签到', color: 'purple' },
    invite: { text: '邀请', color: 'magenta' },
  }

  const currencyMap: Record<string, string> = {
    usdt: 'USDT',
    ton: 'TON',
    stars: 'Stars',
    points: 'Points',
  }

  const isPositive = Number(transaction.amount) >= 0
  const typeConfig = typeMap[transaction.type] || { text: transaction.type, color: 'default' }

  return (
    <div>
      <Space style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/transactions')}>
          返回列表
        </Button>
        <Title level={2} style={{ margin: 0 }}>
          交易详情
        </Title>
      </Space>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="交易金额"
              value={Math.abs(Number(transaction.amount)).toFixed(4)}
              prefix={isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix={currencyMap[transaction.currency]}
              valueStyle={{
                color: isPositive ? '#52c41a' : '#ff4d4f',
              }}
            />
          </Card>
        </Col>
        {transaction.balance_before !== null && transaction.balance_after !== null && (
          <>
            <Col span={8}>
              <Card>
                <Statistic
                  title="交易前余额"
                  value={Number(transaction.balance_before).toFixed(4)}
                  prefix={<DollarOutlined />}
                  suffix={currencyMap[transaction.currency]}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="交易后余额"
                  value={Number(transaction.balance_after).toFixed(4)}
                  prefix={<DollarOutlined />}
                  suffix={currencyMap[transaction.currency]}
                />
              </Card>
            </Col>
          </>
        )}
      </Row>

      {/* 基本信息 */}
      <Card title="基本信息">
        <Descriptions column={2} bordered>
          <Descriptions.Item label="交易ID">
            {transaction.id}
          </Descriptions.Item>
          <Descriptions.Item label="交易类型">
            <Tag color={typeConfig.color}>{typeConfig.text}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="用户">
            <div>
              <div>{transaction.user_name || transaction.user_username || `ID: ${transaction.user_id}`}</div>
              {transaction.user_tg_id && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  TG ID: {transaction.user_tg_id}
                </Text>
              )}
            </div>
          </Descriptions.Item>
          <Descriptions.Item label="币种">
            <Tag color="blue">{currencyMap[transaction.currency]}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="金额">
            <Space>
              {isPositive ? (
                <ArrowUpOutlined style={{ color: '#52c41a' }} />
              ) : (
                <ArrowDownOutlined style={{ color: '#ff4d4f' }} />
              )}
              <Text strong={true} style={{ color: isPositive ? '#52c41a' : '#ff4d4f' }}>
                {isPositive ? '+' : ''}{Number(transaction.amount).toFixed(4)}
              </Text>
              <Text type="secondary">{currencyMap[transaction.currency]}</Text>
            </Space>
          </Descriptions.Item>
          {transaction.ref_id && (
            <Descriptions.Item label="关联ID">
              <Text copyable>{transaction.ref_id}</Text>
            </Descriptions.Item>
          )}
          {transaction.note && (
            <Descriptions.Item label="备注" span={2}>
              {transaction.note}
            </Descriptions.Item>
          )}
          <Descriptions.Item label="交易时间">
            {dayjs(transaction.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  )
}

