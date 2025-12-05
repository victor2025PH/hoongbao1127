/**
 * 调试页面 - 显示所有调试信息
 * 访问方式：在URL后添加 ?debug=1 或 #debug=1
 */
import { useState, useEffect } from 'react'
import { getTelegram, getTelegramUser, getInitData, isTelegramEnv } from '../utils/telegram'

export default function DebugPage() {
  const [logs, setLogs] = useState<string[]>([])
  const [apiTestResult, setApiTestResult] = useState<any>(null)

  const telegram = getTelegram()
  const user = getTelegramUser()
  const initData = getInitData()

  useEffect(() => {
    // 捕获所有console.log
    const originalLog = console.log
    const originalError = console.error
    const originalWarn = console.warn

    console.log = (...args: any[]) => {
      originalLog(...args)
      setLogs(prev => [...prev, `[LOG] ${args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ')}`])
    }

    console.error = (...args: any[]) => {
      originalError(...args)
      setLogs(prev => [...prev, `[ERROR] ${args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ')}`])
    }

    console.warn = (...args: any[]) => {
      originalWarn(...args)
      setLogs(prev => [...prev, `[WARN] ${args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ')}`])
    }

    return () => {
      console.log = originalLog
      console.error = originalError
      console.warn = originalWarn
    }
  }, [])

  const testAPI = async () => {
    try {
      const response = await fetch('/api/v1/tasks/status', {
        headers: {
          'X-Telegram-Init-Data': initData,
        },
      })
      const data = await response.json()
      setApiTestResult({
        status: response.status,
        statusText: response.statusText,
        data,
        headers: Object.fromEntries(response.headers.entries()),
      })
    } catch (error: any) {
      setApiTestResult({
        error: error.message,
        stack: error.stack,
      })
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('已复制到剪贴板')
    })
  }

  return (
    <div style={{ padding: '20px', color: '#fff', backgroundColor: '#1a1a1a', minHeight: '100vh' }}>
      <h1 style={{ marginBottom: '20px' }}>🔍 调试信息</h1>

      {/* Telegram 环境信息 */}
      <section style={{ marginBottom: '30px', padding: '15px', backgroundColor: '#2a2a2a', borderRadius: '8px' }}>
        <h2>📱 Telegram 环境</h2>
        <div style={{ marginTop: '10px' }}>
          <p><strong>是否在Telegram环境:</strong> {isTelegramEnv() ? '✅ 是' : '❌ 否'}</p>
          {telegram && (
            <>
              <p><strong>版本:</strong> {telegram.version}</p>
              <p><strong>平台:</strong> {telegram.platform}</p>
              <p><strong>颜色方案:</strong> {telegram.colorScheme}</p>
              <p><strong>是否展开:</strong> {telegram.isExpanded ? '是' : '否'}</p>
              <p><strong>视口高度:</strong> {telegram.viewportHeight}px</p>
            </>
          )}
        </div>
      </section>

      {/* 用户信息 */}
      <section style={{ marginBottom: '30px', padding: '15px', backgroundColor: '#2a2a2a', borderRadius: '8px' }}>
        <h2>👤 用户信息</h2>
        {user ? (
          <div style={{ marginTop: '10px' }}>
            <p><strong>ID:</strong> {user.id}</p>
            <p><strong>用户名:</strong> {user.username || '无'}</p>
            <p><strong>名字:</strong> {user.first_name || '无'} {user.last_name || ''}</p>
            <p><strong>语言:</strong> {user.language_code || '无'}</p>
          </div>
        ) : (
          <p style={{ color: '#ff6b6b' }}>❌ 未获取到用户信息</p>
        )}
      </section>

      {/* InitData 信息 */}
      <section style={{ marginBottom: '30px', padding: '15px', backgroundColor: '#2a2a2a', borderRadius: '8px' }}>
        <h2>🔐 InitData 信息</h2>
        <div style={{ marginTop: '10px' }}>
          <p><strong>是否有InitData:</strong> {initData ? '✅ 是' : '❌ 否'}</p>
          <p><strong>InitData长度:</strong> {initData?.length || 0}</p>
          {initData && (
            <div style={{ marginTop: '10px' }}>
              <p><strong>InitData (前100字符):</strong></p>
              <pre style={{ 
                padding: '10px', 
                backgroundColor: '#1a1a1a', 
                borderRadius: '4px', 
                overflow: 'auto',
                fontSize: '12px',
                wordBreak: 'break-all'
              }}>
                {initData.substring(0, 100)}...
              </pre>
              <button 
                onClick={() => copyToClipboard(initData)}
                style={{
                  marginTop: '10px',
                  padding: '8px 16px',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                复制完整InitData
              </button>
            </div>
          )}
        </div>
      </section>

      {/* API 测试 */}
      <section style={{ marginBottom: '30px', padding: '15px', backgroundColor: '#2a2a2a', borderRadius: '8px' }}>
        <h2>🌐 API 测试</h2>
        <button
          onClick={testAPI}
          style={{
            marginTop: '10px',
            padding: '10px 20px',
            backgroundColor: '#2196F3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          测试 /api/v1/tasks/status
        </button>
        {apiTestResult && (
          <div style={{ marginTop: '15px' }}>
            <pre style={{
              padding: '10px',
              backgroundColor: '#1a1a1a',
              borderRadius: '4px',
              overflow: 'auto',
              fontSize: '12px',
              maxHeight: '400px'
            }}>
              {JSON.stringify(apiTestResult, null, 2)}
            </pre>
          </div>
        )}
      </section>

      {/* 控制台日志 */}
      <section style={{ marginBottom: '30px', padding: '15px', backgroundColor: '#2a2a2a', borderRadius: '8px' }}>
        <h2>📋 控制台日志</h2>
        <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
          <button
            onClick={() => setLogs([])}
            style={{
              padding: '8px 16px',
              backgroundColor: '#ff6b6b',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            清空日志
          </button>
          <button
            onClick={() => copyToClipboard(logs.join('\n'))}
            style={{
              padding: '8px 16px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            复制所有日志
          </button>
        </div>
        <div style={{
          maxHeight: '400px',
          overflow: 'auto',
          backgroundColor: '#1a1a1a',
          padding: '10px',
          borderRadius: '4px',
          fontSize: '12px',
          fontFamily: 'monospace'
        }}>
          {logs.length === 0 ? (
            <p style={{ color: '#888' }}>暂无日志</p>
          ) : (
            logs.map((log, index) => (
              <div key={index} style={{ marginBottom: '5px', wordBreak: 'break-all' }}>
                {log}
              </div>
            ))
          )}
        </div>
      </section>

      {/* 环境变量 */}
      <section style={{ marginBottom: '30px', padding: '15px', backgroundColor: '#2a2a2a', borderRadius: '8px' }}>
        <h2>⚙️ 环境信息</h2>
        <div style={{ marginTop: '10px' }}>
          <p><strong>User Agent:</strong> {navigator.userAgent}</p>
          <p><strong>当前URL:</strong> {window.location.href}</p>
          <p><strong>API Base URL:</strong> {import.meta.env.VITE_API_URL || '/api'}</p>
        </div>
      </section>
    </div>
  )
}

