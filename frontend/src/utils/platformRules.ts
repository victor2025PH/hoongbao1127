/**
 * 平台規則工具 - 「變色龍」模式
 * 
 * 根據不同平台動態調整 UI 顯示，符合 Apple/Google App Store 政策
 * iOS: 隱藏金融功能（充值法幣、提現 USDT、兌換）
 * Android/Web: 顯示完整功能
 */

import { useState, useEffect } from 'react';

// ==================== 類型定義 ====================

export type PlatformType = 'ios' | 'android' | 'web' | 'telegram_miniapp';

export interface PlatformFeatures {
  // 金融功能
  showDepositFiat: boolean;      // 顯示法幣充值
  showDepositCrypto: boolean;    // 顯示加密貨幣充值
  showWithdrawUSDT: boolean;     // 顯示 USDT 提現
  showWithdrawCrypto: boolean;   // 顯示加密貨幣提現
  showExchange: boolean;         // 顯示兌換功能
  
  // Stars 相關
  showStarsPurchase: boolean;    // 顯示 Stars 購買
  showStarsConversion: boolean;  // 顯示 Stars 兌換
  
  // 儀表板
  showFullDashboard: boolean;    // 顯示完整財務儀表板
  showWalletBalance: boolean;    // 顯示錢包餘額
  showTransactionHistory: boolean; // 顯示交易歷史
  
  // 遊戲功能（所有平台都可用）
  showRedPackets: boolean;
  showGames: boolean;
}

export interface ComplianceSettings {
  showWebPortalBanner: boolean;  // 顯示網頁版提示橫幅
  bannerMessage: string;         // 橫幅訊息
  webPortalUrl: string;          // 網頁版 URL
  showComplianceNotice: boolean; // 顯示合規聲明
}

export interface PlatformRules {
  platform: PlatformType;
  isRestricted: boolean;         // 是否為受限平台
  features: PlatformFeatures;
  compliance: ComplianceSettings;
}

// ==================== 平台偵測 ====================

/**
 * 偵測當前運行平台
 */
export function detectPlatform(): PlatformType {
  // 1. 檢查是否在 Telegram Mini App 內
  if (typeof window !== 'undefined' && window.Telegram?.WebApp?.initData) {
    // Telegram 內部進一步區分 iOS/Android
    const platform = window.Telegram?.WebApp?.platform?.toLowerCase();
    
    if (platform === 'ios' || platform === 'macos') {
      return 'ios';
    }
    if (platform === 'android') {
      return 'android';
    }
    // 其他 Telegram 平台（desktop 等）視為 web
    return 'telegram_miniapp';
  }

  // 2. 非 Telegram 環境，檢查原生平台
  if (typeof navigator !== 'undefined') {
    const userAgent = navigator.userAgent.toLowerCase();
    
    // 檢查 iOS 裝置（Safari、PWA 或 WebView）
    const isIOS = /ipad|iphone|ipod/.test(userAgent) ||
      (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    
    if (isIOS) {
      return 'ios';
    }
    
    // 檢查 Android 裝置
    const isAndroid = /android/.test(userAgent);
    if (isAndroid) {
      return 'android';
    }
  }

  // 3. 預設為 Web
  return 'web';
}

/**
 * 檢查是否在 Telegram Mini App 內
 */
export function isInTelegram(): boolean {
  return typeof window !== 'undefined' && !!window.Telegram?.WebApp?.initData;
}

/**
 * 檢查是否為 PWA 模式
 */
export function isPWA(): boolean {
  if (typeof window === 'undefined') return false;
  
  return window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as any).standalone === true;
}

// ==================== 平台規則 ====================

/**
 * 獲取當前平台的規則配置
 */
