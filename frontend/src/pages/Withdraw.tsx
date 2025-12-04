import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Info, Wallet } from 'lucide-react'
import { useTranslation } from '../providers/I18nProvider'
import TelegramStar from '../components/TelegramStar'
import { createWithdrawOrder } from '../utils/api'
import { haptic, showAlert } from '../utils/telegram'

export default function Withdraw() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const [amount, setAmount] = useState('')
  const [currency, setCurrency] = useState('USDT')
  const [address, setAddress] = useState('')
  const [showRulesModal, setShowRulesModal] = useState(false)
  const [dontShowAgain, setDontShowAgain] = useState(false)

  // 每次進入頁面時檢查是否需要顯示規則彈窗
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const dontShowRules = localStorage.getItem('dont_show_withdraw_rules')
      if (!dontShowRules) {
        const timer = setTimeout(() => {
          setShowRulesModal(true)
        }, 500)
        return () => clearTimeout(timer)
      }
    }
  }, [])

  const withdrawMutation = useMutation({
    mutationFn: () => createWithdrawOrder(parseFloat(amount), currency, address),
    onSuccess: () => {
      haptic('success')
      showAlert(t('withdraw_submitted'))
      queryClient.invalidateQueries({ queryKey: ['balance'] })
      navigate(-1)
    },
    onError: (error: Error) => {
      haptic('error')
      showAlert(error.message)
    },
  })

  const handleSubmit = () => {
    if (!amount || parseFloat(amount) <= 0) {
      showAlert(t('enter_amount'))
      return
    }
    if (!address) {
      showAlert(t('enter_receiving_address'))
      return
    }
    haptic('medium')
    withdrawMutation.mutate()
  }

  return (
    <div className="h-full flex flex-col bg-brand-dark">
      {/* 頂部 */}
      <div className="flex items-center justify-between p-4 border-b border-white/5">
        <button onClick={() => navigate(-1)} className="p-2">
          <X size={24} />
        </button>
        <h1 className="text-lg font-bold">{t('withdraw')}</h1>
        <div className="w-10" />
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 pb-24">
        {/* 幣種選擇 */}
        <div>
          <label className="block text-gray-300 text-base mb-2 font-medium">{t('select_currency')}</label>
          <div className="flex gap-2">
            {['USDT', 'TON', 'Stars'].map((c) => (
              <div key={c} className="flex-1 flex items-center gap-1">
                <button
                  onClick={() => setCurrency(c)}
                  className={`flex-1 py-3 rounded-xl border transition-colors ${
                    currency === c
                      ? 'bg-brand-red border-brand-red text-white'
                      : 'bg-brand-darker border-white/5 text-gray-400'
                  }`}
                >
                  {c}
                </button>
                <button
                  type="button"
                  onClick={() => setShowRulesModal(true)}
                  className="p-2 text-gray-400 hover:text-brand-red transition-colors"
                  title="點擊查看提取規則"
                >
                  <Info size={18} />
                </button>
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setShowRulesModal(true)}
            className="text-brand-red text-sm flex items-center gap-1 hover:opacity-80 mt-2"
          >
            <Info size={14} />
            {t('currency_withdraw_rules')} - {currency}
          </button>
        </div>

        {/* 提現金額 */}
        <div>
          <label className="block text-gray-400 text-sm mb-2">{t('withdraw_amount')}</label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.00"
            className="w-full p-4 bg-brand-darker rounded-xl border border-white/5 text-white text-xl font-bold text-center focus:outline-none focus:border-brand-red"
          />
          <p className="text-gray-400 text-sm mt-2 text-right">
            {t('fee')}: 1 {currency} | {t('min_withdraw')}: 10 {currency}
          </p>
        </div>

        {/* 收款地址 */}
        <div>
          <label className="block text-gray-400 text-sm mb-2">{t('receiving_address')}</label>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder={t('enter_address')}
            className="w-full p-4 bg-brand-darker rounded-xl border border-white/5 text-white focus:outline-none focus:border-brand-red"
          />
        </div>

        {/* 提示 */}
        <div className="bg-brand-red/10 border border-brand-red/30 rounded-xl p-4">
          <h4 className="text-brand-red font-bold mb-2">{t('notice')}</h4>
          <ul className="text-red-200/80 text-base space-y-1.5">
            <li>• {t('confirm_address')}</li>
            <li>• {t('review_time')}</li>
            <li>• {t('large_withdraw')}</li>
          </ul>
        </div>
      </div>

      {/* 提交按鈕 */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-brand-dark/90 backdrop-blur border-t border-white/5">
        <button
          onClick={handleSubmit}
          disabled={withdrawMutation.isPending}
          className="w-full py-4 bg-gradient-to-r from-brand-red to-orange-500 rounded-xl text-white font-bold text-lg disabled:opacity-50"
        >
          {withdrawMutation.isPending ? t('submitting') : t('submit_withdraw')}
        </button>
      </div>

      {/* 提取規則彈窗 */}
      {showRulesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 pb-24" onClick={() => {
          if (dontShowAgain) {
            localStorage.setItem('dont_show_withdraw_rules', 'true')
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
                  <TelegramStar size={18} withSpray={true} />
                  {currency === 'USDT' && t('currency_withdraw_rules_usdt')}
                  {currency === 'TON' && t('currency_withdraw_rules_ton')}
                  {currency === 'Stars' && t('currency_withdraw_rules_stars')}
                  <TelegramStar size={18} withSpray={true} />
                </h3>
              </div>
              <button
                onClick={() => {
                  if (dontShowAgain) {
                    localStorage.setItem('dont_show_withdraw_rules', 'true')
                  }
                  setShowRulesModal(false)
                }}
                className="p-1 hover:bg-white/5 rounded-lg transition-colors"
              >
                <X size={20} className="text-white" />
              </button>
            </div>

            {/* 規則內容 */}
            <div className="space-y-4 overflow-y-auto flex-1 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent">
              {/* 最低提取金額 */}
              <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/30 rounded-xl p-4">
                <h4 className="text-white font-semibold text-base mb-2">{t('currency_withdraw_min_amount')}</h4>
                <p className="text-gray-300 text-sm">
                  {currency === 'USDT' && t('currency_withdraw_min_usdt')}
                  {currency === 'TON' && t('currency_withdraw_min_ton')}
                  {currency === 'Stars' && t('currency_withdraw_min_stars')}
                </p>
              </div>

              {/* 手續費 */}
              <div className="bg-gradient-to-r from-red-500/10 to-pink-500/10 border border-red-500/30 rounded-xl p-4">
                <h4 className="text-white font-semibold text-base mb-2">{t('currency_withdraw_fee')}</h4>
                <div className="text-gray-300 text-sm leading-relaxed space-y-2">
                  {currency === 'USDT' && t('currency_withdraw_fee_usdt').split('\n').map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                  {currency === 'TON' && <p>{t('currency_withdraw_fee_ton')}</p>}
                  {currency === 'Stars' && <p>{t('currency_withdraw_fee_stars')}</p>}
                </div>
              </div>

              {/* 處理時間 */}
              <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-xl p-4">
                <h4 className="text-white font-semibold text-base mb-2">{t('currency_withdraw_processing_time')}</h4>
                <p className="text-gray-300 text-sm">
                  {currency === 'USDT' && t('currency_withdraw_processing_usdt')}
                  {currency === 'TON' && t('currency_withdraw_processing_ton')}
                  {currency === 'Stars' && t('currency_withdraw_processing_stars')}
                </p>
              </div>

              {/* 地址注意事項 */}
              <div className="bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/30 rounded-xl p-4">
                <h4 className="text-white font-semibold text-base mb-2">{t('currency_withdraw_address_note')}</h4>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {t('currency_withdraw_address_note_desc')}
                </p>
              </div>
            </div>

            {/* 不再顯示選擇框 */}
            <div className="flex items-center gap-2 mt-4 mb-4 shrink-0">
              <input
                type="checkbox"
                id="dontShowWithdrawRules"
                checked={dontShowAgain}
                onChange={(e) => setDontShowAgain(e.target.checked)}
                className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-brand-red focus:ring-brand-red focus:ring-2"
              />
              <label htmlFor="dontShowWithdrawRules" className="text-gray-300 text-sm cursor-pointer select-none">
                {t('dont_show_again')}
              </label>
            </div>

            {/* 關閉按鈕 */}
            <button
              onClick={() => {
                if (dontShowAgain) {
                  localStorage.setItem('dont_show_withdraw_rules', 'true')
                }
                setShowRulesModal(false)
              }}
              className="w-full py-3 bg-gradient-to-r from-orange-500 to-red-500 rounded-xl text-white font-semibold hover:from-orange-600 hover:to-red-600 transition-all shrink-0 mb-2"
            >
              {t('got_it')}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

