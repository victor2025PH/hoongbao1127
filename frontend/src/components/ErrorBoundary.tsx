import React, { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    this.setState({
      error,
      errorInfo,
    })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="flex items-center justify-center h-full p-4 bg-brand-dark text-white">
          <div className="text-center space-y-4">
            <h2 className="text-xl font-bold text-red-400">發生錯誤</h2>
            <p className="text-gray-400 text-sm">
              {this.state.error?.message || '未知錯誤'}
            </p>
            {this.state.errorInfo && (
              <details className="text-left text-xs text-gray-500 max-h-40 overflow-auto">
                <summary className="cursor-pointer mb-2">查看詳細信息</summary>
                <pre className="whitespace-pre-wrap">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null, errorInfo: null })
                window.location.reload()
              }}
              className="px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors"
            >
              重新載入
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
