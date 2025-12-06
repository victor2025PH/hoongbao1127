/**
 * 认证Hook
 * 统一管理用户认证状态
 */
import { useState, useEffect, useCallback } from 'react';
import { detectPlatform, isInTelegram } from '../platform';
import { initTelegram, getTelegramUser } from '../telegram';
import { getCurrentUser, googleAuth, walletAuth, verifyMagicLink } from '../api';

export interface User {
  id: number;
  uuid?: string;
  tg_id?: number;
  username?: string;
  first_name?: string;
  last_name?: string;
  wallet_address?: string;
  wallet_network?: string;
  primary_platform?: string;
  balance_usdt?: number;
  balance_ton?: number;
  balance_stars?: number;
  balance_points?: number;
}

export interface AuthState {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  platform: string;
}

export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    loading: true,
    isAuthenticated: false,
    platform: 'unknown'
  });

  // 初始化认证
  const initAuth = useCallback(async () => {
    try {
      const platformInfo = detectPlatform();
      
      // Telegram环境：自动登录
      if (isInTelegram()) {
        await initTelegram();
        const tgUser = getTelegramUser();
        
        if (tgUser) {
          // 通过Telegram initData获取用户信息
          const response = await getCurrentUser();
          setAuthState({
            user: response.data,
            loading: false,
            isAuthenticated: true,
            platform: 'telegram'
          });
          return;
        }
      }
      
      // Web环境：检查是否有JWT Token
      const token = localStorage.getItem('auth_token');
      if (token) {
        try {
          const response = await getCurrentUser();
          setAuthState({
            user: response.data,
            loading: false,
            isAuthenticated: true,
            platform: platformInfo.platform
          });
          return;
        } catch (error) {
          // Token无效，清除
          localStorage.removeItem('auth_token');
        }
      }
      
      // 未认证
      setAuthState({
        user: null,
        loading: false,
        isAuthenticated: false,
        platform: platformInfo.platform
      });
    } catch (error) {
      console.error('Auth initialization error:', error);
      setAuthState({
        user: null,
        loading: false,
        isAuthenticated: false,
        platform: 'unknown'
      });
    }
  }, []);

  // 登录（Web环境）
  const login = useCallback(async (provider: 'google' | 'wallet', credentials: any) => {
    try {
      let response;
      if (provider === 'google') {
        response = await googleAuth(credentials);
      } else {
        response = await walletAuth(credentials);
      }
      
      // 保存Token
      localStorage.setItem('auth_token', response.data.access_token);
      
      setAuthState({
        user: response.data.user,
        loading: false,
        isAuthenticated: true,
        platform: detectPlatform().platform
      });
      
      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }, []);

  // Magic Link登录
  const loginWithMagicLink = useCallback(async (token: string) => {
    try {
      const response = await verifyMagicLink(token);
      
      // 保存Token
      localStorage.setItem('auth_token', response.data.access_token);
      
      setAuthState({
        user: response.data.user,
        loading: false,
        isAuthenticated: true,
        platform: detectPlatform().platform
      });
      
      return response.data;
    } catch (error) {
      console.error('Magic link login error:', error);
      throw error;
    }
  }, []);

  // 登出
  const logout = useCallback(() => {
    localStorage.removeItem('auth_token');
    setAuthState({
      user: null,
      loading: false,
      isAuthenticated: false,
      platform: detectPlatform().platform
    });
  }, []);

  // 初始化
  useEffect(() => {
    initAuth();
  }, [initAuth]);

  return {
    ...authState,
    login,
    loginWithMagicLink,
    logout,
    refresh: initAuth
  };
}

