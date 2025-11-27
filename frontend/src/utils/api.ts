import axios from 'axios'
import { getInitData } from './telegram'

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
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || '請求失敗'
    console.error('[API Error]', message)
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
  return api.post('/v1/redpackets', params)
}

export async function claimRedPacket(id: string): Promise<{ amount: number; message: string }> {
  return api.post(`/v1/redpackets/${id}/claim`)
}

// ============ 群組相關 API ============

export interface ChatInfo {
  id: number
  title: string
  type: string
}

export async function getUserChats(): Promise<ChatInfo[]> {
  return api.get('/v1/chats')
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

