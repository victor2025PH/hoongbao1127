import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { getTelegramUser } from '../utils/telegram'

// 語言類型
type Language = 'zh-TW' | 'zh-CN' | 'en'

// 翻譯文本
const translations: Record<Language, Record<string, string>> = {
  'zh-TW': {
    // 導航
    app_name: '幸運紅包',
    wallet: '錢包',
    packets: '紅包',
    earn: '賺取',
    game: '遊戲',
    profile: '我的',
    
    // 錢包頁
    send_red_packet: '發紅包',
    recharge: '充值',
    withdraw: '提現',
    records: '記錄',
    exchange: '兌換',
    total_assets: '總資產',
    
    // 邀請
    invite_friends: '邀請好友',
    get_rewards: '獲得大獎勵',
    permanent_earn: '永久獲得',
    commission: '返佣',
    
    // 簽到
    daily_checkin: '每日簽到',
    checked_in: '已簽到',
    checking_in: '簽到中...',
    checkin_points: '簽到 +20 積分',
    checkin_success: '簽到成功！',
    
    // 任務
    tasks: '任務',
    complete_for_xp: '完成獲得 XP',
    next_reset: '下次重置',
    view_rules: '查看規則',
    
    // 遊戲
    gold_fortune: '金福寶局',
    start_game: '立即開始遊戲',
    hot_games: '熱門遊戲',
    vip_privileges: '尊享特權',
    slots: '電子',
    live: '真人',
    sports: '體育',
    poker: '棋牌',
    lottery: '彩票',
    fishing: '捕魚',
    security: '安全保障',
    vip_benefits: 'VIP禮遇',
    fast_withdraw: '極速出款',
    first_deposit: '首存送30%',
    max_bonus: '最高888元',
    daily_rebate: '每日返水',
    unlimited: '無上限到賬',
    vip_privilege: 'VIP特權',
    exclusive: '專屬禮遇',
    
    // 雷達
    online: '在線',
    packet_groups: '紅包群',
    gaming: '遊戲中',
    target_locked: '目標鎖定',
    active_scan: '主動掃描中...',
    passive_scan: '被動掃描',
    hold_to_scan: '長按掃描',
    
    // 發紅包
    charging: '充電中',
    hold_charge: '長按充能',
    super_charge: '長按超級充能',
    
    // 能量運勢
    energy_full: '已滿',
    great_luck: '大吉',
    good_luck: '中吉',
    small_luck: '小吉',
    normal: '平',
    small_bad: '小凶',
    
    // 紅包頁
    all: '全部',
    crypto: '加密貨幣',
    points: '積分',
    grab: '領取',
    grabbed: '已領完',
    ordinary: '普通',
    lucky: '幸運',
    share_packet: '分享紅包',
    game_group_packet: '遊戲群專屬紅包',
    
    // 個人頁
    security_settings: '安全設置',
    help_center: '幫助中心',
    user_agreement: '用戶協議',
    
    // 充值頁
    select_currency: '選擇幣種',
    quick_amount: '快捷金額',
    custom_amount: '自定義金額',
    deposit_address: '收款地址',
    copy_failed: '複製失敗',
    notice: '注意事項',
    confirm_network: '請確認轉帳網絡為 TRC-20',
    min_deposit: '最低充值金額為 10 USDT',
    auto_credit: '充值到帳後系統自動到帳',
    
    // 提現頁
    withdraw_amount: '提現金額',
    receiving_address: '收款地址',
    enter_address: '請輸入 TRC-20 地址',
    fee: '手續費',
    min_withdraw: '最低提現',
    confirm_address: '請確認地址正確，轉錯無法找回',
    review_time: '提現申請需要 1-24 小時審核',
    large_withdraw: '大額提現可能需要額外審核',
    submitting: '提交中...',
    submit_withdraw: '提交提現',
    withdraw_submitted: '提現申請已提交，請等待審核',
    enter_amount: '請輸入提現金額',
    enter_receiving_address: '請輸入收款地址',
    
    // 通用
    select_group: '選擇群組',
    amount: '金額',
    quantity: '數量',
    message: '祝福語',
    best_wishes: '恭喜發財！',
    send: '發送',
    cancel: '取消',
    confirm: '確認',
    loading: '載入中...',
    no_data: '暫無數據',
    error: '發生錯誤',
    success: '操作成功',
    notifications: '通知',
    sound: '音效',
    language: '語言',
    settings: '設置',
    level: '等級',
    balance: '餘額',
    come_grab: '來一起搶紅包吧！',
  },
  'zh-CN': {
    // 导航
    app_name: '幸运红包',
    wallet: '钱包',
    packets: '红包',
    earn: '赚取',
    game: '游戏',
    profile: '我的',
    
    // 钱包页
    send_red_packet: '发红包',
    recharge: '充值',
    withdraw: '提现',
    records: '记录',
    exchange: '兑换',
    total_assets: '总资产',
    
    // 邀请
    invite_friends: '邀请好友',
    get_rewards: '获得大奖励',
    permanent_earn: '永久获得',
    commission: '返佣',
    
    // 签到
    daily_checkin: '每日签到',
    checked_in: '已签到',
    checking_in: '签到中...',
    checkin_points: '签到 +20 积分',
    checkin_success: '签到成功！',
    
    // 任务
    tasks: '任务',
    complete_for_xp: '完成获得 XP',
    next_reset: '下次重置',
    view_rules: '查看规则',
    
    // 游戏
    gold_fortune: '金福宝局',
    start_game: '立即开始游戏',
    hot_games: '热门游戏',
    vip_privileges: '尊享特权',
    slots: '电子',
    live: '真人',
    sports: '体育',
    poker: '棋牌',
    lottery: '彩票',
    fishing: '捕鱼',
    security: '安全保障',
    vip_benefits: 'VIP礼遇',
    fast_withdraw: '极速出款',
    first_deposit: '首存送30%',
    max_bonus: '最高888元',
    daily_rebate: '每日返水',
    unlimited: '无上限到账',
    vip_privilege: 'VIP特权',
    exclusive: '专属礼遇',
    
    // 雷达
    online: '在线',
    packet_groups: '红包群',
    gaming: '游戏中',
    target_locked: '目标锁定',
    active_scan: '主动扫描中...',
    passive_scan: '被动扫描',
    hold_to_scan: '长按扫描',
    
    // 发红包
    charging: '充电中',
    hold_charge: '长按充能',
    super_charge: '长按超级充能',
    
    // 能量运势
    energy_full: '已满',
    great_luck: '大吉',
    good_luck: '中吉',
    small_luck: '小吉',
    normal: '平',
    small_bad: '小凶',
    
    // 红包页
    all: '全部',
    crypto: '加密货币',
    points: '积分',
    grab: '领取',
    grabbed: '已领完',
    ordinary: '普通',
    lucky: '幸运',
    share_packet: '分享红包',
    game_group_packet: '游戏群专属红包',
    
    // 个人页
    security_settings: '安全设置',
    help_center: '帮助中心',
    user_agreement: '用户协议',
    
    // 充值页
    select_currency: '选择币种',
    quick_amount: '快捷金额',
    custom_amount: '自定义金额',
    deposit_address: '收款地址',
    copy_failed: '复制失败',
    notice: '注意事项',
    confirm_network: '请确认转账网络为 TRC-20',
    min_deposit: '最低充值金额为 10 USDT',
    auto_credit: '充值到账后系统自动到账',
    
    // 提现页
    withdraw_amount: '提现金额',
    receiving_address: '收款地址',
    enter_address: '请输入 TRC-20 地址',
    fee: '手续费',
    min_withdraw: '最低提现',
    confirm_address: '请确认地址正确，转错无法找回',
    review_time: '提现申请需要 1-24 小时审核',
    large_withdraw: '大额提现可能需要额外审核',
    submitting: '提交中...',
    submit_withdraw: '提交提现',
    withdraw_submitted: '提现申请已提交，请等待审核',
    enter_amount: '请输入提现金额',
    enter_receiving_address: '请输入收款地址',
    
    // 通用
    select_group: '选择群组',
    amount: '金额',
    quantity: '数量',
    message: '祝福语',
    best_wishes: '恭喜发财！',
    send: '发送',
    cancel: '取消',
    confirm: '确认',
    loading: '加载中...',
    no_data: '暂无数据',
    error: '发生错误',
    success: '操作成功',
    notifications: '通知',
    sound: '音效',
    language: '语言',
    settings: '设置',
    level: '等级',
    balance: '余额',
    come_grab: '来一起抢红包吧！',
  },
  'en': {
    // Navigation
    app_name: 'Lucky Red Packet',
    wallet: 'Wallet',
    packets: 'Packets',
    earn: 'Earn',
    game: 'Game',
    profile: 'Profile',
    
    // Wallet
    send_red_packet: 'Send Packet',
    recharge: 'Recharge',
    withdraw: 'Withdraw',
    records: 'Records',
    exchange: 'Exchange',
    total_assets: 'Total Assets',
    
    // Invite
    invite_friends: 'Invite Friends',
    get_rewards: 'Get Big Rewards',
    permanent_earn: 'Earn Forever',
    commission: 'Commission',
    
    // Check-in
    daily_checkin: 'Daily Check-in',
    checked_in: 'Checked In',
    checking_in: 'Checking...',
    checkin_points: 'Check-in +20 Points',
    checkin_success: 'Check-in Success!',
    
    // Tasks
    tasks: 'Tasks',
    complete_for_xp: 'Complete for XP',
    next_reset: 'Next Reset',
    view_rules: 'View Rules',
    
    // Game
    gold_fortune: 'Gold Fortune',
    start_game: 'Start Game Now',
    hot_games: 'Hot Games',
    vip_privileges: 'VIP Privileges',
    slots: 'Slots',
    live: 'Live',
    sports: 'Sports',
    poker: 'Poker',
    lottery: 'Lottery',
    fishing: 'Fishing',
    security: 'Security',
    vip_benefits: 'VIP Benefits',
    fast_withdraw: 'Fast Withdraw',
    first_deposit: '30% First Deposit',
    max_bonus: 'Max 888',
    daily_rebate: 'Daily Rebate',
    unlimited: 'Unlimited',
    vip_privilege: 'VIP Privilege',
    exclusive: 'Exclusive',
    
    // Radar
    online: 'Online',
    packet_groups: 'Groups',
    gaming: 'Gaming',
    target_locked: 'Target Locked',
    active_scan: 'Scanning...',
    passive_scan: 'Passive Scan',
    hold_to_scan: 'Hold to Scan',
    
    // Send packet
    charging: 'Charging',
    hold_charge: 'Hold to Charge',
    super_charge: 'Super Charge',
    
    // Energy & Fortune
    energy_full: 'Full',
    great_luck: 'Great',
    good_luck: 'Good',
    small_luck: 'Fair',
    normal: 'Normal',
    small_bad: 'Poor',
    
    // Packets page
    all: 'All',
    crypto: 'Crypto',
    points: 'Points',
    grab: 'Grab',
    grabbed: 'Empty',
    ordinary: 'Ordinary',
    lucky: 'Lucky',
    share_packet: 'Share Packet',
    game_group_packet: 'Game Group Packet',
    
    // Profile page
    security_settings: 'Security',
    help_center: 'Help Center',
    user_agreement: 'Terms of Service',
    
    // Recharge page
    select_currency: 'Select Currency',
    quick_amount: 'Quick Amount',
    custom_amount: 'Custom Amount',
    deposit_address: 'Deposit Address',
    copy_failed: 'Copy Failed',
    notice: 'Notice',
    confirm_network: 'Please confirm network is TRC-20',
    min_deposit: 'Minimum deposit is 10 USDT',
    auto_credit: 'Auto credit after deposit',
    
    // Withdraw page
    withdraw_amount: 'Withdraw Amount',
    receiving_address: 'Receiving Address',
    enter_address: 'Enter TRC-20 address',
    fee: 'Fee',
    min_withdraw: 'Min Withdraw',
    confirm_address: 'Please confirm address, cannot recover if wrong',
    review_time: 'Withdrawal requires 1-24 hours review',
    large_withdraw: 'Large withdrawals may need extra review',
    submitting: 'Submitting...',
    submit_withdraw: 'Submit Withdrawal',
    withdraw_submitted: 'Withdrawal submitted, please wait for review',
    enter_amount: 'Please enter amount',
    enter_receiving_address: 'Please enter receiving address',
    
    // Common
    select_group: 'Select Group',
    amount: 'Amount',
    quantity: 'Quantity',
    message: 'Message',
    best_wishes: 'Best Wishes!',
    send: 'Send',
    cancel: 'Cancel',
    confirm: 'Confirm',
    loading: 'Loading...',
    no_data: 'No Data',
    error: 'Error',
    success: 'Success',
    notifications: 'Notifications',
    sound: 'Sound',
    language: 'Language',
    settings: 'Settings',
    level: 'Level',
    balance: 'Balance',
    come_grab: 'Come grab red packets!',
  },
}

// Context 類型
interface I18nContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: string) => string
}

const I18nContext = createContext<I18nContextType | null>(null)

// 檢測 Telegram 語言
function detectLanguage(): Language {
  const user = getTelegramUser()
  const langCode = user?.language_code || navigator.language || 'zh-CN'
  
  if (langCode.startsWith('zh')) {
    // 繁體中文地區
    if (['zh-TW', 'zh-HK', 'zh-MO'].some(l => langCode.includes(l))) {
      return 'zh-TW'
    }
    return 'zh-CN'
  }
  
  return 'en'
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('language') as Language
    return saved || detectLanguage()
  })

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang)
    localStorage.setItem('language', lang)
  }, [])

  const t = useCallback((key: string): string => {
    return translations[language][key] || key
  }, [language])

  useEffect(() => {
    document.documentElement.lang = language
  }, [language])

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  )
}

export function useTranslation() {
  const context = useContext(I18nContext)
  if (!context) {
    throw new Error('useTranslation must be used within I18nProvider')
  }
  return context
}
