import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Gift, Zap, Sparkles, Trophy, TrendingUp, ArrowLeft, Star, Coins, DollarSign, Circle } from 'lucide-react'
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
  { id: 1, name: 'Energy', value: 100, icon: Zap, color: 'text-yellow-400', bgGradient: 'from-yellow-500/40 to-orange-500/40', probability: 10 },
  { id: 2, name: 'Energy', value: 50, icon: Zap, color: 'text-yellow-400', bgGradient: 'from-yellow-500/40 to-orange-500/40', probability: 20 },
  { id: 3, name: 'Energy', value: 30, icon: Zap, color: 'text-yellow-400', bgGradient: 'from-yellow-500/40 to-orange-500/40', probability: 25 },
  { id: 4, name: 'Fortune', value: 20, icon: Sparkles, color: 'text-purple-400', bgGradient: 'from-purple-500/40 to-pink-500/40', probability: 15 },
  { id: 5, name: 'Fortune', value: 10, icon: Sparkles, color: 'text-purple-400', bgGradient: 'from-purple-500/40 to-pink-500/40', probability: 20 },
  { id: 6, name: 'XP', value: 50, icon: TrendingUp, color: 'text-cyan-400', bgGradient: 'from-cyan-500/40 to-blue-500/40', probability: 10 },
]

interface FloatingSymbol {
  id: string
  x: number
  y: number
  icon: React.ElementType
  size: number
  rotation: number
  speed: number
  opacity: number
  rotationSpeed: number
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
  const [symbols, setSymbols] = useState<FloatingSymbol[]>([])
  const [showNoChancesModal, setShowNoChancesModal] = useState(false)
  const holdTimerRef = useRef<number | null>(null)
  const progressTimerRef = useRef<number | null>(null)
  const redPacketRef = useRef<HTMLDivElement>(null)
  const animationRef = useRef<number | null>(null)
  const lastTimeRef = useRef<number>(0)
  const isHoldingRef = useRef(false)
  const HOLD_DURATION = 2000

  const symbolIcons = [Coins, DollarSign, Star, Sparkles, Circle, Trophy]

  // 创建新符号
  const createSymbol = (yPosition?: number): FloatingSymbol => {
    return {
      id: `symbol-${Date.now()}-${Math.random()}`,
      x: 5 + Math.random() * 90, // 5-95% 避免边缘
      y: yPosition ?? (85 + Math.random() * 15), // 从底部生成
      icon: symbolIcons[Math.floor(Math.random() * symbolIcons.length)],
      size: 10 + Math.random() * 10,
      rotation: Math.random() * 360,
      speed: 0.15 + Math.random() * 0.1, // 基础上升速度
      opacity: 0.7 + Math.random() * 0.3,
      rotationSpeed: (Math.random() - 0.5) * 2,
    }
  }

  // 初始化符号
  useEffect(() => {
    const initialSymbols: FloatingSymbol[] = []
    for (let i = 0; i < 50; i++) {
      initialSymbols.push(createSymbol(Math.random() * 100))
    }
    setSymbols(initialSymbols)
  }, [])

  // 同步 isHolding 到 ref
  useEffect(() => {
    isHoldingRef.current = isHolding
  }, [isHolding])

