"""
修复users表tg_id字段，允许为NULL
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect, text
from shared.config.settings import get_settings

settings = get_settings()


def upgrade():
    """升级数据库"""
    # 创建同步引擎
    sync_engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', '').replace('+aiosqlite', ''))
    
    with sync_engine.connect() as conn:
        # 检查数据库类型
        db_url = settings.DATABASE_URL
        is_sqlite_db = 'sqlite' in db_url.lower()
        
        inspector = inspect(sync_engine)
        
        # 检查tg_id字段的当前状态
        columns = inspector.get_columns('users')
        tg_id_col = next((col for col in columns if col['name'] == 'tg_id'), None)
        
        if tg_id_col:
            # 检查是否已经是nullable
            if tg_id_col['nullable']:
                print("✅ tg_id字段已经是nullable，无需修改")
                return
            
            print("🔧 修改tg_id字段为nullable...")
            
            if is_sqlite_db:
                # SQLite不支持直接修改NOT NULL约束
                # 需要重建表
                print("⚠️ SQLite不支持直接修改NOT NULL约束")
                print("   需要手动处理或使用迁移工具")
                print("   建议：如果数据库是空的，可以删除表重新创建")
            else:
                # PostgreSQL可以直接修改
                try:
                    conn.execute(text("ALTER TABLE users ALTER COLUMN tg_id DROP NOT NULL;"))
                    conn.commit()
                    print("✅ tg_id字段已修改为nullable")
                except Exception as e:
                    print(f"⚠️ 修改失败: {e}")
                    print("   可能需要先删除UNIQUE约束")
                    # 尝试删除UNIQUE约束后修改
                    try:
                        conn.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_tg_id_key;"))
                        conn.execute(text("ALTER TABLE users ALTER COLUMN tg_id DROP NOT NULL;"))
                        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS users_tg_id_key ON users(tg_id) WHERE tg_id IS NOT NULL;"))
                        conn.commit()
                        print("✅ tg_id字段已修改为nullable（使用部分唯一索引）")
                    except Exception as e2:
                        print(f"❌ 修改失败: {e2}")
        else:
            print("⚠️ 未找到tg_id字段")


if __name__ == "__main__":
    upgrade()

