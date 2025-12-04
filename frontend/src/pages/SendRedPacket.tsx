import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronDown, X, Users, Wallet, Gift, DollarSign, MessageSquare, Info, Bomb, Search, User, CheckCircle, XCircle, Bot, RefreshCw, Trash2 } from 'lucide-react'
import { useTranslation } from '../providers/I18nProvider'
import TelegramStar from '../components/TelegramStar'
import { getUserChats, sendRedPacket, searchChats, searchUsers, checkUserInChat, type ChatInfo } from '../utils/api'
import { haptic, showAlert, showConfirm, getTelegramUser } from '../utils/telegram'

export default function SendRedPacket() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const [selectedChat, setSelectedChat] = useState<ChatInfo | null>(null)
  const [showChatModal, setShowChatModal] = useState(false)
  const [showRulesModal, setShowRulesModal] = useState(false)
  const [dontShowAgain, setDontShowAgain] = useState(false)
  const [showCurrencyModal, setShowCurrencyModal] = useState(false)
  const [selectedCurrencyInfo, setSelectedCurrencyInfo] = useState<'USDT' | 'TON' | 'Stars' | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  
  // 獲取 Telegram 用戶 ID（用於搜索）
  // 優先從 Telegram WebApp 獲取，如果沒有則使用本地存儲的測試 ID
  const telegramUser = getTelegramUser()
  const storedTestTgId = typeof window !== 'undefined' ? localStorage.getItem('test_tg_id') : null
  const tgId = telegramUser?.id || (storedTestTgId ? parseInt(storedTestTgId, 10) : undefined)
  
  // 如果是本地測試環境且沒有用戶 ID，自動設置測試 ID
  useEffect(() => {
    if (!telegramUser && !storedTestTgId && typeof window !== 'undefined') {
      // 檢查 URL 參數中是否有測試 ID
      const urlParams = new URLSearchParams(window.location.search)
      const testTgId = urlParams.get('tg_id')
      if (testTgId) {
        localStorage.setItem('test_tg_id', testTgId)
      } else {
        // 設置默認測試 ID（用於本地開發）
        localStorage.setItem('test_tg_id', '6359371231')
      }
    }
  }, [telegramUser, storedTestTgId])

  // 每次進入頁面時檢查是否需要顯示規則彈窗
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const dontShowRules = localStorage.getItem('dont_show_game_rules')
      if (!dontShowRules) {
        // 延遲一點顯示，讓頁面先加載完成
        const timer = setTimeout(() => {
          setShowRulesModal(true)
        }, 500)
        return () => clearTimeout(timer)
      }
    }
  }, [])

  const [amount, setAmount] = useState('')
  const [quantity, setQuantity] = useState('1')
  const [currency, setCurrency] = useState('USDT')
  const [packetType, setPacketType] = useState<'random' | 'fixed'>('random')
  const [bombNumber, setBombNumber] = useState<number | null>(null)
  const [message, setMessage] = useState('')

  // 獲取群組列表
  const { data: chats } = useQuery({
    queryKey: ['chats'],
    queryFn: getUserChats,
  })

  // 統一搜索：同時搜索群組和用戶
  const { data: searchChatsResult, isLoading: isSearchingChats, error: searchChatsError } = useQuery({
    queryKey: ['searchChats', searchQuery, tgId],
    queryFn: () => {
      console.log('[Search] Searching chats:', searchQuery, 'tgId:', tgId)
      return searchChats(searchQuery, tgId || undefined)
    },
    enabled: searchQuery.length > 0,
    retry: 1,
  })

  const { data: searchUsersResult, isLoading: isSearchingUsers, error: searchUsersError } = useQuery({
    queryKey: ['searchUsers', searchQuery, tgId],
    queryFn: () => {
      console.log('[Search] Searching users:', searchQuery, 'tgId:', tgId)
      return searchUsers(searchQuery, tgId || undefined)
    },
    enabled: searchQuery.length > 0,
    retry: 1,
  })

  // 調試日誌
  useEffect(() => {
    if (searchChatsResult) {
      console.log('[Search] Chats result:', searchChatsResult)
    }
    if (searchChatsError) {
      console.error('[Search] Error searching chats:', searchChatsError)
    }
    if (searchUsersResult) {
      console.log('[Search] Users result:', searchUsersResult)
    }
    if (searchUsersError) {
      console.error('[Search] Error searching users:', searchUsersError)
    }
  }, [searchChatsResult, searchChatsError, searchUsersResult, searchUsersError])

  // 合併所有搜索結果（群組和用戶），統一顯示
  const allSearchResults = useMemo(() => {
    const results: Array<ChatInfo & { isUser?: boolean }> = []
    
    // 添加群組結果
    if (searchChatsResult && Array.isArray(searchChatsResult)) {
      searchChatsResult.forEach((chat: ChatInfo) => {
        results.push({ ...chat, isUser: false })
      })
    }
    
    // 添加用戶結果
    if (searchUsersResult && Array.isArray(searchUsersResult)) {
      searchUsersResult.forEach((user: ChatInfo) => {
        results.push({ ...user, isUser: true })
      })
    }
    
    return results
  }, [searchChatsResult, searchUsersResult])

  // 當選擇群組時，驗證用戶是否在群組中
  const handleSelectChat = async (chat: ChatInfo) => {
    try {
      haptic('light')
      
      // 如果是群組，檢查狀態
      if (chat.type !== 'private') {
        // 如果搜索結果已經包含完整的狀態信息，直接處理選擇邏輯
        if (chat.user_in_group !== undefined && chat.bot_in_group !== undefined) {
        // 如果 Bot 不在群組中，提示用戶（但不阻止選擇，可以通過鏈接發送）
        if (chat.bot_in_group === false) {
          await showAlert(
            '⚠️ 機器人不在群組中\n\n您仍然可以選擇此群組，發送紅包時會生成分享鏈接，您可以手動分享到群組中。',
            'warning'
          )
          // 不 return，繼續選擇流程
        }
          
        // 如果用戶不在群組中，提示加入
        if (chat.user_in_group === false) {
          const groupLink = chat.link
          if (groupLink) {
            const telegram = window.Telegram?.WebApp
            const shouldJoin = await showConfirm(
              '⚠️ 您尚未加入此群組\n\n是否現在加入？',
              undefined,
              '加入',
              '取消'
            )
            if (shouldJoin && telegram) {
              telegram.openLink(groupLink)
              return // 用戶選擇加入群組，取消選擇
            } else if (!shouldJoin) {
              // 用戶選擇不加入，仍然允許選擇（可能想先選擇，稍後加入）
              // 繼續選擇流程
            }
          } else {
            const shouldContinue = await showConfirm('⚠️ 您尚未加入此群組\n\n是否仍然選擇此群組？')
            if (!shouldContinue) {
              return
            }
          }
        }
          
          // 如果搜索結果已經顯示了狀態，直接選擇（不需要再次調用 API）
          setSelectedChat(chat)
          // 立即保存到歷史記錄
          saveChatToHistory(chat)
          setShowChatModal(false)
          setSearchQuery('')
          haptic('success')
          showAlert('✅ 已選擇 ' + chat.title, 'success')
          return
        }
      }
      
      // 如果狀態信息不完整，進行額外驗證
      // 驗證用戶是否在群組中（再次確認）
      try {
        const checkResult = await checkUserInChat(chat.id, chat.link, tgId)
        if (!checkResult.in_group && chat.type !== 'private') {
          const groupLink = chat.link
          if (groupLink) {
            const telegram = window.Telegram?.WebApp
            const shouldJoin = await showConfirm(
              t('join_group_first') + '\n\n' + t('open_group_link'),
              undefined,
              '加入',
              '取消'
            )
            if (shouldJoin && telegram) {
              telegram.openLink(groupLink)
            }
          } else {
            showAlert(checkResult.message || t('user_not_in_group'), 'warning')
          }
          return
        }
      } catch (checkError: any) {
        // 如果檢查失敗，但搜索結果顯示用戶在群組中，仍然允許選擇
        if (chat.user_in_group === true) {
          console.warn('檢查用戶狀態失敗，但搜索結果顯示用戶在群組中，繼續選擇:', checkError)
        } else {
          // 如果沒有狀態信息，允許選擇（可能是基於鏈接的群組）
          console.warn('檢查用戶狀態失敗，繼續選擇:', checkError)
        }
      }
      
      // 選擇成功
      setSelectedChat(chat)
      // 立即保存到歷史記錄
      saveChatToHistory(chat)
      setShowChatModal(false)
      setSearchQuery('')
      haptic('success')
      showAlert('✅ 已選擇 ' + chat.title, 'success')
    } catch (error: any) {
      haptic('error')
      console.error('選擇群組失敗:', error)
      if (error.message?.includes('not in group') || error.message?.includes('不在群組')) {
        const groupLink = chat.link
        if (groupLink) {
          const telegram = window.Telegram?.WebApp
          const shouldJoin = await showConfirm(
            t('join_group_first') + '\n\n' + t('open_group_link'),
            undefined,
            '加入',
            '取消'
          )
          if (shouldJoin && telegram) {
            telegram.openLink(groupLink)
          }
        } else {
          showAlert(t('join_group_first'), 'warning')
        }
      } else {
        const errorMessage = typeof error.message === 'string' ? error.message : String(error.message || '選擇失敗，請重試')
        showAlert(errorMessage, 'error')
      }
    }
  }

  // 保存群組到歷史記錄
  const saveChatToHistory = (chat: ChatInfo) => {
    if (typeof window === 'undefined' || !chat) {
      console.warn('[saveChatToHistory] Invalid chat or window:', { chat, hasWindow: typeof window !== 'undefined' })
      return
    }
    
    try {
      const storageKey = `redpacket_chat_history_${tgId || 'default'}`
      const historyStr = localStorage.getItem(storageKey)
      let history: Array<ChatInfo & { last_used?: string }> = historyStr ? JSON.parse(historyStr) : []
      
      // 檢查是否已存在（根據 id）
      const existingIndex = history.findIndex((c: ChatInfo) => c.id === chat.id)
      if (existingIndex >= 0) {
        // 更新現有記錄（移到最前面）
        history.splice(existingIndex, 1)
      }
      
      // 添加到最前面
      const chatWithTimestamp: ChatInfo & { last_used?: string } = {
        ...chat,
        last_used: new Date().toISOString(),
      }
      history.unshift(chatWithTimestamp)
      
      // 限制最多保存 20 條記錄
      history = history.slice(0, 20)
      
      localStorage.setItem(storageKey, JSON.stringify(history))
      console.log('[saveChatToHistory] Saved chat to history:', { chatId: chat.id, chatTitle: chat.title, historyCount: history.length })
    } catch (error) {
      console.error('[saveChatToHistory] Error saving chat history:', error)
    }
  }

  // 獲取群組歷史記錄
  const getChatHistory = (): Array<ChatInfo & { last_used?: string }> => {
    if (typeof window === 'undefined') return []
    
    try {
      const storageKey = `redpacket_chat_history_${tgId || 'default'}`
      const historyStr = localStorage.getItem(storageKey)
      const history = historyStr ? JSON.parse(historyStr) : []
      console.log('[getChatHistory] Retrieved history:', { count: history.length, tgId, storageKey })
      return history
    } catch (error) {
      console.error('[getChatHistory] Error reading chat history:', error)
      return []
    }
  }

  // 刪除群組歷史記錄
  const deleteChatFromHistory = (chatId: number) => {
    if (typeof window === 'undefined') return
    
    const storageKey = `redpacket_chat_history_${tgId || 'default'}`
    const historyStr = localStorage.getItem(storageKey)
    let history: ChatInfo[] = historyStr ? JSON.parse(historyStr) : []
    
    history = history.filter((c: ChatInfo) => c.id !== chatId)
    localStorage.setItem(storageKey, JSON.stringify(history))
  }

  // 發送紅包
  const sendMutation = useMutation({
    mutationFn: sendRedPacket,
    onSuccess: async (data: any) => {
      haptic('success')
      queryClient.invalidateQueries({ queryKey: ['balance'] })
      queryClient.invalidateQueries({ queryKey: ['redpackets'] })
      
      // 保存群組到歷史記錄
      if (selectedChat) {
        saveChatToHistory(selectedChat)
      }
      
      // 如果機器人不在群組中，顯示分享鏈接
      if (!data.message_sent && data.share_link) {
        const telegram = window.Telegram?.WebApp
        const shouldShare = await showConfirm(
          t('bot_not_in_group') + '\n\n' + t('share_red_packet_link'),
          undefined,
          '分享',
          '取消'
        )
        if (shouldShare && telegram) {
          telegram.openLink(data.share_link)
        }
      } else {
        showAlert(t('success'), 'success')
      }
      
      navigate('/packets')
    },
    onError: (error: Error) => {
      haptic('error')
      const errorMessage = typeof error.message === 'string' ? error.message : String(error.message || '發送失敗，請重試')
      showAlert(errorMessage, 'error')
    },
  })

  const handleSubmit = () => {
    if (!selectedChat) {
      showAlert(t('select_group'), 'warning')
      return
    }
    if (!amount || parseFloat(amount) <= 0) {
      showAlert(t('enter_amount'), 'warning')
      return
    }
    if (!quantity || parseInt(quantity) < 1) {
      showAlert(t('enter_quantity'), 'warning')
      return
    }
    if (packetType === 'fixed' && bombNumber === null) {
      showAlert(t('bomb_number_required'), 'warning')
      return
    }
    
    // 驗證紅包炸彈數量：必須是5個（雙雷）或10個（單雷）
    if (packetType === 'fixed') {
      const count = parseInt(quantity)
      if (count !== 5 && count !== 10) {
        showAlert('紅包炸彈數量必須是 5 個（雙雷）或 10 個（單雷）', 'warning')
        return
      }
    }

    haptic('medium')
    sendMutation.mutate({
      chat_id: selectedChat.id,
      amount: parseFloat(amount),
      currency,
      quantity: parseInt(quantity),
      type: packetType,
      message: message || t('best_wishes'),
      bomb_number: packetType === 'fixed' && bombNumber !== null && bombNumber !== undefined ? bombNumber : undefined,
    })
  }

  return (
    <div className="h-full flex flex-col bg-brand-dark overflow-hidden">
      {/* 頂部 */}
      <div className="flex items-center justify-between p-4 border-b border-white/5 shrink-0">
        <button onClick={() => navigate(-1)} className="p-2">
          <X size={24} />
        </button>
        <h1 className="text-lg font-bold">{t('send_red_packet')}</h1>
        <div className="w-10" />
      </div>

      {/* 表單 - 可滾動區域 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {/* 選擇群組 */}
        <div>
          <label className="block text-gray-300 text-base mb-2 font-medium flex items-center gap-2">
            <Users size={16} className="text-gray-400" />
            {t('select_group')}
          </label>
          <button
            type="button"
            onClick={() => setShowChatModal(true)}
            className="w-full flex items-center justify-between p-4 bg-brand-darker rounded-xl border border-white/5"
          >
            <span className={selectedChat ? 'text-white' : 'text-gray-500'}>
              {selectedChat?.title || t('click_select_group')}
            </span>
            <ChevronDown size={18} className="text-gray-400" />
          </button>
        </div>

        {/* 幣種選擇 */}
        <div>
          <label className="block text-gray-300 text-base mb-2 font-medium flex items-center gap-2">
            <Wallet size={16} className="text-gray-400" />
            {t('currency')}
          </label>
          <div className="flex gap-2">
            {['USDT', 'TON', 'Stars'].map((c) => (
              <div key={c} className="flex-1 relative group">
                <button
                  type="button"
                  onClick={() => setCurrency(c)}
                  className={`w-full py-3 rounded-xl border transition-colors ${
                    currency === c
                      ? 'bg-brand-red border-brand-red text-white'
                      : 'bg-brand-darker border-white/5 text-gray-400'
                  }`}
                >
                  {c}
                </button>
                {/* 點擊幣種名稱查看獲取方式 */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedCurrencyInfo(c as 'USDT' | 'TON' | 'Stars')
                    setShowCurrencyModal(true)
                  }}
                  className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/20 rounded-xl cursor-pointer"
                  title="點擊查看獲取方式"
                >
                  <Info size={16} className="text-white" />
                </button>
                <span className="absolute top-1 right-1 text-xs opacity-50 group-hover:opacity-100 pointer-events-none">ℹ️</span>
              </div>
            ))}
          </div>
          <p className="text-gray-400 text-xs mt-2">
            💡 提示：懸停幣種按鈕並點擊 ℹ️ 圖標可查看獲取方式
          </p>
        </div>

        {/* 紅包類型 */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-gray-300 text-base font-medium flex items-center gap-2">
              <Gift size={16} className="text-gray-400" />
              {t('packet_type')}
            </label>
            <button
              type="button"
              onClick={() => setShowRulesModal(true)}
              className="text-brand-red text-sm flex items-center gap-1 hover:opacity-80 relative group"
            >
              <Info size={14} className="relative z-10" />
              <span className="relative z-10 font-semibold flex items-center gap-1">
                <TelegramStar size={14} withSpray={true} />
                {t('game_rules')}
                <TelegramStar size={14} withSpray={true} />
              </span>
              {/* 發光特效 */}
              <span className="absolute inset-0 bg-gradient-to-r from-red-500/20 via-orange-500/20 to-yellow-500/20 rounded-lg blur-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300 animate-pulse" />
            </button>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => {
                setPacketType('random')
                setBombNumber(null)
              }}
              className={`flex-1 py-3 rounded-xl border transition-colors ${
                packetType === 'random'
                  ? 'bg-brand-red border-brand-red text-white'
                  : 'bg-brand-darker border-white/5 text-gray-400'
              }`}
            >
              {t('random_amount')}
            </button>
            <button
              type="button"
              onClick={() => setPacketType('fixed')}
              className={`flex-1 py-3 rounded-xl border transition-colors ${
                packetType === 'fixed'
                  ? 'bg-brand-red border-brand-red text-white'
                  : 'bg-brand-darker border-white/5 text-gray-400'
              }`}
            >
              {t('fixed_amount')}
            </button>
          </div>
        </div>

        {/* 炸彈數字選擇器 - 僅在選擇紅包炸彈時顯示 */}
        {packetType === 'fixed' && (
          <div>
            <label className="block text-gray-300 text-base mb-2 font-medium flex items-center gap-2">
              <Bomb size={16} className="text-gray-400" />
              {t('bomb_number')}
            </label>
            <div className="grid grid-cols-5 gap-2">
              {Array.from({ length: 10 }, (_, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setBombNumber(i)}
                  className={`py-3 rounded-xl border transition-all ${
                    bombNumber === i
                      ? 'bg-orange-500 border-orange-500 text-white shadow-lg shadow-orange-500/30 scale-105'
                      : 'bg-brand-darker border-white/5 text-gray-400 hover:border-orange-500/50'
                  }`}
                >
                  {i}
                </button>
              ))}
            </div>
            <p className="text-gray-500 text-xs mt-2">{t('select_bomb_number')}</p>
          </div>
        )}

        {/* 金額 */}
        <div>
          <label className="block text-gray-300 text-base mb-2 font-medium flex items-center gap-2">
            <DollarSign size={16} className="text-gray-400" />
            {t('amount')}
          </label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.00"
            className="w-full p-4 bg-brand-darker rounded-xl border border-white/5 text-white text-xl font-bold text-center focus:outline-none focus:border-brand-red"
          />
        </div>

        {/* 數量 */}
        <div>
          <label className="block text-gray-300 text-base mb-2 font-medium flex items-center gap-2">
            <Users size={16} className="text-gray-400" />
            {t('quantity')}
          </label>
          <input
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="1"
            min="1"
            className="w-full p-4 bg-brand-darker rounded-xl border border-white/5 text-white text-center focus:outline-none focus:border-brand-red"
          />
        </div>

        {/* 祝福語 */}
        <div>
          <label className="block text-gray-300 text-base mb-2 font-medium flex items-center gap-2">
            <MessageSquare size={16} className="text-gray-400" />
            {t('message')}
          </label>
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={t('best_wishes')}
            className="w-full p-4 bg-brand-darker rounded-xl border border-white/5 text-white focus:outline-none focus:border-brand-red"
          />
        </div>

        {/* 發送按鈕 - 在內容流中，位於底部導航欄上方 */}
        <div className="pt-4 pb-40">
          <button
            onClick={handleSubmit}
            disabled={sendMutation.isPending}
            className="w-full py-4 bg-gradient-to-r from-brand-red to-orange-500 rounded-xl text-white font-bold text-lg disabled:opacity-50 shadow-lg shadow-brand-red/30"
          >
            {sendMutation.isPending ? t('loading') : t('send')}
          </button>
        </div>
      </div>

      {/* 群組選擇彈窗 - 從頂部彈出 */}
      {showChatModal && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-16" onClick={() => { setShowChatModal(false); setSearchQuery(''); }}>
          <div className="w-full max-w-md max-h-[80vh] bg-brand-darker rounded-b-3xl shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="p-4 border-b border-white/5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-bold">{t('select_group')}</h3>
                <button
                  onClick={() => { setShowChatModal(false); setSearchQuery(''); }}
                  className="p-1 hover:bg-white/5 rounded-lg transition-colors"
                >
                  <X size={20} />
                </button>
              </div>
              
              {/* 統一搜索輸入框 */}
              <div className="relative">
                <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={t('search_placeholder')}
                  className="w-full pl-10 pr-4 py-2 bg-brand-dark rounded-xl border border-white/5 text-white focus:outline-none focus:border-brand-red"
                />
              </div>
            </div>
            
            <div className="overflow-y-auto max-h-[60vh]">
              {/* 顯示歷史記錄（當沒有搜索時） */}
              {searchQuery.length === 0 && (() => {
                const chatHistory = getChatHistory()
                return chatHistory.length > 0 ? (
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-medium text-gray-400">最近使用的群組</h4>
                      <span className="text-xs text-gray-500">{chatHistory.length} 個</span>
                    </div>
                    {chatHistory.map((chat: ChatInfo) => (
                      <div
                        key={chat.id}
                        className="flex items-center justify-between p-3 mb-2 bg-brand-dark rounded-xl border border-white/5 hover:border-brand-red/50 transition-colors group"
                      >
                        <button
                          onClick={async () => {
                            await handleSelectChat(chat)
                            setShowChatModal(false)
                            setSearchQuery('')
                          }}
                          className="flex-1 text-left"
                        >
                          <div className="flex items-center gap-3">
                            {chat.type === 'group' || chat.type === 'supergroup' ? (
                              <Users size={20} className="text-brand-red" />
                            ) : (
                              <User size={20} className="text-blue-400" />
                            )}
                            <div className="flex-1 min-w-0">
                              <div className="text-white font-medium truncate">{chat.title || chat.username || `Chat ${chat.id}`}</div>
                              {chat.username && (
                                <div className="text-gray-400 text-xs truncate">@{chat.username}</div>
                              )}
                              {chat.status_message && (
                                <div className="text-xs mt-1">
                                  {chat.user_in_group && (
                                    <span className="text-green-400 mr-2">✓ 你在群中</span>
                                  )}
                                  {chat.bot_in_group && (
                                    <span className="text-blue-400">✓ 機器人在</span>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </button>
                        <div className="flex items-center gap-2 ml-2">
                          <button
                            onClick={async (e) => {
                              e.stopPropagation()
                              // 更新記錄：重新搜索並更新信息
                              try {
                                const updatedChat = await searchChats((chat as any).username || chat.title || String(chat.id), tgId || undefined)
                                if (updatedChat && updatedChat.length > 0) {
                                  const found = updatedChat.find((c: ChatInfo) => c.id === chat.id) || updatedChat[0]
                                  saveChatToHistory(found)
                                  setSelectedChat(found)
                                  setShowChatModal(false)
                                  setSearchQuery('')
                                  showAlert('群組信息已更新', 'success')
                                }
                              } catch (error) {
                                showAlert('更新失敗，請重試', 'error')
                              }
                            }}
                            className="p-2 hover:bg-white/5 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                            title="更新群組信息"
                          >
                            <RefreshCw size={16} className="text-gray-400" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              deleteChatFromHistory(chat.id)
                              if (selectedChat?.id === chat.id) {
                                setSelectedChat(null)
                              }
                            }}
                            className="p-2 hover:bg-red-500/20 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                            title="刪除記錄"
                          >
                            <Trash2 size={16} className="text-red-400" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center text-gray-500">
                    <Users size={32} className="mx-auto mb-2 opacity-50" />
                    <p className="text-sm">暫無歷史記錄</p>
                    <p className="text-xs mt-1">發送紅包後會自動保存</p>
                  </div>
                )
              })()}

              {/* 顯示搜索結果（同時顯示群組和用戶） */}
              {searchQuery.length > 0 ? (
                <>
                  {/* 搜索中的狀態 */}
                  {(isSearchingChats || isSearchingUsers) && (
                    <div className="p-8 text-center text-gray-400">{t('loading')}</div>
                  )}

                  {/* 錯誤提示 */}
                  {(searchChatsError || searchUsersError) && (
                    <div className="p-4 m-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                      <div className="text-red-400 text-sm">
                        {searchChatsError?.message || searchUsersError?.message || '搜索失敗'}
                      </div>
                      <div className="text-gray-500 text-xs mt-1">
                        請檢查網絡連接或稍後再試
                      </div>
                    </div>
                  )}

                  {/* 合併顯示所有搜索結果（群組和用戶） */}
                  {!isSearchingChats && !isSearchingUsers && !searchChatsError && !searchUsersError && allSearchResults.length > 0 && (
                    <>
                      {allSearchResults.map((item: ChatInfo & { isUser?: boolean }) => {
                        const isUser = item.isUser || item.type === 'private'
                        return (
                          <button
                            key={`${isUser ? 'user' : 'chat'}-${item.id}`}
                            onClick={() => handleSelectChat(item)}
                            className="w-full flex items-center gap-3 p-4 hover:bg-white/5 transition-colors border-b border-white/5"
                          >
                            {/* 圖標 - 根據類型顯示不同的圖標和顏色 */}
                            {isUser ? (
                              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-green-500 to-teal-600 flex items-center justify-center text-white font-bold shrink-0">
                                <User size={20} />
                              </div>
                            ) : (
                              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold shrink-0">
                                <Users size={20} />
                              </div>
                            )}
                            <div className="flex-1 text-left min-w-0">
                              <div className="text-white font-medium truncate">{item.title}</div>
                              <div className="flex items-center gap-2 mt-1 flex-wrap">
                                {/* 類型標籤 */}
                                <span className={`text-xs font-medium ${
                                  isUser ? 'text-green-400' : 'text-blue-400'
                                }`}>
                                  {isUser ? '用戶' : '群組'}
                                </span>
                                {/* 群組狀態指示器（僅對群組顯示） */}
                                {!isUser && (
                                  <>
                                    {item.user_in_group !== undefined && (
                                      <span className={`text-xs flex items-center gap-1 ${
                                        item.user_in_group ? 'text-green-400' : 'text-orange-400'
                                      }`}>
                                        {item.user_in_group ? (
                                          <CheckCircle size={12} />
                                        ) : (
                                          <XCircle size={12} />
                                        )}
                                        {item.user_in_group ? '已加入' : '未加入'}
                                      </span>
                                    )}
                                    {item.bot_in_group !== undefined && (
                                      <span className={`text-xs flex items-center gap-1 ${
                                        item.bot_in_group ? 'text-green-400' : 'text-red-400'
                                      }`}>
                                        <Bot size={12} />
                                        {item.bot_in_group ? '機器人在' : '機器人不在'}
                                      </span>
                                    )}
                                  </>
                                )}
                              </div>
                              {item.status_message && (
                                <div className="text-xs text-gray-500 mt-1">{item.status_message}</div>
                              )}
                            </div>
                            {/* 選擇指示器 */}
                            <ChevronDown size={18} className="text-gray-400 shrink-0" />
                          </button>
                        )
                      })}
                    </>
                  )}

                  {/* 沒有搜索結果 */}
                  {!isSearchingChats && !isSearchingUsers && !searchChatsError && !searchUsersError && allSearchResults.length === 0 && (
                    <div className="p-8 text-center text-gray-400">
                      <div>{t('no_groups_found')}</div>
                      <div className="text-xs text-gray-500 mt-2">
                        請嘗試使用群組鏈接或 @username 格式
                      </div>
                    </div>
                  )}
                </>
              ) : (
                /* 顯示已有群組列表（沒有搜索時） */
                <>
                  {chats?.map((chat) => (
                    <button
                      key={chat.id}
                      onClick={() => handleSelectChat(chat)}
                      className="w-full flex items-center gap-3 p-4 hover:bg-white/5 transition-colors"
                    >
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                        {chat.title[0]}
                      </div>
                      <span className="text-white">{chat.title}</span>
                    </button>
                  ))}
                  {!chats?.length && (
                    <div className="p-8 text-center text-gray-400">
                      {t('no_data')}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 遊戲規則說明彈窗 */}
      {showRulesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 pb-24" onClick={() => setShowRulesModal(false)}>
          <div className="bg-brand-darker rounded-2xl p-6 max-w-md w-full border border-white/10 shadow-2xl max-h-[85vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
            {/* 標題 */}
            <div className="flex items-center justify-between mb-4 shrink-0">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-brand-red flex items-center justify-center">
                  <Info size={16} className="text-white" />
                </div>
                <h3 className="text-white text-lg font-bold flex items-center gap-2">
                  <TelegramStar size={18} withSpray={true} />
                  {t('game_rules_title')}
                  <TelegramStar size={18} withSpray={true} />
                </h3>
              </div>
              <button
                onClick={() => {
                  if (dontShowAgain) {
                    localStorage.setItem('dont_show_game_rules', 'true')
                  }
                  setShowRulesModal(false)
                }}
                className="p-1 hover:bg-white/5 rounded-lg transition-colors"
              >
                <X size={20} className="text-white" />
              </button>
            </div>

            {/* 規則內容 */}
            <div className="space-y-4 overflow-y-auto flex-1">
              {/* 支持幣種 */}
              <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Gift size={20} className="text-purple-400" />
                  <h4 className="text-white font-semibold">{t('game_rules_supported_currencies')}</h4>
                </div>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {t('game_rules_supported_currencies_desc')
                    .replace('{usdt}', '<strong class="text-yellow-400">USDT</strong>')
                    .replace('{ton}', '<strong class="text-blue-400">TON</strong>')
                    .replace('{stars}', '<strong class="text-purple-400">Stars</strong>')
                    .split(/(<strong[^>]*>.*?<\/strong>)/g)
                    .map((part, i) => {
                      if (part.startsWith('<strong')) {
                        return <span key={i} dangerouslySetInnerHTML={{ __html: part }} />
                      }
                      return <span key={i}>{part}</span>
                    })}
                </p>
                <p className="text-gray-400 text-xs mt-2">
                  {t('currency_get_method_hint')}
                </p>
              </div>

              {/* 手氣最佳 */}
              <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Gift size={20} className="text-blue-400" />
                  <h4 className="text-white font-semibold">{t('game_rules_best_mvp')}</h4>
                </div>
                <div className="text-gray-300 text-sm leading-relaxed space-y-2">
                  <p><strong className="text-white">{t('game_rules_best_mvp_howto')}</strong></p>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li>{t('game_rules_best_mvp_rule1').replace('{random}', '<strong class="text-blue-400">隨機算法</strong>').split(/(<strong[^>]*>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)}</li>
                    <li>{t('game_rules_best_mvp_rule2').replace('{max}', '<strong class="text-yellow-400">最大</strong>').split(/(<strong[^>]*>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)}</li>
                    <li>{t('game_rules_best_mvp_rule3')}</li>
                    <li>{t('game_rules_best_mvp_rule4').replace('{algorithm}', '<strong class="text-cyan-400">二倍均值算法</strong>').split(/(<strong[^>]*>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)}</li>
                  </ul>
                  <p className="mt-3"><strong className="text-white">{t('game_rules_best_mvp_scenario')}</strong></p>
                  <p className="text-gray-400 text-xs">{t('game_rules_best_mvp_scenario_desc')}</p>
                </div>
              </div>

              {/* 紅包炸彈 */}
              <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Bomb size={20} className="text-orange-400" />
                  <h4 className="text-white font-semibold">{t('game_rules_bomb')}</h4>
                </div>
                <div className="text-gray-300 text-sm leading-relaxed space-y-2">
                  <p><strong className="text-white">{t('game_rules_bomb_send')}</strong></p>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li>{t('game_rules_bomb_send_rule1').replace('{amount}', '5-10').replace('{currency}', 'USDT').split(/(\d+-\d+|\w+)/g).map((part, i) => /^\d+-\d+$/.test(part) ? <strong key={i} className="text-orange-400">{part}</strong> : /^USDT|TON|STARS|POINTS$/.test(part) ? <strong key={i} className="text-blue-400">{part}</strong> : <span key={i}>{part}</span>)}</li>
                    <li>{t('game_rules_bomb_send_rule2')}
                      <ul className="list-circle list-inside ml-4 mt-1 space-y-1">
                        <li>{t('game_rules_bomb_send_rule2a').replace('{single}', '<strong class="text-orange-400">5-8 個</strong>').replace('{full}', '<strong class="text-red-400">全額</strong>').split(/(<strong[^>]*>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)}</li>
                        <li>{t('game_rules_bomb_send_rule2b').replace('{double}', '<strong class="text-orange-400">10 個</strong>').replace('{double_amount}', '<strong class="text-red-400">雙倍</strong>').split(/(<strong[^>]*>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)}</li>
                      </ul>
                    </li>
                    <li>{t('game_rules_bomb_send_rule3').replace('{number}', '<strong class="text-red-400">炸彈數字</strong>').replace('{example}', '10 USDT/5').replace('{example_amount}', '10').replace('{currency}', 'USDT').replace('{example_number}', '5').split(/(<strong[^>]*>.*?<\/strong>|\d+)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : /^\d+$/.test(part) ? <strong key={i} className="text-yellow-400">{part}</strong> : <span key={i}>{part}</span>)}</li>
                    <li>{t('game_rules_bomb_send_rule4').replace('{average}', '<strong class="text-yellow-400">平均分配</strong>').split(/(<strong[^>]*>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)}</li>
                  </ul>
                  
                  <p className="mt-3"><strong className="text-white">{t('game_rules_bomb_grab')}</strong></p>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li>{t('game_rules_bomb_grab_rule1').replace('{fixed}', '<strong class="text-green-400">固定且相同</strong>').split(/(<strong[^>]*>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)}</li>
                    <li>{t('game_rules_bomb_grab_rule2').replace('{last_digit}', '<strong class="text-cyan-400">最後一位小數</strong>').replace('{example_amount}', '5.25').replace('{example_digit}', '5').split(/(<strong[^>]*>.*?<\/strong>|\d+\.\d+)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : /^\d+\.\d+$/.test(part) ? <strong key={i} className="text-yellow-400">{part}</strong> : <span key={i}>{part}</span>)}</li>
                    <li>{t('game_rules_bomb_grab_rule3').replace('{not_equal}', '<strong class="text-green-400">不等於</strong>').split(/(<strong[^>]*>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)} 🎉</li>
                    <li>{t('game_rules_bomb_grab_rule4').replace('{equal}', '<strong class="text-red-400">等於</strong>').split(/(<strong[^>]*>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)} 💣</li>
                  </ul>
                  
                  <p className="mt-3"><strong className="text-white">{t('game_rules_bomb_pay')}</strong></p>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li>{t('game_rules_bomb_pay_single').replace('{single}', '<strong class="text-orange-400">單炸彈</strong>').replace('{single_count}', '5-8').split(/(<strong[^>]*>.*?<\/strong>|\d+-\d+)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : /^\d+-\d+$/.test(part) ? <strong key={i} className="text-orange-400">{part}</strong> : <span key={i}>{part}</span>)}
                      <ul className="list-circle list-inside ml-4 mt-1">
                        <li>{t('game_rules_bomb_pay_single_rule').replace('{full}', '<strong class="text-red-400">紅包全額</strong>').split(/(<strong[^>]*>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)}</li>
                        <li>{t('game_rules_bomb_pay_single_example').replace(/{example_amount}/g, '10').replace('{currency}', 'USDT').split(/(\d+|USDT|TON|STARS|POINTS)/g).map((part, i) => /^\d+$/.test(part) ? <strong key={i} className="text-yellow-400">{part}</strong> : /^(USDT|TON|STARS|POINTS)$/.test(part) ? <strong key={i} className="text-blue-400">{part}</strong> : <span key={i}>{part}</span>)}</li>
                      </ul>
                    </li>
                    <li>{t('game_rules_bomb_pay_double').replace('{double}', '<strong class="text-orange-400">雙炸彈</strong>').replace('{double_count}', '10').split(/(<strong[^>]*>.*?<\/strong>|\d+)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : /^\d+$/.test(part) ? <strong key={i} className="text-orange-400">{part}</strong> : <span key={i}>{part}</span>)}
                      <ul className="list-circle list-inside ml-4 mt-1">
                        <li>{t('game_rules_bomb_pay_double_rule').replace('{double_amount}', '<strong class="text-red-400">雙倍金額</strong>').split(/(<strong[^>]*>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)}</li>
                        <li>{t('game_rules_bomb_pay_double_example').replace(/{example_amount}/g, '10').replace('{double_example_amount}', '20').replace('{currency}', 'USDT').split(/(\d+|USDT|TON|STARS|POINTS)/g).map((part, i) => /^\d+$/.test(part) ? <strong key={i} className="text-yellow-400">{part}</strong> : /^(USDT|TON|STARS|POINTS)$/.test(part) ? <strong key={i} className="text-blue-400">{part}</strong> : <span key={i}>{part}</span>)}</li>
                      </ul>
                    </li>
                    <li>{t('game_rules_bomb_pay_bonus').replace('{multiple}', '<strong class="text-yellow-400">多人</strong>').split(/(<strong[^>]*>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)}</li>
                  </ul>
                  
                  <p className="mt-3"><strong className="text-red-400">{t('game_rules_bomb_warning')}</strong></p>
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mt-2">
                    <ul className="text-red-300 text-xs space-y-1.5">
                      <li>• {t('game_rules_bomb_warning_rule1').replace('{balance}', '<strong>餘額是否充足</strong>').split(/(<strong>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)}</li>
                      <li>• {t('game_rules_bomb_warning_rule2').replace('{single}', '<strong class="text-red-400">單炸彈</strong>').replace('{example_amount}', '10').replace('{currency}', 'USDT').split(/(<strong[^>]*>.*?<\/strong>|\d+)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : /^\d+$/.test(part) ? <strong key={i} className="text-yellow-400">{part}</strong> : <span key={i}>{part}</span>)}</li>
                      <li>• {t('game_rules_bomb_warning_rule3').replace('{double}', '<strong class="text-red-400">雙炸彈</strong>').replace('{double_example_amount}', '20').replace('{currency}', 'USDT').split(/(<strong[^>]*>.*?<\/strong>|\d+)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : /^\d+$/.test(part) ? <strong key={i} className="text-yellow-400">{part}</strong> : <span key={i}>{part}</span>)}</li>
                      <li>• {t('game_rules_bomb_warning_rule4').replace('{unable}', '<strong>無法參與搶包</strong>').split(/(<strong>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)}</li>
                      <li>• {t('game_rules_bomb_warning_rule5').replace('{deduct}', '<strong>對應幣種餘額</strong>').split(/(<strong>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)}</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* 專屬紅包 */}
              <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <User size={20} className="text-purple-400" />
                  <h4 className="text-white font-semibold">{t('game_rules_exclusive')}</h4>
                </div>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {t('game_rules_exclusive_desc').replace('{specified}', '<strong class="text-purple-400">指定用戶</strong>').split(/(<strong[^>]*>.*?<\/strong>)/g).map((part, i) => part.startsWith('<strong') ? <span key={i} dangerouslySetInnerHTML={{ __html: part }} /> : <span key={i}>{part}</span>)}
                </p>
              </div>

              {/* 娛樂提醒 */}
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
                <p className="text-yellow-200 text-sm leading-relaxed text-center">
                  {t('game_rules_entertainment')}
                </p>
              </div>
            </div>

            {/* 不再顯示選擇框 */}
            <div className="flex items-center gap-2 mt-4 mb-4 shrink-0">
              <input
                type="checkbox"
                id="dontShowAgain"
                checked={dontShowAgain}
                onChange={(e) => setDontShowAgain(e.target.checked)}
                className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-brand-red focus:ring-brand-red focus:ring-2"
              />
              <label htmlFor="dontShowAgain" className="text-gray-300 text-sm cursor-pointer select-none">
                {t('dont_show_again')}
              </label>
            </div>

            {/* 關閉按鈕 */}
            <button
              onClick={() => {
                if (dontShowAgain) {
                  localStorage.setItem('dont_show_game_rules', 'true')
                }
                setShowRulesModal(false)
              }}
              className="w-full py-3 bg-gradient-to-r from-orange-500 to-red-500 rounded-xl text-white font-semibold hover:from-orange-600 hover:to-red-600 transition-all shrink-0 mb-2"
            >
              {t('got_it')}
            </button>
          </div>
        </div>
      )}

      {/* 幣種獲取方式彈窗 */}
      {showCurrencyModal && selectedCurrencyInfo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={() => setShowCurrencyModal(false)}>
          <div className="bg-gradient-to-br from-brand-darker via-brand-darker to-gray-900 rounded-2xl p-6 max-w-md w-full border border-white/20 shadow-2xl max-h-[90vh] overflow-hidden flex flex-col relative" onClick={(e) => e.stopPropagation()}>
            {/* 標題 */}
            <div className="flex items-center justify-between mb-4 shrink-0 relative z-10">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center shadow-lg">
                  <Wallet size={18} className="text-white" />
                </div>
                <h3 className="text-white text-xl font-bold">
                  {selectedCurrencyInfo === 'USDT' && t('currency_usdt_get_methods')}
                  {selectedCurrencyInfo === 'TON' && t('currency_ton_get_methods')}
                  {selectedCurrencyInfo === 'Stars' && t('currency_stars_get_methods')}
                </h3>
              </div>
              <button
                onClick={() => setShowCurrencyModal(false)}
                className="p-1 hover:bg-white/10 rounded-lg transition-colors"
              >
                <X size={20} className="text-white" />
              </button>
            </div>

            {/* 幣種說明 */}
            <div className="mb-4 shrink-0 relative z-10">
              <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-xl p-4">
                <p className="text-gray-300 text-sm leading-relaxed">
                  {selectedCurrencyInfo === 'USDT' && t('currency_usdt_desc')}
                  {selectedCurrencyInfo === 'TON' && t('currency_ton_desc')}
                  {selectedCurrencyInfo === 'Stars' && t('currency_stars_desc')}
                </p>
              </div>
            </div>

            {/* 獲取方式內容 */}
            <div className="space-y-4 overflow-y-auto flex-1 relative z-10 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent">
              {/* Telegram 錢包綁定 */}
              {(selectedCurrencyInfo === 'USDT' || selectedCurrencyInfo === 'TON') && (
                <div className="bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-green-500/30 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Wallet size={20} className="text-green-400" />
                    <h4 className="text-white font-semibold text-base">{t('currency_get_method_telegram_wallet')}</h4>
                  </div>
                  <p className="text-gray-300 text-sm leading-relaxed">
                    {t('currency_get_method_telegram_wallet_desc')}
                  </p>
                </div>
              )}

              {/* 銀行卡充值 */}
              {(selectedCurrencyInfo === 'USDT' || selectedCurrencyInfo === 'TON') && (
                <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/30 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Wallet size={20} className="text-yellow-400" />
                    <h4 className="text-white font-semibold text-base">{t('currency_get_method_bank_card')}</h4>
                  </div>
                  <p className="text-gray-300 text-sm leading-relaxed">
                    {t('currency_get_method_bank_card_desc')}
                  </p>
                </div>
              )}

              {/* 交易所購買 */}
              {(selectedCurrencyInfo === 'USDT' || selectedCurrencyInfo === 'TON') && (
                <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Wallet size={20} className="text-purple-400" />
                    <h4 className="text-white font-semibold text-base">{t('currency_get_method_exchange')}</h4>
                  </div>
                  <p className="text-gray-300 text-sm leading-relaxed">
                    {t('currency_get_method_exchange_desc')}
                  </p>
                </div>
              )}

              {/* Telegram Stars 獲取 */}
              {selectedCurrencyInfo === 'Stars' && (
                <div className="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <TelegramStar size={20} withSpray={true} />
                    <h4 className="text-white font-semibold text-base">{t('currency_get_method_telegram_stars')}</h4>
                  </div>
                  <div className="text-gray-300 text-sm leading-relaxed space-y-2">
                    {t('currency_get_method_telegram_stars_desc').split('\n').map((line, i) => (
                      <p key={i}>{line}</p>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* 關閉按鈕 */}
            <button
              onClick={() => setShowCurrencyModal(false)}
              className="w-full mt-4 py-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl text-white font-semibold hover:from-blue-600 hover:to-purple-600 transition-all shrink-0 shadow-lg shadow-blue-500/30 relative z-10"
            >
              {t('got_it')}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

