-- 添加 deleted_at 字段到 red_packets 表
ALTER TABLE red_packets ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;

-- 添加 deleted_at 字段到 messages 表（如果需要的話）
ALTER TABLE messages ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
