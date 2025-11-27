import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Trophy, ArrowLeft } from 'lucide-react'
import { useTranslation } from '../providers/I18nProvider'
import { useSound } from '../hooks/useSound'
import { useNavigate } from 'react-router-dom'
import PageTransition from '../components/PageTransition'
import confetti from 'canvas-confetti'

interface Prize {
  id: number
  name: string
  value: number
  color: string
  bgGradient: string
  probability: number
}

const prizes: Prize[] = [
  { id: 1, name: 'Energy', value: 100, color: 'text-yellow-400', bgGradient: 'from-yellow-500/40 to-orange-500/40', probability: 10 },
  { id: 2, name: 'Energy', value: 50, color: 'text-yellow-400', bgGradient: 'from-yellow-500/40 to-orange-500/40', probability: 20 },
  { id: 3, name: 'Energy', value: 30, color: 'text-yellow-400', bgGradient: 'from-yellow-500/40 to-orange-500/40', probability: 25 },
  { id: 4, name: 'Fortune', value: 20, color: 'text-purple-400', bgGradient: 'from-purple-500/40 to-pink-500/40', probability: 15 },
  { id: 5, name: 'Fortune', value: 10, color: 'text-purple-400', bgGradient: 'from-purple-500/40 to-pink-500/40', probability: 20 },
  { id: 6, name: 'Stars', value: 5, color: 'text-cyan-400', bgGradient: 'from-cyan-500/40 to-blue-500/40', probability: 10 },
]

// 幸运符号 SVG 组件
const Horseshoe = ({ size = 24, className = "" }: { size?: number; className?: string }) => (
  <svg viewBox="0 0 24 24" width={size} height={size} className={className}>
    <path 
      d="M5 2C3.343 2 2 3.343 2 5v7c0 5.523 4.477 10 10 10s10-4.477 10-10V5c0-1.657-1.343-3-3-3h-2v5c0 2.761-2.239 5-5 5s-5-2.239-5-5V2H5z" 
      fill="currentColor"
    />
  </svg>
)

const FourLeafClover = ({ size = 24, className = "" }: { size?: number; className?: string }) => (
  <svg viewBox="0 0 100 100" width={size} height={size} className={className}>
    <defs>
      <linearGradient id="cloverGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#22c55e" />
        <stop offset="50%" stopColor="#16a34a" />
        <stop offset="100%" stopColor="#15803d" />
      </linearGradient>
    </defs>
    {/* 四片叶子 */}
    <ellipse cx="50" cy="30" rx="18" ry="22" fill="url(#cloverGrad)" transform="rotate(0 50 50)" />
    <ellipse cx="70" cy="50" rx="22" ry="18" fill="url(#cloverGrad)" transform="rotate(0 50 50)" />
    <ellipse cx="50" cy="70" rx="18" ry="22" fill="url(#cloverGrad)" transform="rotate(0 50 50)" />
    <ellipse cx="30" cy="50" rx="22" ry="18" fill="url(#cloverGrad)" transform="rotate(0 50 50)" />
    {/* 茎 */}
    <path d="M50 72 Q48 85, 42 95" stroke="#15803d" strokeWidth="4" fill="none" strokeLinecap="round" />
    {/* 叶脉 */}
    <path d="M50 50 L50 20" stroke="#15803d" strokeWidth="2" opacity="0.5" />
    <path d="M50 50 L80 50" stroke="#15803d" strokeWidth="2" opacity="0.5" />
    <path d="M50 50 L50 80" stroke="#15803d" strokeWidth="2" opacity="0.5" />
    <path d="M50 50 L20 50" stroke="#15803d" strokeWidth="2" opacity="0.5" />
    {/* 高光 */}
    <ellipse cx="45" cy="26" rx="5" ry="6" fill="rgba(255,255,255,0.3)" />
    <ellipse cx="74" cy="45" rx="6" ry="5" fill="rgba(255,255,255,0.3)" />
  </svg>
)

