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
        # 注意：SQLite中'type'是保留字，需要用引号括起来
        type_column = '"type"' if is_sqlite_db else 'type'
        
        # 检查表是否已存在
        inspector = inspect(sync_engine)
        table_exists = 'ledger_entries' in inspector.get_table_names()
        
        if not table_exists:
            # 创建新表
            conn.execute(text(f"""
                CREATE TABLE ledger_entries (
                    id {id_type},
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    amount {decimal_type} NOT NULL,
                    currency VARCHAR(10) NOT NULL,
                    {type_column} VARCHAR(50) NOT NULL,
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
            conn.commit()
            print("✅ Created ledger_entries table")
        else:
            # 表已存在，检查并添加缺失的列
            columns = [col['name'] for col in inspector.get_columns('ledger_entries')]
            print(f"📋 Existing columns: {columns}")
            
            required_columns = {
                'related_type': 'VARCHAR(50)',
                'related_id': bigint_type,
                'balance_before': decimal_type,
                'balance_after': decimal_type,
                'metadata': json_type,
                'description': 'TEXT',
                'created_at': timestamp_type,
                'created_by': 'VARCHAR(50)'
            }
            
            # 检查type列（可能是保留字）
            type_col_name = type_column.replace('"', '')
            if type_col_name not in columns and 'type' not in columns:
                required_columns[type_col_name] = 'VARCHAR(50)'
            
            for col_name, col_type in required_columns.items():
                if col_name not in columns:
                    print(f"➕ Adding missing column: {col_name}")
                    try:
                        if col_name == type_col_name and is_sqlite_db:
                            # SQLite中type是保留字，需要特殊处理
                            conn.execute(text(f'ALTER TABLE ledger_entries ADD COLUMN "{col_name}" {col_type};'))
                        else:
                            conn.execute(text(f"ALTER TABLE ledger_entries ADD COLUMN {col_name} {col_type};"))
                        conn.commit()
                    except Exception as e:
                        print(f"⚠️ Could not add column {col_name}: {e}")
        
        # 2. 创建user_balances表（余额快照）
        inspector = inspect(sync_engine)
        balances_table_exists = 'user_balances' in inspector.get_table_names()
        
        if not balances_table_exists:
            # 创建新表
            conn.execute(text(f"""
                CREATE TABLE user_balances (
                    user_id INTEGER PRIMARY KEY REFERENCES users(id),
                    usdt_balance {decimal_type} DEFAULT 0,
                    ton_balance {decimal_type} DEFAULT 0,
                    stars_balance {decimal_type} DEFAULT 0,
                    points_balance {decimal_type} DEFAULT 0,
                    updated_at {timestamp_type} {default_now}
                );
            """))
            conn.commit()
            print("✅ Created user_balances table")
        else:
            # 表已存在，检查并添加缺失的列
            columns = [col['name'] for col in inspector.get_columns('user_balances')]
            print(f"📋 Existing user_balances columns: {columns}")
            
            required_columns = {
                'usdt_balance': decimal_type,
                'ton_balance': decimal_type,
                'stars_balance': decimal_type,
                'points_balance': decimal_type,
                'updated_at': timestamp_type
            }
            
            for col_name, col_type in required_columns.items():
                if col_name not in columns:
                    print(f"➕ Adding missing column to user_balances: {col_name}")
                    try:
                        if col_name == 'updated_at':
                            conn.execute(text(f"ALTER TABLE user_balances ADD COLUMN {col_name} {col_type} {default_now};"))
                        else:
                            conn.execute(text(f"ALTER TABLE user_balances ADD COLUMN {col_name} {col_type} DEFAULT 0;"))
                        conn.commit()
                    except Exception as e:
                        print(f"⚠️ Could not add column {col_name} to user_balances: {e}")
        
        # 3. 创建索引（SQLite和PostgreSQL都支持IF NOT EXISTS）
        # 注意：SQLite中'type'是保留字，需要用引号括起来
        type_column = '"type"' if is_sqlite_db else 'type'
        
        # 检查表是否存在
        inspector = inspect(sync_engine)
        if 'ledger_entries' not in inspector.get_table_names():
            print("❌ ledger_entries table does not exist, cannot create indexes")
            return
        
        # 检查列是否存在
        columns = [col['name'] for col in inspector.get_columns('ledger_entries')]
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ledger_user_id 
                ON ledger_entries(user_id);
            """))
        except Exception as e:
            print(f"⚠️ Could not create idx_ledger_user_id: {e}")
        
        if type_column.replace('"', '') in columns or 'type' in columns:
            try:
                conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_ledger_type 
                    ON ledger_entries({type_column});
                """))
            except Exception as e:
                print(f"⚠️ Could not create idx_ledger_type: {e}")
        
        if 'related_type' in columns and 'related_id' in columns:
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_ledger_related 
                    ON ledger_entries(related_type, related_id);
                """))
            except Exception as e:
                print(f"⚠️ Could not create idx_ledger_related: {e}")
        else:
            print(f"⚠️ Skipping idx_ledger_related - columns missing: related_type={('related_type' in columns)}, related_id={('related_id' in columns)}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ledger_created_at 
                ON ledger_entries(created_at);
            """))
        except Exception as e:
            print(f"⚠️ Could not create idx_ledger_created_at: {e}")
        
        # 4. 初始化user_balances（从现有users表迁移余额）
        # 先检查列是否存在
        inspector = inspect(sync_engine)
        if 'user_balances' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('user_balances')]
            required_cols = ['usdt_balance', 'ton_balance', 'stars_balance', 'points_balance']
            
            if all(col in columns for col in required_cols):
                # 检查users表是否有这些列
                users_columns = [col['name'] for col in inspector.get_columns('users')]
                users_balance_cols = ['balance_usdt', 'balance_ton', 'balance_stars', 'balance_points']
                
                if all(col in users_columns for col in users_balance_cols):
                    # 检查user_balances表是否有currency列（可能是NOT NULL）
                    has_currency = 'currency' in columns
                    
                    if is_sqlite_db:
                        # SQLite: 使用UPDATE或INSERT OR REPLACE
                        if has_currency:
                            # 如果currency列存在且是NOT NULL，需要包含它
                            # 先尝试UPDATE现有记录
                            conn.execute(text("""
                                UPDATE user_balances
                                SET 
                                    usdt_balance = COALESCE((SELECT balance_usdt FROM users WHERE users.id = user_balances.user_id), 0),
                                    ton_balance = COALESCE((SELECT balance_ton FROM users WHERE users.id = user_balances.user_id), 0),
                                    stars_balance = COALESCE((SELECT balance_stars FROM users WHERE users.id = user_balances.user_id), 0),
                                    points_balance = COALESCE((SELECT balance_points FROM users WHERE users.id = user_balances.user_id), 0)
                                WHERE user_id IN (SELECT id FROM users);
                            """))
                            
                            # 然后插入新用户（如果currency有默认值，或者我们需要设置一个）
                            # 检查currency列是否有默认值
                            currency_col = next((col for col in inspector.get_columns('user_balances') if col['name'] == 'currency'), None)
                            currency_default = currency_col.get('default') if currency_col else None
                            
                            if currency_default:
                                conn.execute(text(f"""
                                    INSERT OR IGNORE INTO user_balances (user_id, currency, usdt_balance, ton_balance, stars_balance, points_balance)
                                    SELECT 
                                        id,
                                        {currency_default},
                                        COALESCE(balance_usdt, 0),
                                        COALESCE(balance_ton, 0),
                                        COALESCE(balance_stars, 0),
                                        COALESCE(balance_points, 0)
                                    FROM users
                                    WHERE id NOT IN (SELECT user_id FROM user_balances);
                                """))
                            else:
                                # 如果没有默认值，尝试使用'USDT'作为默认值
                                conn.execute(text("""
                                    INSERT OR IGNORE INTO user_balances (user_id, currency, usdt_balance, ton_balance, stars_balance, points_balance)
                                    SELECT 
                                        id,
                                        'USDT',
                                        COALESCE(balance_usdt, 0),
                                        COALESCE(balance_ton, 0),
                                        COALESCE(balance_stars, 0),
                                        COALESCE(balance_points, 0)
                                    FROM users
                                    WHERE id NOT IN (SELECT user_id FROM user_balances);
                                """))
                        else:
                            # 没有currency列，直接INSERT OR REPLACE
                            conn.execute(text("""
                                INSERT OR REPLACE INTO user_balances (user_id, usdt_balance, ton_balance, stars_balance, points_balance)
                                SELECT 
                                    id,
                                    COALESCE(balance_usdt, 0),
                                    COALESCE(balance_ton, 0),
                                    COALESCE(balance_stars, 0),
                                    COALESCE(balance_points, 0)
                                FROM users;
                            """))
                    else:
                        # PostgreSQL: 使用ON CONFLICT
                        if has_currency:
                            # 先UPDATE
                            conn.execute(text("""
                                UPDATE user_balances
                                SET 
                                    usdt_balance = COALESCE(users.balance_usdt, 0),
                                    ton_balance = COALESCE(users.balance_ton, 0),
                                    stars_balance = COALESCE(users.balance_stars, 0),
                                    points_balance = COALESCE(users.balance_points, 0)
                                FROM users
                                WHERE user_balances.user_id = users.id;
                            """))
                            
                            # 然后INSERT新用户
                            conn.execute(text("""
                                INSERT INTO user_balances (user_id, currency, usdt_balance, ton_balance, stars_balance, points_balance)
                                SELECT 
                                    id,
                                    COALESCE(currency, 'USDT'),
                                    COALESCE(balance_usdt, 0),
                                    COALESCE(balance_ton, 0),
                                    COALESCE(balance_stars, 0),
                                    COALESCE(balance_points, 0)
                                FROM users
                                WHERE id NOT IN (SELECT user_id FROM user_balances)
                                ON CONFLICT (user_id) DO NOTHING;
                            """))
                        else:
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
                    print("✅ Initialized user_balances from users table")
                else:
                    print("⚠️ Users table missing balance columns, skipping balance migration")
            else:
                print(f"⚠️ user_balances table missing required columns, skipping balance migration")
        
        conn.commit()
        print("✅ Ledger System migration completed")

def downgrade():
    """回滚迁移"""
    with sync_engine.connect() as conn:
        is_sqlite_db = is_sqlite()
        cascade = "" if is_sqlite_db else " CASCADE"
        
        conn.execute(text(f"DROP TABLE IF EXISTS ledger_entries{cascade};"))
        conn.execute(text(f"DROP TABLE IF EXISTS user_balances{cascade};"))
        conn.commit()
        print("✅ Rollback completed")

if __name__ == "__main__":
    upgrade()

