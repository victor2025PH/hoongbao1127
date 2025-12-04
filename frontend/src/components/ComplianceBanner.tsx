/**
 * 合規橫幅組件
 * 
 * 在 iOS 平台上顯示，引導用戶訪問網頁版管理資產
 */

import React, { useState } from 'react';
import { useComplianceSettings, usePlatformRules } from '../utils/platformRules';

interface ComplianceBannerProps {
  className?: string;
  dismissible?: boolean;
  variant?: 'full' | 'compact' | 'inline';
}

export const ComplianceBanner: React.FC<ComplianceBannerProps> = ({
  className = '',
  dismissible = true,
  variant = 'full',
}) => {
  const [isDismissed, setIsDismissed] = useState(false);
  const compliance = useComplianceSettings();
  const { platform, isRestricted } = usePlatformRules();

  // 如果不需要顯示橫幅或已被關閉，不渲染
  if (!compliance.showWebPortalBanner || isDismissed) {
    return null;
  }

  const handleOpenWebPortal = () => {
    if (compliance.webPortalUrl) {
      // 嘗試使用 Telegram 的 openLink 方法
      if (window.Telegram?.WebApp?.openLink) {
        window.Telegram.WebApp.openLink(compliance.webPortalUrl);
      } else {
        window.open(compliance.webPortalUrl, '_blank');
      }
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    // 可選：存儲到 localStorage 以記住用戶選擇
    try {
      localStorage.setItem('compliance_banner_dismissed', 'true');
    } catch (e) {
      // localStorage 可能不可用
    }
  };

  // 緊湊版本（適合頁面頂部）
  if (variant === 'compact') {
    return (
      <div
        className={`bg-gradient-to-r from-amber-500/90 to-orange-500/90 text-white px-4 py-2 ${className}`}
      >
        <div className="flex items-center justify-between max-w-screen-lg mx-auto">
          <div className="flex items-center space-x-2 text-sm">
            <span>💼</span>
            <span>{compliance.bannerMessage}</span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleOpenWebPortal}
              className="bg-white/20 hover:bg-white/30 px-3 py-1 rounded text-sm font-medium transition-colors"
            >
              前往網頁版
            </button>
            {dismissible && (
              <button
                onClick={handleDismiss}
                className="text-white/70 hover:text-white p-1"
                aria-label="關閉"
              >
                ✕
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // 內聯版本（適合錢包頁面內）
  if (variant === 'inline') {
    return (
      <div
        className={`bg-amber-50 border border-amber-200 rounded-xl p-4 ${className}`}
      >
        <div className="flex items-start space-x-3">
          <div className="text-2xl">💼</div>
          <div className="flex-1">
            <h4 className="font-semibold text-amber-800 mb-1">
              資產管理
            </h4>
            <p className="text-amber-700 text-sm mb-3">
              {compliance.bannerMessage}
              <br />
              <span className="text-amber-600">
                在網頁版中您可以進行充值、提現和兌換操作。
              </span>
            </p>
            <button
              onClick={handleOpenWebPortal}
              className="bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              🌐 打開網頁版
            </button>
          </div>
          {dismissible && (
            <button
              onClick={handleDismiss}
              className="text-amber-400 hover:text-amber-600 p-1"
              aria-label="關閉"
            >
              ✕
            </button>
          )}
        </div>
      </div>
    );
  }

  // 完整版本（適合作為獨立提示）
  return (
    <div
      className={`bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-2xl p-6 shadow-sm ${className}`}
    >
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-amber-100 rounded-full mb-4">
          <span className="text-3xl">💼</span>
        </div>
        
        <h3 className="text-xl font-bold text-gray-800 mb-2">
          管理您的資產
        </h3>
        
        <p className="text-gray-600 mb-4 max-w-sm mx-auto">
          {compliance.bannerMessage}
        </p>
        
        <div className="bg-white/60 rounded-xl p-4 mb-4">
          <p className="text-sm text-gray-500 mb-2">在網頁版中您可以：</p>
          <ul className="text-sm text-gray-700 space-y-1">
            <li>💳 法幣充值</li>
            <li>💰 提現 USDT</li>
            <li>🔄 幣種兌換</li>
            <li>📊 完整交易歷史</li>
          </ul>
        </div>
        
        <button
          onClick={handleOpenWebPortal}
          className="w-full bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white py-3 px-6 rounded-xl font-semibold transition-all shadow-lg shadow-amber-500/25"
        >
          🌐 立即前往網頁版
        </button>
        
        {dismissible && (
          <button
            onClick={handleDismiss}
            className="mt-3 text-gray-400 hover:text-gray-600 text-sm"
          >
            稍後再說
          </button>
        )}
        
        {/* 平台標識 */}
        <div className="mt-4 text-xs text-gray-400">
          當前平台：{platform === 'ios' ? 'iOS' : platform}
          {isRestricted && ' (受限模式)'}
        </div>
      </div>
    </div>
  );
};

/**
 * 錢包頁面專用的合規通知
 */
export const WalletComplianceNotice: React.FC<{ className?: string }> = ({
  className = '',
}) => {
  const { isRestricted } = usePlatformRules();
  const compliance = useComplianceSettings();

  if (!isRestricted) return null;

  return (
    <div className={`space-y-4 ${className}`}>
      <ComplianceBanner variant="inline" dismissible={false} />
      
      {compliance.showComplianceNotice && (
        <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-500">
          <p>
            📋 根據平台政策，部分金融功能在此版本中不可用。
            這不會影響您的遊戲體驗和 Stars 使用。
          </p>
        </div>
      )}
    </div>
  );
};

/**
 * 功能不可用提示組件
 */
export const FeatureUnavailableCard: React.FC<{
  featureName: string;
  className?: string;
}> = ({ featureName, className = '' }) => {
  const compliance = useComplianceSettings();

  const handleOpenWebPortal = () => {
    if (compliance.webPortalUrl) {
      if (window.Telegram?.WebApp?.openLink) {
        window.Telegram.WebApp.openLink(compliance.webPortalUrl);
      } else {
        window.open(compliance.webPortalUrl, '_blank');
      }
    }
  };

  return (
    <div
      className={`bg-gray-100 rounded-xl p-6 text-center ${className}`}
    >
      <div className="text-4xl mb-3 opacity-50">🔒</div>
      <h4 className="font-semibold text-gray-700 mb-2">
        {featureName} 暫不可用
      </h4>
      <p className="text-gray-500 text-sm mb-4">
        此功能在當前平台不可用，請使用網頁版。
      </p>
      <button
        onClick={handleOpenWebPortal}
        className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
      >
        前往網頁版
      </button>
    </div>
  );
};

export default ComplianceBanner;
