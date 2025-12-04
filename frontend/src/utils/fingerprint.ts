/**
 * 設備指紋工具
 * 
 * 用於反 Sybil 攻擊檢測
 * 整合 FingerprintJS 進行設備識別
 */

import type { AxiosInstance } from 'axios';

// ==================== 類型定義 ====================

export interface FingerprintResult {
  visitorId: string;
  confidence: number;
  components?: Record<string, any>;
}

export interface DeviceInfo {
  fingerprint: string;
  platform: string;
  userAgent: string;
  screenResolution: string;
  timezone: string;
  language: string;
  colorDepth: number;
  deviceMemory?: number;
  hardwareConcurrency?: number;
  touchSupport: boolean;
}

// ==================== 指紋獲取 ====================

let fpPromise: Promise<any> | null = null;
let cachedFingerprint: string | null = null;

/**
 * 初始化 FingerprintJS
 * 使用動態導入以支持 tree-shaking
 */
async function initFingerprint(): Promise<any> {
  if (!fpPromise) {
    // 動態導入 FingerprintJS
    // 生產環境建議使用 FingerprintJS Pro 以獲得更高精確度
    try {
      const FingerprintJS = await import('@fingerprintjs/fingerprintjs');
      fpPromise = FingerprintJS.load();
    } catch (e) {
      console.warn('[Fingerprint] FingerprintJS not available, using fallback');
      fpPromise = Promise.resolve(null);
    }
  }
  return fpPromise;
}

/**
 * 獲取設備指紋
 * 優先使用 FingerprintJS，失敗時使用備用方案
 */
export async function getDeviceFingerprint(): Promise<string> {
  // 使用快取
  if (cachedFingerprint) {
    return cachedFingerprint;
  }

  try {
    const fp = await initFingerprint();
    
    if (fp) {
      const result = await fp.get();
      cachedFingerprint = result.visitorId;
      return cachedFingerprint;
    }
  } catch (e) {
    console.warn('[Fingerprint] Error getting fingerprint:', e);
  }

  // 備用方案：使用瀏覽器特徵生成簡單指紋
  cachedFingerprint = generateFallbackFingerprint();
  return cachedFingerprint;
}

/**
 * 備用指紋生成方案
 * 當 FingerprintJS 不可用時使用
 */
function generateFallbackFingerprint(): string {
  const components: string[] = [];

  // 收集瀏覽器特徵
  if (typeof navigator !== 'undefined') {
    components.push(navigator.userAgent);
    components.push(navigator.language);
    components.push(String(navigator.hardwareConcurrency || 'unknown'));
    components.push(String((navigator as any).deviceMemory || 'unknown'));
  }

  if (typeof screen !== 'undefined') {
    components.push(`${screen.width}x${screen.height}`);
    components.push(String(screen.colorDepth));
  }

  // 時區
  components.push(Intl.DateTimeFormat().resolvedOptions().timeZone);

  // Canvas 指紋（簡化版）
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.textBaseline = 'top';
      ctx.font = '14px Arial';
      ctx.fillText('fingerprint', 2, 2);
      components.push(canvas.toDataURL().slice(-50));
    }
  } catch (e) {
    // Canvas 不可用
  }

  // 生成哈希
  const fingerprint = hashString(components.join('|'));
  return fingerprint;
}

/**
 * 簡單字符串哈希函數
 */
function hashString(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  // 轉換為 16 進制字符串
  return Math.abs(hash).toString(16).padStart(8, '0');
}

/**
 * 獲取完整的設備信息
 */
export function getDeviceInfo(): DeviceInfo {
  const info: DeviceInfo = {
    fingerprint: cachedFingerprint || 'pending',
    platform: detectPlatformString(),
    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
    screenResolution: typeof screen !== 'undefined' 
      ? `${screen.width}x${screen.height}` 
      : 'unknown',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: typeof navigator !== 'undefined' ? navigator.language : 'unknown',
    colorDepth: typeof screen !== 'undefined' ? screen.colorDepth : 0,
    touchSupport: typeof navigator !== 'undefined' && 'maxTouchPoints' in navigator
      ? navigator.maxTouchPoints > 0
      : false,
  };

  if (typeof navigator !== 'undefined') {
    info.deviceMemory = (navigator as any).deviceMemory;
    info.hardwareConcurrency = navigator.hardwareConcurrency;
  }

  return info;
}

