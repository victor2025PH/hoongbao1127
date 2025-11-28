import axios from 'axios'
import { getInitData, getTelegramUser } from './telegram'

// API 基礎 URL
const API_BASE = import.meta.env.VITE_API_URL || '/api'

// 創建 axios 實例
const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 請求攔截器 - 添加 Telegram 認證
api.interceptors.request.use((config) => {
  const initData = getInitData()
  if (initData) {
    config.headers['X-Telegram-Init-Data'] = initData
  }
  return config
})

// 響應攔截器 - 統一錯誤處理
api.interceptors.response.use(
  (response) => {
    // 記錄成功的響應（僅在開發環境）
    if (import.meta.env.DEV) {
      console.log('[API Success]', response.config.url, response.data)
    }
    return response.data
  },
  (error: any) => {
    let message = '請求失敗'
    if (error.response?.data?.detail) {
      message = typeof error.response.data.detail === 'string' 
        ? error.response.data.detail 
        : JSON.stringify(error.response.data.detail)
    } else if (error.message) {
      message = typeof error.message === 'string' ? error.message : String(error.message)
    }
    console.error('[API Error]', error.config?.url, message, error.response?.data)
    // 對於搜索 API，如果返回空數組，不應該視為錯誤
    if (error.config?.url?.includes('/search') && error.response?.status === 200) {
      return []
    }
    return Promise.reject(new Error(message))
  }
)

export default api

// ============ 用戶相關 API ============

export interface UserProfile {
  id: number
  tg_id: number
  username: string | null
  first_name: string | null
  level: number
  xp: number
  energy_balance?: number
  created_at: string
}

export interface Balance {
  usdt: number
  ton: number
  stars: number
}

export async function getUserProfile(): Promise<UserProfile> {
  return api.get('/v1/users/me')
}

export async function getBalance(): Promise<Balance> {
  return api.get('/v1/users/me/balance')
}

// ============ 紅包相關 API ============

export interface RedPacket {
  id: string
  sender_id: number
  sender_name: string
  amount: number
  currency: string
  quantity: number
  remaining: number
  type: 'random' | 'fixed'
  message: string
  status: 'active' | 'completed' | 'expired'
  created_at: string
  expires_at: string
  message_sent?: boolean  // 消息是否成功發送到群組
  share_link?: string  // 分享鏈接（如果機器人不在群組中）
}

export interface SendRedPacketParams {
  chat_id: number
  amount: number
  currency: string
  quantity: number
  type: 'random' | 'fixed'
  message?: string
  bomb_number?: number  // 0-9, 仅当 type='fixed' 时有效
}

export async function listRedPackets(): Promise<RedPacket[]> {
  return api.get('/v1/redpackets')
}

export async function getRedPacket(id: string): Promise<RedPacket> {
  return api.get(`/v1/redpackets/${id}`)
}

export async function sendRedPacket(params: SendRedPacketParams): Promise<RedPacket> {
  // 轉換參數格式以匹配後端 API
  const requestBody: any = {
    currency: params.currency || 'USDT',
    packet_type: params.type || 'random',
    total_amount: params.amount,
    total_count: params.quantity,
    message: params.message || '恭喜發財！🧧',
    chat_id: params.chat_id,
  }
  
  // 如果提供了 chat_title，添加到請求中
  if ('chat_title' in params && params.chat_title) {
    requestBody.chat_title = params.chat_title
  }
  
  // 如果提供了 bomb_number，添加到請求中
  if (params.bomb_number !== undefined) {
    requestBody.bomb_number = params.bomb_number
  }
  
  console.log('[sendRedPacket] Sending request:', requestBody)
  return api.post('/redpackets/create', requestBody)
}

export async function claimRedPacket(id: string): Promise<{ amount: number; message: string }> {
  return api.post(`/v1/redpackets/${id}/claim`)
}

// ============ 群組相關 API ============

