import { motion } from 'framer-motion'

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg'
  text?: string
  fullScreen?: boolean
}

export default function Loading({ size = 'md', text, fullScreen = false }: LoadingProps) {
  const sizeClasses = {
    sm: 'w-6 h-6 border-2',
    md: 'w-10 h-10 border-3',
    lg: 'w-16 h-16 border-4',
  }

  const content = (
    <div className="flex flex-col items-center justify-center gap-3">
      <motion.div
        className={`${sizeClasses[size]} border-orange-500 border-t-transparent rounded-full`}
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      />
      {text && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-gray-400 text-sm"
        >
          {text}
        </motion.p>
      )}
    </div>
  )

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-brand-dark/80 backdrop-blur-sm">
        {content}
      </div>
    )
  }

  return content
}

// 骨架屏組件
export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <motion.div
      className={`bg-white/5 rounded ${className}`}
      animate={{ opacity: [0.5, 1, 0.5] }}
      transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
    />
  )
}

// 紅包列表骨架屏
export function PacketSkeleton() {
  return (
    <div className="p-3 bg-[#1C1C1E] border border-white/5 rounded-xl flex items-center gap-3">
      <Skeleton className="w-10 h-10 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-3 w-32" />
        <Skeleton className="h-1 w-20 mt-1" />
      </div>
      <div className="space-y-1">
        <Skeleton className="h-7 w-[90px]" />
        <Skeleton className="h-8 w-[90px]" />
      </div>
    </div>
  )
}

// 餘額卡片骨架屏
export function BalanceSkeleton() {
  return (
    <div className="p-4 bg-[#1C1C1E] border border-white/5 rounded-2xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-4 w-20" />
        </div>
        <Skeleton className="w-10 h-10 rounded-full" />
      </div>
      <div className="grid grid-cols-3 gap-3">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-16 rounded-xl" />
        ))}
      </div>
    </div>
  )
}

// 脈動動畫包裝器
export function PulseWrapper({ children, active = false }: { children: React.ReactNode; active?: boolean }) {
  if (!active) return <>{children}</>
  
  return (
    <motion.div
      animate={{
        scale: [1, 1.02, 1],
        boxShadow: [
          '0 0 0 0 rgba(249, 115, 22, 0)',
          '0 0 0 8px rgba(249, 115, 22, 0.2)',
          '0 0 0 0 rgba(249, 115, 22, 0)',
        ],
      }}
      transition={{ duration: 1.5, repeat: Infinity }}
    >
      {children}
    </motion.div>
  )
}