export function getPlatformRules(): PlatformRules {
  const platform = detectPlatform();
  const webPortalUrl = import.meta.env.VITE_WEB_PORTAL_URL || 'https://app.yoursite.com/wallet';

  // iOS 限制模式：符合 App Store 政策
  if (platform === 'ios') {
    return {
      platform,
      isRestricted: true,
      features: {
        // 禁用金融功能
        showDepositFiat: false,
        showDepositCrypto: false,
        showWithdrawUSDT: false,
        showWithdrawCrypto: false,
        showExchange: false,
        
        // 只允許 Stars（遊戲內貨幣）
        showStarsPurchase: true,
        showStarsConversion: false,  // 不允許 Stars 轉換為實際價值
        
        // 限制儀表板
        showFullDashboard: false,
        showWalletBalance: true,     // 可以看餘額
        showTransactionHistory: false,
        
        // 遊戲功能完整保留
        showRedPackets: true,
        showGames: true,
      },
      compliance: {
        showWebPortalBanner: true,
        bannerMessage: '💼 管理您的資產請訪問網頁版',
        webPortalUrl,
        showComplianceNotice: true,
      },
    };
  }

  // Android & Web：完整功能
  return {
    platform,
    isRestricted: false,
    features: {
      showDepositFiat: true,
      showDepositCrypto: true,
      showWithdrawUSDT: true,
      showWithdrawCrypto: true,
      showExchange: true,
      
      showStarsPurchase: true,
      showStarsConversion: true,
      
      showFullDashboard: true,
      showWalletBalance: true,
      showTransactionHistory: true,
      
      showRedPackets: true,
      showGames: true,
    },
    compliance: {
      showWebPortalBanner: false,
      bannerMessage: '',
      webPortalUrl: '',
      showComplianceNotice: false,
    },
  };
}

// ==================== React Hooks ====================

/**
 * React Hook：獲取平台規則
 * 自動響應平台變化
 */
export function usePlatformRules(): PlatformRules {
  const [rules, setRules] = useState<PlatformRules>(() => getPlatformRules());

  useEffect(() => {
    // 初始化時再次檢測（SSR 兼容）
    setRules(getPlatformRules());
    
    // 監聽可能的平台變化（例如：PWA 安裝、視窗大小變化觸發的重新渲染）
    const handleChange = () => {
      const newRules = getPlatformRules();
      setRules(prev => {
        if (prev.platform !== newRules.platform) {
          return newRules;
        }
        return prev;
      });
    };

    // 監聽 resize 事件（某些情況下可能觸發平台重新偵測）
    window.addEventListener('resize', handleChange);
    
    // 監聽 PWA 安裝事件
    window.addEventListener('appinstalled', handleChange);

    return () => {
      window.removeEventListener('resize', handleChange);
      window.removeEventListener('appinstalled', handleChange);
    };
  }, []);

  return rules;
}

/**
 * React Hook：檢查特定功能是否可用
 */
export function useFeatureEnabled(featureName: keyof PlatformFeatures): boolean {
  const rules = usePlatformRules();
  return rules.features[featureName];
}

/**
 * React Hook：獲取合規設定
 */
export function useComplianceSettings(): ComplianceSettings {
  const rules = usePlatformRules();
  return rules.compliance;
}

// ==================== 工具函數 ====================

/**
 * 根據平台過濾功能列表
 * @param features 功能列表
 * @param rules 平台規則
 * @returns 過濾後的功能列表
 */
export function filterFeaturesByPlatform<T extends { featureKey?: keyof PlatformFeatures }>(
  features: T[],
  rules: PlatformRules
): T[] {
  return features.filter(feature => {
    if (!feature.featureKey) return true;
    return rules.features[feature.featureKey];
  });
}

/**
 * 獲取平台顯示名稱
 */
export function getPlatformDisplayName(platform: PlatformType): string {
  const names: Record<PlatformType, string> = {
    ios: 'iOS',
    android: 'Android',
    web: '網頁版',
    telegram_miniapp: 'Telegram',
  };
  return names[platform];
}

/**
 * 檢查是否需要顯示合規橫幅
 */
export function shouldShowComplianceBanner(): boolean {
  const rules = getPlatformRules();
  return rules.compliance.showWebPortalBanner;
}

// ==================== 類型擴展 ====================

// Window.Telegram 類型已在 telegram.ts 中定義，此處不再重複聲明

export default {
  detectPlatform,
  getPlatformRules,
  usePlatformRules,
  useFeatureEnabled,
  useComplianceSettings,
  isInTelegram,
  isPWA,
  filterFeaturesByPlatform,
  getPlatformDisplayName,
  shouldShowComplianceBanner,
};