export interface ChatInfo {
  id: number
  title: string
  type: string
  link?: string  // 群組鏈接（用於基於鏈接的群組）
  user_in_group?: boolean  // 用戶是否在群組中
  bot_in_group?: boolean  // Bot 是否在群組中
  status_message?: string  // 狀態提示信息
}

export async function getUserChats(): Promise<ChatInfo[]> {
  return api.get('/v1/chats')
}

export async function searchChats(query: string, tgId?: number): Promise<ChatInfo[]> {
  // 處理群鏈接格式和 @ 開頭的格式
  let processedQuery = query.trim()
  
  // 處理 @ 開頭的格式（移除 @ 符號）
  if (processedQuery.startsWith('@')) {
    processedQuery = processedQuery.substring(1)
  }
  
  // 處理 t.me/ 鏈接格式
  if (processedQuery.includes('t.me/')) {
    const match = processedQuery.match(/t\.me\/([^/?]+)/)
    if (match) {
      processedQuery = match[1]
    }
  }
  
  // 如果處理後的查詢為空，使用原始查詢
  if (!processedQuery) {
    processedQuery = query.trim()
  }
  
  // 獲取用戶 ID（優先使用傳入的參數，否則從 Telegram WebApp 獲取）
  const userId = tgId || getTelegramUser()?.id
  
  // 構建查詢參數 - 使用完整鏈接格式以便後端正確識別
  let finalQuery = processedQuery
  // 如果查詢看起來像 username（不包含空格和特殊字符），嘗試構建完整鏈接
  if (!finalQuery.includes('://') && !finalQuery.includes('t.me/') && /^[a-zA-Z0-9_]+$/.test(finalQuery)) {
    // 對於純 username，後端會自動處理，這裡保持原樣
    finalQuery = processedQuery
  }
  
  const params = new URLSearchParams({ q: finalQuery })
  if (userId) {
    params.append('tg_id', userId.toString())
  }
  
  try {
    const result = await api.get(`/v1/chats/search?${params.toString()}`)
    console.log('[searchChats] API response:', result)
    // 確保返回的是數組
    return Array.isArray(result) ? result : []
  } catch (error: any) {
    console.error('[searchChats] API error:', error)
    // 如果錯誤是空結果，返回空數組而不是拋出錯誤
    if (error.message?.includes('not found') || error.response?.status === 404) {
      return []
    }
    throw error
  }
}

export async function searchUsers(query: string, tgId?: number): Promise<ChatInfo[]> {
  // 處理用戶名格式（移除 @ 符號）
  let processedQuery = query.trim().replace(/^@/, '')
  // 如果是群鏈接，也嘗試提取用戶名
  if (query.includes('t.me/')) {
    const match = query.match(/t\.me\/([^/?]+)/)
    if (match) {
      processedQuery = match[1]
    }
  }
  
  // 獲取用戶 ID（優先使用傳入的參數，否則從 Telegram WebApp 獲取）
  const userId = tgId || getTelegramUser()?.id
  
  // 構建查詢參數
  const params = new URLSearchParams({ q: processedQuery })
  if (userId) {
    params.append('tg_id', userId.toString())
  }
  
  try {
    const result = await api.get(`/v1/chats/users/search?${params.toString()}`)
    console.log('[searchUsers] API response:', result)
    // 確保返回的是數組
    return Array.isArray(result) ? result : []
  } catch (error: any) {
    console.error('[searchUsers] API error:', error)
    // 如果錯誤是空結果，返回空數組而不是拋出錯誤
    if (error.message?.includes('not found') || error.response?.status === 404) {
      return []
    }
    throw error
  }
}

export async function checkUserInChat(chatId: number, link?: string, tgId?: number): Promise<{ in_group: boolean; message?: string }> {
  const params: Record<string, string> = {}
  if (link) {
    params.link = link
  }
  // 獲取用戶 ID（優先使用傳入的參數，否則從 Telegram WebApp 獲取）
  const userId = tgId || getTelegramUser()?.id
  if (userId) {
    params.tg_id = userId.toString()
  }
  return api.get(`/v1/chats/${chatId}/check`, { params })
}