  // 持续动画循环
  useEffect(() => {
    let spawnTimer = 0
    
    const animate = (timestamp: number) => {
      if (!lastTimeRef.current) lastTimeRef.current = timestamp
      const deltaTime = Math.min(timestamp - lastTimeRef.current, 50) // 限制最大间隔
      lastTimeRef.current = timestamp
      
      const holding = isHoldingRef.current
      const speedMultiplier = holding ? 3 : 1 // 长按时速度x3
      spawnTimer += deltaTime
      
      // 生成新符号的间隔
      const spawnInterval = holding ? 80 : 200 // 长按时生成更频繁
      
      setSymbols(prev => {
        let updated = prev.map(symbol => {
          // 上升
          const newY = symbol.y - symbol.speed * speedMultiplier * (deltaTime / 16)
          // 根据位置计算透明度 - 越往上越透明
          const fadeStart = 30 // 从30%位置开始淡出
          let newOpacity = symbol.opacity
          if (newY < fadeStart) {
            newOpacity = Math.max(0, (newY / fadeStart) * symbol.opacity)
          }
          
          return {
            ...symbol,
            y: newY,
            opacity: newOpacity,
            rotation: symbol.rotation + symbol.rotationSpeed * speedMultiplier,
          }
        }).filter(symbol => symbol.y > -5 && symbol.opacity > 0.01) // 移除顶部消失的符号
        
        // 生成新符号
        if (spawnTimer >= spawnInterval) {
          spawnTimer = 0
          const newCount = holding ? 3 : 1 // 长按时一次生成更多
          for (let i = 0; i < newCount; i++) {
            updated.push(createSymbol())
          }
        }
        
        return updated
      })
      
      animationRef.current = requestAnimationFrame(animate)
    }
    
    animationRef.current = requestAnimationFrame(animate)
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [])

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

    const end = Date.now() + 2000
    const colors = ['#fbbf24', '#f472b6', '#8b5cf6', '#10b981', '#3b82f6', '#ec4899', '#a855f7', '#06b6d4']
    const frame = () => {
      for (let i = 0; i < 8; i++) {
        confetti({
          particleCount: 15,
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

    setTimeout(() => {
      const prize = drawPrize()
      setSelectedPrize(prize)
      setSpinsLeft(prev => prev - 1)
      setIsExploding(false)
    }, 1500)
  }

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
            {t('lucky_red')}
          </h1>
          <div className="w-10" />
        </div>


        {/* 主要内容区域 */}
        <div className="flex-1 flex flex-col items-center justify-start gap-4 p-4 min-h-0 pt-8 relative">
          {/* 大红包 */}
          <div
            ref={redPacketRef}
            className="relative shrink-0 w-72 h-96"
            onMouseDown={handleStart}
            onMouseUp={handleEnd}
            onMouseLeave={handleEnd}
            onTouchStart={handleStart}
            onTouchEnd={handleEnd}
            onTouchCancel={handleEnd}
          >
            {/* 浮动符号层 - 持续上升动画 */}
            <div className="absolute inset-0 pointer-events-none z-10 overflow-hidden rounded-3xl">
              {symbols.map(symbol => {
                const Icon = symbol.icon
                return (
                  <div
                    key={symbol.id}
                    className="absolute text-yellow-400"
                    style={{
                      left: `${symbol.x}%`,
                      top: `${symbol.y}%`,
                      transform: `translate(-50%, -50%) rotate(${symbol.rotation}deg)`,
                      opacity: symbol.opacity,
                      filter: isHolding
                        ? 'drop-shadow(0 0 6px #fbbf24) drop-shadow(0 0 12px #fbbf24)'
                        : 'drop-shadow(0 0 3px rgba(251, 191, 36, 0.4))',
                      transition: 'filter 0.3s ease',
                    }}
                  >
                    <Icon size={symbol.size} />
                  </div>
                )
              })}
            </div>

            {/* 红包主体 */}
            <motion.div
              className="relative w-72 h-96 rounded-3xl shadow-2xl overflow-visible"
              style={{
                background: 'linear-gradient(180deg, #dc2626 0%, #b91c1c 50%, #991b1b 100%)',
                boxShadow: isHolding
                  ? '0 0 80px rgba(220, 38, 38, 0.9), 0 0 120px rgba(220, 38, 38, 0.7), inset 0 0 60px rgba(255, 255, 255, 0.2)'
                  : isExploding
                  ? '0 0 120px rgba(220, 38, 38, 1), 0 0 180px rgba(220, 38, 38, 0.8)'
                  : '0 0 40px rgba(220, 38, 38, 0.6), inset 0 0 30px rgba(255, 255, 255, 0.1)',
              }}
              animate={isHolding ? {
                x: [0, -4, 4, -4, 4, -2, 2, 0],
                y: [0, -2, 2, -2, 2, -1, 1, 0],
                rotate: [0, -1, 1, -1, 1, -0.5, 0.5, 0],
                scale: [1, 1.03, 1, 1.03, 1],
              } : isExploding ? {
                scale: [1, 1.3, 0.9, 1],
                rotate: [0, 8, -8, 0],
              } : {
                scale: 1,
                rotate: 0,
                x: 0,
                y: 0,
              }}
              transition={{
                duration: isHolding ? 0.25 : isExploding ? 0.5 : 0.2,
                repeat: isHolding ? Infinity : 0,
                ease: "easeInOut",
              }}
            >
              <div className="absolute inset-0 overflow-hidden rounded-3xl">
                {/* 光泽效果 */}
                <div
                  className="absolute inset-0"
                  style={{
                    background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.25) 0%, transparent 40%, rgba(0, 0, 0, 0.15) 100%)',
                    mixBlendMode: 'overlay',
                  }}
                />

                {/* 高光反射 */}
                <motion.div
                  className="absolute top-0 left-0 w-full h-1/3"
                  style={{
                    background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.35) 0%, transparent 100%)',
                  }}
                  animate={isHolding ? {
                    opacity: [0.35, 0.6, 0.35],
                  } : {}}
                  transition={{
                    duration: 0.5,
                    repeat: isHolding ? Infinity : 0,
                    ease: "easeInOut",
                  }}
                />

