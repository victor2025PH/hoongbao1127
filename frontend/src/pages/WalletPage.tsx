import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { CreditCard, ArrowUpRight, Gift, FileText, Users, ChevronRight, Send, Gamepad2, ArrowLeftRight, Target, Wifi, Wallet } from 'lucide-react'
import { motion, AnimatePresence, useAnimation } from 'framer-motion'
import { useTranslation } from '../providers/I18nProvider'
import { getBalance, getUserProfile } from '../utils/api'
import { useSound } from '../hooks/useSound'
import TelegramStar from '../components/TelegramStar'
import PageTransition from '../components/PageTransition'
import EnergyFortunePanel from '../components/EnergyFortunePanel'

export default function WalletPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { playSound } = useSound()
  const controls = useAnimation()

  const { data: balance } = useQuery({
    queryKey: ['balance'],
    queryFn: getBalance,
    staleTime: 30000,
  })

  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: getUserProfile,
    staleTime: 60000,
  })

  // --- 長按充電邏輯（參考設計）---
  const [isHolding, setIsHolding] = useState(false)
  const [chargeLevel, setChargeLevel] = useState(0)
  const holdStartTimeRef = useRef<number>(0)
  const chargeFrameRef = useRef<number>(0)
  const [orbitParticles, setOrbitParticles] = useState<{id: number, angle: number, speed: number, radius: number}[]>([])

  const startHold = () => {
    setIsHolding(true)
    setChargeLevel(0)
    holdStartTimeRef.current = Date.now()
    playSound('grab')

    const animateCharge = () => {
      const elapsed = Date.now() - holdStartTimeRef.current
      const progress = Math.min(100, (elapsed / 1500) * 100)
      setChargeLevel(progress)

      if (progress < 100) {
        if (Math.random() < (progress / 200)) {
          setOrbitParticles(prev => [...prev, {
            id: Date.now() + Math.random(),
            angle: Math.random() * 360,
            speed: 5 + (progress / 10),
            radius: 0 
          }])
        }
        if (progress > 50) {
          controls.start({ 
            x: (Math.random() - 0.5) * (progress / 10), 
            y: (Math.random() - 0.5) * (progress / 10), 
            transition: { duration: 0.05 } 
          })
        }
        chargeFrameRef.current = requestAnimationFrame(animateCharge)
      } else {
        triggerExplosion()
      }
    }
    chargeFrameRef.current = requestAnimationFrame(animateCharge)
  }

  const endHold = () => {
    if (!isHolding) return
    setIsHolding(false)
    cancelAnimationFrame(chargeFrameRef.current)
    controls.start({ x: 0, y: 0 })
    setOrbitParticles([])
    if (chargeLevel < 100) navigate('/send')
    setChargeLevel(0)
  }

  const triggerExplosion = () => {
    setIsHolding(false)
    cancelAnimationFrame(chargeFrameRef.current)
    setChargeLevel(100)
    setOrbitParticles([])
    playSound('success')
    controls.start({ 
      scale: [1.1, 1.5, 0], 
      opacity: [1, 0],
      transition: { duration: 0.3 } 
    }).then(() => {
      navigate('/send')
      controls.set({ scale: 1, opacity: 1, x: 0, y: 0 })
      setChargeLevel(0)
    })
  }

  // --- 雷達邏輯（參考設計）---
  const [rotation, setRotation] = useState(0)
  const [targetRotation] = useState(() => Math.floor(Math.random() * 360))
  const [signalStrength, setSignalStrength] = useState(0)
  const [isLocked, setIsLocked] = useState(false)
  const [blips, setBlips] = useState<{id: number, x: number, y: number, delay: number, scale: number}[]>([])
  const [onlineUsers, setOnlineUsers] = useState(1204)
  const [isRadarScanning, setIsRadarScanning] = useState(false)
  const [scanCircleScale, setScanCircleScale] = useState(1)
  const [sparkles, setSparkles] = useState<Array<{id: string, x: number, y: number, life: number, maxLife: number}>>([])
  const [nearbyPacketGroups, setNearbyPacketGroups] = useState(23) // 附近的紅包群數量
  const [activeGamePlayers, setActiveGamePlayers] = useState(156) // 正在遊戲的人數
  const [energy, setEnergy] = useState(100) // 体力值
  const [fortune, setFortune] = useState(100) // 幸运值
  const scanIntervalRef = useRef<number | null>(null)

  // 更新闪烁光点动画
  useEffect(() => {
    if (sparkles.length === 0) return

    const animate = () => {
      setSparkles(prev => {
        const updated = prev
          .map(sparkle => ({
            ...sparkle,
            life: sparkle.life + 1
          }))
          .filter(sparkle => sparkle.life < sparkle.maxLife)

        if (updated.length > 0) {
          requestAnimationFrame(animate)
        }
        return updated
      })
    }

    requestAnimationFrame(animate)
  }, [sparkles.length])

  useEffect(() => {
    const count = Math.floor((signalStrength / 100) * 8) + 2
    const extra = isRadarScanning ? 5 : 0
    const newBlips = Array.from({ length: count + extra }).map((_, i) => ({
      id: Date.now() + i,
      angle: Math.random() * 360,
      dist: Math.random() * 35,
      delay: Math.random() * 2,
      scale: Math.random() * 0.5 + 0.5
    })).map(b => ({
      ...b,
      x: Math.cos(b.angle * Math.PI / 180) * b.dist,
      y: Math.sin(b.angle * Math.PI / 180) * b.dist
    }))
    setBlips(newBlips)
  }, [signalStrength, isRadarScanning])

  useEffect(() => {
    const normalizedRot = ((rotation % 360) + 360) % 360
    const diff = Math.abs(normalizedRot - targetRotation)
    const distance = Math.min(diff, 360 - diff)
    
    let strength = distance < 60 ? (1 - distance / 60) * 100 : 0
    if (isRadarScanning) strength = Math.min(100, strength + 20)
    strength = Math.min(100, Math.max(0, strength + (Math.random() - 0.5) * 5))
    setSignalStrength(strength)

    if (strength > 90 && !isLocked) { setIsLocked(true); playSound('success') }
    else if (strength < 80 && isLocked) { setIsLocked(false) }
  }, [rotation, targetRotation, isLocked, playSound, isRadarScanning])

  const handleRadarDrag = (_: any, info: any) => setRotation(prev => prev + info.delta.y * 0.5)
  
  // 点击扫描面板
  const handleRadarClick = () => {
    // 检查能量和幸运值
    if (energy < 10 || fortune < 10) {
      playSound('notification')
      return
    }

    setIsRadarScanning(true)
    playSound('switch')
    
    // 消耗能量和幸运值
    setEnergy(prev => Math.max(0, prev - 10))
    setFortune(prev => Math.max(0, prev - 10))

    // 圆圈不断放大
    let currentScale = 1
    const scaleInterval = window.setInterval(() => {
      currentScale += 0.1
      setScanCircleScale(currentScale)
      if (currentScale > 3) {
        currentScale = 1
        setScanCircleScale(1)
      }
    }, 100)

    // 生成闪烁光点
    const generateSparkle = () => {
      const sparkleCount = 20
      const newSparkles: Array<{id: string, x: number, y: number, life: number, maxLife: number}> = []
      for (let i = 0; i < sparkleCount; i++) {
        newSparkles.push({
          id: `sparkle-${Date.now()}-${i}`,
          x: Math.random() * 100, // 百分比
          y: Math.random() * 100, // 百分比
          life: 0,
          maxLife: 200 + Math.random() * 100 // 2-3秒后消失
        })
      }
      setSparkles(prev => [...prev, ...newSparkles])
    }

    // 立即生成一批光点
    generateSparkle()
    // 每500ms生成一批光点
    const sparkleInterval = window.setInterval(generateSparkle, 500)

    // 数字上升
    const numberInterval = window.setInterval(() => {
      setOnlineUsers(prev => prev + Math.floor(Math.random() * 3) + 1)
      setNearbyPacketGroups(prev => prev + Math.floor(Math.random() * 2) + 1)
      setActiveGamePlayers(prev => prev + Math.floor(Math.random() * 2) + 1)
    }, 300)

    scanIntervalRef.current = window.setInterval(() => {
      // 持续扫描效果
    }, 100)

    // 3秒后停止
    setTimeout(() => {
      setIsRadarScanning(false)
      setScanCircleScale(1)
      window.clearInterval(scaleInterval)
      window.clearInterval(sparkleInterval)
      window.clearInterval(numberInterval)
      if (scanIntervalRef.current) {
        window.clearInterval(scanIntervalRef.current)
        scanIntervalRef.current = null
      }
    }, 3000)
  }

  const startRadarScan = () => { 
    // 长按功能保留，但不消耗能量
    setIsRadarScanning(true)
    playSound('switch')
  }
  const endRadarScan = () => setIsRadarScanning(false)

  // 視覺效果配置
  const sendParticles = Array.from({ length: 20 }).map((_, i) => ({
    id: `send-${i}`,
    tx: Math.cos(Math.random() * 360) * 80,
    ty: Math.sin(Math.random() * 360) * 80,
    angle: Math.random() * 360,
    delay: Math.random() * 3,
    duration: 2 + Math.random() * 2,
    scale: 0.3 + Math.random() * 0.5
  }))

  const gameRays = Array.from({ length: 24 }).map((_, i) => ({
    id: i,
    angle: (360 / 24) * i + Math.random() * 10,
    width: 2 + Math.random() * 4,
    color: ['rgba(255,0,255,0.6)', 'rgba(0,255,255,0.6)', 'rgba(255,215,0,0.6)', 'rgba(255,69,0,0.5)'][Math.floor(Math.random() * 4)],
    duration: 1.5 + Math.random() * 2,
    delay: Math.random() * 2
  }))

  // 遊戲按鈕 hover 狀態
  const [isGameHovered, setIsGameHovered] = useState(false)
  
  const handleGameHover = () => {
    setIsGameHovered(true)
    playSound('pop')
  }
  
  const handleGameLeave = () => {
    setIsGameHovered(false)
  }
  
  const handleGameClick = () => {
    playSound('pop')
    navigate('/game')
  }

  return (
    <PageTransition>
      {/* 全局邊框發光效果（掃描時） */}
      <div className={`fixed inset-0 pointer-events-none z-40 transition-opacity duration-500 ${
        isRadarScanning ? 'opacity-100' : 'opacity-0'
      }`}>
        <div className="absolute inset-0 border-2 border-cyan-500/30 rounded-3xl m-2 shadow-[0_0_30px_rgba(6,182,212,0.5)]" />
        <div className="absolute inset-0 border-2 border-purple-500/30 rounded-3xl m-3 shadow-[0_0_30px_rgba(168,85,247,0.5)]" />
        <div className="absolute inset-0 border-2 border-emerald-500/30 rounded-3xl m-4 shadow-[0_0_30px_rgba(16,185,129,0.5)]" />
      </div>
      
      <div className={`h-full w-full flex flex-col pb-24 gap-2 overflow-hidden transition-all duration-500 ${
        isRadarScanning ? '[&>*]:border-cyan-500/50 [&>*]:shadow-[0_0_20px_rgba(6,182,212,0.3)]' : ''
      }`}>
        <div className="px-3 flex flex-col gap-2 flex-1 min-h-0">
        {/* 能量运势和邀請好友（並排） */}
        <div className="flex gap-2 shrink-0">
          {/* 能量运势面板 */}
          <EnergyFortunePanel 
            energy={energy}
            maxEnergy={100}
            onEnergyUpdate={setEnergy}
          />

          {/* 邀請好友（縮小版） */}
          <button
            onClick={() => { playSound('pop'); navigate('/earn') }}
            className="relative flex-1 h-20 bg-[#1C1C1E] border border-purple-500/20 rounded-2xl flex items-center justify-between px-3 overflow-hidden group active:scale-[0.98] transition-transform cursor-pointer shadow-lg shadow-purple-900/10"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-purple-900/10 via-[#1C1C1E] to-pink-900/10 opacity-50 group-hover:opacity-100 transition-opacity" />
            <div className="flex items-center gap-2.5 relative z-10">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center shadow-lg shadow-purple-500/20 border border-white/10">
                <Users size={14} className="text-white drop-shadow" />
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="text-white font-bold text-xs">{t('invite_friends')}</span>
                <span className="text-[10px] text-purple-300">{t('permanent_earn')} 10% {t('commission')}</span>
              </div>
            </div>
            <div className="w-5 h-5 rounded-lg bg-white/5 flex items-center justify-center hover:bg-white/10 relative z-10 pointer-events-none">
              <ChevronRight size={8} className="text-gray-400" />
            </div>
          </button>
        </div>

        {/* 發紅包按鈕（長按充電效果，可拉伸） */}
        <motion.div
          animate={controls}
          onPointerDown={startHold}
          onPointerUp={endHold}
          onPointerLeave={endHold}
          onContextMenu={(e) => e.preventDefault()}
          className={`
            relative flex-1 min-h-[80px] bg-[#1C1C1E] border rounded-3xl overflow-hidden flex flex-col items-center justify-center shadow-2xl cursor-pointer select-none touch-none
            ${isHolding ? 'border-orange-400 shadow-orange-500/40' : 'border-orange-500/20 shadow-orange-900/10'} transition-colors duration-300
          `}
        >
          {isHolding && <div className="absolute inset-0 bg-orange-500 mix-blend-overlay transition-opacity" style={{ opacity: chargeLevel / 150 }} />}
          <div className="absolute inset-0 bg-gradient-to-br from-orange-600/10 via-[#1C1C1E] to-red-600/10" />
          
          {/* 軌道粒子 */}
          <div className="absolute inset-0 pointer-events-none">
            {orbitParticles.map((p) => (
              <motion.div
                key={p.id}
                className="absolute w-3 h-3 z-20"
                style={{
                  left: '50%',
                  top: '50%',
                  x: Math.cos(Date.now() / 100 * p.speed + p.angle) * (60 + chargeLevel * 0.5),
                  y: Math.sin(Date.now() / 100 * p.speed + p.angle) * (40 + chargeLevel * 0.3)
                }}
              >
                <TelegramStar size={10 + (chargeLevel / 20)} />
                <div className="absolute inset-0 bg-white/50 blur-sm rounded-full animate-ping" />
              </motion.div>
            ))}
          </div>

          {/* 浮動粒子 */}
          <div className="absolute top-1/2 left-1/2 w-0 h-0 transition-opacity duration-300" style={{ opacity: isHolding ? 0 : 1 }}>
            {sendParticles.map((p) => (
              <motion.div
                key={p.id}
                className="absolute z-0 pointer-events-none"
                initial={{ opacity: 0, x: 0, y: 0, scale: 0 }}
                animate={{ opacity: [0, 1, 0], x: p.tx, y: p.ty, scale: [0, p.scale, 0] }}
                transition={{ duration: p.duration, repeat: Infinity, ease: "easeOut", delay: p.delay }}
              >
                <TelegramStar size={12 * p.scale} />
              </motion.div>
            ))}
          </div>

          {/* 圖標 */}
          <div className={`relative z-10 w-16 h-16 bg-gradient-to-br from-orange-500 to-red-600 rounded-full flex items-center justify-center mb-1.5 border-4 border-[#1C1C1E] transition-transform duration-100 ${isHolding ? 'scale-125 shadow-[0_0_50px_orange]' : 'shadow-[0_0_20px_rgba(234,88,12,0.5)]'}`}>
            <Gift size={28} className={`text-white drop-shadow-md ${!isHolding && 'animate-[wiggle_1s_ease-in-out_infinite]'}`} />
            {isHolding && <div className="absolute inset-0 rounded-full border-2 border-white animate-ping" />}
          </div>

          <div className="relative z-10 text-center">
            <h2 className="text-xl font-black text-white tracking-tight">
              {isHolding ? `${t('charging')} ${Math.floor(chargeLevel)}%` : t('send_red_packet')}
            </h2>
            <p className="text-orange-300/80 text-xs font-bold uppercase tracking-widest mt-1">
              {isHolding ? t('hold_charge') : t('super_charge')}
            </p>
          </div>

          <div className="absolute right-3 bottom-3 w-8 h-8 rounded-full bg-[#2C2C2E] flex items-center justify-center border border-white/10 shadow-lg z-20">
            <Send size={14} className="-ml-0.5 mt-0.5" />
          </div>

          {/* 進度條 */}
          <div className="absolute bottom-0 left-0 w-full h-1.5 bg-orange-500/20">
            <motion.div
              className="h-full bg-orange-500 shadow-[0_0_15px_orange]"
              initial={{ width: '65%' }}
              animate={{ width: isHolding ? `${chargeLevel}%` : '65%' }}
              transition={{ duration: isHolding ? 0 : 1 }}
            />
          </div>
        </motion.div>

        {/* 操作按鈕行 */}
        <div className="grid grid-cols-5 gap-2 shrink-0 relative z-20 mt-2">
          {/* 充值按钮 - 绿色渐变 */}
          <ActionButton 
            icon={CreditCard} 
            label={t('recharge')} 
            color="text-green-300" 
            bgGradient="from-green-500/20 to-emerald-500/20"
            borderColor="border-green-500/30"
            glowColor="shadow-green-500/20"
            onClick={() => { playSound('click'); navigate('/recharge') }} 
          />
          
          {/* 提现按钮 - 蓝色渐变 */}
          <ActionButton 
            icon={ArrowUpRight} 
            label={t('withdraw')} 
            color="text-blue-300" 
            bgGradient="from-blue-500/20 to-cyan-500/20"
            borderColor="border-blue-500/30"
            glowColor="shadow-blue-500/20"
            onClick={() => { playSound('click'); navigate('/withdraw') }} 
          />
          
          {/* 遊戲按鈕（帶特效） */}
          <div
            className="relative flex flex-col items-center justify-center cursor-pointer group"
            style={{ aspectRatio: '1 / 1' }}
            onPointerEnter={handleGameHover}
            onPointerLeave={handleGameLeave}
            onTouchStart={handleGameHover}
            onClick={handleGameClick}
          >
            {/* 光環效果（僅在 hover 時顯示） */}
            <AnimatePresence>
              {isGameHovered && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 flex items-center justify-center pointer-events-none z-0"
                >
                  {gameRays.map((ray) => (
                    <motion.div
                      key={ray.id}
                      className="absolute bottom-1/2 left-1/2 origin-bottom rounded-t-full"
                      style={{
                        width: ray.width,
                        background: `linear-gradient(to top, ${ray.color}, transparent)`,
                        filter: 'blur(3px)'
                      }}
                      initial={{ rotate: ray.angle, height: '40%', opacity: 0 }}
                      animate={{
                        height: ['60%', '160%', '60%'],
                        opacity: [0.1, 0.8, 0.1],
                        rotate: [ray.angle - 5, ray.angle + 5, ray.angle - 5]
                      }}
                      transition={{
                        duration: ray.duration,
                        repeat: Infinity,
                        repeatType: "reverse",
                        ease: "easeInOut",
                        delay: ray.delay
                      }}
                    />
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
            <motion.div
              whileHover={{ scale: 1.15 }}
              whileTap={{ scale: 0.95 }}
              className="w-10 h-10 rounded-xl relative z-10 overflow-hidden shadow-[0_10px_20px_rgba(0,0,0,0.5),0_4px_0_#4c1d95] bg-[#1C1C1E] border border-white/5 mb-1"
            >
              <div className="absolute inset-0 bg-gradient-to-b from-[#fbbf24] via-[#f472b6] to-[#7c3aed]" />
              <div className="absolute inset-0 flex items-center justify-center">
                <Gamepad2 className="text-white drop-shadow-md" size={20} strokeWidth={2.5} />
              </div>
            </motion.div>
            <span className="text-xs font-bold text-gray-500 group-hover:text-white transition-colors">{t('game')}</span>
          </div>

          {/* 记录按钮 - 橙色渐变 */}
          <ActionButton 
            icon={FileText} 
            label={t('records')} 
            color="text-orange-300" 
            bgGradient="from-orange-500/20 to-amber-500/20"
            borderColor="border-orange-500/30"
            glowColor="shadow-orange-500/20"
            onClick={() => { playSound('click'); navigate('/packets') }} 
          />
          
          {/* 兑换按钮 - 紫色渐变 */}
          <ActionButton 
            icon={ArrowLeftRight} 
            label={t('exchange')} 
            color="text-purple-300" 
            bgGradient="from-purple-500/20 to-pink-500/20"
            borderColor="border-purple-500/30"
            glowColor="shadow-purple-500/20"
            onClick={() => { playSound('click'); navigate('/exchange') }} 
          />
        </div>

        {/* 雷達掃描器（全寬，可拉伸） */}
        <motion.div
          className="relative w-full flex-1 min-h-0 bg-[#1C1C1E] border border-emerald-500/20 rounded-3xl overflow-hidden flex flex-row items-center shadow-lg group cursor-pointer transition-all duration-500"
            onPan={handleRadarDrag}
            onContextMenu={(e) => e.preventDefault()}
            onClick={handleRadarClick}
            onPointerDown={startRadarScan}
            onPointerUp={endRadarScan}
            onPointerLeave={endRadarScan}
            style={{ touchAction: 'none' }}
          >
            {/* 技術網格背景（增強科技感） */}
            <div className="absolute inset-0 bg-[linear-gradient(transparent_19px,#00ff88_1px),linear-gradient(90deg,transparent_19px,#00ff88_1px)] bg-[size:24px_24px] opacity-[0.08]" />
            <div className="absolute inset-0 bg-[linear-gradient(transparent_38px,#00d9ff_0.5px),linear-gradient(90deg,transparent_38px,#00d9ff_0.5px)] bg-[size:48px_48px] opacity-[0.05]" />
            <div className="absolute inset-0 bg-gradient-to-b from-emerald-900/20 via-cyan-900/10 to-purple-900/20" />
            
            {/* 掃描光效（多層次） */}
            <motion.div 
              className="absolute inset-0"
              animate={isRadarScanning ? {
                background: [
                  'radial-gradient(circle at 50% 50%, rgba(0,255,136,0.2) 0%, transparent 70%)',
                  'radial-gradient(circle at 50% 50%, rgba(0,217,255,0.2) 0%, transparent 70%)',
                  'radial-gradient(circle at 50% 50%, rgba(168,85,247,0.2) 0%, transparent 70%)',
                  'radial-gradient(circle at 50% 50%, rgba(0,255,136,0.2) 0%, transparent 70%)',
                ]
              } : {}}
              transition={{ duration: 2, repeat: Infinity }}
            />
            
            {/* 脈衝光環 */}
            {isRadarScanning && (
              <>
                <motion.div
                  className="absolute inset-0 border-2 border-emerald-400 rounded-3xl"
                  animate={{
                    scale: [1, 1.05, 1],
                    opacity: [0.3, 0.6, 0.3],
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
                <motion.div
                  className="absolute inset-0 border-2 border-cyan-400 rounded-3xl"
                  animate={{
                    scale: [1, 1.08, 1],
                    opacity: [0.2, 0.5, 0.2],
                  }}
                  transition={{ duration: 2.5, repeat: Infinity, delay: 0.5 }}
                />
              </>
            )}

            {/* 左側統計信息（垂直排列） */}
            <div className="relative z-10 flex flex-col gap-2 px-3 py-2">
              {/* 在線用戶 */}
              <div className="flex items-center gap-2 bg-black/30 backdrop-blur-sm px-2.5 py-2 rounded-full border border-emerald-500/20">
                <motion.div
                  className={`w-2 h-2 rounded-full ${isLocked ? 'bg-white' : 'bg-emerald-500'}`}
                  animate={isRadarScanning ? {
                    scale: [1, 1.8, 1],
                    opacity: [0.7, 1, 0.7]
                  } : {}}
                  transition={{ duration: 0.8, repeat: Infinity }}
                />
                <span className="text-xs font-mono font-bold text-emerald-100 whitespace-nowrap">
                  <motion.span
                    key={onlineUsers}
                    initial={{ scale: 1 }}
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.3 }}
                    className="inline-block"
                  >
                    {onlineUsers}
                  </motion.span> {t('online')}
                </span>
              </div>
              
              {/* 附近的紅包群 */}
              <div className="flex items-center gap-2 bg-black/30 backdrop-blur-sm px-2.5 py-2 rounded-full border border-cyan-500/20">
                <motion.div
                  className="w-2 h-2 rounded-full bg-cyan-400"
                  animate={isRadarScanning ? {
                    scale: [1, 2.2, 1],
                    opacity: [0.7, 1, 0.7]
                  } : {}}
                  transition={{ duration: 1.0, repeat: Infinity, delay: 0.2 }}
                />
                <span className="text-xs font-mono font-bold text-cyan-100 whitespace-nowrap">
                  <motion.span
                    key={nearbyPacketGroups}
                    initial={{ scale: 1 }}
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.3 }}
                    className="inline-block"
                  >
                    {nearbyPacketGroups}
                  </motion.span> {t('packet_groups')}
                </span>
              </div>
              
              {/* 正在遊戲的人數 */}
              <div className="flex items-center gap-2 bg-black/30 backdrop-blur-sm px-2.5 py-2 rounded-full border border-purple-500/20">
                <motion.div
                  className="w-2 h-2 rounded-full bg-purple-400"
                  animate={isRadarScanning ? {
                    scale: [1, 2.5, 1],
                    opacity: [0.7, 1, 0.7]
                  } : {}}
                  transition={{ duration: 1.1, repeat: Infinity, delay: 0.4 }}
                />
                <span className="text-xs font-mono font-bold text-purple-100 whitespace-nowrap">
                  <motion.span
                    key={activeGamePlayers}
                    initial={{ scale: 1 }}
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.3 }}
                    className="inline-block"
                  >
                    {activeGamePlayers}
                  </motion.span> {t('gaming')}
                </span>
              </div>
            </div>

            {/* 右側雷達圖形 */}
            <div className="relative z-10 flex-1 flex items-center justify-center flex-col">
              <div className="relative w-24 h-24 flex items-center justify-center">
              {/* 外層光環（科技感） */}
              <motion.div
                className="absolute inset-0 rounded-full border border-cyan-400/30"
                animate={isRadarScanning ? {
                  rotate: 360,
                  scale: [1, 1.1, 1]
                } : {}}
                transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
              />
              
              {/* 掃描圓圈 - 不斷放大 */}
              <motion.div
                className={`absolute inset-0 rounded-full border-2 border-dashed transition-colors duration-300 ${
                  isLocked ? 'border-white shadow-[0_0_20px_white]' : isRadarScanning ? 'border-emerald-400 shadow-[0_0_15px_#10b981]' : 'border-emerald-500/30'
                }`}
                style={{ 
                  rotate: rotation,
                  scale: scanCircleScale,
                  transformOrigin: 'center'
                }}
                animate={isRadarScanning ? { 
                  rotate: 360,
                  scale: scanCircleScale
                } : {
                  scale: 1
                }}
                transition={isRadarScanning ? { 
                  rotate: { duration: 1, repeat: Infinity, ease: "linear" },
                  scale: { duration: 0.1, ease: "linear" }
                } : {}}
              >
                <motion.div
                  className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1 w-2 h-2 bg-emerald-400 rounded-full shadow-[0_0_10px_lime]"
                  animate={isRadarScanning ? {
                    boxShadow: [
                      '0 0 5px #10b981',
                      '0 0 20px #10b981',
                      '0 0 5px #10b981',
                    ]
                  } : {}}
                  transition={{ duration: 1, repeat: Infinity }}
                />
              </motion.div>
              
              {/* 中層環 */}
              <motion.div
                className="absolute inset-4 rounded-full border border-cyan-500/20"
                animate={isRadarScanning ? {
                  rotate: -360,
                  opacity: [0.3, 0.7, 0.3]
                } : {}}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              />

              {/* 雷達掃描效果（增強科技感） */}
              <div className="absolute inset-4 rounded-full border border-emerald-500/20 overflow-hidden bg-[#0f0f11]">
                <div className="absolute inset-0 rounded-full border border-cyan-500/10" />
                
                {/* 多層旋轉光束（科技感） */}
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: isRadarScanning ? 0.5 : 2, repeat: Infinity, ease: "linear" }}
                  className="absolute inset-0 rounded-full"
                  style={{
                    background: 'conic-gradient(from 0deg, transparent 0deg, rgba(0,255,136,0.6) 90deg, rgba(0,217,255,0.6) 180deg, rgba(168,85,247,0.6) 270deg, transparent 360deg)'
                  }}
                />
                
                {/* 第二層光束 */}
                <motion.div
                  animate={{ rotate: -360 }}
                  transition={{ duration: isRadarScanning ? 0.8 : 3, repeat: Infinity, ease: "linear" }}
                  className="absolute inset-0 rounded-full opacity-50"
                  style={{
                    background: 'conic-gradient(from 180deg, transparent 0deg, rgba(0,217,255,0.4) 90deg, rgba(168,85,247,0.4) 180deg, transparent 270deg)'
                  }}
                />
                
                {/* 中心脈衝 */}
                <motion.div
                  className="absolute inset-1/4 rounded-full border border-cyan-400/30"
                  animate={isRadarScanning ? {
                    scale: [1, 1.5, 1],
                    opacity: [0.3, 0.7, 0.3]
                  } : {}}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
                
                {/* 信號點（增強科技感） */}
                <AnimatePresence>
                  {blips.map(b => (
                    <motion.div
                      key={b.id}
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ 
                        opacity: [0, 1, 0.8, 0], 
                        scale: [0, 1.2, 1, 0.8],
                      }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 1.5, repeat: Infinity, delay: b.delay }}
                      className="absolute z-10"
                      style={{
                        left: `calc(50% + ${b.x}px)`,
                        top: `calc(50% + ${b.y}px)`
                      }}
                    >
                      <div className="w-2 h-2 bg-gradient-to-br from-yellow-300 to-orange-400 rounded-full shadow-[0_0_8px_#fbbf24]" />
                      <motion.div
                        className="absolute inset-0 rounded-full border border-yellow-300/50"
                        animate={{
                          scale: [1, 2, 1],
                          opacity: [0.8, 0, 0.8]
                        }}
                        transition={{ duration: 1.5, repeat: Infinity, delay: b.delay }}
                      />
                    </motion.div>
                  ))}
                </AnimatePresence>

                {/* 闪烁光点 - 在背景上 */}
                <AnimatePresence>
                  {sparkles.map(sparkle => (
                    <motion.div
                      key={sparkle.id}
                      className="absolute z-5"
                      style={{
                        left: `${sparkle.x}%`,
                        top: `${sparkle.y}%`,
                        transform: 'translate(-50%, -50%)'
                      }}
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ 
                        opacity: [0, 1, 1, 0],
                        scale: [0, 1.5, 1, 0],
                      }}
                      exit={{ opacity: 0, scale: 0 }}
                      transition={{ 
                        duration: sparkle.maxLife / 60,
                        ease: "easeOut",
                        repeat: Infinity,
                        repeatType: "reverse"
                      }}
                    >
                      <div className="w-1.5 h-1.5 bg-white rounded-full shadow-[0_0_8px_#ffffff,0_0_16px_#60a5fa]" />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>

                {/* 中心圖標（增強科技感） */}
                <div className="absolute z-20 pointer-events-none">
                  {isLocked ? (
                    <motion.div
                      animate={{
                        scale: [1, 1.2, 1],
                        rotate: [0, 180, 360]
                      }}
                      transition={{ duration: 2, repeat: Infinity }}
                    >
                      <Target size={24} className="text-white drop-shadow-[0_0_10px_white]" />
                    </motion.div>
                  ) : (
                    <motion.div
                      animate={isRadarScanning ? {
                        scale: [1, 1.1, 1],
                        opacity: [0.7, 1, 0.7]
                      } : {}}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      <Wifi size={24} className={`${isRadarScanning ? 'text-cyan-400' : 'text-emerald-500/50'} drop-shadow-[0_0_8px_currentColor]`} />
                    </motion.div>
                  )}
                </div>
              </div>

              {/* 狀態文字（移到最右側） */}
              <div className="absolute right-3 top-1/2 -translate-y-1/2 z-10 select-none">
                <span className={`text-xs font-bold uppercase tracking-widest block ${
                  isLocked ? 'text-white' : isRadarScanning ? 'text-cyan-400' : 'text-emerald-500/70'
                }`}>
                  {isLocked ? t('target_locked') : isRadarScanning ? t('active_scan') : t('passive_scan')}
                </span>
              </div>
            </div>
            
            {/* 幫助文字 */}
            {!isRadarScanning && (
              <div className="absolute bottom-2 right-2 text-[10px] text-emerald-500/60 pointer-events-none animate-pulse uppercase tracking-wide z-10">
                {t('hold_to_scan')}
              </div>
            )}

            {/* 進度條（增強科技感） */}
            <div className="absolute bottom-0 left-0 w-full h-1.5 bg-emerald-900/30 overflow-hidden z-10">
              <motion.div
                className={`h-full shadow-[0_0_15px_currentColor] ${
                  isLocked 
                    ? 'bg-gradient-to-r from-white via-cyan-300 to-white' 
                    : 'bg-gradient-to-r from-emerald-500 via-cyan-400 to-emerald-500'
                }`}
                initial={{ width: '0%' }}
                animate={{ width: `${signalStrength}%` }}
                transition={{ duration: 0.2 }}
              >
                <motion.div
                  className="absolute inset-0 bg-white/30"
                  animate={isRadarScanning ? {
                    x: ['-100%', '100%']
                  } : {}}
                  transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                />
              </motion.div>
            </div>
          </motion.div>

        {/* 用戶等級 */}
        {profile && (
          <div className="bg-[#1C1C1E] border border-white/5 rounded-2xl p-4 shrink-0">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-300 text-base font-medium">{t('level')}</span>
              <span className="text-white font-bold">Lv.{profile.level}</span>
            </div>
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-brand-red to-orange-500"
                initial={{ width: 0 }}
                animate={{ width: `${(profile.xp % 100)}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
            </div>
          </div>
        )}
        </div>
      </div>
    </PageTransition>
  )
}

function ActionButton({ 
  icon: Icon, 
  label, 
  color, 
  bgGradient = "from-gray-500/10 to-gray-500/10",
  borderColor = "border-white/5",
  glowColor = "",
  onClick 
}: {
  icon: React.ElementType
  label: string
  color: string
  bgGradient?: string
  borderColor?: string
  glowColor?: string
  onClick: () => void
}) {
  return (
    <motion.button
      onClick={onClick}
      className={`flex flex-col items-center justify-center gap-1 w-full bg-gradient-to-br ${bgGradient} rounded-xl border ${borderColor} ${glowColor} active:scale-95 transition-all relative overflow-hidden group`}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      style={{ 
        aspectRatio: '1 / 1',
        padding: '0.5rem'
      }}
    >
      {/* 悬停光效 */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
        initial={{ x: '-100%' }}
        whileHover={{ x: '100%' }}
        transition={{ duration: 0.6 }}
      />
      
      {/* 图标容器 - 只保留外部方框，去除内部小方框 */}
      <div className="w-9 h-9 flex items-center justify-center relative z-10">
        <Icon className={color} size={18} strokeWidth={2.5} />
      </div>
      <span className={`text-xs font-bold text-gray-400 group-hover:${color} transition-colors relative z-10`}>
        {label}
      </span>
    </motion.button>
  )
}
