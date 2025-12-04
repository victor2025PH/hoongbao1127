import { useState, useEffect, createContext, useContext, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: string
  type: ToastType
  message: string
  title?: string
  duration?: number
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType, title?: string, duration?: number) => void
  hideToast: (id: string) => void
}

const ToastContext = createContext<ToastContextType | null>(null)

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const showToast = useCallback((
    message: string,
    type: ToastType = 'info',
    title?: string,
    duration: number = 3000
  ) => {
    const id = Date.now().toString()
    setToasts((prev) => [...prev, { id, type, message, title, duration }])

    if (duration > 0) {
      setTimeout(() => {
        hideToast(id)
      }, duration)
    }
  }, [])

  const hideToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ showToast, hideToast }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={hideToast} />
    </ToastContext.Provider>
  )
}

function ToastContainer({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: string) => void }) {
  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
        ))}
      </AnimatePresence>
    </div>
  )
}

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: (id: string) => void }) {
  const icons = {
    success: <CheckCircle className="text-green-400" size={20} />,
    error: <XCircle className="text-red-400" size={20} />,
    warning: <AlertCircle className="text-yellow-400" size={20} />,
    info: <Info className="text-blue-400" size={20} />,
  }

  const colors = {
    success: 'border-green-500/30 bg-green-500/10',
    error: 'border-red-500/30 bg-red-500/10',
    warning: 'border-yellow-500/30 bg-yellow-500/10',
    info: 'border-blue-500/30 bg-blue-500/10',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      className={`pointer-events-auto flex items-start gap-3 p-4 rounded-xl border backdrop-blur-md shadow-lg ${colors[toast.type]}`}
    >
      <div className="shrink-0">{icons[toast.type]}</div>
      <div className="flex-1 min-w-0">
        {toast.title && (
          <div className="font-bold text-white text-sm mb-1">{toast.title}</div>
        )}
        <div className="text-gray-300 text-sm break-words">{toast.message}</div>
      </div>
      <button
        onClick={() => onDismiss(toast.id)}
        className="shrink-0 p-1 hover:bg-white/10 rounded-full transition-colors"
      >
        <X size={16} className="text-gray-400" />
      </button>
    </motion.div>
  )
}

// 簡化的 Toast 顯示函數（不需要 Provider）
let toastInstance: ToastContextType | null = null

export function setToastInstance(instance: ToastContextType) {
  toastInstance = instance
}

export function toast(message: string, type: ToastType = 'info', title?: string) {
  if (toastInstance) {
    toastInstance.showToast(message, type, title)
  } else {
    console.warn('[Toast] No toast instance available')
  }
}

export function toastSuccess(message: string, title?: string) {
  toast(message, 'success', title)
}

export function toastError(message: string, title?: string) {
  toast(message, 'error', title)
}

export function toastWarning(message: string, title?: string) {
  toast(message, 'warning', title)
}

export function toastInfo(message: string, title?: string) {
  toast(message, 'info', title)
}
