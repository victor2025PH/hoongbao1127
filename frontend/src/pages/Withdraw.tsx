import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { useTranslation } from '../providers/I18nProvider'
import { createWithdrawOrder } from '../utils/api'
import { haptic, showAlert } from '../utils/telegram'

export default function Withdraw() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const [amount, setAmount] = useState('')
  const [currency, setCurrency] = useState('USDT')
  const [address, setAddress] = useState('')

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
            {['USDT', 'TON'].map((c) => (
              <button
                key={c}
                onClick={() => setCurrency(c)}
                className={`flex-1 py-3 rounded-xl border transition-colors ${
                  currency === c
                    ? 'bg-brand-red border-brand-red text-white'
                    : 'bg-brand-darker border-white/5 text-gray-400'
                }`}
              >
                {c}
              </button>
            ))}
          </div>
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
    </div>
  )
}

