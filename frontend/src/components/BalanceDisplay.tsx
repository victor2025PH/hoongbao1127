import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RefreshCw, TrendingUp, TrendingDown, Wifi, WifiOff } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getBalance } from '../utils/api'
import { useBalanceUpdates } from '../hooks/useWebSocket'

interface BalanceDisplayProps {
  currency?: 'USDT' | 'TON' | 'Stars' | 'Points'
  showWsStatus?: boolean
  compact?: boolean
  onRefresh?: () => void
}

export default function BalanceDisplay({
  currency = 'USDT',
  showWsStatus = false,
  compact = false,
  onRefresh,
}: BalanceDisplayProps) {
  const [previousBalance, setPreviousBalance] = useState<number | null>(null)
  const [changeAmount, setChangeAmount] = useState<number | null>(null)
  const [showChange, setShowChange] = useState(false)

  const { isConnected, balanceChanged, refreshBalance } = useBalanceUpdates()

  const { data: balance, isLoading, refetch } = useQuery({
    queryKey: ['balance'],
    queryFn: getBalance,
    staleTime: 5000,
    refetchInterval: isConnected ? false : 30000, // 如果 WS 連接，不需要輪詢
  })

  // 獲取當前幣種的餘額
  const getCurrentBalance = () => {
    if (!balance) return 0
    switch (currency) {
      case 'USDT':
        return balance.usdt || 0
      case 'TON':
        return balance.ton || 0
      case 'Stars':
        return balance.stars || 0
      case 'Points':
        return balance.points || 0
      default:
        return 0
    }
  }

  const currentBalance = getCurrentBalance()

  // 監測餘額變化
  useEffect(() => {
    if (previousBalance !== null && currentBalance !== previousBalance) {
      const diff = currentBalance - previousBalance
      setChangeAmount(diff)
      setShowChange(true)

      // 3秒後隱藏變化提示
      const timer = setTimeout(() => {
        setShowChange(false)
        setChangeAmount(null)
      }, 3000)

      return () => clearTimeout(timer)
    }
    setPreviousBalance(currentBalance)
  }, [currentBalance, previousBalance])

  const handleRefresh = () => {
    refetch()
    refreshBalance()
    onRefresh?.()
  }

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <motion.span
          key={currentBalance}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-lg font-bold text-white"
        >
          {currentBalance.toFixed(2)}
        </motion.span>
        <span className="text-sm text-gray-400">{currency}</span>
        
        <AnimatePresence>
          {showChange && changeAmount !== null && (
            <motion.span
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              className={`text-sm font-bold ${changeAmount > 0 ? 'text-green-400' : 'text-red-400'}`}
            >
              {changeAmount > 0 ? '+' : ''}{changeAmount.toFixed(2)}
            </motion.span>
          )}
        </AnimatePresence>
      </div>
    )
  }

  return (
    <div className="relative">
      {/* 主餘額顯示 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <motion.div
            key={currentBalance}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            className="flex items-baseline gap-1"
          >
            <span className="text-3xl font-bold text-white">
              {isLoading ? '---' : currentBalance.toFixed(2)}
            </span>
            <span className="text-lg text-gray-400">{currency}</span>
          </motion.div>

          {/* 餘額變化動畫 */}
          <AnimatePresence>
            {showChange && changeAmount !== null && (
              <motion.div
                initial={{ opacity: 0, y: 20, scale: 0.8 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.8 }}
                className={`flex items-center gap-1 px-2 py-1 rounded-full ${
                  changeAmount > 0 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-red-500/20 text-red-400'
                }`}
              >
                {changeAmount > 0 ? (
                  <TrendingUp size={14} />
                ) : (
                  <TrendingDown size={14} />
                )}
                <span className="text-sm font-bold">
                  {changeAmount > 0 ? '+' : ''}{changeAmount.toFixed(2)}
                </span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* 刷新按鈕和狀態 */}
        <div className="flex items-center gap-2">
          {showWsStatus && (
            <div className={`p-1.5 rounded-full ${isConnected ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
              {isConnected ? (
                <Wifi size={14} className="text-green-400" />
              ) : (
                <WifiOff size={14} className="text-red-400" />
              )}
            </div>
          )}
          
          <motion.button
            onClick={handleRefresh}
            whileTap={{ scale: 0.9, rotate: 180 }}
            className="p-2 bg-white/5 rounded-full hover:bg-white/10 transition-colors"
            disabled={isLoading}
          >
            <RefreshCw 
              size={16} 
              className={`text-gray-400 ${isLoading ? 'animate-spin' : ''}`} 
            />
          </motion.button>
        </div>
      </div>

      {/* 餘額變化時的背景閃爍效果 */}
      <AnimatePresence>
        {balanceChanged && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.3 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl pointer-events-none"
          />
        )}
      </AnimatePresence>
    </div>
  )
}

// 迷你餘額徽章（用於導航欄等）
export function BalanceBadge({ currency = 'USDT' }: { currency?: 'USDT' | 'TON' | 'Stars' }) {
  const { data: balance } = useQuery({
    queryKey: ['balance'],
    queryFn: getBalance,
    staleTime: 10000,
  })

  useBalanceUpdates() // 啟用 WebSocket 更新

  const getBalance_ = () => {
    if (!balance) return 0
    switch (currency) {
      case 'USDT': return balance.usdt || 0
      case 'TON': return balance.ton || 0
      case 'Stars': return balance.stars || 0
      default: return 0
    }
  }

  return (
    <motion.div
      layout
      className="inline-flex items-center gap-1 px-2 py-1 bg-white/10 rounded-full"
    >
      <motion.span
        key={getBalance_()}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-xs font-bold text-white"
      >
        {getBalance_().toFixed(2)}
      </motion.span>
      <span className="text-xs text-gray-400">{currency}</span>
    </motion.div>
  )
}
