import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, Copy, CheckCircle, Info, Wallet } from 'lucide-react'
import { useTranslation } from '../providers/I18nProvider'
import TelegramStar from '../components/TelegramStar'
import { haptic, showAlert } from '../utils/telegram'

const PRESET_AMOUNTS = [10, 50, 100, 500, 1000]

export default function Recharge() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [amount, setAmount] = useState('')
  const [currency, setCurrency] = useState('USDT')
  const [copied, setCopied] = useState(false)
  const [showRulesModal, setShowRulesModal] = useState(false)
  const [dontShowAgain, setDontShowAgain] = useState(false)

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

  // 模擬收款地址
  const depositAddress = 'TXyz...abc123'

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(depositAddress)
      setCopied(true)
      haptic('success')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      showAlert(t('copy_failed'))
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
              <div key={c} className="flex-1 flex items-center gap-1">
                <button
                  onClick={() => setCurrency(c)}
                  className={`flex-1 py-3 rounded-xl border transition-colors ${
                    currency === c
                      ? 'bg-green-500 border-green-500 text-white'
                      : 'bg-brand-darker border-white/5 text-gray-400'
                  }`}
                >
                  {c}
                </button>
                <button
                  type="button"
                  onClick={() => setShowRulesModal(true)}
                  className="p-2 text-gray-400 hover:text-green-400 transition-colors"
                  title="點擊查看充值規則"
                >
                  <Info size={18} />
                </button>
              </div>
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

        {/* 快捷金額 */}
        <div>
          <label className="block text-gray-400 text-sm mb-2">{t('quick_amount')}</label>
          <div className="grid grid-cols-5 gap-2">
            {PRESET_AMOUNTS.map((preset) => (
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

        {/* 收款地址 */}
        <div className="bg-brand-darker rounded-xl p-4">
          <label className="block text-gray-400 text-sm mb-2">{t('deposit_address')} ({currency})</label>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-white text-base bg-white/5 p-3 rounded-lg overflow-hidden text-ellipsis">
              {depositAddress}
            </code>
            <button
              onClick={handleCopy}
              className="p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
            >
              {copied ? (
                <CheckCircle size={18} className="text-green-500" />
              ) : (
                <Copy size={18} className="text-gray-400" />
              )}
            </button>
          </div>
        </div>

        {/* 提示 */}
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
          <h4 className="text-yellow-500 font-bold mb-2">{t('notice')}</h4>
          <ul className="text-yellow-200/80 text-base space-y-1.5">
            <li>• {t('confirm_network')}</li>
            <li>• {t('min_deposit')}</li>
            <li>• {t('auto_credit')}</li>
          </ul>
        </div>
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
                  <TelegramStar size={18} withSpray={true} />
                  {currency === 'USDT' && t('currency_recharge_rules_usdt')}
                  {currency === 'TON' && t('currency_recharge_rules_ton')}
                  {currency === 'Stars' && t('currency_recharge_rules_stars')}
                  <TelegramStar size={18} withSpray={true} />
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
            <div className="space-y-4 overflow-y-auto flex-1 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent">
              {/* 網絡類型 */}
              <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-xl p-4">
                <h4 className="text-white font-semibold text-base mb-2">{t('currency_recharge_network')}</h4>
                <div className="text-gray-300 text-sm leading-relaxed space-y-2">
                  {currency === 'USDT' && t('currency_recharge_network_usdt').split('\n').map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                  {currency === 'TON' && <p>{t('currency_recharge_network_ton')}</p>}
                  {currency === 'Stars' && <p>{t('currency_recharge_network_stars')}</p>}
                </div>
              </div>

              {/* 最低充值金額 */}
              <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/30 rounded-xl p-4">
                <h4 className="text-white font-semibold text-base mb-2">{t('currency_recharge_min_amount')}</h4>
                <p className="text-gray-300 text-sm">
                  {currency === 'USDT' && t('currency_recharge_min_usdt')}
                  {currency === 'TON' && t('currency_recharge_min_ton')}
                  {currency === 'Stars' && t('currency_recharge_min_stars')}
                </p>
              </div>

              {/* 到賬時間 */}
              <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-xl p-4">
                <h4 className="text-white font-semibold text-base mb-2">{t('currency_recharge_confirm_time')}</h4>
                <div className="text-gray-300 text-sm leading-relaxed space-y-2">
                  {currency === 'USDT' && t('currency_recharge_confirm_usdt').split('\n').map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                  {currency === 'TON' && <p>{t('currency_recharge_confirm_ton')}</p>}
                  {currency === 'Stars' && <p>{t('currency_recharge_confirm_stars')}</p>}
                </div>
              </div>

              {/* 獲取方式提示 */}
              <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-xl p-4">
                <h4 className="text-white font-semibold text-base mb-2">{t('currency_get_method')}</h4>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {t('currency_get_method_hint')}
                </p>
              </div>
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

