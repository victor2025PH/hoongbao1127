/**
 * Telegram WebApp SDK 工具
 */

interface TelegramUser {
  id: number
  username?: string
  first_name?: string
  last_name?: string
  language_code?: string
}

interface TelegramWebApp {
  initData: string
  initDataUnsafe: {
    user?: TelegramUser
    auth_date?: number
    hash?: string
  }
  version: string
  platform: string
  colorScheme: 'light' | 'dark'
  themeParams: Record<string, string>
  isExpanded: boolean
  viewportHeight: number
  viewportStableHeight: number
  ready: () => void
  expand: () => void
  close: () => void
  enableClosingConfirmation: () => void
  disableClosingConfirmation: () => void
  showAlert: (message: string, callback?: () => void) => void
  showConfirm: (message: string, callback?: (confirmed: boolean) => void) => void
  showPopup: (params: {
    title?: string
    message: string
    buttons?: Array<{ type?: string; text: string; id?: string }>
  }, callback?: (id: string) => void) => void
  HapticFeedback: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void
    selectionChanged: () => void
  }
  openLink: (url: string) => void
  openTelegramLink: (url: string) => void
}

declare global {
  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp
    }
  }
}

/**
 * 初始化 Telegram WebApp
 */
export function initTelegram(): void {
  const webApp = window.Telegram?.WebApp
  if (!webApp) {
    console.log('[Telegram] Not in Telegram environment')
    return
  }

  try {
    webApp.ready()
    webApp.expand()
    webApp.enableClosingConfirmation()
    console.log('[Telegram] WebApp initialized', {
      version: webApp.version,
      platform: webApp.platform,
      user: webApp.initDataUnsafe.user,
    })
  } catch (error) {
    console.error('[Telegram] Init error:', error)
  }
}

/**
 * 獲取 WebApp 實例
 */
export function getTelegram(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null
}

/**
 * 獲取用戶信息
 */
export function getTelegramUser(): TelegramUser | null {
  return window.Telegram?.WebApp?.initDataUnsafe.user ?? null
}

/**
 * 獲取初始化數據（用於後端驗證）
 */
export function getInitData(): string {
  return window.Telegram?.WebApp?.initData ?? ''
}

/**
 * 是否在 Telegram 環境
 */
export function isTelegramEnv(): boolean {
  return Boolean(window.Telegram?.WebApp)
}

/**
 * 觸覺反饋
 */
export function haptic(type: 'light' | 'medium' | 'heavy' | 'success' | 'error' | 'warning' = 'light'): void {
  const webApp = window.Telegram?.WebApp
  if (!webApp?.HapticFeedback) return

  if (['success', 'error', 'warning'].includes(type)) {
    webApp.HapticFeedback.notificationOccurred(type as 'success' | 'error' | 'warning')
  } else {
    webApp.HapticFeedback.impactOccurred(type as 'light' | 'medium' | 'heavy')
  }
}

// 全局彈窗管理器（用於在 miniapp 內部顯示，而不是使用 Telegram 系統彈窗）
let alertCallback: ((message: string, type?: 'success' | 'error' | 'warning' | 'info', title?: string) => void) | null = null
let confirmCallback: ((message: string, title?: string, confirmText?: string, cancelText?: string) => Promise<boolean>) | null = null

/**
 * 設置 Alert 回調（由組件調用）
 */
export function setAlertCallback(callback: (message: string, type?: 'success' | 'error' | 'warning' | 'info', title?: string) => void) {
  alertCallback = callback
}

/**
 * 設置 Confirm 回調（由組件調用）
 */
export function setConfirmCallback(callback: (message: string, title?: string, confirmText?: string, cancelText?: string) => Promise<boolean>) {
  confirmCallback = callback
}

/**
 * 顯示提示（在 miniapp 內部顯示，不使用 Telegram 系統彈窗）
 */
export function showAlert(message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info', title?: string): Promise<void> {
  return new Promise((resolve) => {
    if (alertCallback) {
      alertCallback(message, type, title)
      // 延遲 resolve，讓用戶有時間看到彈窗
      setTimeout(resolve, 100)
    } else {
      // 如果沒有設置回調，回退到瀏覽器 alert（僅用於開發環境）
      console.warn('[showAlert] Alert callback not set, using fallback')
      alert(message)
      resolve()
    }
  })
}

/**
 * 顯示確認框（在 miniapp 內部顯示，不使用 Telegram 系統彈窗）
 */
export function showConfirm(message: string, title?: string, confirmText?: string, cancelText?: string): Promise<boolean> {
  return new Promise((resolve) => {
    if (confirmCallback) {
      confirmCallback(message, title, confirmText, cancelText).then(resolve)
    } else {
      // 如果沒有設置回調，回退到瀏覽器 confirm（僅用於開發環境）
      console.warn('[showConfirm] Confirm callback not set, using fallback')
      resolve(confirm(message))
    }
  })
}

