import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Copy, CheckCircle, Info, Wallet, Star, Loader2, ExternalLink } from 'lucide-react'
import { useTranslation } from '../providers/I18nProvider'
import TelegramStar from '../components/TelegramStar'
import { haptic, showAlert, getTelegramWebApp } from '../utils/telegram'
import { createRechargeOrder } from '../utils/api'

const PRESET_AMOUNTS = {
  USDT: [10, 50, 100, 500, 1000],
  TON: [5, 10, 50, 100, 500],
  Stars: [100, 500, 1000, 5000, 10000],
}

// 真實充值地址（從環境變量或配置獲取）
const DEPOSIT_ADDRESSES = {
  USDT: {
    TRC20: 'TXyz...abc123', // TODO: 替換為真實地址
    ERC20: '0xabc...def456',
  },
  TON: 'EQCD...xyz789',
}

export default function Recharge() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [amount, setAmount] = useState('')
  const [currency, setCurrency] = useState('USDT')
  const [copied, setCopied] = useState(false)
  const [showRulesModal, setShowRulesModal] = useState(false)
  const [dontShowAgain, setDontShowAgain] = useState(false)
  const [network, setNetwork] = useState('TRC20')
  const [showStarsPayment, setShowStarsPayment] = useState(false)

  // 每次進入頁面時檢查是否需要顯示規則彈窗
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const dontShowRules = localStorage.getItem('dont_show_recharge_rules')
      if (!dontShowRules) {
        const timer = setTimeout(() => {
          setShowRulesModal(true)
        }, 500)
        return () => clearTimeout(timer)
      }
    }
  }, [])

  // 創建充值訂單
  const createOrderMutation = useMutation({
    mutationFn: ({ amount, currency }: { amount: number; currency: string }) =>
      createRechargeOrder(amount, currency.toLowerCase()),
    onSuccess: (data) => {
      haptic('success')
      if (data.payment_url) {
        // 跳轉到支付頁面
        window.open(data.payment_url, '_blank')
      }
      showAlert(t('order_created'))
    },
    onError: (error: any) => {
      haptic('error')
      showAlert(error.message || t('order_failed'))
    },
  })

  // Telegram Stars 支付
  const handleStarsPayment = async () => {
    const tg = getTelegramWebApp()
    if (!tg) {
      showAlert('請在 Telegram 中打開')
      return
    }

    const starsAmount = parseInt(amount)
    if (!starsAmount || starsAmount < 100) {
      showAlert(t('min_stars_100'))
      return
    }

    setShowStarsPayment(true)

    try {
      // 使用 Telegram 內置支付
      // @ts-ignore
      if (tg.openInvoice) {
        // 創建 Stars 支付訂單
        const result = await createOrderMutation.mutateAsync({
          amount: starsAmount,
          currency: 'stars',
        })

        // 打開 Telegram 支付界面
        // @ts-ignore
        tg.openInvoice(result.payment_url, (status: string) => {
          if (status === 'paid') {
            haptic('success')
            queryClient.invalidateQueries({ queryKey: ['balance'] })
            showAlert(t('payment_success'))
            navigate(-1)
          } else if (status === 'cancelled') {
            showAlert(t('payment_cancelled'))
          } else {
            showAlert(t('payment_failed'))
          }
          setShowStarsPayment(false)
        })
      } else {
        // 備用方案：跳轉到 Bot 完成支付
        const botUsername = import.meta.env.VITE_BOT_USERNAME || 'luckyred2025_bot'
        window.open(`https://t.me/${botUsername}?start=recharge_${starsAmount}`, '_blank')
        setShowStarsPayment(false)
      }
    } catch (error: any) {
      setShowStarsPayment(false)
      showAlert(error.message || t('payment_failed'))
    }
  }

  // 獲取當前幣種的收款地址
  const getDepositAddress = () => {
    if (currency === 'USDT') {
      return DEPOSIT_ADDRESSES.USDT[network as keyof typeof DEPOSIT_ADDRESSES.USDT]
    }
    if (currency === 'TON') {
      return DEPOSIT_ADDRESSES.TON
    }
    return ''
  }

  const handleCopy = async () => {
    const address = getDepositAddress()
    if (!address) return

    try {
      await navigator.clipboard.writeText(address)
      setCopied(true)
      haptic('success')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      showAlert(t('copy_failed'))
    }
  }

  const handleSubmit = async () => {
    const numAmount = parseFloat(amount)
    if (!numAmount || numAmount <= 0) {
      showAlert(t('enter_valid_amount'))
      return
    }

    if (currency === 'Stars') {
      handleStarsPayment()
    } else {
      // USDT/TON 顯示地址讓用戶轉賬
      haptic('success')
      showAlert(t('copy_address_to_transfer'))
    }
  }

  return (
    <div className="h-full flex flex-col bg-brand-dark">
      {/* 頂部 */}
      <div className="flex items-center justify-between p-4 border-b border-white/5">
        <button onClick={() => navigate(-1)} className="p-2">
          <X size={24} />
        </button>
        <h1 className="text-lg font-bold">{t('recharge')}</h1>
        <div className="w-10" />
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* 幣種選擇 */}
        <div>
          <label className="block text-gray-300 text-base mb-2 font-medium">{t('select_currency')}</label>
          <div className="flex gap-2">
            {['USDT', 'TON', 'Stars'].map((c) => (
              <button
                key={c}
                onClick={() => {
                  setCurrency(c)
                  setAmount('')
                }}
                className={`flex-1 py-3 rounded-xl border transition-colors flex items-center justify-center gap-2 ${
                  currency === c
                    ? 'bg-green-500 border-green-500 text-white'
                    : 'bg-brand-darker border-white/5 text-gray-400'
                }`}
              >
                {c === 'Stars' && <Star size={16} className="text-yellow-400" />}
                {c}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setShowRulesModal(true)}
            className="text-green-400 text-sm flex items-center gap-1 hover:opacity-80 mt-2"
          >
            <Info size={14} />
            {t('currency_recharge_rules')} - {currency}
          </button>
        </div>

        {/* USDT 網絡選擇 */}
        {currency === 'USDT' && (
          <div>
            <label className="block text-gray-400 text-sm mb-2">{t('select_network')}</label>
            <div className="flex gap-2">
              {['TRC20', 'ERC20'].map((n) => (
                <button
                  key={n}
                  onClick={() => setNetwork(n)}
                  className={`flex-1 py-2.5 rounded-lg border text-sm transition-colors ${
                    network === n
                      ? 'bg-blue-500/20 border-blue-500 text-blue-400'
                      : 'bg-brand-darker border-white/5 text-gray-400'
                  }`}
                >
                  {n}
                  {n === 'TRC20' && <span className="ml-1 text-xs text-green-400">推薦</span>}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 快捷金額 */}
        <div>
          <label className="block text-gray-400 text-sm mb-2">{t('quick_amount')}</label>
          <div className="grid grid-cols-5 gap-2">
            {PRESET_AMOUNTS[currency as keyof typeof PRESET_AMOUNTS].map((preset) => (
              <button
                key={preset}
                onClick={() => setAmount(preset.toString())}
                className={`py-2.5 rounded-lg border text-base transition-colors ${
                  amount === preset.toString()
                    ? 'bg-green-500/20 border-green-500 text-green-400'
                    : 'bg-brand-darker border-white/5 text-gray-400'
                }`}
              >
                {preset}
              </button>
            ))}
          </div>
        </div>

        {/* 自定義金額 */}
        <div>
          <label className="block text-gray-400 text-sm mb-2">{t('custom_amount')}</label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.00"
            className="w-full p-4 bg-brand-darker rounded-xl border border-white/5 text-white text-xl font-bold text-center focus:outline-none focus:border-green-500"
          />
        </div>

        {/* Stars 支付按鈕 */}
        {currency === 'Stars' && (
          <button
            onClick={handleSubmit}
            disabled={!amount || showStarsPayment}
            className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-2 transition-all ${
              amount && !showStarsPayment
                ? 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white hover:from-yellow-400 hover:to-orange-400'
                : 'bg-gray-700 text-gray-400 cursor-not-allowed'
            }`}
          >
            {showStarsPayment ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                處理中...
              </>
            ) : (
              <>
                <Star size={20} />
                使用 Telegram Stars 支付
              </>
            )}
          </button>
        )}

        {/* 收款地址 (USDT/TON) */}
        {currency !== 'Stars' && (
          <div className="bg-brand-darker rounded-xl p-4">
            <label className="block text-gray-400 text-sm mb-2">
              {t('deposit_address')} ({currency} - {currency === 'USDT' ? network : 'TON Network'})
            </label>
            <div className="flex items-center gap-2">
              <code className="flex-1 text-white text-sm bg-white/5 p-3 rounded-lg overflow-hidden text-ellipsis break-all">
                {getDepositAddress()}
              </code>
              <button
                onClick={handleCopy}
                className="p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors shrink-0"
              >
                {copied ? (
                  <CheckCircle size={18} className="text-green-500" />
                ) : (
                  <Copy size={18} className="text-gray-400" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              請確認地址和網絡正確後再轉賬，錯誤轉賬無法找回
            </p>
          </div>
        )}

        {/* 提示 */}
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
          <h4 className="text-yellow-500 font-bold mb-2">{t('notice')}</h4>
          <ul className="text-yellow-200/80 text-sm space-y-1.5">
            {currency === 'Stars' ? (
              <>
                <li>• 最低充值 100 Stars</li>
                <li>• 支付後即時到賬</li>
                <li>• 可用於發送紅包和遊戲</li>
              </>
            ) : (
              <>
                <li>• {t('confirm_network')}</li>
                <li>• {t('min_deposit')}</li>
                <li>• {t('auto_credit')}</li>
              </>
            )}
          </ul>
        </div>

        {/* 訂單記錄入口 */}
        <button
          onClick={() => navigate('/wallet?tab=history')}
          className="w-full py-3 bg-white/5 rounded-xl text-gray-400 flex items-center justify-center gap-2 hover:bg-white/10 transition-colors"
        >
          <Wallet size={18} />
          查看充值記錄
          <ExternalLink size={14} />
        </button>
      </div>

      {/* 充值規則彈窗 */}
      {showRulesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 pb-24" onClick={() => {
          if (dontShowAgain) {
            localStorage.setItem('dont_show_recharge_rules', 'true')
          }
          setShowRulesModal(false)
        }}>
          <div className="bg-brand-darker rounded-2xl p-6 max-w-md w-full border border-white/10 shadow-2xl max-h-[85vh] overflow-hidden flex flex-col relative" onClick={(e) => e.stopPropagation()}>
            {/* 標題 */}
            <div className="flex items-center justify-between mb-4 shrink-0">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-brand-red flex items-center justify-center">
                  <Info size={16} className="text-white" />
                </div>
                <h3 className="text-white text-lg font-bold flex items-center gap-2">
                  {currency === 'Stars' && <Star size={18} className="text-yellow-400" />}
                  {currency} 充值規則
                </h3>
              </div>
              <button
                onClick={() => {
                  if (dontShowAgain) {
                    localStorage.setItem('dont_show_recharge_rules', 'true')
                  }
                  setShowRulesModal(false)
                }}
                className="p-1 hover:bg-white/5 rounded-lg transition-colors"
              >
                <X size={20} className="text-white" />
              </button>
            </div>

            {/* 規則內容 */}
            <div className="space-y-4 overflow-y-auto flex-1">
              {currency === 'Stars' ? (
                <>
                  <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/30 rounded-xl p-4">
                    <h4 className="text-white font-semibold text-base mb-2">支付方式</h4>
                    <p className="text-gray-300 text-sm">使用 Telegram 內置支付，支持 Apple Pay、Google Pay 和銀行卡</p>
                  </div>
                  <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-xl p-4">
                    <h4 className="text-white font-semibold text-base mb-2">到賬時間</h4>
                    <p className="text-gray-300 text-sm">支付成功後即時到賬</p>
                  </div>
                  <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-xl p-4">
                    <h4 className="text-white font-semibold text-base mb-2">最低充值</h4>
                    <p className="text-gray-300 text-sm">100 Stars 起充</p>
                  </div>
                </>
              ) : (
                <>
                  <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-xl p-4">
                    <h4 className="text-white font-semibold text-base mb-2">支持網絡</h4>
                    <p className="text-gray-300 text-sm">
                      {currency === 'USDT' ? 'TRC20（推薦）、ERC20' : 'TON Network'}
                    </p>
                  </div>
                  <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/30 rounded-xl p-4">
                    <h4 className="text-white font-semibold text-base mb-2">最低充值</h4>
                    <p className="text-gray-300 text-sm">{currency === 'USDT' ? '10 USDT' : '5 TON'}</p>
                  </div>
                  <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-xl p-4">
                    <h4 className="text-white font-semibold text-base mb-2">到賬時間</h4>
                    <p className="text-gray-300 text-sm">區塊確認後自動到賬（約1-30分鐘）</p>
                  </div>
                </>
              )}
            </div>

            {/* 不再顯示選擇框 */}
            <div className="flex items-center gap-2 mt-4 mb-4 shrink-0">
              <input
                type="checkbox"
                id="dontShowRechargeRules"
                checked={dontShowAgain}
                onChange={(e) => setDontShowAgain(e.target.checked)}
                className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-brand-red focus:ring-brand-red focus:ring-2"
              />
              <label htmlFor="dontShowRechargeRules" className="text-gray-300 text-sm cursor-pointer select-none">
                {t('dont_show_again')}
              </label>
            </div>

            {/* 關閉按鈕 */}
            <button
              onClick={() => {
                if (dontShowAgain) {
                  localStorage.setItem('dont_show_recharge_rules', 'true')
                }
                setShowRulesModal(false)
              }}
              className="w-full py-3 bg-gradient-to-r from-orange-500 to-red-500 rounded-xl text-white font-semibold hover:from-orange-600 hover:to-red-600 transition-all shrink-0"
            >
              {t('got_it')}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
