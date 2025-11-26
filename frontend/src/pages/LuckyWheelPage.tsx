import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Gift, Zap, Sparkles, Trophy, TrendingUp, ArrowLeft, Star } from 'lucide-react'
import { useTranslation } from '../providers/I18nProvider'
import { useSound } from '../hooks/useSound'
import { useNavigate } from 'react-router-dom'
import PageTransition from '../components/PageTransition'
import TelegramStar from '../components/TelegramStar'
import confetti from 'canvas-confetti'

interface Prize {
  id: number
  name: string
  value: number
  icon: React.ElementType
  color: string
  bgGradient: string
  probability: number
}

const prizes: Prize[] = [
  { id: 1, name: '能量', value: 100, icon: Zap, color: 'text-yellow-400', bgGradient: 'from-yellow-500/40 to-orange-500/40', probability: 10 },
  { id: 2, name: '能量', value: 50, icon: Zap, color: 'text-yellow-400', bgGradient: 'from-yellow-500/40 to-orange-500/40', probability: 20 },
  { id: 3, name: '能量', value: 30, icon: Zap, color: 'text-yellow-400', bgGradient: 'from-yellow-500/40 to-orange-500/40', probability: 25 },
  { id: 4, name: '幸运值', value: 20, icon: Sparkles, color: 'text-purple-400', bgGradient: 'from-purple-500/40 to-pink-500/40', probability: 15 },
  { id: 5, name: '幸运值', value: 10, icon: Sparkles, color: 'text-purple-400', bgGradient: 'from-purple-500/40 to-pink-500/40', probability: 20 },
  { id: 6, name: '经验值', value: 50, icon: TrendingUp, color: 'text-cyan-400', bgGradient: 'from-cyan-500/40 to-blue-500/40', probability: 10 },
]

interface StarParticle {
  id: string
  x: number
  y: number
  vx: number
  vy: number
  size: number
  rotation: number
  rotationSpeed: number
  life: number
  maxLife: number
}

