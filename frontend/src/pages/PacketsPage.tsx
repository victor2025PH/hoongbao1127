import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Box, Sparkles, Crown, Share2, Check, Gift, Gamepad2, RefreshCw, Bomb } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import confetti from 'canvas-confetti'
import { useTranslation } from '../providers/I18nProvider'
import { listRedPackets, claimRedPacket, type RedPacket } from '../utils/api'
import { useSound } from '../hooks/useSound'
import ResultModal from '../components/ResultModal'
import TelegramStar from '../components/TelegramStar'
import PageTransition from '../components/PageTransition'

// 紅包類型映射
interface PacketDisplay {
  id: string
  senderName: string
  senderAvatar: string
  senderLevel: number
  message: string
  totalQuantity: number
  remainingQuantity: number
  type: 'ordinary' | 'lucky' | 'exclusive'
  status: 'active' | 'completed' | 'expired'
  timestamp: number
  currency: 'USDT' | 'TON' | 'Stars'
  amount: number
  chatTitle?: string
  isFromGameGroup?: boolean
  isBomb?: boolean
  uuid?: string
}

// 將 API 紅包轉換為顯示格式
function convertToDisplay(packet: RedPacket): PacketDisplay {
  const packetType = packet.type === 'random' ? 'lucky' : 'ordinary'
  const isBomb = packet.type === 'fixed' && (packet as any).bomb_number !== undefined
  
  return {
    id: packet.id,
    uuid: packet.id,
    senderName: packet.sender_name || '匿名用戶',
    senderAvatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${packet.sender_id}`,
    senderLevel: Math.floor(Math.random() * 50) + 1, // TODO: 從 API 獲取真實等級
    message: packet.message || '恭喜發財！🧧',
    totalQuantity: packet.quantity,
    remainingQuantity: packet.remaining,
    type: isBomb ? 'exclusive' : packetType,
    status: packet.status,
    timestamp: new Date(packet.created_at).getTime(),
    currency: (packet.currency?.toUpperCase() || 'USDT') as 'USDT' | 'TON' | 'Stars',
    amount: packet.amount,
    chatTitle: (packet as any).chat_title,
    isFromGameGroup: !!(packet as any).chat_id,
    isBomb,
  }
}

export default function PacketsPage() {
  const { t } = useTranslation()
  const { playSound } = useSound()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'all' | 'crypto' | 'points'>('all')
  const [selectedPacket, setSelectedPacket] = useState<PacketDisplay | null>(null)
  const [showResultModal, setShowResultModal] = useState(false)
  const [claimAmount, setClaimAmount] = useState(0)
  const [claimMessage, setClaimMessage] = useState('')
  const [loadingId, setLoadingId] = useState<string | null>(null)
  const [isCopied, setIsCopied] = useState<string | null>(null)

  // 使用真實 API 獲取紅包列表
  const { data: rawPackets, isLoading, error, refetch } = useQuery({
    queryKey: ['redpackets'],
    queryFn: listRedPackets,
    staleTime: 10000, // 10秒
    refetchInterval: 30000, // 30秒自動刷新
  })

  // 轉換為顯示格式
  const packets: PacketDisplay[] = (rawPackets || []).map(convertToDisplay)

  // 搶紅包 mutation
  const claimMutation = useMutation({
    mutationFn: (packetId: string) => claimRedPacket(packetId),
    onSuccess: (result, packetId) => {
      // 刷新紅包列表和餘額
      queryClient.invalidateQueries({ queryKey: ['redpackets'] })
      queryClient.invalidateQueries({ queryKey: ['balance'] })
      
      // 顯示結果
      setClaimAmount(result.amount)
      setClaimMessage(result.message)
      setShowResultModal(true)
      setLoadingId(null)
      
      // 成功動畫
      playSound('success')
      triggerSuccessConfetti()
    },
    onError: (error: any) => {
      setLoadingId(null)
      playSound('error')
      alert(error.message || '領取失敗')
    }
  })

  const triggerSuccessConfetti = () => {
    const end = Date.now() + 500
    const colors = ['#bb0000', '#ffffff', '#fb923c', '#fbbf24']
    const frame = () => {
      confetti({
        particleCount: 5,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors: colors,
        zIndex: 1000,
      })
      confetti({
        particleCount: 5,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors: colors,
        zIndex: 1000,
      })
      if (Date.now() < end) {
        requestAnimationFrame(frame)
      }
    }
    frame()
  }

  const filteredPackets = packets.filter((packet) => {
    if (activeTab === 'all') return true
    if (activeTab === 'crypto') return packet.currency === 'USDT' || packet.currency === 'TON'
    if (activeTab === 'points') return packet.currency === 'Stars'
    return true
  })

  const typeConfig = {
    ordinary: {
      labelKey: 'ordinary',
      color: 'text-cyan-400',
      icon: Box,
    },
    lucky: {
      labelKey: 'lucky',
      color: 'text-purple-400',
      icon: TelegramStar,
    },
    exclusive: {
      labelKey: 'exclusive',
      color: 'text-yellow-400',
      icon: Crown,
    },
  }

  const handleShare = async (e: React.MouseEvent, packet: PacketDisplay) => {
    e.stopPropagation()
    playSound('click')
    
    const shareUrl = `${window.location.origin}/claim/${packet.uuid}`
    const shareData = {
      title: '搶紅包',
      text: `🎁 搶 ${packet.senderName} 的紅包！"${packet.message}"`,
      url: shareUrl,
    }

    try {
      if (navigator.share) {
        await navigator.share(shareData)
      } else {
        await navigator.clipboard.writeText(`${shareData.text} ${shareData.url}`)
        setIsCopied(packet.id)
        setTimeout(() => setIsCopied(null), 2000)
      }
    } catch (err) {
      console.error('Error sharing:', err)
    }
  }

  const handleGrab = async (e: React.MouseEvent, packet: PacketDisplay) => {
    if (packet.remainingQuantity <= 0 || packet.status !== 'active') return

    e.stopPropagation()
    setLoadingId(packet.id)
    setSelectedPacket(packet)
    playSound('grab')

    // 獲取按鈕位置用於噴花
    const rect = (e.target as HTMLElement).getBoundingClientRect()
    const x = (rect.left + rect.width / 2) / window.innerWidth
    const y = (rect.top + rect.height / 2) / window.innerHeight

    // 點擊時噴花
    confetti({
      particleCount: 30,
      spread: 60,
      origin: { x, y },
      colors: ['#fb923c', '#ffffff', '#fbbf24'],
      zIndex: 1000,
    })

    // 調用真實 API 領取紅包
    claimMutation.mutate(packet.uuid || packet.id)
  }

  // 加載狀態
  if (isLoading) {
    return (
      <PageTransition>
        <div className="h-full flex flex-col items-center justify-center p-6">
          <div className="w-12 h-12 border-4 border-orange-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400 mt-4">載入中...</p>
        </div>
      </PageTransition>
    )
  }

  // 錯誤狀態
  if (error) {
    return (
      <PageTransition>
        <div className="h-full flex flex-col items-center justify-center p-6">
          <p className="text-red-400 mb-4">載入失敗</p>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 bg-orange-500 text-white rounded-lg"
          >
            <RefreshCw size={16} />
            重試
          </button>
        </div>
      </PageTransition>
    )
  }

  return (
    <PageTransition>
      <div className="h-full flex flex-col p-3 pb-24 gap-3 overflow-y-auto scrollbar-hide">
        {/* 標籤切換 */}
        <div className="flex gap-2 shrink-0">
          {(['all', 'crypto', 'points'] as const).map((tab) => (
            <motion.button
              key={tab}
              onClick={() => {
                setActiveTab(tab)
                playSound('click')
              }}
              className={`px-4 py-2 rounded-full text-sm font-bold transition-all ${
                activeTab === tab
                  ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/20'
                  : 'bg-[#1C1C1E] text-gray-400 border border-white/5 hover:bg-[#2C2C2E]'
              }`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {t(tab)}
            </motion.button>
          ))}
          
          {/* 刷新按鈕 */}
          <motion.button
            onClick={() => {
              refetch()
              playSound('click')
            }}
            className="ml-auto px-3 py-2 rounded-full bg-[#1C1C1E] text-gray-400 border border-white/5 hover:bg-[#2C2C2E]"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <RefreshCw size={16} />
          </motion.button>
        </div>

        {/* 空狀態 */}
        {filteredPackets.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
            <Gift size={48} className="mb-4 opacity-50" />
            <p>暫無紅包</p>
            <p className="text-sm mt-2">發送一個紅包試試吧！</p>
          </div>
        )}

        {/* 紅包列表 */}
        <div className="flex-1 space-y-3">
          <AnimatePresence>
            {filteredPackets.map((packet, index) => {
              const style = typeConfig[packet.type] || typeConfig.ordinary
              const TypeIcon = packet.isBomb ? Bomb : style.icon
              const progressPercent = Math.max(0, (packet.remainingQuantity / packet.totalQuantity) * 100)
              const isGrabbed = packet.remainingQuantity <= 0 || packet.status !== 'active'

              return (
                <motion.div
                  key={packet.id}
                  layout
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ delay: index * 0.05 }}
                  className={`relative w-full p-3 bg-[#1C1C1E] border border-white/5 rounded-xl shadow-lg flex items-start justify-between overflow-hidden group shrink-0 transition-all duration-500 ${
                    packet.isBomb ? 'border-red-500/30' : ''
                  }`}
                >
                  {/* 頂部漸變線 */}
                  <div className={`absolute top-0 left-0 w-full h-1 ${
                    packet.isBomb 
                      ? 'bg-gradient-to-r from-red-500 to-orange-500' 
                      : 'bg-gradient-to-r from-orange-500 to-red-500'
                  } opacity-20`} />

                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {/* 頭像 */}
                    <div className="shrink-0 self-center">
                      <div className="w-10 h-10 rounded-full overflow-hidden border-2 border-white/10">
                        <img
                          src={packet.senderAvatar}
                          alt={packet.senderName}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    </div>

                    {/* 信息 */}
                    <div className="flex flex-col min-w-0 w-full">
                      <span className="text-white font-bold text-sm truncate flex items-center gap-1.5">
                        {packet.senderName}
                        <span
                          className={`text-xs px-1.5 py-0.5 rounded border font-normal ${
                            packet.senderLevel >= 50
                              ? 'border-yellow-500/50 text-yellow-500'
                              : packet.senderLevel >= 10
                              ? 'border-purple-500/50 text-purple-500'
                              : 'border-cyan-500/50 text-cyan-400'
                          }`}
                        >
                          Lv.{packet.senderLevel}
                        </span>
                        {/* 炸彈標識 */}
                        {packet.isBomb && (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30">
                            💣
                          </span>
                        )}
                        {/* 游戏图标 */}
                        {packet.isFromGameGroup && (
                          <div className="flex items-center gap-1" title={t('game_group_packet')}>
                            <Gamepad2 size={14} className="text-purple-400" />
                          </div>
                        )}
                      </span>

                      <span className="text-gray-400 text-xs mt-1 truncate">{packet.message}</span>

                      {/* 金額和剩餘 */}
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-orange-400 text-xs font-bold">
                          {packet.amount} {packet.currency}
                        </span>
                        <span className="text-gray-500 text-xs">
                          {packet.remainingQuantity}/{packet.totalQuantity} 份
                        </span>
                      </div>

                      {/* 進度條 */}
                      <div className="w-24 h-1 bg-gray-700 rounded-full mt-1.5 overflow-hidden shrink-0">
                        <motion.div
                          className={`h-full rounded-full ${packet.isBomb ? 'bg-red-500' : 'bg-orange-500'}`}
                          initial={{ width: 0 }}
                          animate={{ width: `${progressPercent}%` }}
                          transition={{ duration: 0.8, ease: "easeOut" }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* 操作按鈕 */}
                  <div className="flex flex-col items-end gap-1 ml-2 shrink-0 self-center">
                    {/* 分享和類型標籤 */}
                    <div className="flex items-center gap-2 mb-0.5">
                      <button
                        onClick={(e) => handleShare(e, packet)}
                        className={`w-6 h-6 flex items-center justify-center rounded-full transition-colors active:scale-90 ${
                          isCopied === packet.id
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-white/5 hover:bg-white/10 text-gray-500 hover:text-white'
                        }`}
                        title={t('share_packet')}
                      >
                        <AnimatePresence mode="wait">
                          {isCopied === packet.id ? (
                            <motion.div
                              key="check"
                              initial={{ scale: 0 }}
                              animate={{ scale: 1 }}
                              exit={{ scale: 0 }}
                            >
                              <Check size={12} />
                            </motion.div>
                          ) : (
                            <motion.div
                              key="share"
                              initial={{ scale: 0 }}
                              animate={{ scale: 1 }}
                              exit={{ scale: 0 }}
                            >
                              <Share2 size={12} />
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </button>

                      <div className={`w-[90px] h-7 rounded-lg bg-black/40 border flex items-center justify-center gap-1.5 backdrop-blur-sm shadow-inner px-2 ${
                        packet.isBomb ? 'border-red-500/30' : 'border-white/5'
                      }`}>
                        <TypeIcon size={12} className={packet.isBomb ? 'text-red-400' : style.color} />
                        <span className={`text-xs font-bold ${packet.isBomb ? 'text-red-400' : style.color}`}>
                          {packet.isBomb ? '炸彈' : t(style.labelKey)}
                        </span>
                      </div>
                    </div>

                    {/* 領取按鈕 */}
                    <button
                      onClick={(e) => handleGrab(e, packet)}
                      disabled={loadingId === packet.id || isGrabbed}
                      className={`
                        text-sm font-bold py-2 px-4 rounded-lg shadow-lg transform transition-all flex items-center justify-center w-[90px]
                        ${
                          isGrabbed
                            ? 'bg-[#2C2C2E] text-gray-500 cursor-not-allowed border border-white/5'
                            : packet.isBomb
                            ? 'bg-gradient-to-r from-red-600 to-orange-500 hover:from-red-500 hover:to-orange-400 text-white active:scale-95 shadow-red-900/20'
                            : 'bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-400 hover:to-red-400 text-white active:scale-95 shadow-orange-900/20'
                        }
                      `}
                    >
                      {loadingId === packet.id ? (
                        <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      ) : isGrabbed ? (
                        packet.status === 'expired' ? t('expired') : t('grabbed')
                      ) : (
                        t('grab')
                      )}
                    </button>
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>
        </div>
      </div>

      {/* 領取結果彈窗 */}
      {selectedPacket && (
        <ResultModal
          isOpen={showResultModal}
          onClose={() => {
            setShowResultModal(false)
            setSelectedPacket(null)
          }}
          amount={claimAmount}
          currency={selectedPacket.currency}
          senderName={selectedPacket.senderName}
          senderLevel={selectedPacket.senderLevel}
          message={claimMessage || selectedPacket.message}
          senderAvatar={selectedPacket.senderAvatar}
        />
      )}
    </PageTransition>
  )
}
