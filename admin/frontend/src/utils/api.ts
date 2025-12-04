import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 請求攔截器：添加 token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 響應攔截器：處理錯誤
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().clearAuth()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// API 函數
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/v1/admin/auth/login', { username, password }),
  getMe: () => api.get('/v1/admin/auth/me'),
}

export const userApi = {
  list: (params?: any) => api.get('/v1/admin/users/list', { params }),
  detail: (id: number) => api.get(`/api/users/${id}`),
  detailFull: (id: number) => api.get(`/v1/admin/users/${id}/detail`),
  adjustBalance: (data: any) => api.post('/v1/admin/users/adjust-balance', data),
  batchOperation: (data: any) => api.post('/v1/admin/users/batch-operation', data),
}

export const telegramApi = {
  sendMessage: (data: any) => api.post('/v1/admin/telegram/send-message', data),
  sendBatch: (data: any) => api.post('/v1/admin/telegram/send-batch', data),
  getGroups: (params?: any) => api.get('/v1/admin/telegram/groups', { params }),
  getGroupDetail: (chatId: number) => api.get(`/v1/admin/telegram/groups/${chatId}`),
  getMessages: (params?: any) => api.get('/v1/admin/telegram/messages', { params }),
  resolveId: (data: any) => api.post('/v1/admin/telegram/resolve-id', data),
  // 消息模板
  getTemplates: (params?: any) => api.get('/v1/admin/telegram/templates', { params }),
  getTemplateDetail: (id: number) => api.get(`/v1/admin/telegram/templates/${id}`),
  createTemplate: (data: any) => api.post('/v1/admin/telegram/templates', data),
  updateTemplate: (id: number, data: any) => api.put(`/v1/admin/telegram/templates/${id}`, data),
  deleteTemplate: (id: number) => api.delete(`/v1/admin/telegram/templates/${id}`),
  renderTemplate: (id: number, data: any) => api.post(`/v1/admin/telegram/templates/${id}/render`, data),
}

export const dashboardApi = {
  getStats: () => api.get('/v1/admin/dashboard/stats'),
  getTrends: (params?: any) => api.get('/v1/admin/dashboard/trends', { params }),
  getDistribution: () => api.get('/v1/admin/dashboard/distribution'),
}

export const redpacketApi = {
  list: (params?: any) => api.get('/v1/admin/redpackets/list', { params }),
  detail: (id: number) => api.get(`/v1/admin/redpackets/${id}`),
  refund: (id: number) => api.post(`/v1/admin/redpackets/${id}/refund`),
  extend: (id: number, hours: number) => api.post(`/v1/admin/redpackets/${id}/extend`, null, { params: { hours } }),
  complete: (id: number) => api.post(`/v1/admin/redpackets/${id}/complete`),
  delete: (id: number) => api.delete(`/v1/admin/redpackets/${id}`),
  getStats: () => api.get('/v1/admin/redpackets/stats/overview'),
  getTrend: (params?: any) => api.get('/v1/admin/redpackets/stats/trend', { params }),
}

export const transactionApi = {
  list: (params?: any) => api.get('/v1/admin/transactions/list', { params }),
  detail: (id: number) => api.get(`/v1/admin/transactions/${id}`),
  getStats: () => api.get('/v1/admin/transactions/stats/overview'),
  getTrend: (params?: any) => api.get('/v1/admin/transactions/stats/trend', { params }),
}

export const checkinApi = {
  list: (params?: any) => api.get('/v1/admin/checkin/list', { params }),
  getStats: () => api.get('/v1/admin/checkin/stats'),
  getTrend: (params?: any) => api.get('/v1/admin/checkin/trend', { params }),
}

export const inviteApi = {
  list: (params?: any) => api.get('/v1/admin/invite/list', { params }),
  getTree: (userId: number, depth?: number) => api.get(`/v1/admin/invite/tree/${userId}`, { params: { depth } }),
  getStats: () => api.get('/v1/admin/invite/stats'),
  getTrend: (params?: any) => api.get('/v1/admin/invite/trend', { params }),
}

export const reportApi = {
  generate: (data: any) => api.post('/v1/admin/reports/generate', data),
  list: (params?: any) => api.get('/v1/admin/reports', { params }),
  download: (reportId: number) => api.get(`/v1/admin/reports/${reportId}/download`, { responseType: 'blob' }),
}

// 安全中心 API
export const securityApi = {
  // 安全總覽
  getStats: () => api.get('/v1/admin/security/stats'),
  getTrends: (params?: any) => api.get('/v1/admin/security/trends', { params }),
  
  // 風險監控
  getRiskUsers: (params?: any) => api.get('/v1/admin/security/risk/users', { params }),
  
  // 警報管理
  getAlerts: (params?: any) => api.get('/v1/admin/security/alerts', { params }),
  alertAction: (alertId: number, data: any) => api.post(`/v1/admin/security/alerts/${alertId}/action`, data),
  
  // 設備管理
  getDevices: (params?: any) => api.get('/v1/admin/security/devices', { params }),
  deviceAction: (deviceId: number, data: any) => api.post(`/v1/admin/security/devices/${deviceId}/action`, data),
  
  // IP 監控
  getIPSessions: (params?: any) => api.get('/v1/admin/security/ip-sessions', { params }),
  getIPStats: () => api.get('/v1/admin/security/ip-stats'),
  ipAction: (ipAddress: string, data: any) => api.post(`/v1/admin/security/ip/${encodeURIComponent(ipAddress)}/action`, data),
  
  // 流動性管理
  getLiquidityStats: () => api.get('/v1/admin/security/liquidity/stats'),
  getLiquidityEntries: (params?: any) => api.get('/v1/admin/security/liquidity/entries', { params }),
  adjustLiquidity: (data: any) => api.post('/v1/admin/security/liquidity/adjust', data),
}

