import { useEffect, useRef, useCallback, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { getTelegramInitData } from '../utils/telegram'

interface WebSocketMessage {
  type: 'balance_update' | 'packet_claimed' | 'packet_created' | 'notification' | 'pong'
  data: any
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  autoReconnect?: boolean
  reconnectInterval?: number
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    autoReconnect = true,
    reconnectInterval = 5000,
  } = options

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const queryClient = useQueryClient()
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    const initData = getTelegramInitData()
    if (!initData) {
      console.warn('[WebSocket] No init data, skipping connection')
      return
    }

    // 構建 WebSocket URL
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const apiHost = import.meta.env.VITE_API_URL?.replace(/^https?:\/\//, '') || window.location.host
    const wsUrl = `${wsProtocol}//${apiHost}/ws?initData=${encodeURIComponent(initData)}`

    console.log('[WebSocket] Connecting to:', wsUrl)

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('[WebSocket] Connected')
        setIsConnected(true)
        onConnect?.()

        // 開始心跳
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }))
          }
        }, 30000)
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          console.log('[WebSocket] Message:', message.type, message.data)
          setLastMessage(message)

          // 處理不同類型的消息
          switch (message.type) {
            case 'balance_update':
              // 刷新餘額
              queryClient.invalidateQueries({ queryKey: ['balance'] })
              break
            case 'packet_claimed':
              // 刷新紅包列表
              queryClient.invalidateQueries({ queryKey: ['redpackets'] })
              queryClient.invalidateQueries({ queryKey: ['balance'] })
              break
            case 'packet_created':
              // 刷新紅包列表
              queryClient.invalidateQueries({ queryKey: ['redpackets'] })
              break
            case 'notification':
              // 處理通知
              break
            case 'pong':
              // 心跳回應
              break
          }

          onMessage?.(message)
        } catch (err) {
          console.error('[WebSocket] Parse error:', err)
        }
      }

      ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error)
      }

      ws.onclose = (event) => {
        console.log('[WebSocket] Disconnected:', event.code, event.reason)
        setIsConnected(false)
        onDisconnect?.()

        // 清理心跳
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current)
          pingIntervalRef.current = null
        }

        // 自動重連
        if (autoReconnect && event.code !== 1000) {
          console.log(`[WebSocket] Reconnecting in ${reconnectInterval}ms...`)
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval)
        }
      }
    } catch (err) {
      console.error('[WebSocket] Connection error:', err)
    }
  }, [autoReconnect, reconnectInterval, onConnect, onDisconnect, onMessage, queryClient])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }
  }, [])

  const send = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  // 組件掛載時連接，卸載時斷開
  useEffect(() => {
    connect()
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    isConnected,
    lastMessage,
    send,
    connect,
    disconnect,
  }
}

// 簡化的餘額更新 Hook
export function useBalanceUpdates() {
  const queryClient = useQueryClient()
  const [balanceChanged, setBalanceChanged] = useState(false)

  const { isConnected, lastMessage } = useWebSocket({
    onMessage: (message) => {
      if (message.type === 'balance_update') {
        setBalanceChanged(true)
        setTimeout(() => setBalanceChanged(false), 1000)
      }
    },
  })

  // 手動觸發餘額刷新
  const refreshBalance = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['balance'] })
  }, [queryClient])

  return {
    isConnected,
    balanceChanged,
    lastUpdate: lastMessage?.type === 'balance_update' ? lastMessage.data : null,
    refreshBalance,
  }
}
