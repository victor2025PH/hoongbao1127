-- 数据库索引优化脚本
-- 用于创建和优化常用查询的索引

-- 1. 用户表索引
CREATE INDEX IF NOT EXISTS idx_users_tg_id ON users(tg_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username) WHERE username IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_referrer_id ON users(referrer_id) WHERE referrer_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- 2. 红包表索引
CREATE INDEX IF NOT EXISTS idx_red_packets_sender_id ON red_packets(sender_id);
CREATE INDEX IF NOT EXISTS idx_red_packets_status ON red_packets(status);
CREATE INDEX IF NOT EXISTS idx_red_packets_currency ON red_packets(currency);
CREATE INDEX IF NOT EXISTS idx_red_packets_created_at ON red_packets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_red_packets_visibility ON red_packets(visibility);
CREATE INDEX IF NOT EXISTS idx_red_packets_status_created ON red_packets(status, created_at DESC);

-- 3. 红包领取表索引
CREATE INDEX IF NOT EXISTS idx_red_packet_claims_packet_id ON red_packet_claims(packet_id);
CREATE INDEX IF NOT EXISTS idx_red_packet_claims_user_id ON red_packet_claims(user_id);
CREATE INDEX IF NOT EXISTS idx_red_packet_claims_created_at ON red_packet_claims(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_red_packet_claims_packet_user ON red_packet_claims(packet_id, user_id);

-- 4. 账本条目表索引
CREATE INDEX IF NOT EXISTS idx_ledger_entries_user_id ON ledger_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_currency ON ledger_entries(currency);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_entry_type ON ledger_entries(entry_type);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_created_at ON ledger_entries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_user_currency ON ledger_entries(user_id, currency);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_user_created ON ledger_entries(user_id, created_at DESC);

-- 5. 交易表索引
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_user_created ON transactions(user_id, created_at DESC);

-- 6. 签到记录索引（如果有单独的表）
-- CREATE INDEX IF NOT EXISTS idx_checkins_user_id ON checkins(user_id);
-- CREATE INDEX IF NOT EXISTS idx_checkins_date ON checkins(checkin_date);

-- 7. 任务完成记录索引（如果有单独的表）
-- CREATE INDEX IF NOT EXISTS idx_task_completions_user_id ON task_completions(user_id);
-- CREATE INDEX IF NOT EXISTS idx_task_completions_task_id ON task_completions(task_id);

-- 8. 复合索引优化（用于常见查询组合）
CREATE INDEX IF NOT EXISTS idx_red_packets_active_public ON red_packets(status, visibility, created_at DESC) 
    WHERE status = 'active' AND visibility = 'public';

-- 9. 部分索引（用于特定条件的查询）
CREATE INDEX IF NOT EXISTS idx_users_active_referrers ON users(referrer_id) 
    WHERE referrer_id IS NOT NULL;

-- 10. 分析表以更新统计信息
ANALYZE users;
ANALYZE red_packets;
ANALYZE red_packet_claims;
ANALYZE ledger_entries;
ANALYZE transactions;

-- 查看索引使用情况
-- SELECT 
--     schemaname,
--     tablename,
--     indexname,
--     idx_scan,
--     idx_tup_read,
--     idx_tup_fetch
-- FROM pg_stat_user_indexes
-- WHERE schemaname = 'public'
-- ORDER BY idx_scan DESC;

