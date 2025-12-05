"""
添加任务红包系统数据库字段
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from shared.database.connection import sync_engine

def upgrade():
    """添加任务红包系统相关字段"""
    with sync_engine.connect() as conn:
        # 检查数据库类型
        db_type = sync_engine.url.drivername
        
        # 1. 添加红包可见性和来源类型字段
        try:
            if db_type == 'sqlite':
                # SQLite 不支持 IF NOT EXISTS，需要先检查
                from sqlalchemy import inspect
                inspector = inspect(sync_engine)
                columns = [col['name'] for col in inspector.get_columns('red_packets')]
                
                if 'visibility' not in columns:
                    conn.execute(text("ALTER TABLE red_packets ADD COLUMN visibility VARCHAR(20) DEFAULT 'private'"))
                if 'source_type' not in columns:
                    conn.execute(text("ALTER TABLE red_packets ADD COLUMN source_type VARCHAR(20) DEFAULT 'user_private'"))
                if 'task_type' not in columns:
                    conn.execute(text("ALTER TABLE red_packets ADD COLUMN task_type VARCHAR(50)"))
                if 'task_requirement' not in columns:
                    conn.execute(text("ALTER TABLE red_packets ADD COLUMN task_requirement TEXT"))
                if 'task_completed_users' not in columns:
                    conn.execute(text("ALTER TABLE red_packets ADD COLUMN task_completed_users TEXT DEFAULT '[]'"))
            else:
                # PostgreSQL 支持 IF NOT EXISTS
                conn.execute(text("""
                    ALTER TABLE red_packets 
                    ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) DEFAULT 'private'
                """))
                conn.execute(text("""
                    ALTER TABLE red_packets 
                    ADD COLUMN IF NOT EXISTS source_type VARCHAR(20) DEFAULT 'user_private'
                """))
                conn.execute(text("""
                    ALTER TABLE red_packets 
                    ADD COLUMN IF NOT EXISTS task_type VARCHAR(50)
                """))
                conn.execute(text("""
                    ALTER TABLE red_packets 
                    ADD COLUMN IF NOT EXISTS task_requirement JSONB
                """))
                conn.execute(text("""
                    ALTER TABLE red_packets 
                    ADD COLUMN IF NOT EXISTS task_completed_users JSONB DEFAULT '[]'::jsonb
                """))
            conn.commit()
            print("✅ 已添加红包任务相关字段")
        except Exception as e:
            print(f"⚠️ 添加字段时出错（可能已存在）: {e}")
            conn.rollback()
        
        # 2. 创建任务完成记录表
        try:
            if db_type == 'sqlite':
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS task_completions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        red_packet_id INTEGER NOT NULL REFERENCES red_packets(id),
                        task_type VARCHAR(50) NOT NULL,
                        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        claimed_at TIMESTAMP,
                        reward_amount NUMERIC(20, 8),
                        UNIQUE(user_id, red_packet_id, task_type)
                    )
                """))
            else:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS task_completions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        red_packet_id INTEGER NOT NULL REFERENCES red_packets(id),
                        task_type VARCHAR(50) NOT NULL,
                        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        claimed_at TIMESTAMP,
                        reward_amount NUMERIC(20, 8),
                        UNIQUE(user_id, red_packet_id, task_type)
                    )
                """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_task_completions_user_id 
                ON task_completions(user_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_task_completions_red_packet_id 
                ON task_completions(red_packet_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_task_completions_task_type 
                ON task_completions(task_type)
            """))
            conn.commit()
            print("✅ 已创建任务完成记录表")
        except Exception as e:
            print(f"⚠️ 创建表时出错（可能已存在）: {e}")
            conn.rollback()
        
        # 3. 创建每日任务配置表（可选）
        try:
            if db_type == 'sqlite':
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS daily_tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_type VARCHAR(50) UNIQUE NOT NULL,
                        task_name VARCHAR(100) NOT NULL,
                        task_description VARCHAR(500) NOT NULL,
                        requirement TEXT NOT NULL,
                        reward_amount NUMERIC(20, 8) NOT NULL,
                        reward_currency VARCHAR(10) DEFAULT 'usdt',
                        is_active BOOLEAN DEFAULT TRUE,
                        sort_order INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
            else:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS daily_tasks (
                        id SERIAL PRIMARY KEY,
                        task_type VARCHAR(50) UNIQUE NOT NULL,
                        task_name VARCHAR(100) NOT NULL,
                        task_description VARCHAR(500) NOT NULL,
                        requirement JSONB NOT NULL,
                        reward_amount NUMERIC(20, 8) NOT NULL,
                        reward_currency VARCHAR(10) DEFAULT 'usdt',
                        is_active BOOLEAN DEFAULT TRUE,
                        sort_order INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_daily_tasks_task_type 
                ON daily_tasks(task_type)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_daily_tasks_is_active 
                ON daily_tasks(is_active)
            """))
            conn.commit()
            print("✅ 已创建每日任务配置表")
        except Exception as e:
            print(f"⚠️ 创建表时出错（可能已存在）: {e}")
            conn.rollback()
        
        # 4. 更新现有红包数据
        try:
            # 检查字段是否存在
            from sqlalchemy import inspect
            inspector = inspect(sync_engine)
            columns = [col['name'] for col in inspector.get_columns('red_packets')]
            
            if 'visibility' in columns and 'source_type' in columns:
                # 将 chat_id 为 NULL 的红包标记为公开红包
                if db_type == 'sqlite':
                    conn.execute(text("""
                        UPDATE red_packets 
                        SET visibility = 'public', source_type = 'user_public'
                        WHERE chat_id IS NULL AND (visibility = 'private' OR visibility IS NULL)
                    """))
                else:
                    conn.execute(text("""
                        UPDATE red_packets 
                        SET visibility = 'public', source_type = 'user_public'
                        WHERE chat_id IS NULL AND visibility = 'private'
                    """))
                conn.commit()
                print("✅ 已更新现有红包数据")
            else:
                print("⚠️ 字段不存在，跳过数据更新")
        except Exception as e:
            print(f"⚠️ 更新数据时出错: {e}")
            conn.rollback()

def downgrade():
    """回滚迁移"""
    with sync_engine.connect() as conn:
        try:
            conn.execute(text("DROP TABLE IF EXISTS task_completions"))
            conn.execute(text("DROP TABLE IF EXISTS daily_tasks"))
            conn.execute(text("ALTER TABLE red_packets DROP COLUMN IF EXISTS visibility"))
            conn.execute(text("ALTER TABLE red_packets DROP COLUMN IF EXISTS source_type"))
            conn.execute(text("ALTER TABLE red_packets DROP COLUMN IF EXISTS task_type"))
            conn.execute(text("ALTER TABLE red_packets DROP COLUMN IF EXISTS task_requirement"))
            conn.execute(text("ALTER TABLE red_packets DROP COLUMN IF EXISTS task_completed_users"))
            conn.commit()
            print("✅ 已回滚迁移")
        except Exception as e:
            print(f"⚠️ 回滚时出错: {e}")
            conn.rollback()

if __name__ == "__main__":
    upgrade()

