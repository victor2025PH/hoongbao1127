import { X, AlertCircle, HelpCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface ConfirmModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  message: string
  title?: string
  confirmText?: string
  cancelText?: string
  type?: 'warning' | 'info'
}

export default function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  message,
  title,
  confirmText = '確定',
  cancelText = '取消',
  type = 'warning'
}: ConfirmModalProps) {
  if (!isOpen) return null

  const handleConfirm = () => {
    onConfirm()
    onClose()
  }

  const handleCancel = () => {
    onClose()
  }

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
          className={`relative w-full max-w-sm bg-brand-dark border rounded-2xl p-6 shadow-2xl pointer-events-auto ${
            type === 'warning' 
              ? 'border-orange-500/30 bg-orange-500/10' 
              : 'border-blue-500/30 bg-blue-500/10'
          }`}
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
              {type === 'warning' ? (
                <AlertCircle size={24} className="text-orange-400" />
              ) : (
                <HelpCircle size={24} className="text-blue-400" />
              )}
            </div>

            {/* 內容 */}
            <div className="flex-1 min-w-0">
              {title && (
                <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
              )}
              <p className="text-sm text-gray-200 whitespace-pre-line">{message}</p>
            </div>
          </div>

          {/* 按鈕組 */}
          <div className="flex gap-3 mt-6">
            <button
              onClick={handleCancel}
              className="flex-1 py-2.5 px-4 rounded-xl font-medium bg-white/10 hover:bg-white/20 text-gray-200 transition-colors"
            >
              {cancelText}
            </button>
            <button
              onClick={handleConfirm}
              className={`flex-1 py-2.5 px-4 rounded-xl font-medium text-white transition-colors ${
                type === 'warning'
                  ? 'bg-orange-500 hover:bg-orange-600'
                  : 'bg-blue-500 hover:bg-blue-600'
              }`}
            >
              {confirmText}
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}

