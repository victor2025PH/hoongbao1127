import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronDown, X, Users, Wallet, Gift, DollarSign, MessageSquare, Info, Bomb, Search, User } from 'lucide-react'
import { useTranslation } from '../providers/I18nProvider'
import { getUserChats, sendRedPacket, searchChats, searchUsers, checkUserInChat, type ChatInfo } from '../utils/api'
import { haptic, showAlert } from '../utils/telegram'

export default function SendRedPacket() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const queryClient = useQueryClient()

  const [selectedChat, setSelectedChat] = useState<ChatInfo | null>(null)
  const [showChatModal, setShowChatModal] = useState(false)
  const [showRulesModal, setShowRulesModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
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
  const { data: searchChatsResult, isLoading: isSearchingChats } = useQuery({
    queryKey: ['searchChats', searchQuery],
    queryFn: () => searchChats(searchQuery),
    enabled: searchQuery.length > 0,
  })

  const { data: searchUsersResult, isLoading: isSearchingUsers } = useQuery({
    queryKey: ['searchUsers', searchQuery],
    queryFn: () => searchUsers(searchQuery),
    enabled: searchQuery.length > 0,
  })

  // 當選擇群組時，驗證用戶是否在群組中
  const handleSelectChat = async (chat: ChatInfo) => {
    try {
      // 如果是基於鏈接的群組（負數 ID），傳遞鏈接給後端
      const checkResult = await checkUserInChat(chat.id, chat.link)
      if (!checkResult.in_group) {
        // 如果用戶不在群組中，提供加入群組的選項
        if (chat.link) {
          const telegram = window.Telegram?.WebApp
          if (telegram) {
            const shouldJoin = await new Promise<boolean>((resolve) => {
              telegram.showConfirm(
                t('join_group_first') + '\n\n' + t('open_group_link'),
                (confirmed) => resolve(confirmed)
              )
            })
            if (shouldJoin) {
              telegram.openLink(chat.link)
            }
          } else {
            showAlert(t('join_group_first'))
          }
        } else {
          showAlert(checkResult.message || t('user_not_in_group'))
        }
        return
      }
      setSelectedChat(chat)
      setShowChatModal(false)
      setSearchQuery('')
    } catch (error: any) {
      if (error.message?.includes('not in group') || error.message?.includes('不在群組')) {
        if (chat.link) {
          const telegram = window.Telegram?.WebApp
          if (telegram) {
            telegram.showConfirm(
              t('join_group_first') + '\n\n' + t('open_group_link'),
              (confirmed) => {
                if (confirmed) {
                  telegram.openLink(chat.link)
                }
              }
            )
          } else {
            showAlert(t('join_group_first'))
          }
        } else {
          showAlert(t('join_group_first'))
        }
      } else {
        showAlert(error.message || t('user_not_in_group'))
      }
    }
  }

  // 發送紅包
  const sendMutation = useMutation({
    mutationFn: sendRedPacket,
    onSuccess: (data: any) => {
      haptic('success')
      queryClient.invalidateQueries({ queryKey: ['balance'] })
      queryClient.invalidateQueries({ queryKey: ['redpackets'] })
      
      // 如果機器人不在群組中，顯示分享鏈接
      if (!data.message_sent && data.share_link) {
        const telegram = window.Telegram?.WebApp
        if (telegram) {
          telegram.showConfirm(
            t('bot_not_in_group') + '\n\n' + t('share_red_packet_link'),
            (confirmed) => {
              if (confirmed) {
                telegram.openLink(data.share_link)
              }
            }
          )
        } else {
          showAlert(t('bot_not_in_group') + '\n' + t('share_link') + ': ' + data.share_link)
        }
      } else {
        showAlert(t('success'))
      }
      
      navigate('/packets')
    },
    onError: (error: Error) => {
      haptic('error')
      showAlert(error.message)
    },
  })

  const handleSubmit = () => {
    if (!selectedChat) {
      showAlert(t('select_group'))
      return
    }
    if (!amount || parseFloat(amount) <= 0) {
      showAlert(t('enter_amount'))
      return
    }
    if (!quantity || parseInt(quantity) < 1) {
      showAlert(t('enter_quantity'))
      return
    }
    if (packetType === 'fixed' && bombNumber === null) {
      showAlert(t('bomb_number_required'))
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

                  {/* 群組搜索結果 */}
                  {!isSearchingChats && searchChatsResult && searchChatsResult.length > 0 && (
                    <>
                      <div className="px-4 py-2 text-xs text-gray-500 font-medium">{t('search_group')}</div>
                      {searchChatsResult.map((chat) => (
                        <button
                          key={`chat-${chat.id}`}
                          onClick={() => handleSelectChat(chat)}
                          className="w-full flex items-center gap-3 p-4 hover:bg-white/5 transition-colors"
                        >
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                            {chat.title[0]}
                          </div>
                          <div className="flex-1 text-left">
                            <div className="text-white font-medium">{chat.title}</div>
                            <div className="text-xs text-gray-500">群組</div>
                          </div>
                        </button>
                      ))}
                    </>
                  )}

                  {/* 用戶搜索結果 */}
                  {!isSearchingUsers && searchUsersResult && searchUsersResult.length > 0 && (
                    <>
                      <div className="px-4 py-2 text-xs text-gray-500 font-medium border-t border-white/5 mt-2 pt-2">{t('search_user')}</div>
                      {searchUsersResult.map((user) => (
                        <button
                          key={`user-${user.id}`}
                          onClick={() => handleSelectChat(user)}
                          className="w-full flex items-center gap-3 p-4 hover:bg-white/5 transition-colors"
                        >
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-teal-600 flex items-center justify-center text-white font-bold">
                            {user.title[0]}
                          </div>
                          <div className="flex-1 text-left">
                            <div className="text-white font-medium">{user.title}</div>
                            <div className="text-xs text-gray-500">用戶</div>
                          </div>
                        </button>
                      ))}
                    </>
                  )}

                  {/* 沒有搜索結果 */}
                  {!isSearchingChats && !isSearchingUsers && 
                   (!searchChatsResult || searchChatsResult.length === 0) && 
                   (!searchUsersResult || searchUsersResult.length === 0) && (
                    <div className="p-8 text-center text-gray-400">{t('no_groups_found')}</div>
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

