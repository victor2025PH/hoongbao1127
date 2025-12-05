"""
添加 bomb_number 字段到 red_packets 表
支持 SQLite 和 PostgreSQL
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database.connection import get_db, sync_engine
from sqlalchemy import text, inspect
from loguru import logger
from shared.config.settings import get_settings

settings = get_settings()

def is_sqlite():
    """检查是否使用 SQLite"""
    database_url = settings.DATABASE_URL
    return database_url.startswith("sqlite")

def check_column_exists(engine, table_name, column_name):
    """检查列是否存在（兼容 SQLite 和 PostgreSQL）"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate():
    """执行迁移"""
    engine = sync_engine
    
    # 检测数据库类型
    db_url = str(engine.url)
    is_sqlite_db = is_sqlite()
    is_postgres = 'postgresql' in db_url.lower()
    
    logger.info(f"数据库类型: {'SQLite' if is_sqlite_db else 'PostgreSQL' if is_postgres else 'Unknown'}")
    
    try:
        with get_db() as db:
            # 检查 red_packets 表是否存在
            if is_sqlite_db:
                result = db.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='red_packets'
                """))
            else:  # PostgreSQL
                result = db.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'red_packets'
                """))
            
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                logger.warning("red_packets 表不存在，跳过迁移")
                return
            
            # 检查 bomb_number 列是否已存在
            if check_column_exists(engine, 'red_packets', 'bomb_number'):
                logger.info("bomb_number 列已存在，跳过迁移")
                return
            
            logger.info("开始添加 bomb_number 列...")
            
            # 添加 bomb_number 列
            if is_sqlite_db:
                # SQLite 需要特殊处理
                db.execute(text("""
                    ALTER TABLE red_packets 
                    ADD COLUMN bomb_number INTEGER NULL
                """))
            else:  # PostgreSQL
                db.execute(text("""
                    ALTER TABLE red_packets 
                    ADD COLUMN bomb_number INTEGER NULL
                """))
            
            db.commit()
            logger.info("✅ 成功添加 bomb_number 列到 red_packets 表")
            
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("开始迁移: 添加 bomb_number 字段")
    try:
        migrate()
        logger.info("迁移完成！")
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        sys.exit(1)
