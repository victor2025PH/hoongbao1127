import { useState, useRef, useCallback } from 'react'
import { motion, useMotionValue, useTransform } from 'framer-motion'
import { RefreshCw } from 'lucide-react'

interface PullToRefreshProps {
  children: React.ReactNode
  onRefresh: () => Promise<void>
  threshold?: number
  disabled?: boolean
}

export default function PullToRefresh({
  children,
  onRefresh,
  threshold = 80,
  disabled = false,
}: PullToRefreshProps) {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const startY = useRef(0)
  const containerRef = useRef<HTMLDivElement>(null)
  const pullDistance = useMotionValue(0)

  const indicatorOpacity = useTransform(pullDistance, [0, threshold / 2, threshold], [0, 0.5, 1])
  const indicatorScale = useTransform(pullDistance, [0, threshold], [0.5, 1])
  const indicatorRotate = useTransform(pullDistance, [0, threshold], [0, 180])

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (disabled || isRefreshing) return
    
    const container = containerRef.current
    if (container && container.scrollTop <= 0) {
      startY.current = e.touches[0].clientY
    }
  }, [disabled, isRefreshing])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (disabled || isRefreshing || startY.current === 0) return

    const container = containerRef.current
    if (!container || container.scrollTop > 0) {
      startY.current = 0
      pullDistance.set(0)
      return
    }

    const currentY = e.touches[0].clientY
    const diff = Math.max(0, currentY - startY.current)
    
    // 阻尼效果
    const dampedDiff = Math.min(diff * 0.5, threshold * 1.5)
    pullDistance.set(dampedDiff)

    if (diff > 10) {
      e.preventDefault()
    }
  }, [disabled, isRefreshing, pullDistance, threshold])

  const handleTouchEnd = useCallback(async () => {
    if (disabled || isRefreshing) return

    const distance = pullDistance.get()
    
    if (distance >= threshold) {
      setIsRefreshing(true)
      try {
        await onRefresh()
      } finally {
        setIsRefreshing(false)
      }
    }

    pullDistance.set(0)
    startY.current = 0
  }, [disabled, isRefreshing, onRefresh, pullDistance, threshold])

  return (
    <div className="relative h-full">
      {/* 刷新指示器 */}
      <motion.div
        className="absolute top-0 left-0 right-0 flex items-center justify-center z-10 pointer-events-none"
        style={{
          height: pullDistance,
          opacity: indicatorOpacity,
        }}
      >
        <motion.div
          className="w-10 h-10 bg-white/10 rounded-full flex items-center justify-center"
          style={{ scale: indicatorScale }}
        >
          {isRefreshing ? (
            <RefreshCw size={20} className="text-orange-500 animate-spin" />
          ) : (
            <motion.div style={{ rotate: indicatorRotate }}>
              <RefreshCw size={20} className="text-orange-500" />
            </motion.div>
          )}
        </motion.div>
      </motion.div>

      {/* 內容區域 */}
      <motion.div
        ref={containerRef}
        className="h-full overflow-y-auto"
        style={{ y: pullDistance }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {children}
      </motion.div>
    </div>
  )
}
