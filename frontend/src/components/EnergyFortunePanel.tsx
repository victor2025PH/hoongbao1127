import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Zap, Sparkles, TrendingUp } from 'lucide-react'
import { useTranslation } from '../providers/I18nProvider'
import { useSound } from '../hooks/useSound'

interface EnergyFortunePanelProps {
  energy?: number
  maxEnergy?: number
  onEnergyUpdate?: (energy: number) => void
}

// 计算每日幸运值（基于用户ID和日期）
function calculateDailyFortune(userId?: number): { value: number; label: string; color: string } {
  const today = new Date()
  const seed = (userId || 0) + today.getDate() + today.getMonth() * 31 + today.getFullYear() * 365
  const fortune = (seed * 9301 + 49297) % 100 // 伪随机数生成，范围 0-99
  
  if (fortune >= 90) {
    return { value: fortune, label: '大吉', color: 'text-yellow-400' }
  } else if (fortune >= 70) {
    return { value: fortune, label: '中吉', color: 'text-green-400' }
  } else if (fortune >= 50) {
    return { value: fortune, label: '小吉', color: 'text-cyan-400' }
  } else if (fortune >= 30) {
    return { value: fortune, label: '平', color: 'text-gray-400' }
  } else {
    return { value: fortune, label: '小凶', color: 'text-orange-400' }
  }
}

// 计算能量恢复时间
function calculateEnergyRecoveryTime(currentEnergy: number, maxEnergy: number): number {
  const missing = maxEnergy - currentEnergy
  return missing * 5 * 60 * 1000 // 每5分钟恢复1点能量（毫秒）
}

export default function EnergyFortunePanel({ 
  energy = 50, 
  maxEnergy = 100,
  onEnergyUpdate 
}: EnergyFortunePanelProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { playSound } = useSound()
  const [currentEnergy, setCurrentEnergy] = useState(energy)
  const [recoveryTime, setRecoveryTime] = useState(0)
  const [fortune] = useState(() => calculateDailyFortune())

  // 同步外部能量值
  useEffect(() => {
    setCurrentEnergy(energy)
  }, [energy])

  const handleClick = () => {
    playSound('click')
    navigate('/lucky-wheel')
  }

  // 能量恢复逻辑
  useEffect(() => {
    if (currentEnergy >= maxEnergy) {
      setRecoveryTime(0)
      return
    }

    const recoveryInterval = calculateEnergyRecoveryTime(currentEnergy, maxEnergy)
    const startTime = Date.now()
    
    const timer = setInterval(() => {
      const elapsed = Date.now() - startTime
      const remaining = Math.max(0, recoveryInterval - elapsed)
      
      if (remaining === 0) {
        // 恢复1点能量
        const newEnergy = Math.min(maxEnergy, currentEnergy + 1)
        setCurrentEnergy(newEnergy)
        onEnergyUpdate?.(newEnergy)
      } else {
        setRecoveryTime(remaining)
      }
    }, 1000)

    return () => clearInterval(timer)
  }, [currentEnergy, maxEnergy, onEnergyUpdate])

  // 格式化倒计时
  const formatCountdown = (ms: number): string => {
    if (ms === 0) return '已满'
    const minutes = Math.floor(ms / 60000)
    const seconds = Math.floor((ms % 60000) / 1000)
    return `${minutes}:${String(seconds).padStart(2, '0')}`
  }

  const energyPercent = (currentEnergy / maxEnergy) * 100

  return (
    <div 
      onClick={handleClick}
      className="relative flex-1 bg-gradient-to-br from-purple-900/20 via-[#1C1C1E] to-cyan-900/20 border border-purple-500/20 rounded-2xl overflow-hidden flex flex-col items-center justify-center shadow-lg group active:scale-[0.98] transition-all h-20 cursor-pointer hover:border-purple-500/40"
    >
      {/* 背景光晕 */}
      <div className="absolute top-0 inset-x-0 h-8 bg-gradient-to-b from-purple-500/10 via-cyan-500/10 to-transparent opacity-60" />
      
      {/* 能量粒子效果 */}
      {currentEnergy >= maxEnergy && (
        <div className="absolute inset-0 pointer-events-none">
          {Array.from({ length: 5 }).map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-yellow-400 rounded-full"
              style={{
                left: `${20 + i * 15}%`,
                top: '50%',
              }}
              animate={{
                y: [0, -20, 0],
                opacity: [0.5, 1, 0.5],
                scale: [1, 1.5, 1],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                delay: i * 0.3,
              }}
            />
          ))}
        </div>
      )}
      
      <div className="z-10 flex flex-col items-center gap-1 w-full px-2">
        {/* 能量条 */}
        <div className="flex items-center gap-1.5 w-full mb-0.5">
          <motion.div
            animate={currentEnergy >= maxEnergy ? {
              scale: [1, 1.2, 1],
              rotate: [0, 180, 360],
            } : {}}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Zap size={12} className="text-yellow-400" fill={currentEnergy >= maxEnergy ? 'currentColor' : 'none'} />
          </motion.div>
          <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden relative">
            <motion.div
              className="h-full bg-gradient-to-r from-yellow-400 via-yellow-500 to-orange-500 rounded-full relative"
              initial={{ width: 0 }}
              animate={{ width: `${energyPercent}%` }}
              transition={{ duration: 0.5 }}
            >
              {/* 能量流动效果 */}
              {currentEnergy < maxEnergy && (
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                  animate={{
                    x: ['-100%', '100%'],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: 'linear',
                  }}
                />
              )}
            </motion.div>
          </div>
          <span className="text-[10px] font-bold text-yellow-300 min-w-[35px] text-right">
            {currentEnergy}/{maxEnergy}
          </span>
        </div>

        {/* 运势显示 */}
        <div className="flex items-center gap-1.5 w-full justify-center">
          <motion.div
            animate={{
              rotate: [0, 360],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: 'linear',
            }}
          >
            <Sparkles size={10} className={fortune.color} />
          </motion.div>
          <span className={`text-xs font-bold ${fortune.color}`}>
            {fortune.label}
          </span>
          <span className="text-[10px] text-gray-400 font-mono">
            {fortune.value}
          </span>
        </div>

        {/* 恢复倒计时 */}
        {recoveryTime > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-[9px] text-purple-300/80 font-mono flex items-center gap-1"
          >
            <TrendingUp size={8} />
            {formatCountdown(recoveryTime)}
          </motion.div>
        )}
      </div>

      {/* 底部进度条 */}
      <div className="absolute bottom-0 left-0 w-full h-0.5 bg-purple-500/20">
        <motion.div
          className="h-full bg-gradient-to-r from-purple-500 to-cyan-500 shadow-[0_0_10px_purple]"
          initial={{ width: '0%' }}
          animate={{ width: `${energyPercent}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
    </div>
  )
}

