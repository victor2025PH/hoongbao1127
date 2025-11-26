import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import confetti from 'canvas-confetti'
import { useSound } from '../hooks/useSound'

interface ResultModalProps {
  isOpen: boolean
  onClose: () => void
  amount: number
  currency: string
  senderName: string
  senderLevel: number
  message: string
  senderAvatar?: string
}

export default function ResultModal({
  isOpen,
  onClose,
  amount,
  currency,
  senderName,
  senderLevel,
  message,
  senderAvatar
}: ResultModalProps) {
  const { playSound } = useSound()

  // 觸發噴花特效和音效
  useEffect(() => {
    if (isOpen) {
      playSound('success')
      
      // 持續噴花效果（參考設計）
      const end = Date.now() + 1000
      const colors = ['#bb0000', '#ffffff', '#fb923c', '#fbbf24']

      const frame = () => {
        // 左側噴花
        confetti({
          particleCount: 3,
          angle: 60,
          spread: 55,
          origin: { x: 0 },
          colors: colors,
          zIndex: 1000,
        })
        
        // 右側噴花
        confetti({
          particleCount: 3,
          angle: 120,
          spread: 55,
          origin: { x: 1 },
          colors: colors,
          zIndex: 1000,
        })
        
        // 頂部噴花
        confetti({
          particleCount: 5,
          angle: 90,
          spread: 70,
          origin: { x: 0.5, y: 0 },
          colors: colors,
          zIndex: 1000,
        })

        if (Date.now() < end) {
          requestAnimationFrame(frame)
        }
      }
      
      frame()
    }
  }, [isOpen, playSound])

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* 背景遮罩 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        />

        {/* 彈窗內容 */}
        <motion.div
          initial={{ scale: 0.5, opacity: 0, y: 50 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.5, opacity: 0, y: 50 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="relative w-full max-w-sm bg-[#1C1C1E] border border-orange-500/30 rounded-3xl p-6 shadow-2xl text-center overflow-hidden"
        >
          {/* 裝飾光暈 */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-32 bg-orange-500/20 blur-[50px] rounded-full" />

          {/* 關閉按鈕 */}
          <button
            onClick={() => { playSound('click'); onClose(); }}
            className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors z-10"
          >
            <X size={20} />
          </button>

          <div className="relative z-10 flex flex-col items-center">
            {/* 頭像 */}
            {senderAvatar && (
              <div className="mb-4 w-16 h-16 rounded-full overflow-hidden border-2 border-orange-500/50">
                <img src={senderAvatar} alt={senderName} className="w-full h-full object-cover" />
              </div>
            )}

            {/* 發送者信息 */}
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-gray-300 font-medium text-sm">{senderName} 的紅包</h3>
              <span
                className={`px-1.5 py-0.5 rounded text-[9px] border font-bold ${
                  senderLevel >= 50
                    ? 'border-yellow-500 text-yellow-500'
                    : senderLevel >= 10
                    ? 'border-purple-500 text-purple-500'
                    : 'border-cyan-500 text-cyan-500'
                }`}
              >
                Lv.{senderLevel}
              </span>
            </div>

            {/* 消息 */}
            <p className="text-gray-500 text-xs mb-6 italic">"{message}"</p>

            {/* 金額 */}
            <div className="mb-6">
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", delay: 0.2 }}
                className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-yellow-300"
              >
                {amount.toFixed(2)}
              </motion.span>
              <span className="text-yellow-500 ml-1 font-bold text-lg">{currency}</span>
            </div>

            {/* 成功提示 */}
            <p className="text-xs text-green-400 bg-green-500/10 px-3 py-1 rounded-full border border-green-500/20 mb-6">
              已成功存入錢包
            </p>

            {/* 確認按鈕 */}
            <motion.button
              onClick={() => {
                playSound('pop')
                onClose()
              }}
              className="w-full py-3 bg-gradient-to-r from-orange-600 to-red-600 text-white rounded-xl font-bold shadow-lg shadow-orange-900/40"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              太棒了！
            </motion.button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}

