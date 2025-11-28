/**
 * WebSocket 連接管理
 */
import { getTelegramUser } from './telegram'

export type MessageData = {
  type: 'new_message' | 'ping' | 'pong'
  message?: {
    id: number
    message_type: string
    title?: string
    content: string
    action_url?: string
    created_at: string
  }
}

class WebSocketManager {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private heartbeatInterval: number | null = null
  private listeners: Map<string, Set<(data: MessageData) => void>> = new Map()
  private isConnecting = false

  /**
   * 連接 WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      if (this.isConnecting) {
        // 等待現有連接完成
        const checkInterval = setInterval(() => {
          if (!this.isConnecting) {
            clearInterval(checkInterval)
            if (this.ws?.readyState === WebSocket.OPEN) {
              resolve()
            } else {
              reject(new Error('Connection failed'))
            }
          }
        }, 100)
        return
      }

      this.isConnecting = true

      try {
        // 獲取 initData
        const user = getTelegramUser()
        let wsUrl = 'ws://localhost:8080/api/v1/messages/ws'
        
        if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
          // 生產環境使用 wss
          const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
          wsUrl = `${protocol}//${window.location.host}/api/v1/messages/ws`
        }

        // 添加 initData 到查詢參數
        if (user && (window as any).Telegram?.WebApp?.initData) {
          const initData = (window as any).Telegram.WebApp.initData
          wsUrl += `?init_data=${encodeURIComponent(initData)}`
        } else if (user?.id) {
          // 本地測試：使用 localStorage 中的 tg_id 或 user.id
          const tgId = localStorage.getItem('tg_id') || user.id.toString()
          // 構建一個簡單的 initData 格式
          const userData = JSON.stringify({ id: parseInt(tgId) })
          wsUrl += `?init_data=user=${encodeURIComponent(userData)}`
        } else {
          // 如果沒有用戶信息，嘗試從 localStorage 獲取
          const tgId = localStorage.getItem('tg_id')
          if (tgId) {
            const userData = JSON.stringify({ id: parseInt(tgId) })
            wsUrl += `?init_data=user=${encodeURIComponent(userData)}`
          }
        }

        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected')
          this.isConnecting = false
          this.reconnectAttempts = 0
          this.startHeartbeat()
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            // 處理文本消息（心跳）
            if (typeof event.data === 'string') {
              if (event.data === 'pong') {
                // 心跳響應，不需要處理
                return
              }
              // 嘗試解析 JSON
              const data: MessageData = JSON.parse(event.data)
              
              // 觸發所有監聽器
              this.listeners.forEach((callbacks) => {
                callbacks.forEach((callback) => {
                  try {
                    callback(data)
                  } catch (error) {
                    console.error('[WebSocket] Listener error:', error)
                  }
                })
              })
            }
          } catch (error) {
            // 如果不是 JSON，可能是純文本，忽略
            if (event.data !== 'pong') {
              console.error('[WebSocket] Parse error:', error, 'Data:', event.data)
            }
          }
        }

        this.ws.onerror = (error) => {
          console.error('[WebSocket] Error:', error)
          this.isConnecting = false
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('[WebSocket] Disconnected')
          this.isConnecting = false
          this.stopHeartbeat()
          
          // 嘗試重連
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
            console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
            setTimeout(() => {
              this.connect().catch(console.error)
            }, delay)
          } else {
            console.error('[WebSocket] Max reconnection attempts reached')
          }
        }
      } catch (error) {
        this.isConnecting = false
        reject(error)
      }
    })
  }

  /**
   * 斷開連接
   */
  disconnect(): void {
    this.stopHeartbeat()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.listeners.clear()
  }

  /**
   * 添加消息監聽器
   */
  on(event: string, callback: (data: MessageData) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(callback)

    // 返回取消監聽的函數
    return () => {
      const callbacks = this.listeners.get(event)
      if (callbacks) {
        callbacks.delete(callback)
        if (callbacks.size === 0) {
          this.listeners.delete(event)
        }
      }
    }
  }

  /**
   * 發送消息
   */
  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('[WebSocket] Not connected, cannot send message')
    }
  }

  /**
   * 開始心跳
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send('ping')
      }
    }, 30000) // 每 30 秒發送一次心跳
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval !== null) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  /**
   * 檢查是否已連接
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

// 導出單例
export const wsManager = new WebSocketManager()

