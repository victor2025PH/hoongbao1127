import { useState } from 'react'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useThemeStore } from '../stores/themeStore'
import { authApi } from '../utils/api'

export default function Login() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const { mode } = useThemeStore()

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const response = await authApi.login(values.username, values.password)
      if (response.data.success) {
        setAuth(response.data.token, response.data.admin)
        navigate('/')
        message.success('登錄成功')
      } else {
        message.error('登錄失敗')
      }
    } catch (error: any) {
      console.error('Login error:', error)
      const errorMsg = error.response?.data?.detail || error.message || '登錄失敗'
      message.error(errorMsg)
      
      // 临时开发模式：如果登录失败但用户名密码正确，尝试直接设置测试 token
      // 注意：这仅用于开发测试，生产环境必须移除
      if (values.username === 'admin' && values.password === 'admin123' && (import.meta as any).env?.DEV) {
        console.warn('⚠️ 开发模式：使用测试 token 登录')
        try {
          // 直接调用后端生成 token（绕过登录验证）
          const testResponse = await fetch('http://localhost:8080/api/v1/admin/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: 'admin', password: 'admin123' })
          })
          if (testResponse.ok) {
            const data = await testResponse.json()
            setAuth(data.token, data.admin)
            navigate('/')
            message.success('登錄成功（开发模式）')
            return
          }
        } catch (e) {
          console.error('测试登录也失败:', e)
        }
      }
    } finally {
      setLoading(false)
    }
  }

  const bgColor = mode === 'dark' ? '#1a1a1a' : '#f7f8fa'
  const cardBg = mode === 'dark' ? '#252525' : '#ffffff'
  const textColor = mode === 'dark' ? '#e8e8e8' : '#2c3e50'

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh', 
      background: bgColor,
      transition: 'background-color 0.3s ease',
    }}>
      <Card 
        title={<span style={{ color: textColor }}>Lucky Red 管理後台</span>} 
        style={{ 
          width: 400,
          background: cardBg,
          borderColor: mode === 'dark' ? '#404040' : '#e1e8ed',
        }}
      >
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '請輸入用戶名' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="用戶名" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '請輸入密碼' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密碼" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登錄
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

