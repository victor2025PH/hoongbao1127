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
        if is_sqlite_db:
            # SQLite: 使用INSERT OR REPLACE或先删除再插入
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
        is_sqlite_db = is_sqlite()
        cascade = "" if is_sqlite_db else " CASCADE"
        
        conn.execute(text(f"DROP TABLE IF EXISTS ledger_entries{cascade};"))
        conn.execute(text(f"DROP TABLE IF EXISTS user_balances{cascade};"))
        conn.commit()
        print("✅ Rollback completed")

if __name__ == "__main__":
    upgrade()

