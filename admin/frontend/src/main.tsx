import React, { useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import App from './App'
import './index.css'
import { useThemeStore, lightTheme, darkTheme } from './stores/themeStore'

dayjs.locale('zh-cn')

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function AppWithTheme() {
  const { mode } = useThemeStore()
  const theme = mode === 'dark' ? darkTheme : lightTheme

  // 设置 body 的 data-theme 属性，用于 CSS 选择器
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode)
    document.body.style.backgroundColor = mode === 'dark' ? '#1a1a1a' : '#f7f8fa'
    document.body.style.color = mode === 'dark' ? '#e8e8e8' : '#2c3e50'
    document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease'
  }, [mode])

  return (
    <ConfigProvider locale={zhCN} theme={theme}>
      <App />
    </ConfigProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AppWithTheme />
    </QueryClientProvider>
  </React.StrictMode>,
)

