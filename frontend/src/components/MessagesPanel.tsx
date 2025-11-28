/**
 * 消息面板組件（居中彈窗）
 */
import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Trash2, Reply, CheckCircle, Circle, Clock, MessageSquare, Bell, Info, Sparkles } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { getMessages, markMessageAsRead, deleteMessage, replyMessage, Message } from '../utils/api'
import { showAlert, showConfirm } from '../utils/telegram'
import { useSound } from '../hooks/useSound'

interface MessagesPanelProps {
  isOpen: boolean
  onClose: () => void
}

// 消息類型圖標組件映射
const messageTypeIconComponents: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  system: Bell,
  redpacket: Sparkles,
  balance: Circle,
  activity: Sparkles,
  miniapp: MessageSquare,
  telegram: MessageSquare,
  bot: MessageSquare,
}

const messageTypeIcons: Record<string, string> = {
  system: '🔔',
  redpacket: '🧧',
  balance: '💰',
  activity: '🎉',
  miniapp: '📱',
  telegram: '✉️',
  bot: '🤖',
}

const messageTypeColors: Record<string, string> = {
  system: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
  redpacket: 'text-red-400 bg-red-500/10 border-red-500/30',
  balance: 'text-green-400 bg-green-500/10 border-green-500/30',
  activity: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
  miniapp: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
  telegram: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
  bot: 'text-gray-400 bg-gray-500/10 border-gray-500/30',
}

