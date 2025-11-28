/**
 * 通知管理器 - 雙提示系統
 */
import { wsManager, MessageData } from './websocket'
import { showAlert } from './telegram'
import { getTelegramUser } from './telegram'

class NotificationManager {
  private initialized = false
  private wsListener: (() => void) | null = null

  /**
   * 初始化通知管理器
   */
  async init(): Promise<void> {
    if (this.initialized) return

    try {
      // 連接 WebSocket
      await wsManager.connect()
      
      // 監聽新消息
      this.wsListener = wsManager.on('new_message', (data: MessageData) => {
        if (data.type === 'new_message' && data.message) {
          this.handleNewMessage(data.message)
        }
      })
      
      this.initialized = true
      console.log('[NotificationManager] Initialized')
    } catch (error) {
      console.error('[NotificationManager] Failed to initialize:', error)
    }
  }

  /**
   * 處理新消息
   */
  private handleNewMessage(message: any): void {
    // 在 miniapp 中顯示通知
    const messageType = message.message_type || 'info'
    const typeMap: Record<string, 'success' | 'error' | 'warning' | 'info'> = {
      redpacket: 'success',
      balance: 'success',
      system: 'info',
      activity: 'warning',
      error: 'error',
    }
    
    const alertType = typeMap[messageType] || 'info'
    showAlert(message.content || message.title || '新消息', alertType, message.title)
  }

  /**
   * 檢查用戶是否在 miniapp 中
   */
  isInMiniapp(): boolean {
    if (typeof window === 'undefined') return false
    
    // 檢查 Telegram WebApp
    const webApp = (window as any).Telegram?.WebApp
    if (webApp) {
      return webApp.isExpanded || true // 如果在 Telegram 環境中，認為是在 miniapp 中
    }
    
    // 檢查是否有用戶信息（本地測試）
    const user = getTelegramUser()
    return !!user
  }

  /**
   * 發送通知（自動判斷方式）
   */
  async notify(
    message: string,
    type: 'success' | 'error' | 'warning' | 'info' = 'info',
    title?: string
  ): Promise<void> {
    // 如果用戶在 miniapp 中，直接顯示
    if (this.isInMiniapp()) {
      showAlert(message, type, title)
    } else {
      // 如果不在 miniapp 中，通知會通過 Telegram Bot 發送（由後端處理）
      // 這裡只記錄日誌
      console.log('[NotificationManager] User not in miniapp, notification will be sent via Telegram')
    }
  }

  /**
   * 僅在 miniapp 中提示
   */
  async notifyInMiniappOnly(
    message: string,
    type: 'success' | 'error' | 'warning' | 'info' = 'info',
    title?: string
  ): Promise<void> {
    if (this.isInMiniapp()) {
      showAlert(message, type, title)
    }
  }

  /**
   * 清理資源
   */
  cleanup(): void {
    if (this.wsListener) {
      this.wsListener()
      this.wsListener = null
    }
    wsManager.disconnect()
    this.initialized = false
  }
}

// 導出單例
export const notificationManager = new NotificationManager()

