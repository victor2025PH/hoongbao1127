import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { ThemeConfig } from 'antd'
import { theme } from 'antd'

export type ThemeMode = 'light' | 'dark'

interface ThemeState {
  mode: ThemeMode
  setMode: (mode: ThemeMode) => void
  toggleMode: () => void
}

const { defaultAlgorithm, darkAlgorithm } = theme

// 护眼主题配置
export const lightTheme: ThemeConfig = {
  algorithm: defaultAlgorithm,
  token: {
    // 护眼浅色主题 - 使用柔和的米白色和浅灰色
    colorPrimary: '#52c41a', // 柔和的绿色
    colorBgBase: '#f7f8fa', // 柔和的浅灰背景
    colorBgContainer: '#ffffff', // 白色容器
    colorBgElevated: '#ffffff', // 白色悬浮层
    colorText: '#2c3e50', // 柔和的深灰文字
    colorTextSecondary: '#6c757d', // 柔和的灰色文字
    colorBorder: '#e1e8ed', // 柔和的边框色
    colorBorderSecondary: '#f0f0f0', // 更柔和的边框色
    borderRadius: 8,
    // 降低对比度，使用更柔和的颜色
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff7875', // 柔和的红色
    colorInfo: '#1890ff',
    // 护眼背景色
    colorFill: '#f5f5f5',
    colorFillSecondary: '#fafafa',
    colorFillTertiary: '#f0f0f0',
  },
}

export const darkTheme: ThemeConfig = {
  algorithm: darkAlgorithm,
  token: {
    // 护眼深色主题 - 使用柔和的深灰和暖色调
    colorPrimary: '#52c41a', // 保持绿色
    colorBgBase: '#1a1a1a', // 柔和的深灰背景（不是纯黑）
    colorBgContainer: '#252525', // 稍亮的深灰容器
    colorBgElevated: '#2d2d2d', // 悬浮层
    colorText: '#e8e8e8', // 柔和的浅色文字
    colorTextSecondary: '#b0b0b0', // 柔和的灰色文字
    colorBorder: '#404040', // 柔和的边框色
    colorBorderSecondary: '#333333', // 更柔和的边框色
    borderRadius: 8,
    // 护眼深色模式下的柔和颜色
    colorSuccess: '#73d13d',
    colorWarning: '#ffc53d',
    colorError: '#ff7875', // 柔和的红色
    colorInfo: '#40a9ff',
    // 护眼深色背景色
    colorFill: '#2d2d2d',
    colorFillSecondary: '#1f1f1f',
    colorFillTertiary: '#141414',
  },
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      mode: 'light',
      setMode: (mode) => set({ mode }),
      toggleMode: () => set((state) => ({ mode: state.mode === 'light' ? 'dark' : 'light' })),
    }),
    {
      name: 'theme-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
)

