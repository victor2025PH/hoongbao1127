import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Box, Sparkles, Crown, Share2, Check, Gift, Gamepad2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import confetti from 'canvas-confetti'
import { useTranslation } from '../providers/I18nProvider'
import { listRedPackets } from '../utils/api'
import { useSound } from '../hooks/useSound'
import { MOCK_RED_PACKETS, type MockRedPacket } from '../utils/mockData'
import ResultModal from '../components/ResultModal'
import TelegramStar from '../components/TelegramStar'
import PageTransition from '../components/PageTransition'

export default function PacketsPage() {
  const { t } = useTranslation()
  const { playSound } = useSound()
  const [activeTab, setActiveTab] = useState<'all' | 'crypto' | 'points'>('all')
  const [selectedPacket, setSelectedPacket] = useState<MockRedPacket | null>(null)
  const [showResultModal, setShowResultModal] = useState(false)
  const [claimAmount, setClaimAmount] = useState(0)
  const [loadingId, setLoadingId] = useState<string | null>(null)
  const [isCopied, setIsCopied] = useState<string | null>(null)

  // 使用模擬數據
  const packets = MOCK_RED_PACKETS

  const filteredPackets = packets.filter((packet) => {
    if (activeTab === 'all') return true
    if (activeTab === 'crypto') return packet.currency === 'USDT' || packet.currency === 'TON'
    if (activeTab === 'points') return packet.currency === 'Stars'
    return true
  })

  const typeConfig = {
    ordinary: {
      label: 'Ordinary',
      color: 'text-cyan-400',
      icon: Box,
    },
    lucky: {
      label: 'Lucky',
      color: 'text-purple-400',
      icon: TelegramStar,
    },
    exclusive: {
      label: 'Exclusive',
      color: 'text-yellow-400',
      icon: Crown,
    },
  }

  const handleShare = async (e: React.MouseEvent, packet: MockRedPacket) => {
    e.stopPropagation()
    playSound('click')
    
    const shareData = {
      title: '搶紅包',
      text: `🎁 搶 ${packet.senderName} 的紅包！"${packet.message}"`,
      url: window.location.origin,
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

  const handleGrab = (e: React.MouseEvent, packet: MockRedPacket) => {
    if (packet.remainingQuantity <= 0) return

    e.stopPropagation()
    setLoadingId(packet.id)
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

    // 模擬領取過程
    setTimeout(() => {
      const randomAmount = Math.random() * (packet.amount / packet.totalQuantity) + 0.1
      setClaimAmount(randomAmount)
      setSelectedPacket(packet)
      setShowResultModal(true)
      setLoadingId(null)

      // 領取成功時再次噴花
      setTimeout(() => {
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
      }, 100)
    }, 1000)
  }

  return (
    <PageTransition>
      <div className="h-full flex flex-col p-3 pb-24 gap-3 overflow-y-auto scrollbar-hide">
        {/* 標籤切換 */}
        <div className="flex gap-2 shrink-0">
          {(['all', 'crypto', 'points'] as const).map((tab, i) => (
            <motion.button
              key={tab}
              onClick={() => {
                setActiveTab(tab)
                playSound('click')
              }}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
                activeTab === tab
                  ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/20'
                  : 'bg-[#1C1C1E] text-gray-400 border border-white/5 hover:bg-[#2C2C2E]'
              }`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {tab === 'all' ? '全部' : tab === 'crypto' ? '加密貨幣' : '積分'}
            </motion.button>
          ))}
        </div>

        {/* 紅包列表 */}
        <div className="flex-1 space-y-3">
          <AnimatePresence>
            {filteredPackets.map((packet, index) => {
              const style = typeConfig[packet.type] || typeConfig.ordinary
              const TypeIcon = style.icon
              const progressPercent = Math.max(0, (packet.remainingQuantity / packet.totalQuantity) * 100)
              const isGrabbed = packet.remainingQuantity <= 0

              return (
                <motion.div
                  key={packet.id}
                  layout
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ delay: index * 0.1 }}
                  className="relative w-full p-3 bg-[#1C1C1E] border border-white/5 rounded-xl shadow-lg flex items-start justify-between overflow-hidden group shrink-0 transition-all duration-500"
                >
                  {/* 頂部漸變線 */}
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-orange-500 to-red-500 opacity-20" />

                  {/* 遊戲群標籤 */}
                  {packet.isFromGameGroup && (
                    <div className="absolute top-2 right-2 flex items-center gap-1 bg-purple-500/20 border border-purple-500/30 px-2 py-0.5 rounded-full">
                      <Gamepad2 size={10} className="text-purple-400" />
                      <span className="text-[8px] text-purple-300 font-bold">{packet.chatTitle}</span>
                    </div>
                  )}

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
                      <span className="text-white font-bold text-xs truncate flex items-center gap-1">
                        {packet.senderName}
                        <span
                          className={`text-[9px] px-1 rounded border font-normal ${
                            packet.senderLevel >= 50
                              ? 'border-yellow-500/50 text-yellow-500'
                              : packet.senderLevel >= 10
                              ? 'border-purple-500/50 text-purple-500'
                              : 'border-cyan-500/50 text-cyan-400'
                          }`}
                        >
                          Lv.{packet.senderLevel}
                        </span>
                      </span>

                      <span className="text-gray-400 text-[10px] mt-0.5 truncate">{packet.message}</span>

                      {/* 進度條 */}
                      <div className="w-20 h-1 bg-gray-700 rounded-full mt-1.5 overflow-hidden shrink-0">
                        <motion.div
                          className="h-full bg-orange-500 rounded-full"
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
                        title="分享紅包"
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

                      <div className="w-[80px] h-6 rounded-lg bg-black/40 border border-white/5 flex items-center justify-center gap-1.5 backdrop-blur-sm shadow-inner">
                        <TypeIcon size={11} className={style.color} />
                        <span className={`text-[10px] font-bold ${style.color}`}>{style.label}</span>
                      </div>
                    </div>

                    {/* 領取按鈕 */}
                    <button
                      onClick={(e) => handleGrab(e, packet)}
                      disabled={loadingId === packet.id || isGrabbed}
                      className={`
                        text-xs font-bold py-1.5 px-4 rounded-lg shadow-lg transform transition-all flex items-center justify-center w-[80px]
                        ${
                          isGrabbed
                            ? 'bg-[#2C2C2E] text-gray-500 cursor-not-allowed border border-white/5'
                            : 'bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-400 hover:to-red-400 text-white active:scale-95 shadow-orange-900/20'
                        }
                      `}
                    >
                      {loadingId === packet.id ? (
                        <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      ) : isGrabbed ? (
                        '已領完'
                      ) : (
                        '領取'
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
          message={selectedPacket.message}
          senderAvatar={selectedPacket.senderAvatar}
        />
      )}
    </PageTransition>
  )
}
