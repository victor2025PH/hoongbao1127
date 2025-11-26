import { useQuery } from '@tanstack/react-query'
import { Settings, ChevronRight, Shield, HelpCircle, FileText, LogOut } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from '../providers/I18nProvider'
import { getUserProfile, getBalance } from '../utils/api'
import { getTelegramUser } from '../utils/telegram'

export default function ProfilePage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const tgUser = getTelegramUser()

  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: getUserProfile,
  })

  const { data: balance } = useQuery({
    queryKey: ['balance'],
    queryFn: getBalance,
  })

  const displayName = profile?.first_name || tgUser?.first_name || 'User'
  const username = profile?.username || tgUser?.username

  return (
    <div className="h-full overflow-y-auto scrollbar-hide pb-20 p-4 space-y-4">
      {/* 用戶卡片 */}
      <div className="bg-gradient-to-br from-brand-red/20 via-brand-darker to-orange-500/20 border border-brand-red/30 rounded-2xl p-4">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-brand-red to-orange-500 flex items-center justify-center text-2xl font-bold text-white">
            {displayName[0]?.toUpperCase()}
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">{displayName}</h2>
            {username && <p className="text-gray-400">@{username}</p>}
            <div className="flex items-center gap-2 mt-1">
              <span className="px-2.5 py-1 bg-brand-red/20 text-brand-red text-sm rounded-full font-bold">
                Lv.{profile?.level || 1}
              </span>
            </div>
          </div>
        </div>

        {/* 資產 */}
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-white/5 rounded-xl p-3 text-center">
            <div className="text-lg font-bold text-white">{balance?.usdt?.toFixed(2) || '0.00'}</div>
            <div className="text-sm text-gray-400 font-medium">USDT</div>
          </div>
          <div className="bg-white/5 rounded-xl p-3 text-center">
            <div className="text-lg font-bold text-white">{balance?.ton?.toFixed(2) || '0.00'}</div>
            <div className="text-xs text-gray-400">TON</div>
          </div>
          <div className="bg-white/5 rounded-xl p-3 text-center">
            <div className="text-lg font-bold text-brand-gold">{balance?.stars || 0}</div>
            <div className="text-xs text-gray-400">Stars</div>
          </div>
        </div>
      </div>

      {/* 菜單列表 */}
      <div className="space-y-2">
        <MenuItem
          icon={Settings}
          title={t('settings')}
          onClick={() => navigate('/settings')}
        />
        <MenuItem
          icon={Shield}
          title={t('security_settings')}
          onClick={() => {}}
        />
        <MenuItem
          icon={HelpCircle}
          title={t('help_center')}
          onClick={() => {}}
        />
        <MenuItem
          icon={FileText}
          title={t('user_agreement')}
          onClick={() => {}}
        />
      </div>

      {/* 版本信息 */}
      <div className="text-center text-gray-500 text-sm mt-8">
        <p>Version 1.0.0</p>
        <p className="mt-1">© 2024 {t('app_name')}</p>
      </div>
    </div>
  )
}

function MenuItem({ icon: Icon, title, onClick }: {
  icon: React.ElementType
  title: string
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-center justify-between p-4 bg-brand-darker rounded-xl active:bg-white/5 transition-colors"
    >
      <div className="flex items-center gap-3">
        <Icon size={20} className="text-gray-400" />
        <span className="text-white">{title}</span>
      </div>
      <ChevronRight size={18} className="text-gray-500" />
    </button>
  )
}