const LuckyStar = ({ size = 24, className = "" }: { size?: number; className?: string }) => (
  <svg viewBox="0 0 24 24" width={size} height={size} className={className}>
    <path 
      d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" 
      fill="currentColor"
    />
  </svg>
)

const Clover = ({ size = 24, className = "" }: { size?: number; className?: string }) => (
  <svg viewBox="0 0 24 24" width={size} height={size} className={className}>
    <circle cx="9" cy="9" r="5" fill="currentColor" />
    <circle cx="15" cy="9" r="5" fill="currentColor" />
    <circle cx="12" cy="15" r="5" fill="currentColor" />
    <rect x="11" y="16" width="2" height="6" fill="currentColor" />
  </svg>
)

const Gem = ({ size = 24, className = "" }: { size?: number; className?: string }) => (
  <svg viewBox="0 0 24 24" width={size} height={size} className={className}>
    <path d="M6 3h12l4 6-10 12L2 9l4-6z" fill="currentColor" />
    <path d="M2 9h20M6 3l6 18M18 3l-6 18M6 3l6 6 6-6" stroke="rgba(255,255,255,0.3)" strokeWidth="0.5" fill="none" />
  </svg>
)

const Coin = ({ size = 24, className = "" }: { size?: number; className?: string }) => (
  <svg viewBox="0 0 24 24" width={size} height={size} className={className}>
    <circle cx="12" cy="12" r="10" fill="currentColor" />
    <circle cx="12" cy="12" r="7" stroke="rgba(0,0,0,0.2)" strokeWidth="1" fill="none" />
    <text x="12" y="16" textAnchor="middle" fontSize="10" fill="rgba(0,0,0,0.3)" fontWeight="bold">$</text>
  </svg>
)