export default function LuckyWheelPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { playSound } = useSound()
  const [isHolding, setIsHolding] = useState(false)
  const [holdProgress, setHoldProgress] = useState(0)
  const [isExploding, setIsExploding] = useState(false)
  const [selectedPrize, setSelectedPrize] = useState<Prize | null>(null)
  const [spinsLeft, setSpinsLeft] = useState(3)
  const [stars, setStars] = useState<StarParticle[]>([])
  const holdTimerRef = useRef<number | null>(null)
  const progressTimerRef = useRef<number | null>(null)
  const starIntervalRef = useRef<number | null>(null)
  const redPacketRef = useRef<HTMLDivElement>(null)
  const HOLD_DURATION = 2000 // 长按2秒触发

  // 抽奖逻辑
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

  // 开始长按
  const handleStart = () => {
    if (spinsLeft <= 0 || isExploding) return

    setIsHolding(true)
    setHoldProgress(0)
    playSound('click')

    // 开始生成星星
    const generateStars = () => {
      if (!redPacketRef.current || !isHolding) return

      const rect = redPacketRef.current.getBoundingClientRect()
      const centerX = rect.left + rect.width / 2
      const topY = rect.top + 20 // 红包开口位置

      // 每次生成更多星星
      const newStars: StarParticle[] = []
      for (let i = 0; i < 8; i++) {
        const angle = (Math.PI / 2) + (Math.random() - 0.5) * 0.8 // 向上喷发，稍微分散
        const speed = 2 + Math.random() * 3
        newStars.push({
          id: `star-${Date.now()}-${i}`,
          x: centerX + (Math.random() - 0.5) * 40, // 从开口处分散
          y: topY,
          vx: Math.cos(angle) * speed,
          vy: -Math.abs(Math.sin(angle) * speed), // 向上
          size: 8 + Math.random() * 12,
          rotation: Math.random() * 360,
          rotationSpeed: (Math.random() - 0.5) * 15,
          life: 0,
          maxLife: 60 + Math.random() * 40,
        })
      }
      setStars(prev => [...prev, ...newStars])
    }

    // 持续生成星星
    starIntervalRef.current = window.setInterval(generateStars, 100)

    // 进度条
    const startTime = Date.now()
    progressTimerRef.current = window.setInterval(() => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(100, (elapsed / HOLD_DURATION) * 100)
      setHoldProgress(progress)

      if (progress >= 100) {
        handleComplete()
      }
    }, 16) // 60fps
  }

  // 结束长按
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
    if (starIntervalRef.current) {
      window.clearInterval(starIntervalRef.current)
      starIntervalRef.current = null
    }
    setHoldProgress(0)
  }

  // 完成长按，触发爆炸
  const handleComplete = () => {
    if (isExploding) return

    setIsHolding(false)
    setIsExploding(true)
    playSound('success')

    // 停止生成星星
    if (starIntervalRef.current) {
      window.clearInterval(starIntervalRef.current)
      starIntervalRef.current = null
    }
    if (progressTimerRef.current) {
      window.clearInterval(progressTimerRef.current)
      progressTimerRef.current = null
    }

    // 生成大量爆炸星星
    if (redPacketRef.current) {
      const rect = redPacketRef.current.getBoundingClientRect()
      const centerX = rect.left + rect.width / 2
      const centerY = rect.top + rect.height / 2

      const explosionStars: StarParticle[] = []
      for (let i = 0; i < 100; i++) {
        const angle = (Math.PI * 2 * i) / 100 + Math.random() * 0.5
        const speed = 3 + Math.random() * 5
        explosionStars.push({
          id: `explosion-${Date.now()}-${i}`,
          x: centerX,
          y: centerY,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          size: 6 + Math.random() * 10,
          rotation: Math.random() * 360,
          rotationSpeed: (Math.random() - 0.5) * 20,
          life: 0,
          maxLife: 80 + Math.random() * 40,
        })
      }
      setStars(prev => [...prev, ...explosionStars])
    }

    // 彩纸特效
    const end = Date.now() + 2000
    const colors = ['#fbbf24', '#f472b6', '#8b5cf6', '#10b981', '#3b82f6', '#ec4899', '#a855f7', '#06b6d4']
    const frame = () => {
      for (let i = 0; i < 8; i++) {
        confetti({
          particleCount: 10,
          angle: i * 45,
          spread: 70,
          origin: { x: 0.5, y: 0.5 },
          colors: colors,
          zIndex: 1000,
          gravity: 0.8,
          drift: (Math.random() - 0.5) * 0.5,
        })
      }
      if (Date.now() < end) {
        requestAnimationFrame(frame)
      }
    }
    frame()

    // 延迟显示奖品
    setTimeout(() => {
      const prize = drawPrize()
      setSelectedPrize(prize)
      setSpinsLeft(prev => prev - 1)
      setIsExploding(false)
    }, 1500)
  }

  // 更新星星动画
  useEffect(() => {
    if (stars.length === 0) return

    const animate = () => {
      setStars(prev => {
        const updated = prev
          .map(star => ({
            ...star,
            x: star.x + star.vx,
            y: star.y + star.vy,
            rotation: star.rotation + star.rotationSpeed,
            life: star.life + 1,
            vy: star.vy + 0.15, // 重力
          }))
          .filter(star => star.life < star.maxLife && star.y < window.innerHeight + 100)

        if (updated.length > 0) {
          requestAnimationFrame(animate)
        }
        return updated
      })
    }

    requestAnimationFrame(animate)
  }, [stars.length])

  return (
    <PageTransition>
      <div className="h-full flex flex-col overflow-hidden">
        {/* 顶部标题栏 */}
        <div className="flex items-center justify-between px-4 py-3 shrink-0 border-b border-white/5">
          <button
            onClick={() => navigate(-1)}
            className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center hover:bg-white/10 transition-colors"
          >
            <ArrowLeft size={20} className="text-white" />
          </button>
          <h1 className="text-lg font-bold text-white flex items-center gap-2">
            <Trophy size={20} className="text-yellow-400" />
            幸运转盘
          </h1>
          <div className="w-10" />
        </div>

        {/* 星星粒子层 */}
        <div className="fixed inset-0 pointer-events-none z-30">
          {stars.map(star => (
            <motion.div
              key={star.id}
              className="absolute"
              style={{
                left: star.x,
                top: star.y,
                transform: `translate(-50%, -50%) rotate(${star.rotation}deg)`,
              }}
              animate={{
                scale: [1, 1.2, 0.8, 1],
              }}
              transition={{
                duration: 0.5,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            >
              <TelegramStar
                size={star.size}
                className="drop-shadow-[0_0_8px_rgba(255,215,0,0.8)]"
              />
            </motion.div>
          ))}
        </div>

        {/* 主要内容区域 */}
        <div className="flex-1 flex flex-col items-center justify-center gap-6 p-4 min-h-0">
          {/* 大红包 */}
          <div
            ref={redPacketRef}
            className="relative shrink-0"
            onMouseDown={handleStart}
            onMouseUp={handleEnd}
            onMouseLeave={handleEnd}
            onTouchStart={handleStart}
            onTouchEnd={handleEnd}
            onTouchCancel={handleEnd}
          >
            {/* 红包主体 */}
            <motion.div
              className="relative w-64 h-80 bg-gradient-to-b from-red-600 via-red-700 to-red-800 rounded-t-3xl rounded-b-2xl shadow-2xl border-4 border-red-900/50 overflow-hidden"
              animate={isHolding ? {
                x: [0, -5, 5, -5, 5, -3, 3, 0],
                y: [0, -3, 3, -3, 3, -2, 2, 0],
                rotate: [0, -2, 2, -2, 2, -1, 1, 0],
                scale: [1, 1.05, 1, 1.05, 1],
              } : isExploding ? {
                scale: [1, 1.2, 0.8, 1],
                rotate: [0, 10, -10, 0],
              } : {
                scale: 1,
                rotate: 0,
              }}
              transition={{
                duration: isHolding ? 0.3 : isExploding ? 0.5 : 0.2,
                repeat: isHolding ? Infinity : 0,
                ease: "easeInOut",
              }}
              style={{
                boxShadow: isHolding
                  ? '0 0 60px rgba(239, 68, 68, 0.8), 0 0 100px rgba(239, 68, 68, 0.6), inset 0 0 50px rgba(255, 255, 255, 0.2)'
                  : isExploding
                  ? '0 0 100px rgba(239, 68, 68, 1), 0 0 150px rgba(239, 68, 68, 0.8)'
                  : '0 0 30px rgba(239, 68, 68, 0.5)',
              }}
            >
              {/* 发光效果 */}
              {isHolding && (
                <motion.div
                  className="absolute inset-0 bg-gradient-to-b from-yellow-400/30 via-orange-400/20 to-red-600/30"
                  animate={{
                    opacity: [0.5, 1, 0.5],
                  }}
                  transition={{
                    duration: 0.5,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                />
              )}

              {/* 红包开口（顶部） */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-8 bg-gradient-to-b from-red-500 to-red-600 rounded-b-full border-2 border-red-800/50">
                {/* 开口装饰线 */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-24 h-1 bg-red-900/50 rounded-full" />
              </div>

              {/* 红包装饰 - 金色边框 */}
              <div className="absolute inset-0 border-4 border-yellow-400/30 rounded-t-3xl rounded-b-2xl pointer-events-none" />

              {/* 红包装饰 - 福字区域 */}
              <div className="absolute top-24 left-1/2 -translate-x-1/2 w-32 h-32 flex items-center justify-center">
                <motion.div
                  className="text-6xl font-black text-yellow-300 drop-shadow-[0_0_10px_rgba(251,191,36,0.8)]"
                  animate={isHolding ? {
                    scale: [1, 1.1, 1],
                  } : {}}
                  transition={{
                    duration: 0.3,
                    repeat: isHolding ? Infinity : 0,
                    ease: "easeInOut",
                  }}
                >
                  福
                </motion.div>
              </div>

              {/* 进度条 */}
              {isHolding && (
                <div className="absolute bottom-4 left-4 right-4 h-2 bg-white/20 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-yellow-400 via-orange-400 to-red-500 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${holdProgress}%` }}
                    transition={{ duration: 0.1 }}
                  />
                </div>
              )}

              {/* 爆炸光效 */}
              {isExploding && (
                <motion.div
                  className="absolute inset-0 rounded-full"
                  style={{
                    background: 'radial-gradient(circle, rgba(251, 191, 36, 0.8) 0%, rgba(249, 115, 22, 0.6) 30%, transparent 70%)',
                  }}
                  initial={{ scale: 0, opacity: 1 }}
                  animate={{ scale: 3, opacity: 0 }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                />
              )}
            </motion.div>

            {/* 提示文字 */}
            {!isHolding && !isExploding && (
              <motion.div
                className="absolute -bottom-12 left-1/2 -translate-x-1/2 text-center"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <p className="text-sm text-gray-300 font-medium">
                  {spinsLeft <= 0 ? '今日次数已用完' : '长按红包开启'}
                </p>
              </motion.div>
            )}
          </div>

          {/* 剩余次数 */}
          <div className="w-full max-w-sm shrink-0">
            <div className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles size={18} className="text-purple-400" />
                <span className="text-sm text-gray-300">今日剩余次数</span>
              </div>
              <span className="text-2xl font-bold text-purple-400">{spinsLeft}</span>
            </div>
          </div>
        </div>

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
                className="relative bg-[#1C1C1E] border border-purple-500/30 rounded-3xl p-8 text-center shadow-2xl max-w-sm w-full"
              >
                <motion.div
                  animate={{ rotate: [0, 360] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  className={`w-20 h-20 mx-auto mb-4 bg-gradient-to-br ${selectedPrize.bgGradient} rounded-full flex items-center justify-center border-4 border-white/20`}
                >
                  <selectedPrize.icon size={40} className={selectedPrize.color} />
                </motion.div>
                <h2 className="text-2xl font-bold text-white mb-2">恭喜获得！</h2>
                <p className={`text-4xl font-black ${selectedPrize.color} mb-1`}>
                  +{selectedPrize.value}
                </p>
                <p className={`text-lg font-bold ${selectedPrize.color} mb-6`}>
                  {selectedPrize.name}
                </p>
                <motion.button
                  onClick={() => setSelectedPrize(null)}
                  className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-bold"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  太棒了！
                </motion.button>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </PageTransition>
  )
}
