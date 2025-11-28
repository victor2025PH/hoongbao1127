import { useState, useEffect } from 'react'
import { Bell, Volume2, VolumeX, Globe, ChevronDown } from 'lucide-react'
import { motion } from 'framer-motion'
import { useTranslation } from '../providers/I18nProvider'
import { useGlobalAudio, useSound } from '../hooks/useSound'
import { useQuery } from '@tanstack/react-query'
import { getUnreadCount } from '../utils/api'
import TelegramStar from './TelegramStar'
import MessagesPanel from './MessagesPanel'

export default function TopToolbar() {
  const { t, language, setLanguage } = useTranslation()
  const { isMuted, toggleMute } = useGlobalAudio()
  const { playSound } = useSound()
  const [showLangMenu, setShowLangMenu] = useState(false)
  const [showMessagesPanel, setShowMessagesPanel] = useState(false)
  
  // 獲取未讀消息數量
  const { data: unreadData } = useQuery({
    queryKey: ['unread-count'],
    queryFn: getUnreadCount,
    refetchInterval: 30000, // 每 30 秒刷新一次
  })
  
  const unreadCount = unreadData?.unread_count || 0
  const hasNotification = unreadCount > 0

  const langLabel = {
    'zh-TW': '繁',
    'zh-CN': '简',
    'en': 'EN',
  }[language]

  return (
    <div className="relative z-50 flex items-center justify-between px-4 py-2 bg-gradient-to-b from-brand-dark/80 to-transparent backdrop-blur-sm border-b border-white/5">
      {/* 左側：通知和音效 */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => { playSound('notification'); }}
          className="relative p-1.5 rounded-full bg-[#1C1C1E] border border-white/5 hover:bg-[#2C2C2E] transition-colors active:scale-95"
          title={t('notifications')}
        >
          <motion.div
            animate={hasNotification ? { rotate: [0, -15, 15, -15, 15, 0] } : {}}
            transition={{ duration: 1.5, repeat: hasNotification ? Infinity : 0, repeatDelay: 1 }}
          >
            <Bell size={18} className={hasNotification ? 'text-white' : 'text-gray-400'} />
          </motion.div>
          {hasNotification && (
            <span className="absolute top-1.5 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-[#1C1C1E] animate-pulse" />
          )}
        </button>
        
        <button
          className="p-1.5 rounded-full bg-[#1C1C1E] border border-white/5 hover:bg-[#2C2C2E] transition-colors active:scale-95 group"
          onClick={() => { toggleMute(); playSound('click'); }}
          title={t('sound')}
        >
          {isMuted ? (
            <VolumeX size={18} className="text-gray-500 group-hover:text-red-400" />
          ) : (
            <Volume2 size={18} className="text-gray-400 group-hover:text-green-400" />
          )}
        </button>

        <div className="relative">
          <button
            className="flex items-center gap-1.5 h-9 px-3 rounded-full bg-[#1C1C1E] border border-white/5 hover:bg-[#2C2C2E] transition-colors active:scale-95 group"
            onClick={() => { setShowLangMenu(!showLangMenu); playSound('click'); }}
            title={t('language')}
          >
            <Globe size={16} className="text-gray-400 group-hover:text-white" />
            <span className="text-xs font-bold text-gray-500 group-hover:text-white">{langLabel}</span>
            <ChevronDown size={12} className={`text-gray-400 transition-transform ${showLangMenu ? 'rotate-180' : ''}`} />
          </button>

          {showLangMenu && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute right-0 mt-2 w-32 bg-[#1C1C1E] rounded-lg shadow-xl overflow-hidden border border-white/10"
            >
              <button
                className="block w-full px-4 py-2 text-left text-sm text-gray-200 hover:bg-white/10"
                onClick={() => { setLanguage('zh-TW'); setShowLangMenu(false); playSound('click'); }}
              >
                繁體中文
              </button>
              <button
                className="block w-full px-4 py-2 text-left text-sm text-gray-200 hover:bg-white/10"
                onClick={() => { setLanguage('zh-CN'); setShowLangMenu(false); playSound('click'); }}
              >
                简体中文
              </button>
              <button
                className="block w-full px-4 py-2 text-left text-sm text-gray-200 hover:bg-white/10"
                onClick={() => { setLanguage('en'); setShowLangMenu(false); playSound('click'); }}
              >
                English
              </button>
            </motion.div>
          )}
        </div>
      </div>

      {/* 右側：星星（消息中心） */}
      <div className="relative">
        <button
          onClick={() => {
            playSound('pop')
            setShowMessagesPanel(!showMessagesPanel)
          }}
          className="relative group cursor-pointer flex items-center gap-2"
        >
          <div className="relative">
            <TelegramStar size={32} withSpray={true} />
            <div className="absolute inset-0 bg-yellow-500/20 blur-md rounded-full pointer-events-none group-hover:bg-yellow-500/40 transition-colors" />
            
            {/* 未讀消息徽章 */}
            {unreadCount > 0 && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -left-2 -top-1 min-w-[20px] h-5 px-1.5 bg-red-500 rounded-full border-2 border-brand-dark flex items-center justify-center"
              >
                <span className="text-xs font-bold text-white">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              </motion.div>
            )}
            
            {/* 小紅點提示 */}
            {unreadCount > 0 && (
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="absolute top-0 right-0 w-3 h-3 bg-red-500 rounded-full border-2 border-brand-dark"
              />
            )}
          </div>
          
          {/* 提示文字 */}
          <motion.span
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-xs text-gray-400 whitespace-nowrap group-hover:text-white transition-colors"
          >
            {showMessagesPanel ? '關閉消息' : '打開消息'}
          </motion.span>
        </button>
      </div>

      {/* 消息面板 */}
      <MessagesPanel
        isOpen={showMessagesPanel}
        onClose={() => setShowMessagesPanel(false)}
      />
    </div>
  )
}
