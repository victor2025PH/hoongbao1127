import { Layout, Menu, Avatar, Dropdown, Switch, Space, Tooltip } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  UserOutlined,
  RobotOutlined,
  FileTextOutlined,
  GiftOutlined,
  DollarOutlined,
  CalendarOutlined,
  UserAddOutlined,
  LogoutOutlined,
  SunOutlined,
  MoonOutlined,
  SafetyOutlined,
  WarningOutlined,
  MobileOutlined,
  GlobalOutlined,
  BellOutlined,
  WalletOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../../stores/authStore'
import { useThemeStore } from '../../stores/themeStore'

const { Header, Sider, Content } = Layout

interface AppLayoutProps {
  children: React.ReactNode
}

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: '儀表盤',
  },
  {
    key: '/users',
    icon: <UserOutlined />,
    label: '用戶管理',
  },
  {
    key: '/telegram',
    icon: <RobotOutlined />,
    label: 'Telegram 管理',
  },
  {
    key: '/redpackets',
    icon: <GiftOutlined />,
    label: '紅包管理',
  },
  {
    key: '/transactions',
    icon: <DollarOutlined />,
    label: '交易管理',
  },
  {
    key: '/checkin',
    icon: <CalendarOutlined />,
    label: '簽到管理',
  },
  {
    key: '/invite',
    icon: <UserAddOutlined />,
    label: '邀請管理',
  },
  {
    key: '/reports',
    icon: <FileTextOutlined />,
    label: '報表管理',
  },
  {
    key: 'security',
    icon: <SafetyOutlined />,
    label: '安全中心',
    children: [
      {
        key: '/security',
        icon: <SafetyOutlined />,
        label: '安全總覽',
      },
      {
        key: '/security/risk',
        icon: <WarningOutlined />,
        label: '風險監控',
      },
      {
        key: '/security/devices',
        icon: <MobileOutlined />,
        label: '設備管理',
      },
      {
        key: '/security/ip',
        icon: <GlobalOutlined />,
        label: 'IP 監控',
      },
      {
        key: '/security/alerts',
        icon: <BellOutlined />,
        label: '警報日誌',
      },
      {
        key: '/security/liquidity',
        icon: <WalletOutlined />,
        label: '流動性管理',
      },
    ],
  },
]

export default function AppLayout({ children }: AppLayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { admin, clearAuth } = useAuthStore()
  const { mode, toggleMode } = useThemeStore()

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  const handleLogout = () => {
    clearAuth()
    navigate('/login')
  }

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登錄',
      onClick: handleLogout,
    },
  ]

  // 根据主题模式设置样式
  const siderTheme = mode === 'dark' ? 'dark' : 'light'
  const headerBg = mode === 'dark' ? '#252525' : '#ffffff'
  const headerTextColor = mode === 'dark' ? '#e8e8e8' : '#2c3e50'
  const contentBg = mode === 'dark' ? '#252525' : '#ffffff'
  const contentTextColor = mode === 'dark' ? '#e8e8e8' : '#2c3e50'

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme={siderTheme} width={200}>
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          color: mode === 'dark' ? '#e8e8e8' : '#2c3e50',
          fontSize: 18, 
          fontWeight: 'bold',
          background: mode === 'dark' ? '#1a1a1a' : '#f7f8fa',
        }}>
          🧧 Lucky Red
        </div>
        <Menu
          theme={siderTheme}
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header style={{ 
          background: headerBg, 
          padding: '0 24px', 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          borderBottom: `1px solid ${mode === 'dark' ? '#404040' : '#e1e8ed'}`,
        }}>
          <div style={{ fontSize: 20, fontWeight: 'bold', color: headerTextColor }}>管理後台</div>
          <Space size="middle">
            <Tooltip title={mode === 'dark' ? '切換到白天模式' : '切換到夜間模式'}>
              <Switch
                checked={mode === 'dark'}
                onChange={toggleMode}
                checkedChildren={<MoonOutlined />}
                unCheckedChildren={<SunOutlined />}
                style={{ background: mode === 'dark' ? '#52c41a' : '#d9d9d9' }}
              />
            </Tooltip>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, color: headerTextColor }}>
                <Avatar icon={<UserOutlined />} />
                <span>{admin?.username || 'Admin'}</span>
              </div>
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ 
          margin: '24px', 
          background: contentBg, 
          padding: 24, 
          minHeight: 280,
          color: contentTextColor,
          borderRadius: 8,
        }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}

