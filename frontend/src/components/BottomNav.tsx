import { NavLink, useLocation } from 'react-router-dom'
import { Wallet, Gift, TrendingUp, Gamepad2, User } from 'lucide-react'
import { motion } from 'framer-motion'
import { useTranslation } from '../providers/I18nProvider'

const navItems = [
  { 
    path: '/', 
    icon: Wallet, 
    labelKey: 'wallet',
    gradient: 'from-cyan-400 to-blue-500',
    shadow: 'shadow-[0_0_15px_rgba(6,182,212,0.5)]',
    iconColor: 'text-cyan-400'
  },
  { 
    path: '/packets', 
    icon: Gift, 
    labelKey: 'packets',
    gradient: 'from-orange-500 to-red-500',
    shadow: 'shadow-[0_0_15px_rgba(249,115,22,0.5)]',
    iconColor: 'text-orange-400'
  },
  { 
    path: '/earn', 
    icon: TrendingUp, 
    labelKey: 'earn',
    gradient: 'from-emerald-400 to-green-500',
    shadow: 'shadow-[0_0_15px_rgba(16,185,129,0.5)]',
    iconColor: 'text-emerald-400'
  },
  { 
    path: '/game', 
    icon: Gamepad2, 
    labelKey: 'game',
    gradient: 'from-purple-400 to-pink-500',
    shadow: 'shadow-[0_0_15px_rgba(168,85,247,0.5)]',
    iconColor: 'text-purple-400'
  },
  { 
    path: '/profile', 
    icon: User, 
    labelKey: 'profile',
    gradient: 'from-gray-200 to-gray-400',
    shadow: 'shadow-[0_0_15px_rgba(255,255,255,0.3)]',
    iconColor: 'text-gray-200'
  },
]

export default function BottomNav() {
  const { t } = useTranslation()
  const location = useLocation()

  return (
    <nav className="fixed bottom-0 left-0 w-full z-50 px-4 pb-4 pt-2 pointer-events-none">
      {/* 玻璃感浮動容器 */}
      <div className="bg-[#15161a]/90 backdrop-blur-2xl border border-white/10 rounded-3xl shadow-2xl h-16 pointer-events-auto max-w-md mx-auto flex items-center justify-between relative px-2 overflow-visible">
        {/* 頂部高光線（玻璃感） */}
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/30 to-transparent rounded-t-3xl" />
        
        {navItems.map(({ path, icon: Icon, labelKey, gradient, shadow, iconColor }) => {
          const isActive = location.pathname === path || (path === '/' && location.pathname === '/')

          return (
            <NavLink
              key={path}
              to={path}
              className="relative flex-1 h-full flex flex-col items-center justify-center gap-1 cursor-pointer outline-none"
            >
              {/* 活動背景指示器（滑動效果） */}
              {isActive && (
                <motion.div
                  layoutId="nav-pill"
                  className="absolute inset-0 mx-auto w-14 h-full rounded-2xl bg-white/5 border border-white/10"
                  initial={false}
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                >
                  {/* 頂部高光（玻璃感） */}
                  <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-white/50 to-transparent rounded-t-2xl" />
                  {/* 底部發光 */}
                  <div className={`absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-1 ${iconColor.replace('text-', 'bg-')} blur-md opacity-70 rounded-full`} />
                </motion.div>
              )}

              {/* 圖標容器 */}
              <motion.div
                className="relative z-10"
                animate={isActive ? {
                  scale: 1.1,
                  rotate: path === '/game' ? [0, -10, 10, 0] : path === '/packets' ? [0, -15, 15, 0] : 0,
                  y: path === '/earn' ? [0, -2, 0] : 0,
                } : {
                  scale: 1,
                  rotate: 0,
                  y: 0
                }}
                transition={{ duration: 0.4, ease: "backOut" }}
              >
                {/* 非活動狀態（輪廓） */}
                <Icon 
                  size={24} 
                  className={`transition-all duration-300 ${isActive ? 'opacity-0 scale-50' : 'text-gray-500 opacity-100'}`} 
                  strokeWidth={1.5}
                />

                {/* 活動狀態（漸變填充） */}
                <div className={`absolute inset-0 transition-all duration-300 ${isActive ? 'opacity-100 scale-100' : 'opacity-0 scale-0'}`}>
                  <Icon 
                    size={24} 
                    className={`${iconColor} drop-shadow-[0_0_8px_currentColor]`}
                    strokeWidth={2.5}
                  />
                </div>
              </motion.div>

              {/* 標籤 */}
              <span className={`text-[9px] font-bold tracking-wide relative z-10 transition-colors duration-300 ${isActive ? 'text-white' : 'text-gray-600'}`}>
                {t(labelKey)}
              </span>
            </NavLink>
          )
        })}
      </div>
    </nav>
  )
}
