"""
迁移脚本：添加Off-Chain Ledger System
复式记账系统
兼容SQLite和PostgreSQL
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from shared.database.connection import sync_engine

def is_sqlite():
    """检测是否为SQLite数据库"""
    return sync_engine.url.drivername == 'sqlite'

def upgrade():
    """执行迁移"""
    with sync_engine.connect() as conn:
        is_sqlite_db = is_sqlite()
        
        # 根据数据库类型选择合适的数据类型
        id_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite_db else "BIGSERIAL PRIMARY KEY"
        decimal_type = "NUMERIC" if is_sqlite_db else "DECIMAL(20, 8)"
        json_type = "TEXT" if is_sqlite_db else "JSONB"
        timestamp_type = "DATETIME" if is_sqlite_db else "TIMESTAMP"
        default_now = "DEFAULT CURRENT_TIMESTAMP" if is_sqlite_db else "DEFAULT NOW()"
        bigint_type = "INTEGER" if is_sqlite_db else "BIGINT"
        
        # 1. 创建ledger_entries表
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS ledger_entries (
                id {id_type},
                user_id INTEGER NOT NULL REFERENCES users(id),
                amount {decimal_type} NOT NULL,
                currency VARCHAR(10) NOT NULL,
                type VARCHAR(50) NOT NULL,
                related_type VARCHAR(50),
                related_id {bigint_type},
                balance_before {decimal_type} NOT NULL,
                balance_after {decimal_type} NOT NULL,
                metadata {json_type},
                description TEXT,
                created_at {timestamp_type} {default_now},
                created_by VARCHAR(50) DEFAULT 'system'
            );
        """))
        
        # 2. 创建user_balances表（余额快照）
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS user_balances (
                user_id INTEGER PRIMARY KEY REFERENCES users(id),
                usdt_balance {decimal_type} DEFAULT 0,
                ton_balance {decimal_type} DEFAULT 0,
                stars_balance {decimal_type} DEFAULT 0,
                points_balance {decimal_type} DEFAULT 0,
                updated_at {timestamp_type} {default_now}
            );
        """))
        
        # 3. 创建索引（SQLite和PostgreSQL都支持IF NOT EXISTS）
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ledger_user_id 
            ON ledger_entries(user_id);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ledger_type 
            ON ledger_entries(type);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ledger_related 
            ON ledger_entries(related_type, related_id);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ledger_created_at 
            ON ledger_entries(created_at);
        """))
        
        # 4. 初始化user_balances（从现有users表迁移余额）
        conn.execute(text("""
            INSERT INTO user_balances (user_id, usdt_balance, ton_balance, stars_balance, points_balance)
            SELECT 
                id,
                COALESCE(balance_usdt, 0),
                COALESCE(balance_ton, 0),
                COALESCE(balance_stars, 0),
                COALESCE(balance_points, 0)
            FROM users
            ON CONFLICT (user_id) DO UPDATE
            SET 
                usdt_balance = EXCLUDED.usdt_balance,
                ton_balance = EXCLUDED.ton_balance,
                stars_balance = EXCLUDED.stars_balance,
                points_balance = EXCLUDED.points_balance;
        """))
        
        conn.commit()
        print("✅ Ledger System migration completed")

def downgrade():
    """回滚迁移"""
    with sync_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS ledger_entries CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS user_balances CASCADE;"))
        conn.commit()
        print("✅ Rollback completed")

if __name__ == "__main__":
    upgrade()