                {/* 红包纹理 */}
                <div
                  className="absolute inset-0 opacity-10"
                  style={{
                    backgroundImage: `
                      repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(0,0,0,0.05) 10px, rgba(0,0,0,0.05) 20px),
                      repeating-linear-gradient(-45deg, transparent, transparent 10px, rgba(0,0,0,0.05) 10px, rgba(0,0,0,0.05) 20px)
                    `,
                  }}
                />

                {/* 金色横带 */}
                <div className="absolute bottom-32 left-0 right-0 h-12 bg-gradient-to-b from-amber-300 via-amber-400 to-amber-500 border-y-2 border-amber-600/30 shadow-inner">
                  <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/20 to-transparent" />
                </div>

                {/* 进度条 */}
                {isHolding && (
                  <div className="absolute bottom-8 left-8 right-8 h-2 bg-white/20 rounded-full overflow-hidden z-30">
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
                      background: 'radial-gradient(circle, rgba(255, 215, 0, 0.9) 0%, rgba(220, 38, 38, 0.7) 30%, transparent 70%)',
                    }}
                    initial={{ scale: 0, opacity: 1 }}
                    animate={{ scale: 3, opacity: 0 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                  />
                )}
              </div>
            </motion.div>
            
          {/* 盾牌形状底座 + 大星星 - 完美融合 */}
          <div 
            className="absolute w-24 h-24 z-30 pointer-events-none"
            style={{
              top: '12%',
              left: '50%',
              transform: 'translateX(-50%)',
            }}
          >
              <motion.div
                className="w-full h-full flex items-center justify-center"
                animate={isHolding ? {
                  scale: [1, 1.12, 1],
                } : {
                  scale: 1,
                }}
                transition={{
                  duration: 0.5,
                  repeat: isHolding ? Infinity : 0,
                  ease: "easeInOut",
                }}
                style={{
                  transformOrigin: 'center center',
                }}
              >
                <div className="relative w-full h-full flex items-center justify-center">
                  {/* 盾牌 3D 立体底座 */}
                  
                  {/* 最底层投影 */}
                  <div
                    className="absolute"
                    style={{
                      width: '100%',
                      height: '100%',
                      top: '8%',
                      clipPath: 'polygon(50% 0%, 100% 20%, 100% 65%, 50% 100%, 0% 65%, 0% 20%)',
                      background: 'rgba(0, 0, 0, 0.4)',
                      filter: 'blur(6px)',
                    }}
                  />
                  
                  {/* 盾牌外框 - 深色边缘 */}
                  <div
                    className="absolute"
                    style={{
                      width: '100%',
                      height: '100%',
                      clipPath: 'polygon(50% 0%, 100% 20%, 100% 65%, 50% 100%, 0% 65%, 0% 20%)',
                      background: 'linear-gradient(180deg, #78350f 0%, #451a03 100%)',
                    }}
                  />
                  
                  {/* 盾牌主体 - 金色渐变 */}
                  <div
                    className="absolute"
                    style={{
                      width: '92%',
                      height: '92%',
                      top: '4%',
                      left: '4%',
                      clipPath: 'polygon(50% 0%, 100% 20%, 100% 65%, 50% 100%, 0% 65%, 0% 20%)',
                      background: 'linear-gradient(165deg, #fde68a 0%, #fbbf24 25%, #f59e0b 50%, #d97706 75%, #b45309 100%)',
                      filter: isHolding 
                        ? 'drop-shadow(0 0 12px #fbbf24) drop-shadow(0 0 24px #f59e0b)'
                        : 'drop-shadow(0 0 6px rgba(251, 191, 36, 0.5))',
                    }}
                  />
                  