export default function LuckyWheelPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { playSound } = useSound()
  const [isHolding, setIsHolding] = useState(false)
  const [holdProgress, setHoldProgress] = useState(0)
  const [isExploding, setIsExploding] = useState(false)
  const [selectedPrize, setSelectedPrize] = useState<Prize | null>(null)
  const [spinsLeft, setSpinsLeft] = useState(3)
  const [showNoChancesModal, setShowNoChancesModal] = useState(false)
  const [ringRotations, setRingRotations] = useState({ outer: 0, middle: 0, inner: 0 })
  const holdTimerRef = useRef<number | null>(null)
  const progressTimerRef = useRef<number | null>(null)
  const animationRef = useRef<number | null>(null)
  const coinRef = useRef<HTMLDivElement>(null)
  const HOLD_DURATION = 2000

  // 持续旋转动画
  useEffect(() => {
    let lastTime = 0
    const animate = (timestamp: number) => {
      if (!lastTime) lastTime = timestamp
      const delta = timestamp - lastTime
      lastTime = timestamp
      
      const speed = isHolding ? 8 : 1 // 按住时速度x8
      
      setRingRotations(prev => ({
        outer: prev.outer + 0.05 * speed * (delta / 16),
        middle: prev.middle - 0.08 * speed * (delta / 16),
        inner: prev.inner + 0.12 * speed * (delta / 16),
      }))
      
      animationRef.current = requestAnimationFrame(animate)
    }
    
    animationRef.current = requestAnimationFrame(animate)
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [isHolding])

  const drawPrize = () => {
    const totalWeight = prizes.reduce((sum, p) => sum + p.probability, 0)
    let random = Math.random() * totalWeight
    let selected: Prize | null = null

    for (const prize of prizes) {
      random -= prize.probability
      if (random <= 0) {
        selected = prize
        break
      }
    }

    if (!selected) selected = prizes[prizes.length - 1]
    return selected
  }

  const handleStart = () => {
    if (spinsLeft <= 0) {
      setShowNoChancesModal(true)
      return
    }
    if (isExploding) return

    setIsHolding(true)
    setHoldProgress(0)
    playSound('click')

    const startTime = Date.now()
    progressTimerRef.current = window.setInterval(() => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(100, (elapsed / HOLD_DURATION) * 100)
      setHoldProgress(progress)

      if (progress >= 100) {
        handleComplete()
      }
    }, 16)
  }

  const handleEnd = () => {
    setIsHolding(false)
    if (holdTimerRef.current) {
      window.clearTimeout(holdTimerRef.current)
      holdTimerRef.current = null
    }
    if (progressTimerRef.current) {
      window.clearInterval(progressTimerRef.current)
      progressTimerRef.current = null
    }
    setHoldProgress(0)
  }

  const handleComplete = () => {
    if (isExploding) return

    setIsHolding(false)
    setIsExploding(true)
    playSound('success')

    if (progressTimerRef.current) {
      window.clearInterval(progressTimerRef.current)
      progressTimerRef.current = null
    }

    // 爆炸彩纸效果
    const end = Date.now() + 2500
    const colors = ['#22c55e', '#fbbf24', '#f472b6', '#8b5cf6', '#10b981', '#3b82f6', '#ec4899', '#06b6d4', '#eab308']
    
    const frame = () => {
      // 从中心向四周爆炸
      confetti({
        particleCount: 12,
        angle: Math.random() * 360,
        spread: 80,
        origin: { x: 0.5, y: 0.45 },
        colors: colors,
        zIndex: 1000,
        gravity: 0.6,
        scalar: 1.2,
        drift: (Math.random() - 0.5) * 2,
      })
      
      if (Date.now() < end) {
        requestAnimationFrame(frame)
      }
    }
    frame()

    setTimeout(() => {
      const prize = drawPrize()
      setSelectedPrize(prize)
      setSpinsLeft(prev => prev - 1)
      setIsExploding(false)
    }, 2000)
  }

  // 外圈符号配置 - 绿宝石和金点
  const outerSymbols = Array.from({ length: 12 }).map((_, i) => ({
    angle: (360 / 12) * i,
    type: i % 2 === 0 ? 'gem' : 'dot',
  }))

  // 中圈符号配置 - 马蹄铁、星星、三叶草、金币
  const middleSymbols = Array.from({ length: 8 }).map((_, i) => ({
    angle: (360 / 8) * i,
    type: ['horseshoe', 'star', 'clover', 'coin'][i % 4],
  }))

  // 内圈符号配置 - 小星星
  const innerSymbols = Array.from({ length: 6 }).map((_, i) => ({
    angle: (360 / 6) * i,
    type: 'star',
  }))

  const renderSymbol = (type: string, size: number) => {
    switch (type) {
      case 'horseshoe':
        return <Horseshoe size={size} className="text-amber-600" />
      case 'star':
        return <LuckyStar size={size} className="text-amber-400" />
      case 'clover':
        return <Clover size={size} className="text-green-500" />
      case 'gem':
        return <Gem size={size} className="text-emerald-400" />
      case 'coin':
        return <Coin size={size} className="text-yellow-500" />
      case 'dot':
        return <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-lg shadow-emerald-400/50" />
      default:
        return null
    }
  }

  return (
    <PageTransition>
      <div className="h-full flex flex-col overflow-hidden bg-gradient-to-b from-amber-900/30 via-[#0a0a0a] to-[#0a0a0a]">
        {/* 顶部标题栏 */}
        <div className="flex items-center justify-between px-4 py-3 shrink-0 border-b border-amber-500/10">
          <button
            onClick={() => navigate(-1)}
            className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center hover:bg-white/10 transition-colors"
          >
            <ArrowLeft size={20} className="text-white" />
          </button>
          <h1 className="text-lg font-bold text-amber-400 flex items-center gap-2">
            <Trophy size={20} className="text-amber-400" />
            Lucky Coin
          </h1>
          <div className="w-10" />
        </div>

        {/* 主要内容区域 */}
        <div className="flex-1 flex flex-col items-center justify-center gap-6 p-4 min-h-0 relative overflow-hidden">
          {/* 背景光效 */}
          <div className="absolute inset-0 pointer-events-none">
            <div 
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full"
              style={{
                background: isHolding 
                  ? 'radial-gradient(circle, rgba(34, 197, 94, 0.3) 0%, rgba(251, 191, 36, 0.2) 30%, transparent 70%)'
                  : 'radial-gradient(circle, rgba(251, 191, 36, 0.15) 0%, transparent 60%)',
                filter: 'blur(40px)',
                transition: 'all 0.5s ease',
              }}
            />
          </div>

          {/* 幸运金币 */}
          <div
            ref={coinRef}
            className="relative w-80 h-80 cursor-pointer"
            onMouseDown={handleStart}
            onMouseUp={handleEnd}
            onMouseLeave={handleEnd}
            onTouchStart={handleStart}
            onTouchEnd={handleEnd}
            onTouchCancel={handleEnd}
          >
            <motion.div
              className="w-full h-full"
              animate={isExploding ? {
                scale: [1, 1.2, 0],
                opacity: [1, 1, 0],
                rotate: [0, 720],
              } : isHolding ? {
                scale: [1, 1.05, 1],
              } : {}}
              transition={{
                duration: isExploding ? 1.5 : 0.5,
                repeat: isExploding ? 0 : isHolding ? Infinity : 0,
              }}
            >
              {/* 金币阴影 */}
              <div 
                className="absolute inset-4 rounded-full"
                style={{
                  background: 'rgba(0, 0, 0, 0.5)',
                  filter: 'blur(20px)',
                  transform: 'translateY(10px)',
                }}
              />

              {/* 最外层金边 */}
              <div 
                className="absolute inset-0 rounded-full"
                style={{
                  background: 'linear-gradient(145deg, #fcd34d 0%, #b45309 50%, #78350f 100%)',
                  boxShadow: isHolding 
                    ? '0 0 60px rgba(251, 191, 36, 0.6), inset 0 0 30px rgba(255, 255, 255, 0.2)'
                    : '0 0 30px rgba(251, 191, 36, 0.3), inset 0 0 20px rgba(255, 255, 255, 0.1)',
                  transition: 'box-shadow 0.3s ease',
                }}
              />

              {/* 外圈装饰层 - 深棕色带绿宝石 */}
              <div 
                className="absolute rounded-full overflow-hidden"
                style={{
                  inset: '3%',
                  background: 'linear-gradient(145deg, #78350f 0%, #451a03 50%, #27150a 100%)',
                  boxShadow: 'inset 0 4px 8px rgba(0,0,0,0.5), inset 0 -4px 8px rgba(255,255,255,0.1)',
                }}
              >
                {/* 外圈旋转符号 */}
                <motion.div 
                  className="absolute inset-0"
                  style={{ rotate: ringRotations.outer }}
                >
                  {outerSymbols.map((sym, i) => {
                    const radius = 45 // 百分比
                    const angleRad = (sym.angle * Math.PI) / 180
                    const x = 50 + radius * Math.sin(angleRad)
                    const y = 50 - radius * Math.cos(angleRad)
                    return (
                      <div
                        key={i}
                        className="absolute"
                        style={{
                          left: `${x}%`,
                          top: `${y}%`,
                          transform: `translate(-50%, -50%) rotate(${sym.angle}deg)`,
                        }}
                      >
                        {sym.type === 'gem' ? (
                          <div className="w-4 h-4 rounded-full bg-gradient-to-br from-emerald-300 to-emerald-600 shadow-lg shadow-emerald-500/50" />
                        ) : (
                          <div className="w-2 h-2 rounded-full bg-amber-400 shadow-lg shadow-amber-400/50" />
                        )}
                      </div>
                    )
                  })}
                </motion.div>
              </div>

              {/* 中圈金色层 */}
              <div 
                className="absolute rounded-full"
                style={{
                  inset: '14%',
                  background: 'linear-gradient(145deg, #fde68a 0%, #fbbf24 30%, #d97706 70%, #92400e 100%)',
                  boxShadow: 'inset 0 4px 12px rgba(255,255,255,0.4), inset 0 -6px 12px rgba(0,0,0,0.3)',
                }}
              >
                {/* 中圈旋转符号 */}
                <motion.div 
                  className="absolute inset-0"
                  style={{ rotate: ringRotations.middle }}
                >
                  {middleSymbols.map((sym, i) => {
                    const radius = 40
                    const angleRad = (sym.angle * Math.PI) / 180
                    const x = 50 + radius * Math.sin(angleRad)
                    const y = 50 - radius * Math.cos(angleRad)
                    return (
                      <div
                        key={i}
                        className="absolute"
                        style={{
                          left: `${x}%`,
                          top: `${y}%`,
                          transform: `translate(-50%, -50%)`,
                          filter: 'drop-shadow(0 2px 3px rgba(0,0,0,0.3))',
                        }}
                      >
                        {renderSymbol(sym.type, 22)}
                      </div>
                    )
                  })}
                </motion.div>
              </div>

              {/* 内圈深棕层 */}
              <div 
                className="absolute rounded-full"
                style={{
                  inset: '28%',
                  background: 'linear-gradient(145deg, #78350f 0%, #451a03 50%, #1c0a00 100%)',
                  boxShadow: 'inset 0 3px 8px rgba(0,0,0,0.6), inset 0 -3px 8px rgba(255,255,255,0.05)',
                }}
              >
                {/* 内圈旋转符号 */}
                <motion.div 
                  className="absolute inset-0"
                  style={{ rotate: ringRotations.inner }}
                >
                  {innerSymbols.map((sym, i) => {
                    const radius = 35
                    const angleRad = (sym.angle * Math.PI) / 180
                    const x = 50 + radius * Math.sin(angleRad)
                    const y = 50 - radius * Math.cos(angleRad)
                    return (
                      <div
                        key={i}
                        className="absolute"
                        style={{
                          left: `${x}%`,
                          top: `${y}%`,
                          transform: `translate(-50%, -50%)`,
                          filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.4))',
                        }}
                      >
                        <LuckyStar size={16} className="text-amber-400" />
                      </div>
                    )
                  })}
                </motion.div>
              </div>

              {/* 中心四叶草区域 */}
              <div 
                className="absolute rounded-full flex items-center justify-center"
                style={{
                  inset: '38%',
                  background: 'linear-gradient(145deg, #fde68a 0%, #fbbf24 50%, #b45309 100%)',
                  boxShadow: 'inset 0 4px 10px rgba(255,255,255,0.5), inset 0 -4px 10px rgba(0,0,0,0.3), 0 0 20px rgba(251, 191, 36, 0.3)',
                }}
              >
                {/* 放射线纹理 */}
                <div 
                  className="absolute inset-0 rounded-full overflow-hidden opacity-30"
                  style={{
                    background: `repeating-conic-gradient(from 0deg, transparent 0deg, transparent 5deg, rgba(255,255,255,0.1) 5deg, rgba(255,255,255,0.1) 10deg)`,
                  }}
                />
                
                {/* 四叶草 */}
                <motion.div
                  animate={isHolding ? {
                    scale: [1, 1.15, 1],
                    rotate: [0, 10, -10, 0],
                  } : {
                    scale: [1, 1.05, 1],
                  }}
                  transition={{
                    duration: isHolding ? 0.3 : 2,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                  style={{
                    filter: isHolding 
                      ? 'drop-shadow(0 0 15px rgba(34, 197, 94, 0.8)) drop-shadow(0 0 30px rgba(34, 197, 94, 0.5))'
                      : 'drop-shadow(0 0 8px rgba(34, 197, 94, 0.5))',
                  }}
                >
                  <FourLeafClover size={70} />
                </motion.div>
              </div>

              {/* 高光效果 */}
              <div 
                className="absolute rounded-full pointer-events-none"
                style={{
                  top: '5%',
                  left: '15%',
                  width: '40%',
                  height: '25%',
                  background: 'linear-gradient(180deg, rgba(255,255,255,0.4) 0%, transparent 100%)',
                  filter: 'blur(4px)',
                  borderRadius: '50%',
                }}
              />

              {/* 进度环 */}
              {isHolding && (
                <svg className="absolute inset-0 w-full h-full -rotate-90">
                  <circle
                    cx="50%"
                    cy="50%"
                    r="48%"
                    fill="none"
                    stroke="rgba(34, 197, 94, 0.3)"
                    strokeWidth="4"
                  />
                  <motion.circle
                    cx="50%"
                    cy="50%"
                    r="48%"
                    fill="none"
                    stroke="#22c55e"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeDasharray={`${2 * Math.PI * 48} ${2 * Math.PI * 48}`}
                    initial={{ strokeDashoffset: 2 * Math.PI * 48 }}
                    animate={{ strokeDashoffset: 2 * Math.PI * 48 * (1 - holdProgress / 100) }}
                    style={{
                      filter: 'drop-shadow(0 0 8px #22c55e)',
                    }}
                  />
                </svg>
              )}
            </motion.div>
          </div>

          {/* 剩余次数 */}
          <div className="w-full max-w-sm shrink-0 z-10">
            <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles size={18} className="text-amber-400" />
                <span className="text-sm text-gray-300">{t('remaining_today')}</span>
              </div>
              <span className="text-2xl font-bold text-amber-400">{spinsLeft}</span>
            </div>
          </div>

          {/* 提示文字 */}
          <p className="text-amber-400/60 text-sm text-center">
            {isHolding ? '🍀 Keep holding...' : '👆 Press and hold the coin'}
          </p>
        </div>

        {/* 次数用完提示窗 */}
        <AnimatePresence>
          {showNoChancesModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                onClick={() => setShowNoChancesModal(false)}
              />
              <motion.div
                initial={{ scale: 0.5, opacity: 0, y: 50 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                exit={{ scale: 0.5, opacity: 0, y: 50 }}
                className="relative bg-[#1C1C1E] border border-amber-500/30 rounded-3xl p-8 text-center shadow-2xl max-w-sm w-full"
              >
                <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-amber-500/40 to-green-500/40 rounded-full flex items-center justify-center border-4 border-white/20">
                  <FourLeafClover size={40} />
                </div>
                <h2 className="text-2xl font-bold text-white mb-4">{t('no_chances_left')}</h2>
                <p className="text-gray-400 mb-6">{t('come_tomorrow')}</p>
                <motion.button
                  onClick={() => setShowNoChancesModal(false)}
                  className="w-full py-3 bg-gradient-to-r from-amber-600 to-green-600 text-white rounded-xl font-bold"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {t('got_it')}
                </motion.button>
              </motion.div>
            </div>
          )}
        </AnimatePresence>

        {/* 结果弹窗 */}
        <AnimatePresence>
          {selectedPrize && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                onClick={() => setSelectedPrize(null)}
              />
              <motion.div
                initial={{ scale: 0.5, opacity: 0, y: 50 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                exit={{ scale: 0.5, opacity: 0, y: 50 }}
                className="relative bg-[#1C1C1E] border border-green-500/30 rounded-3xl p-8 text-center shadow-2xl max-w-sm w-full"
              >
                <motion.div
                  animate={{ rotate: [0, 360] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-green-500/40 to-amber-500/40 rounded-full flex items-center justify-center border-4 border-white/20"
                >
                  <FourLeafClover size={50} />
                </motion.div>
                <h2 className="text-2xl font-bold text-white mb-2">🍀 Lucky!</h2>
                <p className={`text-4xl font-black ${selectedPrize.color} mb-1`}>
                  +{selectedPrize.value}
                </p>
                <p className={`text-lg font-bold ${selectedPrize.color} mb-6`}>
                  {selectedPrize.name}
                </p>
                <motion.button
                  onClick={() => setSelectedPrize(null)}
                  className="w-full py-3 bg-gradient-to-r from-green-600 to-amber-600 text-white rounded-xl font-bold"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {t('awesome')}
                </motion.button>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </PageTransition>
  )
}
