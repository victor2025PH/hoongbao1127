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
  { id: 1, name: '能量', value: 100, icon: Zap, color: 'text-yellow-400', bgGradient: 'from-yellow-500/40 to-orange-500/40', probability: 10 },
  { id: 2, name: '能量', value: 50, icon: Zap, color: 'text-yellow-400', bgGradient: 'from-yellow-500/40 to-orange-500/40', probability: 20 },
  { id: 3, name: '能量', value: 30, icon: Zap, color: 'text-yellow-400', bgGradient: 'from-yellow-500/40 to-orange-500/40', probability: 25 },
  { id: 4, name: '幸运值', value: 20, icon: Sparkles, color: 'text-purple-400', bgGradient: 'from-purple-500/40 to-pink-500/40', probability: 15 },
  { id: 5, name: '幸运值', value: 10, icon: Sparkles, color: 'text-purple-400', bgGradient: 'from-purple-500/40 to-pink-500/40', probability: 20 },
  { id: 6, name: '经验值', value: 50, icon: TrendingUp, color: 'text-cyan-400', bgGradient: 'from-cyan-500/40 to-blue-500/40', probability: 10 },
]

interface CoinSymbol {
  id: string
  x: number
  y: number
  icon: React.ElementType
  size: number
  rotation: number
  isFlying: boolean
  vx: number
  vy: number
  life: number
  maxLife: number
}

interface LightRay {
  id: string
  angle: number
  distance: number
  opacity: number
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
  const [coins, setCoins] = useState<CoinSymbol[]>([])
  const [showNoChancesModal, setShowNoChancesModal] = useState(false)
  const holdTimerRef = useRef<number | null>(null)
  const progressTimerRef = useRef<number | null>(null)
  const coinIntervalRef = useRef<number | null>(null)
  const redPacketRef = useRef<HTMLDivElement>(null)
  const HOLD_DURATION = 2000 // 长按2秒触发

  // 虚拟币图标类型
  const coinIcons = [Coins, DollarSign, Star, Sparkles, Circle, Trophy]

  // 初始化红包上的虚拟币符号 - 底部密集，向上稀疏
  useEffect(() => {
    if (!redPacketRef.current) return

    const initialCoins: CoinSymbol[] = []
    // 使用百分比定位，相对于红包容器
    const packetWidth = 100 // 使用百分比
    const packetHeight = 100 // 使用百分比

    // 底部密集，向上稀疏的分布
    // 底部区域（0-40%）：密集分布
    for (let i = 0; i < 40; i++) {
      const yPercent = Math.random() * 0.4 // 0-40%
      const xPercent = Math.random() * 100 // 0-100%
      initialCoins.push({
        id: `coin-bottom-${i}`,
        x: xPercent, // 使用百分比
        y: 100 - yPercent * 100, // 从底部开始，使用百分比
        icon: coinIcons[Math.floor(Math.random() * coinIcons.length)],
        size: 10 + Math.random() * 8,
        rotation: Math.random() * 360,
        isFlying: false,
        vx: 0,
        vy: 0,
        life: 0,
        maxLife: 100,
      })
    }

    // 中部区域（40-70%）：中等密度
    for (let i = 0; i < 20; i++) {
      const yPercent = 0.4 + Math.random() * 0.3 // 40-70%
      const xPercent = Math.random() * 100
      initialCoins.push({
        id: `coin-middle-${i}`,
        x: xPercent,
        y: 100 - yPercent * 100,
        icon: coinIcons[Math.floor(Math.random() * coinIcons.length)],
        size: 8 + Math.random() * 6,
        rotation: Math.random() * 360,
        isFlying: false,
        vx: 0,
        vy: 0,
        life: 0,
        maxLife: 100,
      })
    }

    // 上部区域（70-100%）：稀疏分布
    for (let i = 0; i < 10; i++) {
      const yPercent = 0.7 + Math.random() * 0.3 // 70-100%
      const xPercent = Math.random() * 100
      initialCoins.push({
        id: `coin-top-${i}`,
        x: xPercent,
        y: 100 - yPercent * 100,
        icon: coinIcons[Math.floor(Math.random() * coinIcons.length)],
        size: 6 + Math.random() * 6,
        rotation: Math.random() * 360,
        isFlying: false,
        vx: 0,
        vy: 0,
        life: 0,
        maxLife: 100,
      })
    }

    setCoins(initialCoins)
  }, [])

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
    if (spinsLeft <= 0) {
      setShowNoChancesModal(true)
      return
    }
    if (isExploding) return