                  {/* 盾牌凹陷区域 - 星星的背景 */}
                  <div
                    className="absolute"
                    style={{
                      width: '72%',
                      height: '72%',
                      top: '14%',
                      left: '14%',
                      clipPath: 'polygon(50% 2%, 98% 20%, 98% 62%, 50% 98%, 2% 62%, 2% 20%)',
                      background: 'linear-gradient(180deg, #d97706 0%, #b45309 40%, #92400e 100%)',
                    }}
                  />
                  
                  {/* 顶部高光 */}
                  <div
                    className="absolute"
                    style={{
                      width: '45%',
                      height: '18%',
                      top: '6%',
                      left: '20%',
                      background: 'linear-gradient(180deg, rgba(255,255,255,0.5) 0%, transparent 100%)',
                      borderRadius: '50%',
                      filter: 'blur(1px)',
                    }}
                  />

                  {/* 星星 - 和右上角完全一样，完美嵌入盾牌内部 */}
                  <div 
                    className="absolute flex items-center justify-center z-10"
                    style={{
                      width: '55%',
                      height: '55%',
                      top: '22%',
                      left: '22.5%',
                    }}
                  >
                    <motion.div
                      animate={isHolding ? {
                        rotate: [0, 5, -5, 0],
                        scale: [1, 1.1, 1],
                      } : {
                        scale: [1, 1.02, 1],
                      }}
                      transition={{
                        duration: isHolding ? 0.25 : 2.5,
                        repeat: Infinity,
                        ease: "easeInOut",
                      }}
                      style={{
                        filter: isHolding 
                          ? 'drop-shadow(0 0 10px #ffd700) drop-shadow(0 0 20px #fbbf24)'
                          : 'drop-shadow(0 0 4px rgba(255, 215, 0, 0.6))',
                      }}
                    >
                      <TelegramStar 
                        size={40} 
                        withSpray={isHolding}
                      />
                    </motion.div>
                  </div>
                  
                  {/* 按下时的内部发光 */}
                  {isHolding && (
                    <motion.div
                      className="absolute"
                      style={{
                        width: '72%',
                        height: '72%',
                        top: '14%',
                        left: '14%',
                        clipPath: 'polygon(50% 2%, 98% 20%, 98% 62%, 50% 98%, 2% 62%, 2% 20%)',
                        background: 'radial-gradient(circle, rgba(255,215,0,0.4) 0%, transparent 70%)',
                      }}
                      animate={{
                        opacity: [0.3, 0.7, 0.3],
                      }}
                      transition={{
                        duration: 0.35,
                        repeat: Infinity,
                      }}
                    />
                  )}
                </div>
              </motion.div>
          </div>
          </div>

          {/* 剩余次数 */}
          <div className="w-full max-w-sm shrink-0">
            <div className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles size={18} className="text-purple-400" />
                <span className="text-sm text-gray-300">{t('remaining_today')}</span>
              </div>
              <span className="text-2xl font-bold text-purple-400">{spinsLeft}</span>
            </div>
          </div>
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
                className="relative bg-[#1C1C1E] border border-purple-500/30 rounded-3xl p-8 text-center shadow-2xl max-w-sm w-full"
              >
                <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-purple-500/40 to-pink-500/40 rounded-full flex items-center justify-center border-4 border-white/20">
                  <Sparkles size={32} className="text-purple-400" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-4">{t('no_chances_left')}</h2>
                <p className="text-gray-400 mb-6">{t('come_tomorrow')}</p>
                <motion.button
                  onClick={() => setShowNoChancesModal(false)}
                  className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-bold"
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
                className="relative bg-[#1C1C1E] border border-purple-500/30 rounded-3xl p-8 text-center shadow-2xl max-w-sm w-full"
              >
                <motion.div
                  animate={{ rotate: [0, 360] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  className={`w-20 h-20 mx-auto mb-4 bg-gradient-to-br ${selectedPrize.bgGradient} rounded-full flex items-center justify-center border-4 border-white/20`}
                >
                  <selectedPrize.icon size={40} className={selectedPrize.color} />
                </motion.div>
                <h2 className="text-2xl font-bold text-white mb-2">{t('congrats')}</h2>
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
