import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronDown, X, Users, Wallet, Gift, DollarSign, MessageSquare, Info, Bomb, Search, User, CheckCircle, XCircle, Bot } from 'lucide-react'
import { useTranslation } from '../providers/I18nProvider'
import { getUserChats, sendRedPacket, searchChats, searchUsers, checkUserInChat, type ChatInfo } from '../utils/api'
import { haptic, showAlert, showConfirm, getTelegramUser } from '../utils/telegram'

export default function SendRedPacket() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const [selectedChat, setSelectedChat] = useState<ChatInfo | null>(null)
  const [showChatModal, setShowChatModal] = useState(false)
  const [showRulesModal, setShowRulesModal] = useState(false)
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

  // 發送紅包
  const sendMutation = useMutation({
    mutationFn: sendRedPacket,
    onSuccess: async (data: any) => {
      haptic('success')
      queryClient.invalidateQueries({ queryKey: ['balance'] })
      queryClient.invalidateQueries({ queryKey: ['redpackets'] })
      
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
              <button
                key={c}
                type="button"
                onClick={() => setCurrency(c)}
                className={`flex-1 py-3 rounded-xl border transition-colors ${
                  currency === c
                    ? 'bg-brand-red border-brand-red text-white'
                    : 'bg-brand-darker border-white/5 text-gray-400'
                }`}
              >
                {c}
              </button>
            ))}
          </div>
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
              className="text-brand-red text-sm flex items-center gap-1 hover:opacity-80"
            >
              <Info size={14} />
              {t('view_rules')}
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={() => setShowRulesModal(false)}>
          <div className="w-full max-w-md bg-brand-darker rounded-2xl border border-white/10 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="p-4 border-b border-white/5 flex items-center justify-between">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <Info size={20} className="text-brand-red" />
                {t('game_rules')}
              </h3>
              <button
                onClick={() => setShowRulesModal(false)}
                className="p-1 hover:bg-white/5 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-4 space-y-4">
              {/* 最佳手氣規則 */}
              <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl p-4 border border-blue-500/20">
                <h4 className="text-base font-bold text-white mb-2 flex items-center gap-2">
                  <Gift size={18} className="text-blue-400" />
                  {t('random_amount')}
                </h4>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {t('best_mvp_rules')}
                </p>
              </div>

              {/* 紅包炸彈規則 */}
              <div className="bg-gradient-to-r from-orange-500/10 to-red-500/10 rounded-xl p-4 border border-orange-500/20">
                <h4 className="text-base font-bold text-white mb-2 flex items-center gap-2">
                  <Bomb size={18} className="text-orange-400" />
                  {t('fixed_amount')}
                </h4>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {t('bomb_rules')}
                </p>
              </div>
            </div>
            <div className="p-4 border-t border-white/5">
              <button
                onClick={() => setShowRulesModal(false)}
                className="w-full py-3 bg-gradient-to-r from-brand-red to-orange-500 rounded-xl text-white font-bold"
              >
                {t('got_it')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