    setIsHolding(true)
    setHoldProgress(0)
    playSound('click')

    // 让虚拟币符号开始飞升
    setCoins(prev => prev.map(coin => ({
      ...coin,
      isFlying: true,
      vx: (Math.random() - 0.5) * 2,
      vy: -3 - Math.random() * 3, // 向上飞
      life: 0,
    })))

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
    if (coinIntervalRef.current) {
      window.clearInterval(coinIntervalRef.current)
      coinIntervalRef.current = null
    }
    setHoldProgress(0)
  }

  // 完成长按，触发爆炸
  const handleComplete = () => {
    if (isExploding) return

    setIsHolding(false)
    setIsExploding(true)
    playSound('success')

    // 停止所有定时器
    if (progressTimerRef.current) {
      window.clearInterval(progressTimerRef.current)
      progressTimerRef.current = null
    }

    // 生成大量爆炸虚拟币
    if (redPacketRef.current) {
      const rect = redPacketRef.current.getBoundingClientRect()
      const centerX = rect.left + rect.width / 2
      const centerY = rect.top + rect.height / 2

      const explosionCoins: CoinSymbol[] = []
      for (let i = 0; i < 50; i++) {
        const angle = (Math.PI * 2 * i) / 50 + Math.random() * 0.5
        const speed = 4 + Math.random() * 4
        explosionCoins.push({
          id: `explosion-${Date.now()}-${i}`,
          x: centerX,
          y: centerY,
          icon: coinIcons[Math.floor(Math.random() * coinIcons.length)],
          size: 10 + Math.random() * 12,
          rotation: Math.random() * 360,
          isFlying: true,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          life: 0,
          maxLife: 80 + Math.random() * 40,
        })
      }
      setCoins(prev => [...prev, ...explosionCoins])
    }

    // 彩纸特效
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

    // 延迟显示奖品
    setTimeout(() => {
      const prize = drawPrize()
      setSelectedPrize(prize)
      setSpinsLeft(prev => prev - 1)
      setIsExploding(false)
    }, 1500)
  }

  // 更新虚拟币动画
  useEffect(() => {
    if (coins.length === 0) return

    const animate = () => {
      setCoins(prev => {
        const updated = prev
          .map(coin => {
            if (!coin.isFlying) return coin

            return {
              ...coin,
              x: coin.x + coin.vx,
              y: coin.y + coin.vy,
              rotation: coin.rotation + 5,
              life: coin.life + 1,
              vy: coin.vy + 0.1, // 重力
            }
          })
          .filter(coin => {
            if (!coin.isFlying) return true
            return coin.life < coin.maxLife && coin.y > -100 && coin.y < window.innerHeight + 100
          })

        if (updated.some(c => c.isFlying)) {
          requestAnimationFrame(animate)
        }
        return updated
      })
    }

    requestAnimationFrame(animate)
  }, [coins.length])

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
            抢红包
          </h1>
          <div className="w-10" />
        </div>

        {/* 飞行的虚拟币符号层 - 使用固定定位 */}
        <div className="fixed inset-0 pointer-events-none z-30">
          {coins.filter(coin => coin.isFlying).map(coin => {
            const Icon = coin.icon
            return (
              <motion.div
                key={coin.id}
                className="absolute"
                style={{
                  left: coin.x,
                  top: coin.y,
                  transform: `translate(-50%, -50%) rotate(${coin.rotation}deg)`,
                }}
                animate={{
                  scale: [1, 1.2, 0.8],
                }}
                transition={{
                  duration: 0.5,
                  ease: "easeInOut",
                }}
              >
                <Icon
                  size={coin.size}
                  className="text-yellow-400"
                  style={{
                    filter: 'drop-shadow(0 0 6px #fbbf24)',
                  }}
                />
              </motion.div>
            )
          })}
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
            {/* 虚拟币符号层 - 相对于红包容器 */}
            <div className="absolute inset-0 pointer-events-none z-10 overflow-hidden">
              {coins.filter(coin => !coin.isFlying).map(coin => {
                const Icon = coin.icon
                return (
                  <motion.div
                    key={coin.id}
                    className="absolute"
                    style={{
                      left: `${coin.x}%`,
                      top: `${coin.y}%`,
                      transform: `translate(-50%, -50%) rotate(${coin.rotation}deg)`,
                    }}
                    animate={isHolding ? {
                      scale: [1, 1.3, 1],
                      opacity: [0.8, 1, 0.8],
                    } : {}}
                    transition={{
                      duration: 0.5,
                      repeat: isHolding ? Infinity : 0,
                      ease: "easeInOut",
                    }}
                  >
                    <Icon
                      size={coin.size}
                      className="text-yellow-400"
                      style={{
                        filter: isHolding
                          ? 'drop-shadow(0 0 8px #fbbf24) drop-shadow(0 0 16px #fbbf24)'
                          : 'drop-shadow(0 0 4px rgba(251, 191, 36, 0.5))',
                      }}
                    />
                  </motion.div>
                )
              })}
            </div>
            {/* 顶部标签 */}
            <div className="absolute -top-6 left-1/2 -translate-x-1/2 w-20 h-6 bg-gradient-to-b from-amber-100 to-amber-200 rounded-t-lg border-2 border-amber-300/50 shadow-md z-10">
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs font-bold text-red-600">抢红包</span>
              </div>
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
              </div>
            </motion.div>
            
          {/* 星星按钮 - 固定在横带中心，不受红包动画影响，相对于父容器定位 */}
          <div 
            className="absolute w-28 h-28 z-30 pointer-events-none"
            style={{
              bottom: 'calc(50% - 48px)', // 横带位置（bottom-32 = 128px，从底部算起，横带中心在 128px + 24px = 152px，按钮中心应该在 152px）
              left: '50%',
              transform: 'translateX(-50%)',
            }}
          >
              <motion.div
                className="w-full h-full flex items-center justify-center"
                animate={isHolding ? {
                  scale: [1, 1.15, 1],
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
                <div className="relative w-full h-full">
                  {/* 四叶草形状背景 */}
                  <div
                    className="absolute inset-0 bg-gradient-to-br from-amber-400 via-amber-500 to-amber-600 rounded-full"
                    style={{
                      clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
                      boxShadow: '0 0 20px rgba(245, 158, 11, 0.6), inset 0 0 20px rgba(255, 255, 255, 0.3)',
                    }}
                  />
                  {/* 星星图标 */}
                  <div className="absolute inset-0 flex items-center justify-center z-10">
                    <TelegramStar size={48} withSpray={isHolding} className="drop-shadow-[0_0_12px_rgba(255,215,0,0.8)]" />
                  </div>
                  {/* 按钮高光 */}
                  <div
                    className="absolute top-0 left-1/2 -translate-x-1/2 w-1/2 h-1/2 bg-gradient-to-b from-white/40 to-transparent rounded-full"
                    style={{
                      clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 50%, 0% 75%, 0% 25%)',
                    }}
                  />
                </div>
              </motion.div>

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
            </motion.div>

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
                <h2 className="text-2xl font-bold text-white mb-4">今日次数已用完</h2>
                <p className="text-gray-400 mb-6">明日再来</p>
                <motion.button
                  onClick={() => setShowNoChancesModal(false)}
                  className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-bold"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  知道了
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
