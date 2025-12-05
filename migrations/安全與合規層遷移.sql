-- =====================================================================
-- 安全與合規層數據庫遷移腳本
-- 
-- 此腳本添加以下功能所需的表和欄位：
-- 1. 流動性管理（Stars 冷卻期）
-- 2. Magic Link 認證
-- 3. 設備指紋追蹤
-- 4. 反 Sybil 防禦
-- 
-- 執行前請確保已備份數據庫！
-- =====================================================================

-- 1. 添加新的列舉類型
DO $$ BEGIN
    CREATE TYPE currency_source AS ENUM ('real_crypto', 'stars_credit', 'bonus', 'referral');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE withdrawable_status AS ENUM ('locked', 'cooldown', 'withdrawable');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE risk_level AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ledger_category AS ENUM (
        'deposit', 'withdraw', 'send_packet', 'claim_packet', 
        'refund', 'stars_conversion', 'fiat_deposit', 
        'referral_bonus', 'game_win', 'game_loss', 'fee'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


-- 2. 創建帳本條目表（複式記帳）
CREATE TABLE IF NOT EXISTS ledger_entries (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- 交易信息
    currency VARCHAR(20) NOT NULL,
    amount NUMERIC(20, 8) NOT NULL,
    balance_after NUMERIC(20, 8) NOT NULL,
    category ledger_category NOT NULL,
    
    -- 資金來源追蹤
    currency_source currency_source DEFAULT 'real_crypto',
    withdrawable_status withdrawable_status DEFAULT 'withdrawable',
    cooldown_until TIMESTAMP,
    
    -- 流水要求
    turnover_required NUMERIC(20, 8) DEFAULT 0,
    turnover_completed NUMERIC(20, 8) DEFAULT 0,
    
    -- 關聯引用
    ref_type VARCHAR(32),
    ref_id VARCHAR(64),
    paired_entry_id INTEGER REFERENCES ledger_entries(id),
    
    -- 備註
    note TEXT,
    meta_data JSONB,
    
    -- 時間戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 帳本索引
CREATE INDEX IF NOT EXISTS ix_ledger_user_currency ON ledger_entries(user_id, currency);
CREATE INDEX IF NOT EXISTS ix_ledger_user_created ON ledger_entries(user_id, created_at);
CREATE INDEX IF NOT EXISTS ix_ledger_category ON ledger_entries(category);
CREATE INDEX IF NOT EXISTS ix_ledger_ref ON ledger_entries(ref_type, ref_id);
CREATE INDEX IF NOT EXISTS ix_ledger_source_status ON ledger_entries(currency_source, withdrawable_status);
CREATE INDEX IF NOT EXISTS ix_ledger_cooldown ON ledger_entries(cooldown_until);
CREATE INDEX IF NOT EXISTS ix_ledger_uuid ON ledger_entries(uuid);


-- 3. 創建 Magic Link 令牌表
CREATE TABLE IF NOT EXISTS magic_link_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    tg_id BIGINT NOT NULL,
    token VARCHAR(64) UNIQUE NOT NULL,
    
    -- 安全性
    ip_address VARCHAR(64),
    user_agent VARCHAR(512),
    
    -- 狀態
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Magic Link 索引
CREATE INDEX IF NOT EXISTS ix_magic_link_token ON magic_link_tokens(token);
CREATE INDEX IF NOT EXISTS ix_magic_link_tg_id ON magic_link_tokens(tg_id);
CREATE INDEX IF NOT EXISTS ix_magic_link_expires ON magic_link_tokens(expires_at);


-- 4. 創建設備指紋表
CREATE TABLE IF NOT EXISTS device_fingerprints (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    fingerprint_id VARCHAR(64) NOT NULL,
    
    -- 設備信息
    device_info JSONB,
    browser_info JSONB,
    
    -- 風險評估
    confidence_score NUMERIC(5, 4),
    risk_level risk_level DEFAULT 'low',
    
    -- 追蹤
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    request_count INTEGER DEFAULT 0
);

-- 設備指紋索引
CREATE INDEX IF NOT EXISTS ix_fingerprint_id ON device_fingerprints(fingerprint_id);
CREATE INDEX IF NOT EXISTS ix_fingerprint_user ON device_fingerprints(user_id);
CREATE INDEX IF NOT EXISTS ix_fingerprint_risk ON device_fingerprints(risk_level);


-- 5. 創建 IP 會話表
CREATE TABLE IF NOT EXISTS ip_sessions (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(64) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    
    -- 會話信息
    session_id VARCHAR(64),
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 活動統計
    packet_claims INTEGER DEFAULT 0,
    suspicious_actions INTEGER DEFAULT 0,
    
    -- 地理信息
    country_code VARCHAR(2),
    city VARCHAR(128)
);

-- IP 會話索引
CREATE INDEX IF NOT EXISTS ix_ip_session_ip ON ip_sessions(ip_address);
CREATE INDEX IF NOT EXISTS ix_ip_session_user ON ip_sessions(user_id);
CREATE INDEX IF NOT EXISTS ix_ip_session_active ON ip_sessions(is_active);
CREATE INDEX IF NOT EXISTS ix_ip_session_activity ON ip_sessions(last_activity);


-- 6. 創建 Sybil 警報表
CREATE TABLE IF NOT EXISTS sybil_alerts (
    id SERIAL PRIMARY KEY,
    
    -- 關聯信息
    user_id INTEGER REFERENCES users(id),
    ip_address VARCHAR(64),
    fingerprint_id VARCHAR(64),
    
    -- 警報類型
    alert_type VARCHAR(32) NOT NULL,
    alert_code VARCHAR(64) NOT NULL,
    
    -- 詳情
    message TEXT,
    request_path VARCHAR(256),
    request_method VARCHAR(16),
    meta_data JSONB,
    
    -- 處理狀態
    is_reviewed BOOLEAN DEFAULT FALSE,
    reviewed_by INTEGER REFERENCES admin_users(id),
    reviewed_at TIMESTAMP,
    action_taken VARCHAR(64),
    
    -- 時間戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sybil 警報索引
CREATE INDEX IF NOT EXISTS ix_sybil_alert_type ON sybil_alerts(alert_type);
CREATE INDEX IF NOT EXISTS ix_sybil_alert_user ON sybil_alerts(user_id);
CREATE INDEX IF NOT EXISTS ix_sybil_alert_ip ON sybil_alerts(ip_address);
CREATE INDEX IF NOT EXISTS ix_sybil_alert_reviewed ON sybil_alerts(is_reviewed);
CREATE INDEX IF NOT EXISTS ix_sybil_alert_created ON sybil_alerts(created_at);


-- 7. 創建用戶餘額快取表
CREATE TABLE IF NOT EXISTS user_balances (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    currency VARCHAR(20) NOT NULL,
    
    -- 總餘額
    total_balance NUMERIC(20, 8) DEFAULT 0,
    
    -- 按來源分類
    balance_real_crypto NUMERIC(20, 8) DEFAULT 0,
    balance_stars_credit NUMERIC(20, 8) DEFAULT 0,
    balance_bonus NUMERIC(20, 8) DEFAULT 0,
    balance_referral NUMERIC(20, 8) DEFAULT 0,
    
    -- 可提現/鎖定
    withdrawable_balance NUMERIC(20, 8) DEFAULT 0,
    locked_balance NUMERIC(20, 8) DEFAULT 0,
    
    -- 流水
    total_turnover NUMERIC(20, 8) DEFAULT 0,
    pending_turnover NUMERIC(20, 8) DEFAULT 0,
    
    -- 更新時間
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一約束
    CONSTRAINT uq_user_balance_currency UNIQUE (user_id, currency)
);

-- 用戶餘額索引
CREATE INDEX IF NOT EXISTS ix_user_balance_user_currency ON user_balances(user_id, currency);


-- 8. 創建清理過期數據的函數
CREATE OR REPLACE FUNCTION cleanup_expired_magic_links()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM magic_link_tokens 
    WHERE expires_at < NOW() - INTERVAL '1 day'
    OR (is_used = TRUE AND used_at < NOW() - INTERVAL '7 days');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;


-- 9. 創建清理非活躍 IP 會話的函數
CREATE OR REPLACE FUNCTION cleanup_inactive_ip_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    UPDATE ip_sessions 
    SET is_active = FALSE 
    WHERE last_activity < NOW() - INTERVAL '30 minutes'
    AND is_active = TRUE;
    
    DELETE FROM ip_sessions 
    WHERE last_activity < NOW() - INTERVAL '7 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;


-- 10. 創建更新冷卻期狀態的函數
CREATE OR REPLACE FUNCTION update_cooldown_status()
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE ledger_entries 
    SET withdrawable_status = 'withdrawable'
    WHERE withdrawable_status = 'cooldown'
    AND cooldown_until <= NOW()
    AND turnover_completed >= turnover_required;
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;


-- =====================================================================
-- 完成提示
-- =====================================================================
SELECT '安全與合規層遷移完成！' AS status;
SELECT '請確保運行以下定時任務：' AS reminder;
SELECT '1. cleanup_expired_magic_links() - 每小時' AS task1;
SELECT '2. cleanup_inactive_ip_sessions() - 每小時' AS task2;
SELECT '3. update_cooldown_status() - 每天' AS task3;
