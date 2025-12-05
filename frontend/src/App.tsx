import { lazy, Suspense, useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import BottomNav from './components/BottomNav'
import TopToolbar from './components/TopToolbar'
import Loading from './components/Loading'
import AlertModal from './components/AlertModal'
import ConfirmModal from './components/ConfirmModal'
import ErrorBoundary from './components/ErrorBoundary'
import DebugPanel from './components/DebugPanel'
import { setAlertCallback, setConfirmCallback } from './utils/telegram'
import { notificationManager } from './utils/notification'

// 懒加载页面
const WalletPage = lazy(() => import('./pages/WalletPage'))
const PacketsPage = lazy(() => import('./pages/PacketsPage'))
const EarnPage = lazy(() => import('./pages/EarnPage'))
const GamePage = lazy(() => import('./pages/GamePage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const SendRedPacket = lazy(() => import('./pages/SendRedPacket'))
const Recharge = lazy(() => import('./pages/Recharge'))
const Withdraw = lazy(() => import('./pages/Withdraw'))
const ExchangePage = lazy(() => import('./pages/ExchangePage'))
const LuckyWheelPage = lazy(() => import('./pages/LuckyWheelPage'))
const TasksPage = lazy(() => import('./pages/TasksPage'))

export default function App() {
  const [alertState, setAlertState] = useState<{
    isOpen: boolean
    message: string
    type: 'success' | 'error' | 'warning' | 'info'
    title?: string
  }>({
    isOpen: false,
    message: '',
    type: 'info',
  })

  const [confirmState, setConfirmState] = useState<{
    isOpen: boolean
    message: string
    title?: string
    confirmText?: string
    cancelText?: string
    onConfirm?: () => void
    onCancel?: () => void
  }>({
    isOpen: false,
    message: '',
  })

  // 初始化通知管理器
  useEffect(() => {
    notificationManager.init().catch(console.error)
    
    return () => {
      notificationManager.cleanup()
    }
  }, [])

  // 初始化通知管理器
  useEffect(() => {
    notificationManager.init().catch(console.error)
    
    return () => {
      notificationManager.cleanup()
    }
  }, [])

  // 設置全局 Alert 回調
  useEffect(() => {
    setAlertCallback((message, type = 'info', title) => {
      // 確保 message 和 title 都是字符串
      const messageStr = typeof message === 'string' ? message : String(message || '')
      const titleStr = title && typeof title === 'string' ? title : undefined
      setAlertState({
        isOpen: true,
        message: messageStr,
        type,
        title: titleStr,
      })
    })

    setConfirmCallback((message, title, confirmText, cancelText) => {
      return new Promise((resolve) => {
        setConfirmState({
          isOpen: true,
          message,
          title,
          confirmText,
          cancelText,
          onConfirm: () => {
            resolve(true)
            setConfirmState(prev => ({ ...prev, isOpen: false, onConfirm: undefined, onCancel: undefined }))
          },
          onCancel: () => {
            resolve(false)
            setConfirmState(prev => ({ ...prev, isOpen: false, onConfirm: undefined, onCancel: undefined }))
          },
        })
      })
    })
  }, [])

  const closeAlert = () => {
    setAlertState(prev => ({ ...prev, isOpen: false }))
  }

  const closeConfirm = () => {
    if (confirmState.onCancel) {
      confirmState.onCancel()
    } else {
      setConfirmState(prev => ({ ...prev, isOpen: false, onConfirm: undefined, onCancel: undefined }))
    }
  }

  const handleConfirm = () => {
    if (confirmState.onConfirm) {
      confirmState.onConfirm()
    }
  }

  return (
    <div className="fixed inset-0 bg-brand-dark text-white flex flex-col overflow-hidden">
      <TopToolbar />
      
      <main className="flex-1 overflow-hidden">
        <ErrorBoundary>
          <Suspense fallback={<Loading />}>
            <Routes>
              <Route path="/" element={<WalletPage />} />
              <Route path="/packets" element={<PacketsPage />} />
              <Route path="/tasks" element={<TasksPage />} />
              <Route path="/send" element={<SendRedPacket />} />
              <Route path="/earn" element={<EarnPage />} />
              <Route path="/game" element={<GamePage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/recharge" element={<Recharge />} />
              <Route path="/withdraw" element={<Withdraw />} />
              <Route path="/exchange" element={<ExchangePage />} />
              <Route path="/lucky-wheel" element={<LuckyWheelPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </ErrorBoundary>
      </main>
      
      <BottomNav />

      {/* 全局 Alert 彈窗 */}
      <AlertModal
        isOpen={alertState.isOpen}
        onClose={closeAlert}
        message={alertState.message}
        type={alertState.type}
        title={alertState.title}
      />

      {/* 全局 Confirm 彈窗 */}
      <ConfirmModal
        isOpen={confirmState.isOpen}
        onClose={closeConfirm}
        onConfirm={handleConfirm}
        message={confirmState.message}
        title={confirmState.title}
        confirmText={confirmState.confirmText}
        cancelText={confirmState.cancelText}
        type="warning"
      />

      {/* 調試面板 - 在 URL 後加 #debug=1 啟用 */}
      <DebugPanel />
    </div>
  )
}

