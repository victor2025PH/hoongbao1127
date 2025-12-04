import { useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowRightLeft, Wallet, Zap, Sparkles, TrendingUp } from 'lucide-react'
import { useTranslation } from '../providers/I18nProvider'
import { useSound } from '../hooks/useSound'
import PageTransition from '../components/PageTransition'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getBalance, getUserProfile, exchangeCurrency, getExchangeRate } from '../utils/api'

export default function ExchangePage() {
  // Hooks 必須在頂層調用（不能在條件語句或 try-catch 中）
  const translationHook = useTranslation()
  const soundHook = useSound()
  
  // 安全的默認值處理
  const t = translationHook?.t || ((key: string) => key)
  const playSound = soundHook?.playSound || (() => {})
  
  const [fromToken, setFromToken] = useState<'USDT' | 'TON' | 'ENERGY'>('USDT')
  const [toToken, setToToken] = useState<'USDT' | 'TON' | 'ENERGY'>('TON')
  const [amount, setAmount] = useState('')
  
  // 安全的默認值
  const safeT = (key: string, fallback?: string) => {
    try {
      if (t && typeof t === 'function') {
        return t(key) || fallback || key
      }
      return fallback || key
    } catch (e) {
      console.warn('Translation error:', e)
      return fallback || key
    }
  }
  
  const safePlaySound = (sound: 'click' | 'grab' | 'success' | 'switch' | 'notification' | 'pop' | 'startup') => {
    try {
      if (playSound && typeof playSound === 'function') {
        playSound(sound)
      }
    } catch (e) {
      console.warn('Sound play failed:', e)
    }
  }

  // 獲取實時匯率 - 先定義貨幣類型（在查詢之前）
  const fromCurrency = fromToken === 'ENERGY' ? 'points' : fromToken.toLowerCase()
  const toCurrency = toToken === 'ENERGY' ? 'points' : toToken.toLowerCase()

  // 安全的查詢，即使失敗也不阻止渲染
  const { data: balance } = useQuery({
    queryKey: ['balance'],
    queryFn: async () => {
      try {
        return await getBalance()
      } catch (error) {
        console.warn('Failed to fetch balance:', error)
        return { usdt: 0, ton: 0, stars: 0, points: 0 }
      }
    },
    retry: 1,
    throwOnError: false,
  })

  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      try {
        return await getUserProfile()
      } catch (error) {
        console.warn('Failed to fetch profile:', error)
        return { energy_balance: 0 }
      }
    },
    retry: 1,
    throwOnError: false,
  })
  
  const { data: rateData, isLoading: rateLoading, error: rateError } = useQuery({
    queryKey: ['exchangeRate', fromCurrency, toCurrency],
    queryFn: async () => {
      try {
        const result = await getExchangeRate({
          from_currency: fromCurrency,
          to_currency: toCurrency
        })
        return result
      } catch (error: any) {
        console.warn('Failed to fetch exchange rate, using fallback:', error)
        // 返回 null，讓備用匯率生效，不拋出錯誤
        return null
      }
    },
    enabled: fromToken !== toToken && fromCurrency !== toCurrency,
    refetchInterval: 60000, // 每分鐘刷新一次
    staleTime: 30000, // 30秒內認為數據新鮮
    retry: 0, // 不重試，直接使用備用匯率
    // 即使失敗也不阻止頁面渲染
    throwOnError: false,
  })

  // 備用匯率（如果 API 失敗）
  const fallbackRates: Record<string, number> = {
    'usdt_ton': 1.2,
    'ton_usdt': 0.83,
    'usdt_points': 10,
    'points_usdt': 0.1,
    'ton_points': 12,
    'points_ton': 0.083,
  }
  
  const rateKey = `${fromCurrency}_${toCurrency}`
  // 優先使用 API 返回的匯率，失敗時使用備用匯率
  const rate = (rateData && typeof rateData.rate === 'number' && rateData.rate > 0) 
    ? rateData.rate 
    : (fallbackRates[rateKey] || 1)
  
  // 安全計算轉換金額
  let convertedAmount = '0.00'
  try {
    const amountNum = parseFloat(amount)
    if (!isNaN(amountNum) && amountNum > 0 && rate > 0) {
      convertedAmount = (amountNum * rate).toFixed(6)
    }
  } catch (e) {
    console.error('Error calculating converted amount:', e)
    convertedAmount = '0.00'
  }

  const getBalanceValue = (token: string): number => {
    try {
      if (!balance && !profile) return 0
      if (token === 'USDT') return Number(balance?.usdt) || 0
      if (token === 'TON') return Number(balance?.ton) || 0
      if (token === 'ENERGY') return Number(profile?.energy_balance) || 0
    } catch (e) {
      console.error('Error getting balance:', e)
    }
    return 0
  }

  const queryClient = useQueryClient()
  
  // 確保所有必要的值都有默認值（在 mutation 之前定義）
  const safeFromToken = fromToken || 'USDT'
  const safeToToken = toToken || 'TON'
  const safeAmount = amount || ''
  const safeRate = (typeof rate === 'number' && !isNaN(rate) && rate > 0) ? rate : (fallbackRates[rateKey] || 1)
  const safeConvertedAmount = convertedAmount || '0.00'
  
  const exchangeMutation = useMutation({
    mutationFn: async () => {
      try {
        // 將 ENERGY 映射為 POINTS（如果後端使用 POINTS）
        const fromCurrency = safeFromToken === 'ENERGY' ? 'points' : safeFromToken.toLowerCase()
        const toCurrency = safeToToken === 'ENERGY' ? 'points' : safeToToken.toLowerCase()
        const amountNum = parseFloat(safeAmount)
        
        if (isNaN(amountNum) || amountNum <= 0) {
          throw new Error('無效的金額')
        }
        
        return await exchangeCurrency({
          from_currency: fromCurrency,
          to_currency: toCurrency,
          amount: amountNum
        })
      } catch (error: any) {
        console.error('Exchange mutation error:', error)
        throw error
      }
    },
    onSuccess: (data) => {
      try {
        safePlaySound('success')
        // 刷新餘額
        queryClient.invalidateQueries({ queryKey: ['balance'] })
        queryClient.invalidateQueries({ queryKey: ['profile'] })
        // 顯示成功消息
        const successMsg = data?.message || `${safeT('exchange_success', '兌換成功！')} ${safeAmount} ${safeFromToken} = ${safeConvertedAmount} ${safeToToken}`
        alert(successMsg)
        // 清空輸入
        setAmount('')
      } catch (error) {
        console.error('Error in exchange success handler:', error)
        alert('兌換成功，但刷新數據時出錯')
      }
    },
    onError: (error: any) => {
      safePlaySound('click')
      alert(error.message || safeT('exchange_failed', '兌換失敗'))
    }
  })

  const handleExchange = () => {
    try {
      if (!safeAmount || parseFloat(safeAmount) <= 0) {
        safePlaySound('click')
        return
      }
      const amountNum = parseFloat(safeAmount)
      if (isNaN(amountNum) || amountNum <= 0) {
        safePlaySound('click')
        return
      }
      if (amountNum > getBalanceValue(safeFromToken)) {
        safePlaySound('click')
        alert(safeT('insufficient_balance', '餘額不足'))
        return
      }
      exchangeMutation.mutate()
    } catch (error) {
      console.error('Error in handleExchange:', error)
      alert('兌換操作失敗，請重試')
    }
  }

  const tokenConfig = {
    USDT: { icon: Wallet, color: 'text-green-400', bg: 'from-green-500/20 to-emerald-500/20', border: 'border-green-500/30' },
    TON: { icon: TrendingUp, color: 'text-blue-400', bg: 'from-blue-500/20 to-cyan-500/20', border: 'border-blue-500/30' },
    ENERGY: { icon: Zap, color: 'text-yellow-400', bg: 'from-yellow-500/20 to-orange-500/20', border: 'border-yellow-500/30' },
  }

  return (
    <PageTransition>
      <div className="h-full flex flex-col p-4 pb-24 gap-4 overflow-y-auto scrollbar-hide">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <ArrowRightLeft size={24} className="text-purple-400" />
          {safeT('currency_exchange', '幣種兌換')}
        </h1>

        {/* 兑换卡片 */}
        <div className="bg-[#1C1C1E] border border-white/5 rounded-3xl p-6 space-y-4">
          {/* 从 */}
          <div className="space-y-2">
            <label className="block text-gray-300 text-sm font-medium">{safeT('from', '從')}</label>
            <div className="flex gap-3">
              <div className="flex-1">
                <input
                  type="number"
                  value={safeAmount}
                  onChange={(e) => {
                    try {
                      setAmount(e.target.value)
                    } catch (err) {
                      console.error('Error setting amount:', err)
                    }
                  }}
                  placeholder="0.00"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-lg font-bold focus:outline-none focus:border-purple-500/50 transition-colors"
                />
                <div className="mt-1 text-xs text-gray-500">
                  {safeT('balance', '餘額')}: {(() => {
                    const val = getBalanceValue(fromToken)
                    return typeof val === 'number' && !isNaN(val) ? val.toFixed(6) : '0.000000'
                  })()}
                </div>
              </div>
              <select
                value={safeFromToken}
                onChange={(e) => {
                  try {
                    setFromToken(e.target.value as any)
                  } catch (err) {
                    console.error('Error setting fromToken:', err)
                  }
                }}
                className="bg-gradient-to-br px-4 py-3 rounded-xl border text-white font-bold focus:outline-none"
                style={{
                  background: `linear-gradient(135deg, ${tokenConfig[safeFromToken]?.bg?.split(' ')[1] || 'green-500/20'}, ${tokenConfig[safeFromToken]?.bg?.split(' ')[3] || 'emerald-500/20'})`,
                  borderColor: tokenConfig[safeFromToken]?.border?.split(' ')[1]?.replace('border-', '')?.replace('/30', '') || 'green-500/30',
                }}
              >
                <option value="USDT">USDT</option>
                <option value="TON">TON</option>
                <option value="ENERGY">{safeT('energy', '能量')}</option>
              </select>
            </div>
          </div>

          {/* 交换箭头 */}
          <div className="flex justify-center">
            <motion.button
              onClick={() => {
                const temp = fromToken
                setFromToken(toToken)
                setToToken(temp)
                safePlaySound('click')
              }}
              className="w-12 h-12 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center hover:bg-purple-500/30 transition-colors"
              whileHover={{ rotate: 180, scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <ArrowRightLeft size={20} className="text-purple-400" />
            </motion.button>
          </div>

          {/* 到 */}
          <div className="space-y-2">
            <label className="block text-gray-300 text-sm font-medium">{safeT('to', '到')}</label>
            <div className="flex gap-3">
              <div className="flex-1">
                <div className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-lg font-bold">
                  {safeConvertedAmount}
                </div>
                <div className="mt-1 text-xs text-gray-500">
                  {safeT('balance', '餘額')}: {(() => {
                    const val = getBalanceValue(toToken)
                    return typeof val === 'number' && !isNaN(val) ? val.toFixed(6) : '0.000000'
                  })()}
                </div>
              </div>
              <select
                value={safeToToken}
                onChange={(e) => {
                  try {
                    setToToken(e.target.value as any)
                  } catch (err) {
                    console.error('Error setting toToken:', err)
                  }
                }}
                className="bg-gradient-to-br px-4 py-3 rounded-xl border text-white font-bold focus:outline-none"
                style={{
                  background: `linear-gradient(135deg, ${tokenConfig[safeToToken]?.bg?.split(' ')[1] || 'blue-500/20'}, ${tokenConfig[safeToToken]?.bg?.split(' ')[3] || 'cyan-500/20'})`,
                  borderColor: tokenConfig[safeToToken]?.border?.split(' ')[1]?.replace('border-', '')?.replace('/30', '') || 'blue-500/30',
                }}
              >
                <option value="USDT">USDT</option>
                <option value="TON">TON</option>
                <option value="ENERGY">{safeT('energy', '能量')}</option>
              </select>
            </div>
          </div>

          {/* 汇率显示 */}
          <div className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">{safeT('exchange_rate', '匯率')}</span>
              {rateData?.source === 'market' && (
                <span className="text-xs text-green-400 bg-green-500/20 px-2 py-0.5 rounded">
                  📊 市場匯率
                </span>
              )}
              {rateData?.source === 'fixed' && !rateLoading && (
                <span className="text-xs text-yellow-400 bg-yellow-500/20 px-2 py-0.5 rounded">
                  ⚙️ 固定匯率
                </span>
              )}
              {rateLoading && (
                <span className="text-xs text-gray-500 animate-pulse">載入中...</span>
              )}
              {rateError && (
                <span className="text-xs text-orange-400 bg-orange-500/20 px-2 py-0.5 rounded">
                  ⚠️ 使用備用匯率
                </span>
              )}
            </div>
            <span className="text-sm font-bold text-purple-300">
              1 {safeFromToken} = {safeRate.toFixed(6)} {safeToToken}
            </span>
          </div>

          {/* 兑换按钮 */}
          <motion.button
            onClick={handleExchange}
            disabled={exchangeMutation.isPending}
            className="w-full py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-bold text-base shadow-lg shadow-purple-500/20 active:scale-[0.98] transition-transform flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            whileHover={{ scale: exchangeMutation.isPending ? 1 : 1.02 }}
            whileTap={{ scale: exchangeMutation.isPending ? 1 : 0.98 }}
          >
            <Sparkles size={18} />
            {exchangeMutation.isPending ? safeT('processing', '處理中...') : safeT('exchange_now', '立即兌換')}
          </motion.button>
        </div>

        {/* 说明 */}
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4">
          <h3 className="text-sm font-bold text-blue-300 mb-2">💡 {safeT('exchange_desc', '兌換說明')}</h3>
          <ul className="text-xs text-gray-400 space-y-1">
            <li>• {safeT('exchange_tip_1', '支持 USDT、TON、能量之間的互相兌換')}</li>
            <li>• {safeT('exchange_tip_2', '匯率實時更新，以實際兌換時為準')}</li>
            <li>• {safeT('exchange_tip_3', '兌換即時到帳，無需等待')}</li>
            <li>• {safeT('exchange_tip_4', '能量可通過簽到、邀請等方式獲得')}</li>
          </ul>
        </div>
      </div>
    </PageTransition>
  )
}

