import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Plus, Minus, Gift, Clock, Users, ChevronRight, Send, Gamepad2, TrendingUp, Target, Wifi, Wallet } from 'lucide-react'
import { motion, AnimatePresence, useAnimation } from 'framer-motion'
import { useTranslation } from '../providers/I18nProvider'
import { getBalance, getUserProfile } from '../utils/api'
import { useSound } from '../hooks/useSound'
import TelegramStar from '../components/TelegramStar'
import PageTransition from '../components/PageTransition'
import AssetHeader from '../components/AssetHeader'

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

  useEffect(() => {
    const interval = setInterval(() => {
      setOnlineUsers(prev => prev + Math.floor((Math.random() - 0.5) * 10))
    }, 2000)
    return () => clearInterval(interval)
  }, [])

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
  const startRadarScan = () => { setIsRadarScanning(true); playSound('switch') }
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
      <div className="h-full w-full flex flex-col pb-24 gap-2 overflow-y-auto scrollbar-hide">
        {/* 總資產頭部（僅在首頁顯示） */}
        <AssetHeader />
        
        <div className="px-3 space-y-2">
        {/* 發紅包按鈕（長按充電效果） */}
        <motion.div
          animate={controls}
          onPointerDown={startHold}
          onPointerUp={endHold}
          onPointerLeave={endHold}
          onContextMenu={(e) => e.preventDefault()}
          className={`
            relative h-[22%] min-h-[150px] shrink-0 bg-[#1C1C1E] border rounded-3xl overflow-hidden flex flex-col items-center justify-center shadow-2xl cursor-pointer select-none touch-none
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
              {isHolding ? `充電中 ${Math.floor(chargeLevel)}%` : t('send_red_packet')}
            </h2>
            <p className="text-orange-300/80 text-[10px] font-bold uppercase tracking-widest mt-0.5">
              {isHolding ? '長按充能' : '長按超級充能'}
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
        <div className="grid grid-cols-5 gap-2 shrink-0 h-14 items-center relative z-20">
          <ActionButton icon={Plus} label={t('recharge')} color="text-green-400" onClick={() => { playSound('click'); navigate('/recharge') }} />
          <ActionButton icon={Minus} label={t('withdraw')} color="text-white" onClick={() => { playSound('click'); navigate('/withdraw') }} />
          
          {/* 遊戲按鈕（帶特效） */}
          <div
            className="relative flex flex-col items-center justify-center cursor-pointer group h-full"
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
            <span className="text-[8px] font-bold text-gray-500 group-hover:text-white transition-colors">{t('game')}</span>
          </div>

          <ActionButton icon={Clock} label={t('records')} color="text-white" onClick={() => { playSound('click'); navigate('/packets') }} />
          <ActionButton icon={TrendingUp} label={t('exchange')} color="text-white" onClick={() => playSound('click')} />
        </div>

        {/* 邀請好友 */}
        <button
          onClick={() => { playSound('pop'); navigate('/earn') }}
          className="h-12 shrink-0 bg-[#1C1C1E] border border-purple-500/20 rounded-2xl flex items-center justify-between px-3 relative overflow-hidden group active:scale-[0.99] transition-transform cursor-pointer shadow-lg shadow-purple-900/10"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-purple-900/10 via-[#1C1C1E] to-pink-900/10 opacity-50 group-hover:opacity-100 transition-opacity" />
          <div className="flex items-center gap-3 relative z-10">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center shadow-lg shadow-purple-500/20 border border-white/10">
              <Users size={14} className="text-white drop-shadow" />
            </div>
            <div className="flex flex-col">
              <span className="text-white font-bold text-xs">{t('invite_friends')}</span>
              <span className="text-[9px] text-purple-300">永久獲得 10% 返佣</span>
            </div>
          </div>
          <button className="w-6 h-6 rounded-lg bg-white/5 flex items-center justify-center hover:bg-white/10 relative z-10">
            <ChevronRight size={10} className="text-gray-400" />
          </button>
        </button>

        {/* 總資產和雷達掃描器（並排） */}
        <div className="flex flex-row gap-2 flex-1 min-h-0">
          {/* 總資產卡片 */}
          <div className="relative flex-1 bg-gradient-to-br from-cyan-900/20 via-[#1C1C1E] to-blue-900/20 border border-cyan-500/20 rounded-3xl overflow-hidden flex flex-col items-center justify-center shadow-lg group active:scale-[0.98] transition-all">
            <div className="absolute top-0 inset-x-0 h-16 bg-gradient-to-b from-cyan-500/10 to-transparent opacity-60" />
            <div className="z-10 flex flex-col items-center gap-1 mb-2">
              <span className="text-cyan-300/60 text-[9px] font-bold uppercase tracking-[0.15em] flex items-center gap-1">
                <Wallet size={10} /> {t('total_assets')}
              </span>
              <span className="text-2xl font-black text-white tracking-tighter drop-shadow-md">
                {balance?.usdt?.toFixed(2) ?? '0.00'}
              </span>
              <div className="bg-[#0f0f11]/60 backdrop-blur-md px-2 py-0.5 rounded-full border border-cyan-500/20 flex items-center gap-1 shadow-sm mt-1">
                <motion.div
                  className="w-1.5 h-1.5 rounded-full bg-cyan-400"
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
                <span className="text-cyan-200 text-[8px] font-bold">Stars</span>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 w-full h-1 bg-cyan-500/20">
              <motion.div
                className="h-full bg-cyan-500 shadow-[0_0_10px_cyan]"
                initial={{ width: '0%' }}
                animate={{ width: '45%' }}
                transition={{ duration: 1.5, ease: "easeOut", delay: 0.2 }}
              />
            </div>
          </div>

          {/* 雷達掃描器 */}
          <motion.div
            className="relative flex-[1.5] bg-[#1C1C1E] border border-emerald-500/20 rounded-3xl overflow-hidden flex flex-col items-center justify-center shadow-lg group cursor-grab active:cursor-grabbing"
            onPan={handleRadarDrag}
            onContextMenu={(e) => e.preventDefault()}
            onPointerDown={startRadarScan}
            onPointerUp={endRadarScan}
            onPointerLeave={endRadarScan}
            style={{ touchAction: 'none' }}
          >
            {/* 技術網格背景 */}
            <div className="absolute inset-0 bg-[linear-gradient(transparent_19px,#10b981_1px),linear-gradient(90deg,transparent_19px,#10b981_1px)] bg-[size:24px_24px] opacity-[0.05]" />
            <div className="absolute inset-0 bg-gradient-to-b from-emerald-900/10 to-transparent" />
            
            {/* 掃描光效 */}
            <div className={`absolute inset-0 transition-opacity duration-300 ${isRadarScanning ? 'opacity-30 bg-emerald-500/30' : 'opacity-0'}`} />

            <div className="relative z-10 w-20 h-20 flex items-center justify-center mb-2">
              {/* 雷達外環 */}
              <motion.div
                className={`absolute inset-0 rounded-full border-2 border-dashed transition-colors duration-300 ${
                  isLocked ? 'border-white' : isRadarScanning ? 'border-emerald-400' : 'border-emerald-500/30'
                }`}
                style={{ rotate: rotation }}
                animate={isRadarScanning ? { rotate: 360 } : {}}
                transition={isRadarScanning ? { duration: 1, repeat: Infinity, ease: "linear" } : {}}
              >
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1 w-1.5 h-1.5 bg-emerald-400 rounded-full shadow-[0_0_5px_lime]" />
              </motion.div>

              {/* 雷達掃描效果 */}
              <div className="absolute inset-2 rounded-full border border-emerald-500/20 overflow-hidden bg-[#0f0f11]">
                <div className="absolute inset-0 rounded-full border border-emerald-500/10" />
                {/* 旋轉光束 */}
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: isRadarScanning ? 0.5 : 2, repeat: Infinity, ease: "linear" }}
                  className="absolute inset-0 rounded-full"
                  style={{
                    background: 'conic-gradient(from 0deg, transparent 0deg, rgba(16,185,129,0.5) 360deg)'
                  }}
                />
                
                {/* 信號點 */}
                <AnimatePresence>
                  {blips.map(b => (
                    <motion.div
                      key={b.id}
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ opacity: [0, 1, 0], scale: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 1.5, repeat: Infinity, delay: b.delay }}
                      className="absolute w-1.5 h-1.5 bg-yellow-300 rounded-full shadow-[0_0_4px_gold] z-10"
                      style={{
                        left: `calc(50% + ${b.x}px)`,
                        top: `calc(50% + ${b.y}px)`
                      }}
                    />
                  ))}
                </AnimatePresence>
              </div>

              {/* 中心圖標 */}
              <div className="absolute z-20 pointer-events-none">
                {isLocked ? (
                  <Target size={20} className="text-white animate-ping" />
                ) : (
                  <Wifi size={20} className={`text-emerald-500/50 ${isRadarScanning && 'text-emerald-400 animate-pulse'}`} />
                )}
              </div>
            </div>

            <div className="mt-0 text-center z-10 select-none">
              <span className={`text-[8px] font-bold uppercase tracking-widest block mb-0.5 ${
                isLocked ? 'text-white' : 'text-emerald-500/70'
              }`}>
                {isLocked ? '目標鎖定' : isRadarScanning ? '掃描中...' : '被動掃描'}
              </span>
              
              {/* 在線用戶計數 */}
              <div className="flex items-center justify-center gap-1.5 bg-black/20 px-2 py-0.5 rounded-full border border-white/5">
                <div className={`w-1.5 h-1.5 rounded-full ${isLocked ? 'bg-white animate-pulse' : 'bg-emerald-500'}`} />
                <span className="text-[10px] font-mono font-bold text-emerald-100">
                  {onlineUsers} 附近
                </span>
              </div>
            </div>
            
            {/* 幫助文字 */}
            {!isRadarScanning && (
              <div className="absolute bottom-2 text-[7px] text-emerald-500/40 pointer-events-none animate-pulse uppercase tracking-wide">
                長按掃描
              </div>
            )}

            {/* 進度條 */}
            <div className="absolute bottom-0 left-0 w-full h-1 bg-emerald-900/30">
              <motion.div
                className={`h-full shadow-[0_0_10px_lime] ${isLocked ? 'bg-white' : 'bg-emerald-500'}`}
                initial={{ width: '0%' }}
                animate={{ width: `${signalStrength}%` }}
                transition={{ duration: 0.2 }}
              />
            </div>
          </motion.div>
        </div>

        {/* 用戶等級 */}
        {profile && (
          <div className="bg-[#1C1C1E] border border-white/5 rounded-2xl p-4 shrink-0">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400 text-sm">{t('level')}</span>
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

function ActionButton({ icon: Icon, label, color, onClick }: {
  icon: React.ElementType
  label: string
  color: string
  onClick: () => void
}) {
  return (
    <motion.button
      onClick={onClick}
      className="flex flex-col items-center gap-1 h-full w-full bg-[#1C1C1E] rounded-xl border border-white/5 active:bg-white/5 transition-colors"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      <div className="w-9 h-9 rounded-xl bg-white/5 flex items-center justify-center">
        <Icon className={color} size={16} strokeWidth={2.5} />
      </div>
      <span className="text-[8px] text-gray-500 font-bold">{label}</span>
    </motion.button>
  )
}
