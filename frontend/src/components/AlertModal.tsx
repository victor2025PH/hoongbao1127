import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface AlertModalProps {
  isOpen: boolean
  onClose: () => void
  message: string
  type?: 'success' | 'error' | 'warning' | 'info'
  title?: string
}

export default function AlertModal({
  isOpen,
  onClose,
  message,
  type = 'info',
  title
}: AlertModalProps) {
  if (!isOpen) return null

  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  }

  const colors = {
    success: 'text-green-400 border-green-500/30 bg-green-500/10',
    error: 'text-red-400 border-red-500/30 bg-red-500/10',
    warning: 'text-orange-400 border-orange-500/30 bg-orange-500/10',
    info: 'text-blue-400 border-blue-500/30 bg-blue-500/10',
  }

  const Icon = icons[type]
  const colorClass = colors[type]

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 pointer-events-none">
        {/* 背景遮罩 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm pointer-events-auto"
        />

        {/* 彈窗內容 */}
        <motion.div
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: 20 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className={`relative w-full max-w-sm bg-brand-dark border rounded-2xl p-6 shadow-2xl pointer-events-auto ${colorClass}`}
        >
          {/* 關閉按鈕 */}
          <button
            onClick={onClose}
            className="absolute top-3 right-3 text-gray-400 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>

          <div className="flex items-start gap-4">
            {/* 圖標 */}
            <div className="shrink-0">
              <Icon size={24} className={colorClass.split(' ')[0]} />
            </div>

            {/* 內容 */}
            <div className="flex-1 min-w-0">
              {title && (
                <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
              )}
              <p className="text-sm text-gray-200 whitespace-pre-line">{message}</p>
            </div>
          </div>

          {/* 確認按鈕 */}
          <button
            onClick={onClose}
            className={`w-full mt-4 py-2.5 px-4 rounded-xl font-medium transition-colors ${
              type === 'success' ? 'bg-green-500 hover:bg-green-600' :
              type === 'error' ? 'bg-red-500 hover:bg-red-600' :
              type === 'warning' ? 'bg-orange-500 hover:bg-orange-600' :
              'bg-blue-500 hover:bg-blue-600'
            } text-white`}
          >
            確定
          </button>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}

