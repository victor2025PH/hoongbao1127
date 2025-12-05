"""
数据库迁移：添加用户交互模式偏好字段
支持 SQLite 和 PostgreSQL
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from shared.database.connection import get_db, sync_engine
from shared.config.settings import get_settings
from loguru import logger

settings = get_settings()


def is_sqlite():
    """检查是否使用 SQLite"""
    database_url = settings.DATABASE_URL
    return database_url.startswith("sqlite")


def column_exists_sqlite(db, table_name, column_name):
    """SQLite: 检查字段是否存在"""
    try:
        # SQLite 使用 PRAGMA table_info
        result = db.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result.fetchall()]
        return column_name in columns
    except Exception as e:
        logger.error(f"检查字段失败: {e}")
        return False


def column_exists_postgresql(db, table_name, column_name):
    """PostgreSQL: 检查字段是否存在"""
    try:
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name=:table_name AND column_name=:column_name
        """), {"table_name": table_name, "column_name": column_name})
        return result.fetchone() is not None
    except Exception as e:
        logger.error(f"检查字段失败: {e}")
        return False


def upgrade():
    """添加新字段"""
    try:
        with get_db() as db:
            # 检查字段是否已存在
            if is_sqlite():
                column_exists = column_exists_sqlite
            else:
                column_exists = column_exists_postgresql
            
            if column_exists(db, "users", "interaction_mode"):
                logger.info("字段 interaction_mode 已存在，跳过迁移")
                return
            
            # 添加新字段
            logger.info("正在添加 interaction_mode 字段...")
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN interaction_mode VARCHAR(20) DEFAULT 'auto'
            """))
            
            logger.info("正在添加 last_interaction_mode 字段...")
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN last_interaction_mode VARCHAR(20) DEFAULT 'keyboard'
            """))
            
            logger.info("正在添加 seamless_switch_enabled 字段...")
            if is_sqlite():
                # SQLite 使用 INTEGER 表示 BOOLEAN
                db.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN seamless_switch_enabled INTEGER DEFAULT 1
                """))
            else:
                # PostgreSQL 使用 BOOLEAN
                db.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN seamless_switch_enabled BOOLEAN DEFAULT TRUE
                """))
            
            db.commit()
            logger.info("✅ 成功添加交互模式字段")
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}", exc_info=True)
        raise


def downgrade():
    """移除字段"""
    try:
        with get_db() as db:
            # SQLite 不支持 DROP COLUMN IF EXISTS，需要先检查
            if is_sqlite():
                # SQLite 的 DROP COLUMN 需要特殊处理
                logger.warning("SQLite 不支持直接删除列，需要重建表")
                logger.warning("建议手动备份数据后重建表")
            else:
                db.execute(text("""
                    ALTER TABLE users 
                    DROP COLUMN IF EXISTS interaction_mode
                """))
                
                db.execute(text("""
                    ALTER TABLE users 
                    DROP COLUMN IF EXISTS last_interaction_mode
                """))
                
                db.execute(text("""
                    ALTER TABLE users 
                    DROP COLUMN IF EXISTS seamless_switch_enabled
                """))
            
            db.commit()
            logger.info("✅ 成功移除交互模式字段")
    except Exception as e:
        logger.error(f"❌ 回滚失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    upgrade()