export default function MessagesPanel({ isOpen, onClose }: MessagesPanelProps) {
  const { playSound } = useSound()
  const queryClient = useQueryClient()
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null)
  const [replyContent, setReplyContent] = useState('')
  const [showReplyInput, setShowReplyInput] = useState(false)

  // 獲取消息列表
  const { data: messagesData, isLoading } = useQuery({
    queryKey: ['messages'],
    queryFn: () => getMessages({ limit: 50 }),
    enabled: isOpen,
    refetchInterval: 30000, // 每 30 秒刷新一次
  })

  // 標記已讀
  const markReadMutation = useMutation({
    mutationFn: markMessageAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages'] })
      queryClient.invalidateQueries({ queryKey: ['unread-count'] })
    },
  })

  // 刪除消息
  const deleteMutation = useMutation({
    mutationFn: deleteMessage,
    onSuccess: () => {
      playSound('success')
      showAlert('消息已刪除', 'success')
      queryClient.invalidateQueries({ queryKey: ['messages'] })
      queryClient.invalidateQueries({ queryKey: ['unread-count'] })
      setSelectedMessage(null)
    },
    onError: (error: Error) => {
      playSound('error')
      showAlert(error.message || '刪除失敗', 'error')
    },
  })

  // 回復消息
  const replyMutation = useMutation({
    mutationFn: ({ messageId, content }: { messageId: number; content: string }) =>
      replyMessage(messageId, content),
    onSuccess: () => {
      playSound('success')
      showAlert('回復成功', 'success')
      setReplyContent('')
      setShowReplyInput(false)
      queryClient.invalidateQueries({ queryKey: ['messages'] })
    },
    onError: (error: Error) => {
      playSound('error')
      showAlert(error.message || '回復失敗', 'error')
    },
  })

  const handleMessageClick = async (message: Message) => {
    setSelectedMessage(message)
    playSound('click')
    
    // 如果未讀，標記為已讀
    if (message.status === 'unread') {
      markReadMutation.mutate(message.id)
    }
  }

  const handleDelete = async (message: Message) => {
    const confirmed = await showConfirm(
      '確定要刪除這條消息嗎？',
      '刪除消息',
      '刪除',
      '取消'
    )
    if (confirmed) {
      deleteMutation.mutate(message.id)
    }
  }

  const handleReply = () => {
    if (!selectedMessage || !replyContent.trim()) {
      showAlert('請輸入回復內容', 'warning')
      return
    }
    replyMutation.mutate({ messageId: selectedMessage.id, content: replyContent })
  }

  const handleActionClick = (actionUrl?: string) => {
    if (actionUrl) {
      if (actionUrl.startsWith('http')) {
        window.open(actionUrl, '_blank')
      } else {
        // 內部路由
        window.location.href = actionUrl
      }
    }
  }

  if (!isOpen) return null

  const messages = messagesData?.messages || []
  const unreadCount = messagesData?.unread_count || 0

  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <div className="fixed top-16 left-1/2 -translate-x-1/2 z-[40] pointer-events-none w-full max-w-md px-4" style={{ maxHeight: 'calc(100vh - 5rem)' }}>
          {/* 消息面板 - 在屏幕左右居中，炫酷動畫 */}
          <motion.div
            initial={{ 
              scale: 0.9, 
              opacity: 0, 
              y: -20
            }}
            animate={{ 
              scale: 1, 
              opacity: 1, 
              y: 0
            }}
            exit={{ 
              scale: 0.9, 
              opacity: 0, 
              y: -20
            }}
            transition={{ 
              type: "spring", 
              damping: 25, 
              stiffness: 300,
              mass: 0.8
            }}
            className="relative w-full h-[80vh] max-h-[700px] bg-gradient-to-br from-brand-dark via-[#0a0a15] to-[#050508] border border-white/30 rounded-3xl shadow-2xl pointer-events-auto flex flex-col overflow-hidden backdrop-blur-xl"
            style={{
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5), 0 0 100px rgba(59, 130, 246, 0.1), inset 0 0 60px rgba(147, 51, 234, 0.05)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
          {/* 標題欄 - 美化，帶動畫 */}
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="relative p-6 border-b border-white/20 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20 overflow-hidden"
          >
            {/* 背景動畫效果 */}
            <motion.div
              animate={{
                backgroundPosition: ['0% 0%', '100% 100%'],
              }}
              transition={{
                duration: 10,
                repeat: Infinity,
                repeatType: 'reverse',
              }}
              className="absolute inset-0 opacity-30"
              style={{
                background: 'linear-gradient(45deg, rgba(59, 130, 246, 0.1), rgba(147, 51, 234, 0.1), rgba(236, 72, 153, 0.1))',
                backgroundSize: '200% 200%',
              }}
            />
            
            <div className="relative flex items-center justify-between z-10">
              <div className="flex items-center gap-4">
                <motion.div 
                  whileHover={{ scale: 1.1, rotate: 5 }}
                  whileTap={{ scale: 0.95 }}
                  className="p-3 rounded-2xl bg-gradient-to-br from-blue-500/30 to-purple-500/30 border border-blue-500/40 shadow-lg shadow-blue-500/20"
                >
                  <MessageSquare size={26} className="text-blue-300" />
                </motion.div>
                <div>
                  <motion.h2 
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                    className="text-2xl font-bold text-white flex items-center gap-2"
                  >
                    我的消息
                    {unreadCount > 0 && (
                      <motion.span
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 500 }}
                        className="px-2.5 py-1 text-xs font-bold bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-full shadow-lg shadow-red-500/50"
                      >
                        {unreadCount > 99 ? '99+' : unreadCount}
                      </motion.span>
                    )}
                  </motion.h2>
                  <motion.p 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="text-sm text-gray-300 mt-1"
                  >
                    查看和管理您的所有消息
                  </motion.p>
                </div>
              </div>
              <motion.button
                whileHover={{ scale: 1.1, rotate: 90 }}
                whileTap={{ scale: 0.9 }}
                onClick={onClose}
                className="relative p-3 rounded-xl bg-white/10 hover:bg-red-500/20 border border-white/20 hover:border-red-500/40 transition-all group backdrop-blur-sm"
                title="關閉"
              >
                <X size={22} className="text-gray-300 group-hover:text-red-400 transition-colors" />
                <motion.div
                  className="absolute inset-0 rounded-xl bg-red-500/20"
                  initial={{ scale: 0, opacity: 0 }}
                  whileHover={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.2 }}
                />
              </motion.button>
            </div>
            
            {/* 功能說明 - 帶動畫 */}
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="mt-4 flex flex-wrap items-center gap-3 text-xs text-gray-300"
            >
              <motion.div 
                whileHover={{ scale: 1.05 }}
                className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/5 border border-white/10"
              >
                <Info size={14} className="text-blue-400" />
                <span>點擊消息查看詳情</span>
              </motion.div>
              <motion.div 
                whileHover={{ scale: 1.05 }}
                className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/5 border border-white/10"
              >
                <Trash2 size={14} className="text-red-400" />
                <span>點擊詳情頁刪除</span>
              </motion.div>
              {messages.some(m => m.can_reply) && (
                <motion.div 
                  whileHover={{ scale: 1.05 }}
                  className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/5 border border-white/10"
                >
                  <Reply size={14} className="text-green-400" />
                  <span>部分消息支持回復</span>
                </motion.div>
              )}
            </motion.div>
          </motion.div>

          {/* 消息列表 - 炫酷動畫 */}
          <div className="flex-1 overflow-y-auto p-6 space-y-3 custom-scrollbar">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center h-full gap-4">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                  className="relative w-16 h-16"
                >
                  <div className="absolute inset-0 border-4 border-blue-500/20 border-t-blue-500 rounded-full" />
                  <div className="absolute inset-0 border-4 border-purple-500/20 border-r-purple-500 rounded-full animate-spin" style={{ animationDuration: '2s' }} />
                </motion.div>
                <motion.p
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="text-gray-400"
                >
                  加載中...
                </motion.p>
              </div>
            ) : messages.length === 0 ? (
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
                className="flex flex-col items-center justify-center h-full gap-6"
              >
                <motion.div
                  animate={{ 
                    scale: [1, 1.1, 1],
                    rotate: [0, 5, -5, 0]
                  }}
                  transition={{ 
                    duration: 3,
                    repeat: Infinity,
                    repeatType: 'reverse'
                  }}
                  className="relative"
                >
                  <div className="text-7xl mb-4 filter drop-shadow-lg">📭</div>
                  <motion.div
                    animate={{ 
                      scale: [1, 1.5, 1],
                      opacity: [0.5, 1, 0.5]
                    }}
                    transition={{ 
                      duration: 2,
                      repeat: Infinity
                    }}
                    className="absolute -top-2 -right-2 w-5 h-5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full shadow-lg shadow-blue-500/50"
                  />
                </motion.div>
                <div className="text-center space-y-2">
                  <motion.h3 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent"
                  >
                    暫無消息
                  </motion.h3>
                  <motion.p 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.4 }}
                    className="text-sm text-gray-400"
                  >
                    當您收到新消息時，它們會顯示在這裡
                  </motion.p>
                </div>
              </motion.div>
            ) : (
              messages.map((message, index) => {
                const IconComponent = messageTypeIconComponents[message.message_type] || MessageSquare
                const isSelected = selectedMessage?.id === message.id
                return (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, x: -30, scale: 0.95 }}
                    animate={{ opacity: 1, x: 0, scale: 1 }}
                    exit={{ opacity: 0, x: 30, scale: 0.95 }}
                    transition={{ 
                      delay: index * 0.05,
                      type: "spring",
                      stiffness: 300,
                      damping: 25
                    }}
                    whileHover={{ 
                      scale: 1.02,
                      y: -2,
                      transition: { duration: 0.2 }
                    }}
                    whileTap={{ scale: 0.98 }}
                    className={`group relative p-4 rounded-2xl border cursor-pointer transition-all duration-300 overflow-hidden ${
                      isSelected
                        ? 'bg-gradient-to-r from-blue-500/30 to-purple-500/30 border-blue-500/60 shadow-2xl shadow-blue-500/30'
                        : 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/30 hover:shadow-xl'
                    } ${messageTypeColors[message.message_type] || messageTypeColors.system}`}
                    onClick={() => handleMessageClick(message)}
                  >
                    {/* 背景光效動畫 */}
                    {isSelected && (
                      <motion.div
                        animate={{
                          backgroundPosition: ['0% 0%', '100% 100%'],
                        }}
                        transition={{
                          duration: 3,
                          repeat: Infinity,
                          repeatType: 'reverse',
                        }}
                        className="absolute inset-0 opacity-20"
                        style={{
                          background: 'linear-gradient(45deg, rgba(59, 130, 246, 0.3), rgba(147, 51, 234, 0.3))',
                          backgroundSize: '200% 200%',
                        }}
                      />
                    )}
                    <div className="relative flex items-start gap-4 z-10">
                      {/* 消息類型圖標 - 美化，帶動畫 */}
                      <motion.div 
                        whileHover={{ scale: 1.1, rotate: 5 }}
                        className={`relative p-3 rounded-xl ${
                          message.status === 'unread' 
                            ? 'bg-gradient-to-br from-blue-500/30 to-purple-500/30 border border-blue-500/50 shadow-lg shadow-blue-500/20' 
                            : 'bg-white/5 border border-white/10'
                        }`}
                      >
                        <IconComponent size={20} className={
                          message.status === 'unread' ? 'text-blue-300' : 'text-gray-400'
                        } />
                        {message.status === 'unread' && (
                          <motion.div
                            animate={{ 
                              scale: [1, 1.3, 1],
                              opacity: [1, 0.7, 1]
                            }}
                            transition={{ 
                              duration: 1.5,
                              repeat: Infinity
                            }}
                            className="absolute -top-1 -right-1 w-3 h-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full border-2 border-brand-dark shadow-lg shadow-blue-500/50"
                          />
                        )}
                      </motion.div>

                      {/* 消息內容 */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-semibold text-white truncate flex-1">
                            {message.title || '無標題'}
                          </h3>
                          <span className="text-xs text-gray-400 whitespace-nowrap">
                            {new Date(message.created_at).toLocaleDateString('zh-TW', {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </div>
                        <p className="text-sm text-gray-300 line-clamp-2 leading-relaxed">
                          {message.content}
                        </p>
                        {message.source_name && (
                          <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
                            <span>來自</span>
                            <span className="px-2 py-0.5 bg-white/5 rounded-md">
                              {message.source_name}
                            </span>
                          </div>
                        )}
                        {message.status === 'unread' && (
                          <div className="mt-2 flex items-center gap-1 text-xs text-blue-400">
                            <Circle size={8} className="fill-blue-400" />
                            <span>未讀</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )
              })
            )}
          </div>

          {/* 消息詳情（底部） - 美化，炫酷動畫 */}
          <AnimatePresence>
            {selectedMessage && (
              <motion.div
                initial={{ height: 0, opacity: 0, y: 20 }}
                animate={{ height: 'auto', opacity: 1, y: 0 }}
                exit={{ height: 0, opacity: 0, y: 20 }}
                transition={{ 
                  type: "spring",
                  damping: 25,
                  stiffness: 300
                }}
                className="border-t border-white/20 bg-gradient-to-t from-brand-dark via-[#0a0a15] to-transparent p-6 space-y-4 backdrop-blur-sm"
              >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-bold text-white">
                      {selectedMessage.title || '無標題'}
                    </h3>
                    {selectedMessage.status === 'unread' && (
                      <span className="px-2 py-0.5 text-xs font-medium bg-blue-500/20 text-blue-400 rounded-full border border-blue-500/30">
                        未讀
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-400 mb-3">
                    <span>
                      {new Date(selectedMessage.created_at).toLocaleString('zh-TW', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                    {selectedMessage.source_name && (
                      <>
                        <span>•</span>
                        <span>來自: {selectedMessage.source_name}</span>
                      </>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {selectedMessage.can_reply && (
                    <button
                      onClick={() => setShowReplyInput(!showReplyInput)}
                      className="p-2.5 rounded-xl hover:bg-blue-500/20 transition-all active:scale-95 group"
                      title="回復消息"
                    >
                      <Reply size={18} className="text-gray-400 group-hover:text-blue-400 transition-colors" />
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(selectedMessage)}
                    className="p-2.5 rounded-xl hover:bg-red-500/20 transition-all active:scale-95 group"
                    title="刪除消息"
                  >
                    <Trash2 size={18} className="text-gray-400 group-hover:text-red-400 transition-colors" />
                  </button>
                </div>
              </div>
              
              <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                <p className="text-sm text-gray-200 whitespace-pre-line leading-relaxed">
                  {selectedMessage.content}
                </p>
              </div>
              
              {selectedMessage.action_url && (
                <button
                  onClick={() => handleActionClick(selectedMessage.action_url)}
                  className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 rounded-xl text-white font-medium transition-all shadow-lg shadow-blue-500/20 active:scale-95"
                >
                  查看詳情 →
                </button>
              )}

              {/* 回復輸入框 - 美化 */}
              {showReplyInput && selectedMessage.can_reply && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-3 p-4 rounded-xl bg-white/5 border border-white/10"
                >
                  <div className="flex items-center gap-2 text-sm text-gray-300">
                    <Reply size={16} />
                    <span>回復消息</span>
                  </div>
                  <textarea
                    value={replyContent}
                    onChange={(e) => setReplyContent(e.target.value)}
                    placeholder="輸入回復內容..."
                    className="w-full p-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 resize-none focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                    rows={4}
                  />
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleReply}
                      disabled={!replyContent.trim() || replyMutation.isPending}
                      className="flex-1 py-2.5 px-4 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:from-gray-600 disabled:to-gray-600 disabled:cursor-not-allowed rounded-xl text-white font-medium transition-all shadow-lg shadow-blue-500/20 active:scale-95"
                    >
                      {replyMutation.isPending ? (
                        <span className="flex items-center justify-center gap-2">
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                            className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                          />
                          發送中...
                        </span>
                      ) : (
                        '發送回復'
                      )}
                    </button>
                    <button
                      onClick={() => {
                        setShowReplyInput(false)
                        setReplyContent('')
                      }}
                      className="py-2.5 px-4 bg-gray-600/50 hover:bg-gray-600 rounded-xl text-white font-medium transition-all active:scale-95"
                    >
                      取消
                    </button>
                  </div>
                </motion.div>
              )}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}

