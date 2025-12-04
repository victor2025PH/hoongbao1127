import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import UserManagement from './pages/UserManagement'
import UserDetail from './pages/UserDetail'
import TelegramManagement from './pages/TelegramManagement'
import GroupDetail from './pages/GroupDetail'
import MessageTemplateManagement from './pages/MessageTemplateManagement'
import ReportManagement from './pages/ReportManagement'
import RedPacketManagement from './pages/RedPacketManagement'
import RedPacketDetail from './pages/RedPacketDetail'
import TransactionManagement from './pages/TransactionManagement'
import TransactionDetail from './pages/TransactionDetail'
import CheckinManagement from './pages/CheckinManagement'
import InviteManagement from './pages/InviteManagement'
// 安全中心頁面
import SecurityDashboard from './pages/SecurityDashboard'
import RiskMonitor from './pages/RiskMonitor'
import DeviceManagement from './pages/DeviceManagement'
import IPMonitor from './pages/IPMonitor'
import AlertLogs from './pages/AlertLogs'
import LiquidityManagement from './pages/LiquidityManagement'
import { useAuthStore } from './stores/authStore'

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            isAuthenticated ? (
              <AppLayout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/users" element={<UserManagement />} />
                  <Route path="/users/:id" element={<UserDetail />} />
                  <Route path="/telegram" element={<TelegramManagement />} />
                  <Route path="/telegram/groups/:chatId" element={<GroupDetail />} />
                  <Route path="/message-templates" element={<MessageTemplateManagement />} />
                  <Route path="/reports" element={<ReportManagement />} />
                  <Route path="/redpackets" element={<RedPacketManagement />} />
                  <Route path="/redpackets/:id" element={<RedPacketDetail />} />
                  <Route path="/transactions" element={<TransactionManagement />} />
                  <Route path="/transactions/:id" element={<TransactionDetail />} />
                  <Route path="/checkin" element={<CheckinManagement />} />
                  <Route path="/invite" element={<InviteManagement />} />
                  {/* 安全中心路由 */}
                  <Route path="/security" element={<SecurityDashboard />} />
                  <Route path="/security/risk" element={<RiskMonitor />} />
                  <Route path="/security/devices" element={<DeviceManagement />} />
                  <Route path="/security/ip" element={<IPMonitor />} />
                  <Route path="/security/alerts" element={<AlertLogs />} />
                  <Route path="/security/liquidity" element={<LiquidityManagement />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </AppLayout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App

