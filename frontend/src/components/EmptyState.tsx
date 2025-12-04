import { motion } from 'framer-motion'
import { Gift, Inbox, Search, UserX, Wallet, History } from 'lucide-react'

type EmptyType = 'packets' | 'transactions' | 'search' | 'users' | 'wallet' | 'default'

interface EmptyStateProps {
  type?: EmptyType
  title?: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
}

const configs: Record<EmptyType, { icon: React.ReactNode; title: string; description: string }> = {
  packets: {
    icon: <Gift size={48} className="text-gray-600" />,
    title: '暫無紅包',
    description: '快去發送一個紅包吧！',
  },
  transactions: {
    icon: <History size={48} className="text-gray-600" />,
    title: '暫無記錄',
    description: '您的交易記錄將顯示在這裡',
  },
  search: {
    icon: <Search size={48} className="text-gray-600" />,
    title: '未找到結果',
    description: '試試其他搜索條件',
  },
  users: {
    icon: <UserX size={48} className="text-gray-600" />,
    title: '暫無用戶',
    description: '邀請好友加入吧',
  },
  wallet: {
    icon: <Wallet size={48} className="text-gray-600" />,
    title: '錢包為空',
    description: '充值後開始您的紅包之旅',
  },
  default: {
    icon: <Inbox size={48} className="text-gray-600" />,
    title: '暫無數據',
    description: '這裡什麼都沒有',
  },
}

export default function EmptyState({ type = 'default', title, description, action }: EmptyStateProps) {
  const config = configs[type]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-12 px-4 text-center"
    >
      <motion.div
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 15 }}
        className="mb-4 p-4 bg-white/5 rounded-full"
      >
        {config.icon}
      </motion.div>

      <h3 className="text-lg font-bold text-white mb-2">
        {title || config.title}
      </h3>

      <p className="text-gray-500 text-sm mb-6 max-w-xs">
        {description || config.description}
      </p>

      {action && (
        <motion.button
          onClick={action.onClick}
          className="px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold rounded-xl shadow-lg shadow-orange-500/20"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {action.label}
        </motion.button>
      )}
    </motion.div>
  )
}
