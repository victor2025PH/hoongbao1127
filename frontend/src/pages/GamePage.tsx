import { useState, useEffect } from 'react'
import { Crown, Zap, Trophy, Star, Sparkles, ChevronRight, Shield, Gift, Gem } from 'lucide-react'
import { getTelegram } from '../utils/telegram'
import { useTranslation } from '../providers/I18nProvider'

export default function GamePage() {
  const { t } = useTranslation()
  const [isLoading, setIsLoading] = useState(false)
  const [currentSlide, setCurrentSlide] = useState(0)

  const gameCategories = [
    { id: 'slots', name: t('slots'), icon: '🎰', color: 'from-purple-500 to-pink-500' },
    { id: 'live', name: t('live'), icon: '🎭', color: 'from-red-500 to-orange-500' },
    { id: 'sports', name: t('sports'), icon: '⚽', color: 'from-green-500 to-emerald-500' },
    { id: 'poker', name: t('poker'), icon: '🃏', color: 'from-blue-500 to-cyan-500' },
    { id: 'lottery', name: t('lottery'), icon: '🎱', color: 'from-yellow-500 to-amber-500' },
    { id: 'fishing', name: t('fishing'), icon: '🐟', color: 'from-teal-500 to-blue-500' },
  ]

  const promotions = [
    { title: t('first_deposit'), desc: t('max_bonus'), gradient: 'from-amber-400 via-yellow-500 to-orange-500' },
    { title: t('daily_rebate'), desc: t('unlimited'), gradient: 'from-purple-400 via-pink-500 to-red-500' },
    { title: t('vip_privilege'), desc: t('exclusive'), gradient: 'from-cyan-400 via-blue-500 to-purple-500' },
  ]

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % promotions.length)
    }, 3000)
    return () => clearInterval(timer)
  }, [promotions.length])

  const handleOpenGame = () => {
    setIsLoading(true)
    const telegram = getTelegram()
    const gameUrl = 'https://8887893.com'
    
    setTimeout(() => {
      if (telegram) {
        telegram.openLink(gameUrl)
      } else {
        window.open(gameUrl, '_blank')
      }
      setIsLoading(false)
    }, 500)
  }

  return (
    <div className="h-full overflow-y-auto scrollbar-hide pb-20">
      {/* 頂部區域 */}
      <div className="relative bg-gradient-to-b from-[#1a0a2e] via-[#2d1b4e] to-[#0d0d1a] px-4 pt-4 pb-4">
        {/* 裝飾光效 */}
        <div className="absolute top-0 left-1/4 w-48 h-48 bg-purple-600/30 rounded-full blur-[80px]" />
        <div className="absolute top-10 right-0 w-40 h-40 bg-pink-600/20 rounded-full blur-[60px]" />

        {/* 星星裝飾 */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(12)].map((_, i) => (
            <div
              key={i}
              className="absolute w-1 h-1 bg-white rounded-full animate-pulse"
              style={{
                top: `${Math.random() * 100}%`,
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 2}s`,
                opacity: Math.random() * 0.5 + 0.3,
              }}
            />
          ))}
        </div>

        {/* Logo 和標題 */}
        <div className="relative text-center mb-3">
          <div className="inline-flex items-center justify-center w-16 h-16 mb-2 relative">
            <div className="absolute inset-0 rounded-full bg-gradient-to-r from-amber-400 via-yellow-500 to-orange-500 animate-spin opacity-40" style={{ animationDuration: '8s' }} />
            <div className="absolute inset-1 rounded-full bg-[#1a0a2e]" />
            <div className="relative w-12 h-12 rounded-full bg-gradient-to-br from-amber-400 via-yellow-500 to-orange-600 flex items-center justify-center shadow-xl shadow-amber-500/40">
              <Crown className="w-6 h-6 text-white" />
            </div>
          </div>
          
          <h1 className="text-2xl font-black bg-gradient-to-r from-amber-200 via-yellow-400 to-amber-200 bg-clip-text text-transparent mb-0.5">
            {t('gold_fortune')}
          </h1>
          <p className="text-purple-300/70 text-xs tracking-widest">GOLD FORTUNE BUREAU</p>
        </div>

        {/* 輪播優惠 - 更緊湊 */}
        <div className="relative h-16 mb-3 overflow-hidden rounded-xl">
          {promotions.map((promo, idx) => (
            <div
              key={idx}
              className={`absolute inset-0 transition-all duration-500 ${
                idx === currentSlide ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-full'
              }`}
            >
              <div className={`h-full bg-gradient-to-r ${promo.gradient} px-4 py-2 flex items-center justify-between`}>
                <div>
                  <h3 className="text-white text-lg font-black">{promo.title}</h3>
                  <p className="text-white/80 text-xs">{promo.desc}</p>
                </div>
                <Gift className="w-8 h-8 text-white/70" />
              </div>
            </div>
          ))}
          <div className="absolute bottom-1.5 left-1/2 -translate-x-1/2 flex gap-1">
            {promotions.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentSlide(idx)}
                className={`h-1.5 rounded-full transition-all ${
                  idx === currentSlide ? 'w-4 bg-white' : 'w-1.5 bg-white/40'
                }`}
              />
            ))}
          </div>
        </div>

        {/* 開始遊戲按鈕 */}
        <button
          onClick={handleOpenGame}
          disabled={isLoading}
          className="relative w-full py-3.5 rounded-xl overflow-hidden group active:scale-[0.98] transition-all"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-amber-500 via-yellow-500 to-orange-500" />
          <div className="absolute inset-0 bg-gradient-to-b from-white/25 via-transparent to-transparent" />
          <div className="absolute top-0 left-0 right-0 h-px bg-white/50" />
          
          <div className="relative flex items-center justify-center gap-2">
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <Zap className="w-5 h-5 text-white" />
                <span className="text-white text-lg font-black">{t('start_game')}</span>
                <ChevronRight className="w-5 h-5 text-white/80" />
              </>
            )}
          </div>
        </button>
      </div>

      {/* 遊戲分類 - 更緊湊的網格 */}
      <div className="px-4 py-3 bg-[#0d0d1a]">
        <div className="flex items-center gap-1.5 mb-2">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-bold text-white">{t('hot_games')}</h2>
        </div>

        <div className="grid grid-cols-6 gap-2">
          {gameCategories.map((cat) => (
            <button
              key={cat.id}
              onClick={handleOpenGame}
              className="relative p-2 rounded-xl overflow-hidden group active:scale-95 transition-transform"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${cat.color} opacity-20`} />
              <div className="absolute inset-0 bg-white/5" />
              <div className="absolute inset-px rounded-xl border border-white/10" />
              
              <div className="relative flex flex-col items-center gap-1">
                <span className="text-xl">{cat.icon}</span>
                <span className="text-white text-[10px] font-medium">{cat.name}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 特色優勢 - 橫向排列 */}
      <div className="px-4 py-3 bg-[#0a0a12]">
        <div className="flex items-center gap-1.5 mb-2">
          <Trophy className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-bold text-white">{t('vip_privileges')}</h2>
        </div>

        <div className="grid grid-cols-3 gap-2">
          <FeatureCard
            icon={<Shield className="w-5 h-5" />}
            title={t('security')}
            gradient="from-emerald-500 to-teal-600"
          />
          <FeatureCard
            icon={<Gem className="w-5 h-5" />}
            title={t('vip_benefits')}
            gradient="from-purple-500 to-pink-600"
          />
          <FeatureCard
            icon={<Star className="w-5 h-5" />}
            title={t('fast_withdraw')}
            gradient="from-amber-500 to-orange-600"
          />
        </div>
      </div>

      {/* 底部說明 */}
      <div className="px-4 py-3 bg-[#0a0a12] text-center">
        <p className="text-white/20 text-[10px]">© 2025 Gold Fortune Bureau</p>
      </div>
    </div>
  )
}

function FeatureCard({ 
  icon, 
  title, 
  gradient 
}: { 
  icon: React.ReactNode
  title: string
  gradient: string 
}) {
  return (
    <div className="relative p-3 rounded-xl overflow-hidden bg-white/5 border border-white/10">
      <div className="flex flex-col items-center gap-1.5">
        <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${gradient} flex items-center justify-center text-white`}>
          {icon}
        </div>
        <span className="text-white text-xs font-medium">{title}</span>
      </div>
    </div>
  )
}
