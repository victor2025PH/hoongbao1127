import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, Star, Sparkles, UserPlus, Trophy } from 'lucide-react'
import { motion } from 'framer-motion'
import { useTranslation } from '../providers/I18nProvider'
import { checkIn, getCheckInStatus } from '../utils/api'
import { haptic, showAlert, getTelegram } from '../utils/telegram'
import { useSound } from '../hooks/useSound'
import TelegramStar from '../components/TelegramStar'
import PageTransition from '../components/PageTransition'

export default function EarnPage() {
  const { t } = useTranslation()
  const { playSound } = useSound()
  const queryClient = useQueryClient()

  const { data: checkInStatus } = useQuery({
    queryKey: ['checkin-status'],
    queryFn: getCheckInStatus,
  })

  const checkInMutation = useMutation({
    mutationFn: checkIn,
    onSuccess: (data) => {
      haptic('success')
      playSound('success')
      showAlert(`${t('checkin_success')} +${data.reward} points, ${data.streak} days`)
      queryClient.invalidateQueries({ queryKey: ['checkin-status'] })
    },
    onError: (error: Error) => {
      haptic('error')
      playSound('click')
      showAlert(error.message)
    },
  })

  const handleInvite = () => {
    playSound('pop')
    const telegram = getTelegram()
    if (telegram) {
      const inviteLink = `https://t.me/YourBotUsername?start=invite_${Date.now()}`
      telegram.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(inviteLink)}&text=${encodeURIComponent(t('come_grab'))}`)
    }
  }

  const totalDays = 7
  const DURATION = 4 // 動畫週期

  return (
    <PageTransition>
      <div className="h-full flex flex-col p-3 pb-20 gap-3 overflow-y-auto scrollbar-hide">
        {/* 響應式網格 */}
        <div className="flex flex-col lg:grid lg:grid-cols-12 gap-4 h-full">
          {/* 左側/頂部：每日簽到（大） */}
          <div className="lg:col-span-7 bg-[#1C1C1E] border border-white/5 rounded-2xl p-4 shadow-xl relative overflow-hidden shrink-0 group flex flex-col justify-between">
            <div className="absolute top-0 right-0 w-64 h-64 bg-orange-500/5 blur-[80px] rounded-full pointer-events-none" />
            
            <h2 className="text-base font-bold text-white mb-4 relative z-10 pl-1">{t('daily_checkin')}</h2>
            
            {/* 時間線容器 */}
            <div className="relative mb-4 px-2 h-24 flex items-center justify-center">
              <div className="absolute left-[14px] right-[14px] top-[50%] -translate-y-1/2 h-[4px] z-0">
                <div className="w-full h-full bg-[#2C2C2E] rounded-full overflow-hidden relative">
                  <motion.div
                    className="w-[18%] h-full bg-orange-500/50 blur-[1px]"
                    initial={{ width: 0 }}
                    animate={{ width: `${((checkInStatus?.streak || 0) / totalDays) * 100}%` }}
                    transition={{ duration: 0.8 }}
                  />
                </div>
              </div>

              {/* 軌道星星 */}
              <div className="absolute left-[14px] right-[14px] top-[50%] -translate-y-1/2 h-0 pointer-events-none z-0">
                <motion.div
                  className="absolute top-0"
                  style={{ width: 0, height: 0 }}
                  initial={{ left: '0%' }}
                  animate={{ left: '100%' }}
                  transition={{ duration: DURATION, repeat: Infinity, ease: "linear" }}
                >
                  <motion.div
                    animate={{
                      y: [0, -18, 0, 18, 0],
                      scale: [1.3, 1, 0.6, 1, 1.3],
                      zIndex: [30, 20, 0, 20, 30]
                    }}
                    transition={{
                      duration: DURATION / (totalDays - 1) * 2,
                      repeat: Infinity,
                      ease: "linear"
                    }}
                    className="relative flex items-center justify-center"
                  >
                    <TelegramStar size={12} withSpray={false} className="drop-shadow-[0_0_8px_rgba(255,215,0,1)] relative z-20" />
                    {Array.from({ length: 8 }).map((_, i) => (
                      <motion.div
                        key={i}
                        className="absolute bg-white rounded-full blur-[0.5px] z-10"
                        style={{
                          width: Math.random() * 3 + 1,
                          height: Math.random() * 3 + 1
                        }}
                        initial={{ x: 0, y: 0, opacity: 0.6, scale: 1 }}
                        animate={{
                          x: -15 - Math.random() * 30,
                          y: (Math.random() - 0.5) * 4,
                          opacity: 0,
                          scale: 0
                        }}
                        transition={{
                          duration: 0.2 + Math.random() * 0.3,
                          repeat: Infinity,
                          ease: "easeOut",
                          delay: Math.random() * 0.1
                        }}
                      />
                    ))}
                  </motion.div>
                </motion.div>
              </div>

              {/* 龍珠網格 */}
              <div className="w-full flex justify-between relative z-10">
                {Array.from({ length: totalDays }).map((_, i) => {
                  const day = i + 1
                  const isChecked = day <= (checkInStatus?.streak || 0)
                  const isToday = day === (checkInStatus?.streak || 0) + 1 && !checkInStatus?.checked_today
                  const cycleDelay = (i / (totalDays - 1)) * DURATION
                  return (
                    <div key={day} className="flex flex-col items-center gap-3 relative group/day">
                      <motion.div
                        className={`w-9 h-9 rounded-full flex items-center justify-center relative shadow-[inset_-3px_-3px_6px_rgba(0,0,0,0.5),inset_2px_2px_4px_rgba(255,255,255,0.2),0_4px_6px_rgba(0,0,0,0.3)]`}
                        style={{
                          background: isChecked || isToday
                            ? 'radial-gradient(circle at 35% 35%, #fbbf24, #f97316, #ea580c)'
                            : 'radial-gradient(circle at 35% 35%, #52525b, #27272a, #18181b)'
                        }}
                        animate={{
                          scale: [1, 1.2, 1],
                          filter: ['brightness(1)', 'brightness(1.4)', 'brightness(1)']
                        }}
                        transition={{
                          duration: 0.5,
                          repeat: Infinity,
                          delay: cycleDelay,
                          repeatDelay: DURATION - 0.5,
                          ease: "easeOut"
                        }}
                      >
                        {isChecked ? (
                          <Check size={16} strokeWidth={4} className="text-red-900 drop-shadow-sm" />
                        ) : (
                          <Star size={14} className={`${isChecked || isToday ? 'fill-red-600 text-red-700' : 'fill-gray-600 text-gray-700'}`} />
                        )}
                        <div className="absolute top-1.5 left-2 w-2.5 h-1.5 bg-white/30 rounded-full blur-[0.5px] -rotate-45" />
                      </motion.div>
                      <span className={`text-xs font-bold uppercase tracking-wide ${isToday || isChecked ? 'text-white' : 'text-gray-600'}`}>
                        Day {day}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>

            <motion.button
              onClick={() => checkInMutation.mutate()}
              disabled={checkInStatus?.checked_today || checkInMutation.isPending}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-orange-500 to-red-600 text-white font-bold text-sm shadow-lg shadow-orange-500/20 active:scale-[0.98] transition-transform flex items-center justify-center gap-2 relative overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed"
              whileHover={{ scale: checkInStatus?.checked_today ? 1 : 1.02 }}
              whileTap={{ scale: checkInStatus?.checked_today ? 1 : 0.98 }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-100%] animate-shimmer" />
              <Sparkles size={16} className="fill-white" />
              {checkInStatus?.checked_today ? t('checked_in') : checkInMutation.isPending ? t('checking_in') : t('checkin_points')}
            </motion.button>
          </div>

          {/* 右側/底部：操作網格（較小） */}
          <div className="lg:col-span-5 grid grid-cols-2 gap-3 flex-1">
            <motion.div
              onClick={() => { playSound('pop'); handleInvite(); }}
              className="bg-[#1C1C1E] border border-white/5 rounded-2xl p-4 flex flex-col items-center justify-center text-center border-dashed border-2 border-[#2C2C2E] hover:border-orange-500/30 transition-colors cursor-pointer group h-full active:bg-[#252527]"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="w-12 h-12 bg-[#2C2C2E] rounded-full flex items-center justify-center mb-3 group-hover:scale-110 transition-transform shadow-lg group-hover:shadow-orange-500/10">
                <UserPlus className="text-orange-500" size={20} />
              </div>
              <h3 className="text-white text-sm font-bold mb-1.5">{t('invite_friends')}</h3>
              <p className="text-gray-500 text-xs">{t('get_rewards')}</p>
            </motion.div>

            <motion.div
              onClick={() => playSound('pop')}
              className="bg-[#1C1C1E] border border-white/5 rounded-2xl p-4 flex flex-col items-center justify-center text-center border-dashed border-2 border-[#2C2C2E] hover:border-blue-500/30 transition-colors cursor-pointer group h-full active:bg-[#252527]"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="w-12 h-12 bg-[#2C2C2E] rounded-full flex items-center justify-center mb-3 group-hover:scale-110 transition-transform shadow-lg group-hover:shadow-blue-500/10">
                <Trophy className="text-blue-500" size={20} />
              </div>
              <h3 className="text-white text-sm font-bold mb-1.5">{t('tasks')}</h3>
              <p className="text-gray-500 text-xs">{t('complete_for_xp')}</p>
            </motion.div>
          </div>
        </div>

        {/* 重置提示 */}
        <div className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-white/5 rounded-xl p-3 flex items-center justify-between shrink-0">
          <span className="text-xs text-gray-400 font-medium">{t('next_reset')} 12h 30m</span>
          <span className="text-xs text-orange-400 font-bold cursor-pointer hover:underline">{t('view_rules')}</span>
        </div>
      </div>
    </PageTransition>
  )
}
