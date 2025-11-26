import { useState, useEffect } from 'react'
import { Crown, Zap, Trophy, Star, Sparkles, ChevronRight, Shield, Gift, Gem } from 'lucide-react'
import { getTelegram } from '../utils/telegram'

export default function GamePage() {
  const [isLoading, setIsLoading] = useState(false)
  const [currentSlide, setCurrentSlide] = useState(0)

  const gameCategories = [
    { id: 'slots', name: '電子遊戲', icon: '🎰', color: 'from-purple-500 to-pink-500', games: 500 },
    { id: 'live', name: '真人娛樂', icon: '🎭', color: 'from-red-500 to-orange-500', games: 200 },
    { id: 'sports', name: '體育競技', icon: '⚽', color: 'from-green-500 to-emerald-500', games: 100 },
    { id: 'poker', name: '棋牌遊戲', icon: '🃏', color: 'from-blue-500 to-cyan-500', games: 80 },
    { id: 'lottery', name: '彩票投注', icon: '🎱', color: 'from-yellow-500 to-amber-500', games: 50 },
    { id: 'fishing', name: '捕魚達人', icon: '🐟', color: 'from-teal-500 to-blue-500', games: 30 },
  ]

  const promotions = [
    { title: '首存送30%', desc: '最高可獲得888元獎金', gradient: 'from-amber-400 via-yellow-500 to-orange-500' },
    { title: '每日返水', desc: '無上限即時到賬', gradient: 'from-purple-400 via-pink-500 to-red-500' },
    { title: 'VIP特權', desc: '專屬客服尊享禮遇', gradient: 'from-cyan-400 via-blue-500 to-purple-500' },
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
    }, 800)
  }

  return (
    <div className="min-h-screen overflow-y-auto scrollbar-hide pb-24">
      {/* 頂部背景 - 豪華紫金漸變 */}
      <div className="relative">
        {/* 主背景 */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#1a0a2e] via-[#2d1b4e] to-[#0d0d1a]" />
        
        {/* 裝飾光效 */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-600/30 rounded-full blur-[120px]" />
        <div className="absolute top-20 right-0 w-80 h-80 bg-pink-600/20 rounded-full blur-[100px]" />
        <div className="absolute top-40 left-0 w-60 h-60 bg-amber-500/20 rounded-full blur-[80px]" />

        {/* 星星裝飾 */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(20)].map((_, i) => (
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

        <div className="relative px-4 pt-6 pb-8">
          {/* Logo 和標題 */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-20 h-20 mb-4 relative">
              {/* 外圈動畫 */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-r from-amber-400 via-yellow-500 to-orange-500 animate-spin-slow opacity-50" style={{ animationDuration: '8s' }} />
              <div className="absolute inset-1 rounded-full bg-[#1a0a2e]" />
              {/* Logo */}
              <div className="relative w-16 h-16 rounded-full bg-gradient-to-br from-amber-400 via-yellow-500 to-orange-600 flex items-center justify-center shadow-2xl shadow-amber-500/50">
                <Crown className="w-8 h-8 text-white drop-shadow-lg" />
              </div>
            </div>
            
            <h1 className="text-3xl font-black bg-gradient-to-r from-amber-200 via-yellow-400 to-amber-200 bg-clip-text text-transparent drop-shadow-lg mb-1">
              金福寶局
            </h1>
            <p className="text-purple-300/80 text-sm font-medium tracking-widest">GOLD FORTUNE BUREAU</p>
          </div>

          {/* 輪播優惠 */}
          <div className="relative h-24 mb-6 overflow-hidden rounded-2xl">
            {promotions.map((promo, idx) => (
              <div
                key={idx}
                className={`absolute inset-0 transition-all duration-700 ease-in-out ${
                  idx === currentSlide ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-full'
                }`}
              >
                <div className={`h-full bg-gradient-to-r ${promo.gradient} p-4 flex items-center justify-between`}>
                  <div>
                    <h3 className="text-white text-xl font-black drop-shadow-lg">{promo.title}</h3>
                    <p className="text-white/90 text-sm">{promo.desc}</p>
                  </div>
                  <Gift className="w-12 h-12 text-white/80" />
                </div>
              </div>
            ))}
            {/* 指示器 */}
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5">
              {promotions.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setCurrentSlide(idx)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    idx === currentSlide ? 'w-6 bg-white' : 'bg-white/40'
                  }`}
                />
              ))}
            </div>
          </div>

          {/* 開始遊戲主按鈕 */}
          <button
            onClick={handleOpenGame}
            disabled={isLoading}
            className="relative w-full py-5 rounded-2xl overflow-hidden group active:scale-[0.98] transition-all duration-200"
          >
            {/* 按鈕背景 */}
            <div className="absolute inset-0 bg-gradient-to-r from-amber-500 via-yellow-500 to-orange-500" />
            <div className="absolute inset-0 bg-gradient-to-r from-amber-400 via-yellow-400 to-orange-400 opacity-0 group-hover:opacity-100 transition-opacity" />
            
            {/* 光澤效果 */}
            <div className="absolute inset-0 bg-gradient-to-b from-white/30 via-transparent to-transparent" />
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/60 to-transparent" />
            
            {/* 動態光線 */}
            <div className="absolute inset-0 overflow-hidden">
              <div className="absolute -inset-full bg-gradient-to-r from-transparent via-white/20 to-transparent skew-x-12 group-hover:translate-x-full transition-transform duration-1000" />
            </div>

            <div className="relative flex items-center justify-center gap-3">
              {isLoading ? (
                <div className="w-7 h-7 border-3 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Zap className="w-7 h-7 text-white drop-shadow-lg" />
                  <span className="text-white text-xl font-black tracking-wide drop-shadow-lg">
                    立即開始遊戲
                  </span>
                  <ChevronRight className="w-6 h-6 text-white/80 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </div>
          </button>
        </div>
      </div>

      {/* 遊戲分類 */}
      <div className="px-4 py-6 bg-gradient-to-b from-[#0d0d1a] to-[#0a0a12]">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-amber-400" />
          <h2 className="text-lg font-bold text-white">熱門遊戲</h2>
        </div>

        <div className="grid grid-cols-3 gap-3">
          {gameCategories.map((cat) => (
            <button
              key={cat.id}
              onClick={handleOpenGame}
              className="relative p-4 rounded-2xl overflow-hidden group active:scale-95 transition-transform"
            >
              {/* 背景 */}
              <div className={`absolute inset-0 bg-gradient-to-br ${cat.color} opacity-20 group-hover:opacity-30 transition-opacity`} />
              <div className="absolute inset-0 bg-white/5 backdrop-blur-sm" />
              <div className="absolute inset-px rounded-2xl border border-white/10" />
              
              <div className="relative flex flex-col items-center gap-2">
                <span className="text-3xl">{cat.icon}</span>
                <span className="text-white text-xs font-semibold">{cat.name}</span>
                <span className="text-white/50 text-[10px]">{cat.games}+ 遊戲</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 特色優勢 */}
      <div className="px-4 py-6 bg-[#0a0a12]">
        <div className="flex items-center gap-2 mb-4">
          <Trophy className="w-5 h-5 text-amber-400" />
          <h2 className="text-lg font-bold text-white">尊享特權</h2>
        </div>

        <div className="space-y-3">
          <FeatureCard
            icon={<Shield className="w-6 h-6" />}
            title="安全保障"
            desc="國際認證 · 資金安全"
            gradient="from-emerald-500 to-teal-600"
          />
          <FeatureCard
            icon={<Gem className="w-6 h-6" />}
            title="VIP 禮遇"
            desc="專屬客服 · 尊享回饋"
            gradient="from-purple-500 to-pink-600"
          />
          <FeatureCard
            icon={<Star className="w-6 h-6" />}
            title="極速出款"
            desc="24小時 · 閃電到賬"
            gradient="from-amber-500 to-orange-600"
          />
        </div>
      </div>

      {/* 底部裝飾 */}
      <div className="px-4 py-8 bg-[#0a0a12] text-center">
        <p className="text-white/30 text-xs mb-2">Powered by Gold Fortune Bureau</p>
        <p className="text-white/20 text-[10px]">© 2025 All Rights Reserved</p>
      </div>
    </div>
  )
}

function FeatureCard({ 
  icon, 
  title, 
  desc, 
  gradient 
}: { 
  icon: React.ReactNode
  title: string
  desc: string
  gradient: string 
}) {
  return (
    <div className="relative p-4 rounded-2xl overflow-hidden bg-white/5 backdrop-blur-sm border border-white/10">
      <div className="flex items-center gap-4">
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center text-white shadow-lg`}>
          {icon}
        </div>
        <div>
          <h3 className="text-white font-bold">{title}</h3>
          <p className="text-white/50 text-sm">{desc}</p>
        </div>
      </div>
    </div>
  )
}