/**
 * 偵測平台字符串
 */
function detectPlatformString(): string {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp?.platform) {
    return `telegram_${window.Telegram.WebApp.platform}`;
  }

  if (typeof navigator !== 'undefined') {
    const ua = navigator.userAgent.toLowerCase();
    if (/iphone|ipad|ipod/.test(ua)) return 'ios';
    if (/android/.test(ua)) return 'android';
    if (/windows/.test(ua)) return 'windows';
    if (/macintosh|mac os/.test(ua)) return 'macos';
    if (/linux/.test(ua)) return 'linux';
  }

  return 'unknown';
}

// ==================== API 整合 ====================

/**
 * 設置 Axios 攔截器，自動添加指紋到請求頭
 */
export function setupFingerprintInterceptor(api: AxiosInstance): void {
  api.interceptors.request.use(async (config) => {
    try {
      const fingerprint = await getDeviceFingerprint();
      config.headers['X-Fingerprint-ID'] = fingerprint;
      
      // 可選：添加完整設備信息（用於風險評估）
      const deviceInfo = getDeviceInfo();
      config.headers['X-Device-Platform'] = deviceInfo.platform;
    } catch (e) {
      console.warn('[Fingerprint] Failed to add fingerprint header:', e);
    }
    return config;
  });
}

/**
 * 發送設備信息到服務器進行註冊/更新
 */
export async function registerDeviceFingerprint(
  api: AxiosInstance,
  userId?: number
): Promise<void> {
  try {
    const fingerprint = await getDeviceFingerprint();
    const deviceInfo = getDeviceInfo();
    
    await api.post('/api/v2/security/fingerprint', {
      fingerprint_id: fingerprint,
      device_info: deviceInfo,
      user_id: userId,
    });
  } catch (e) {
    console.warn('[Fingerprint] Failed to register device:', e);
  }
}

// ==================== 風險評估 ====================

/**
 * 本地風險檢測（輔助服務端）
 */
export function detectLocalRisks(): string[] {
  const risks: string[] = [];

  // 檢測是否使用自動化工具
  if (typeof navigator !== 'undefined') {
    // @ts-ignore
    if (navigator.webdriver) {
      risks.push('webdriver_detected');
    }

    // 檢測 Puppeteer/Playwright
    // @ts-ignore
    if (window._phantom || window.__nightmare || window.callPhantom) {
      risks.push('automation_framework_detected');
    }
  }

  // 檢測 DevTools 是否打開（可能是調試/逆向）
  const devToolsThreshold = 160;
  if (
    window.outerWidth - window.innerWidth > devToolsThreshold ||
    window.outerHeight - window.innerHeight > devToolsThreshold
  ) {
    risks.push('devtools_possibly_open');
  }

  // 檢測是否在 iframe 中（可能是點擊劫持）
  if (window.self !== window.top) {
    risks.push('iframe_detected');
  }

  return risks;
}

/**
 * 獲取本地風險評分（0-1）
 */
export function getLocalRiskScore(): number {
  const risks = detectLocalRisks();
  
  // 基礎分數
  let score = 0;
  
  // 每個風險因素增加分數
  const riskWeights: Record<string, number> = {
    webdriver_detected: 0.4,
    automation_framework_detected: 0.5,
    devtools_possibly_open: 0.1,
    iframe_detected: 0.2,
  };

  for (const risk of risks) {
    score += riskWeights[risk] || 0.1;
  }

  return Math.min(score, 1);
}

// ==================== 導出 ====================

export default {
  getDeviceFingerprint,
  getDeviceInfo,
  setupFingerprintInterceptor,
  registerDeviceFingerprint,
  detectLocalRisks,
  getLocalRiskScore,
};
