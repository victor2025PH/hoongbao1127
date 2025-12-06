"""
迁移脚本：添加Universal Identity System
支持多平台身份认证
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

def column_exists(conn, table_name, column_name):
    """检查列是否存在"""
    inspector = inspect(sync_engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def upgrade():
    """执行迁移"""
    with sync_engine.connect() as conn:
        is_sqlite_db = is_sqlite()
        
        # 1. 添加新字段到users表（兼容SQLite和PostgreSQL）
        columns_to_add = [
            ('uuid', 'TEXT' if is_sqlite_db else 'UUID', 'UNIQUE', None),
            ('wallet_address', 'VARCHAR(255)', None, None),
            ('wallet_network', 'VARCHAR(50)', None, None),
            ('referrer_id', 'INTEGER', None, 'REFERENCES users(id)'),
            ('referral_code', 'VARCHAR(20)', 'UNIQUE', None),
            ('total_referrals', 'INTEGER', None, "DEFAULT 0"),
            ('tier1_commission', 'NUMERIC(5, 2)' if is_sqlite_db else 'DECIMAL(5, 2)', None, "DEFAULT 0.10"),
            ('tier2_commission', 'NUMERIC(5, 2)' if is_sqlite_db else 'DECIMAL(5, 2)', None, "DEFAULT 0.05"),
            ('primary_platform', 'VARCHAR(20)', None, None),
            ('last_active_at', 'DATETIME' if is_sqlite_db else 'TIMESTAMP', None, None),
            ('kyc_status', 'VARCHAR(20)', None, "DEFAULT 'pending'"),
            ('kyc_verified_at', 'DATETIME' if is_sqlite_db else 'TIMESTAMP', None, None),
        ]
        
        for col_name, col_type, col_constraint, col_default in columns_to_add:
            if not column_exists(conn, 'users', col_name):
                if is_sqlite_db:
                    # SQLite不支持IF NOT EXISTS，需要手动检查
                    sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
                    if col_constraint:
                        sql += f" {col_constraint}"
                    if col_default:
                        sql += f" {col_default}"
                    conn.execute(text(sql))
                else:
                    # PostgreSQL支持IF NOT EXISTS
                    sql = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                    if col_constraint:
                        sql += f" {col_constraint}"
                    if col_default:
                        sql += f" {col_default}"
                    conn.execute(text(sql))
        
        # 为uuid生成默认值（SQLite需要）
        if is_sqlite_db:
            # SQLite不支持UUID类型，使用TEXT存储
            # 为现有记录生成UUID
            conn.execute(text("""
                UPDATE users 
                SET uuid = lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(2)) || '-' || hex(randomblob(6)))
                WHERE uuid IS NULL;
            """))
        else:
            # PostgreSQL: 为现有记录生成UUID
            conn.execute(text("""
                UPDATE users 
                SET uuid = gen_random_uuid()
                WHERE uuid IS NULL;
            """))
        
        # 2. 创建user_identities表
        id_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite_db else "SERIAL PRIMARY KEY"
        json_type = "TEXT" if is_sqlite_db else "JSONB"
        timestamp_type = "DATETIME" if is_sqlite_db else "TIMESTAMP"
        default_now = "DEFAULT CURRENT_TIMESTAMP" if is_sqlite_db else "DEFAULT NOW()"
        
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS user_identities (
                id {id_type},
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                provider VARCHAR(50) NOT NULL,
                provider_user_id VARCHAR(255) NOT NULL,
                provider_data {json_type},
                is_primary BOOLEAN DEFAULT 0,
                verified_at {timestamp_type},
                created_at {timestamp_type} {default_now},
                UNIQUE(provider, provider_user_id)
            );
        """))
        
        # 3. 创建account_links表
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS account_links (
                id {id_type},
                user_id INTEGER NOT NULL REFERENCES users(id),
                link_token VARCHAR(64) UNIQUE NOT NULL,
                link_type VARCHAR(20) NOT NULL,
                expires_at {timestamp_type} NOT NULL,
                used_at {timestamp_type},
                metadata {json_type},
                created_at {timestamp_type} {default_now}
            );
        """))
        
        # 4. 创建索引（兼容SQLite和PostgreSQL）
        index_sql = "CREATE INDEX IF NOT EXISTS" if not is_sqlite_db else "CREATE INDEX IF NOT EXISTS"
        # SQLite也支持IF NOT EXISTS，所以可以统一使用
        
        conn.execute(text(f"""
            {index_sql} idx_user_identities_user_id 
            ON user_identities(user_id);
        """))
        
        conn.execute(text(f"""
            {index_sql} idx_user_identities_provider 
            ON user_identities(provider, provider_user_id);
        """))
        
        conn.execute(text(f"""
            {index_sql} idx_users_referral_code 
            ON users(referral_code);
        """))
        
        conn.execute(text(f"""
            {index_sql} idx_account_links_token 
            ON account_links(link_token);
        """))
        
        # 5. 迁移现有Telegram用户到user_identities
        conn.execute(text("""
            INSERT INTO user_identities (user_id, provider, provider_user_id, is_primary, verified_at)
            SELECT id, 'telegram', tg_id::text, TRUE, created_at
            FROM users
            WHERE tg_id IS NOT NULL
            ON CONFLICT (provider, provider_user_id) DO NOTHING;
        """))
        
        # 6. 生成referral_code（如果还没有）
        conn.execute(text("""
            UPDATE users
            SET referral_code = 'REF' || LPAD(id::text, 8, '0')
            WHERE referral_code IS NULL;
        """))
        
        conn.commit()
        print("✅ Universal Identity System migration completed")

def downgrade():
    """回滚迁移"""
    with sync_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS account_links CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS user_identities CASCADE;"))
        conn.execute(text("""
            ALTER TABLE users 
            DROP COLUMN IF EXISTS uuid,
            DROP COLUMN IF EXISTS wallet_address,
            DROP COLUMN IF EXISTS wallet_network,
            DROP COLUMN IF EXISTS referrer_id,
            DROP COLUMN IF EXISTS referral_code,
            DROP COLUMN IF EXISTS total_referrals,
            DROP COLUMN IF EXISTS tier1_commission,
            DROP COLUMN IF EXISTS tier2_commission,
            DROP COLUMN IF EXISTS primary_platform,
            DROP COLUMN IF EXISTS last_active_at,
            DROP COLUMN IF EXISTS kyc_status,
            DROP COLUMN IF EXISTS kyc_verified_at;
        """))
        conn.commit()
        print("✅ Rollback completed")

if __name__ == "__main__":
    upgrade()

