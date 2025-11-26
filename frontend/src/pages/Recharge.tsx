import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, Copy, CheckCircle } from 'lucide-react'
import { useTranslation } from '../providers/I18nProvider'
import { haptic, showAlert } from '../utils/telegram'

const PRESET_AMOUNTS = [10, 50, 100, 500, 1000]

export default function Recharge() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [amount, setAmount] = useState('')
  const [currency, setCurrency] = useState('USDT')
  const [copied, setCopied] = useState(false)

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
            {['USDT', 'TON'].map((c) => (
              <button
                key={c}
                onClick={() => setCurrency(c)}
                className={`flex-1 py-3 rounded-xl border transition-colors ${
                  currency === c
                    ? 'bg-green-500 border-green-500 text-white'
                    : 'bg-brand-darker border-white/5 text-gray-400'
                }`}
              >
                {c}
              </button>
            ))}
          </div>
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
    </div>
  )
}