// ============ 簽到相關 API ============

export interface CheckInResult {
  success: boolean
  reward: number
  streak: number
  message: string
}

export async function checkIn(): Promise<CheckInResult> {
  return api.post('/v1/checkin')
}

export async function getCheckInStatus(): Promise<{
  checked_today: boolean
  streak: number
  last_check_in: string | null
}> {
  return api.get('/v1/checkin/status')
}

// ============ 錢包相關 API ============

export async function createRechargeOrder(amount: number, currency: string): Promise<{
  order_id: string
  payment_url: string
}> {
  return api.post('/v1/wallet/recharge', { amount, currency })
}

export async function createWithdrawOrder(amount: number, currency: string, address: string): Promise<{
  order_id: string
  status: string
}> {
  return api.post('/v1/wallet/withdraw', { amount, currency, address })
}

// ============ 消息相關 API ============

export interface Message {
  id: number
  message_type: string
  status: string
  title?: string
  content: string
  action_url?: string
  source?: string
  source_name?: string
  can_reply: boolean
  meta_data?: Record<string, any>  // 使用 meta_data 而不是 metadata
  created_at: string
  read_at?: string
  reply_to_id?: number
}

export interface MessageListResponse {
  total: number
  page: number
  limit: number
  unread_count: number
  messages: Message[]
}

export interface UnreadCountResponse {
  unread_count: number
  unread_by_type: Record<string, number>
}

export interface NotificationSettings {
  notification_method: string
  enable_system: boolean
  enable_redpacket: boolean
  enable_balance: boolean
  enable_activity: boolean
  enable_miniapp: boolean
  enable_telegram: boolean
}

export async function getMessages(params?: {
  message_type?: string
  status?: string
  page?: number
  limit?: number
}): Promise<MessageListResponse> {
  const queryParams = new URLSearchParams()
  if (params?.message_type) queryParams.append('message_type', params.message_type)
  if (params?.status) queryParams.append('status', params.status)
  if (params?.page) queryParams.append('page', params.page.toString())
  if (params?.limit) queryParams.append('limit', params.limit.toString())
  
  const query = queryParams.toString()
  // 如果沒有認證信息，返回空結果（本地測試）
  try {
    return await api.get(`/v1/messages/${query ? '?' + query : ''}`)
  } catch (error: any) {
    // 如果是認證錯誤，返回空結果
    if (error.message?.includes('Unauthorized') || error.response?.status === 401) {
      return {
        total: 0,
        page: 1,
        limit: params?.limit || 20,
        unread_count: 0,
        messages: []
      }
    }
    throw error
  }
}

export async function getUnreadCount(): Promise<UnreadCountResponse> {
  try {
    return await api.get('/v1/messages/unread-count')
  } catch (error: any) {
    // 如果是認證錯誤，返回空結果
    if (error.message?.includes('Unauthorized') || error.response?.status === 401) {
      return {
        unread_count: 0,
        unread_by_type: {}
      }
    }
    throw error
  }
}

export async function getMessage(messageId: number): Promise<Message> {
  return api.get(`/v1/messages/${messageId}`)
}

export async function markMessageAsRead(messageId: number): Promise<{ success: boolean }> {
  return api.put(`/v1/messages/${messageId}/read`)
}

export async function deleteMessage(messageId: number): Promise<{ success: boolean }> {
  return api.delete(`/v1/messages/${messageId}`)
}

export async function replyMessage(messageId: number, content: string): Promise<Message> {
  return api.post(`/v1/messages/${messageId}/reply`, { content })
}

export async function getNotificationSettings(): Promise<NotificationSettings> {
  return api.get('/v1/messages/settings')
}

export async function updateNotificationSettings(settings: Partial<NotificationSettings>): Promise<NotificationSettings> {
  return api.put('/v1/messages/settings', settings)
}

