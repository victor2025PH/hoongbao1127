import { motion } from 'framer-motion'
import { Users, ChevronRight, Gift, Zap } from 'lucide-react'
import { useTranslation } from '../providers/I18nProvider'

interface InviteCardProps {
  onClick: () => void
}

export default function InviteCard({ onClick }: InviteCardProps) {
  const { t } = useTranslation()
  
  return (
    <motion.button
      onClick={onClick}
      className="w-full relative overflow-hidden rounded-2xl"
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      {/* 背景漸變 */}
      <div className="absolute inset-0 bg-gradient-to-r from-purple-900/50 via-pink-900/30 to-purple-900/50" />
      
      {/* 動態光效 */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"
        animate={{
          x: ['-100%', '100%'],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: 'linear',
        }}
      />
      
      {/* 邊框 */}
      <div className="absolute inset-0 rounded-2xl border border-purple-500/30" />
      
      {/* 內容 */}
      <div className="relative flex items-center justify-between px-4 py-4">
        <div className="flex items-center gap-4">
          {/* 圖標 */}
          <motion.div
            className="relative w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center"
            animate={{
              boxShadow: [
                '0 0 10px rgba(168, 85, 247, 0.3)',
                '0 0 20px rgba(168, 85, 247, 0.5)',
                '0 0 10px rgba(168, 85, 247, 0.3)',
              ],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
            }}
          >
            <Users size={22} className="text-white" />
            
            {/* 角標 */}
            <motion.div
              className="absolute -top-1 -right-1 w-5 h-5 bg-yellow-400 rounded-full flex items-center justify-center"
              animate={{
                scale: [1, 1.2, 1],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
              }}
            >
              <Gift size={10} className="text-yellow-900" />
            </motion.div>
          </motion.div>
          
          {/* 文字 */}
          <div className="text-left">
            <div className="flex items-center gap-2">
              <span className="text-white font-bold text-base">{t('invite_friends')}</span>
              <motion.div
                animate={{ x: [0, 3, 0] }}
                transition={{ duration: 1, repeat: Infinity }}
              >
                <Zap size={14} className="text-yellow-400 fill-yellow-400" />
              </motion.div>
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-purple-300 text-sm">{t('permanent_earn')}</span>
              <span className="text-yellow-400 font-bold text-sm">10% {t('commission')}</span>
            </div>
          </div>
        </div>
        
        {/* 箭頭 */}
        <motion.div
          animate={{ x: [0, 5, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        >
          <ChevronRight size={20} className="text-purple-400" />
        </motion.div>
      </div>
      
      {/* 底部高亮 */}
      <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-purple-400/50 to-transparent" />
    </motion.button>
  )
}

