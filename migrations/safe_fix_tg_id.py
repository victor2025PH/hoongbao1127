"""
安全修复SQLite数据库users表tg_id字段，允许为NULL
此脚本会保留现有数据
"""
import sys
from pathlib import Path
import shutil
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect, text
from shared.config.settings import get_settings

settings = get_settings()


def upgrade():
    """安全升级数据库（保留数据）"""
    # 创建同步引擎
    sync_engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', '').replace('+aiosqlite', ''))
    
    with sync_engine.connect() as conn:
        # 检查数据库类型
        db_url = settings.DATABASE_URL
        is_sqlite_db = 'sqlite' in db_url.lower()
        
        if not is_sqlite_db:
            print("⚠️ 这不是SQLite数据库，请使用fix_tg_id_nullable.py")
            return
        
        inspector = inspect(sync_engine)
        
        # 检查tg_id字段的当前状态
        columns = inspector.get_columns('users')
        tg_id_col = next((col for col in columns if col['name'] == 'tg_id'), None)
        
        if not tg_id_col:
            print("⚠️ 未找到tg_id字段")
            return
        
        if tg_id_col['nullable']:
            print("✅ tg_id字段已经是nullable，无需修改")
            return
        
        # 检查数据
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        
        if count == 0:
            print("✅ 数据库为空，可以安全重建表")
            # 使用简单的重建方法
            conn.execute(text("DROP TABLE users;"))
            print("✅ 表已删除，请运行数据库初始化脚本重新创建")
            return
        
        print(f"📊 数据库中有 {count} 条用户记录")
        print("🔧 开始安全迁移（保留所有数据）...")
        
        # 备份数据库
        if 'sqlite:///' in db_url:
            db_path = db_url.replace('sqlite:///', '')
            backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                shutil.copy2(db_path, backup_path)
                print(f"✅ 数据库已备份到: {backup_path}")
            except Exception as e:
                print(f"⚠️ 备份失败: {e}")
                print("   继续执行迁移（风险自负）...")
        
        # 开始事务
        trans = conn.begin()
        try:
            # 1. 获取所有列名（除了tg_id）
            all_columns = [col['name'] for col in columns if col['name'] != 'tg_id']
            columns_str = ', '.join(all_columns)
            
            # 2. 创建新表（tg_id可为NULL）
            print("📝 创建新表结构...")
            conn.execute(text("""
                CREATE TABLE users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_id BIGINT,
                    username VARCHAR(64),
                    first_name VARCHAR(64),
                    last_name VARCHAR(64),
                    language_code VARCHAR(10) DEFAULT 'zh-TW',
                    balance_usdt NUMERIC(20, 8) DEFAULT 0,
                    balance_ton NUMERIC(20, 8) DEFAULT 0,
                    balance_stars BIGINT DEFAULT 0,
                    balance_points BIGINT DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    xp BIGINT DEFAULT 0,
                    invited_by BIGINT,
                    invite_code VARCHAR(16),
                    invite_count INTEGER DEFAULT 0,
                    invite_earnings NUMERIC(20, 8) DEFAULT 0,
                    last_checkin DATETIME,
                    checkin_streak INTEGER DEFAULT 0,
                    is_banned BOOLEAN DEFAULT 0,
                    is_admin BOOLEAN DEFAULT 0,
                    interaction_mode VARCHAR(20) DEFAULT 'auto',
                    last_interaction_mode VARCHAR(20) DEFAULT 'keyboard',
                    seamless_switch_enabled BOOLEAN DEFAULT 1,
                    uuid VARCHAR(36),
                    wallet_address VARCHAR(255),
                    wallet_network VARCHAR(50),
                    referrer_id INTEGER,
                    referral_code VARCHAR(20),
                    total_referrals INTEGER DEFAULT 0,
                    tier1_commission NUMERIC(5, 2) DEFAULT 0.10,
                    tier2_commission NUMERIC(5, 2) DEFAULT 0.05,
                    primary_platform VARCHAR(20),
                    last_active_at DATETIME,
                    kyc_status VARCHAR(20) DEFAULT 'pending',
                    kyc_verified_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # 3. 复制数据（保留tg_id值，即使为NULL也可以）
            print("📋 复制数据到新表...")
            conn.execute(text(f"""
                INSERT INTO users_new ({columns_str}, tg_id)
                SELECT {columns_str}, tg_id FROM users;
            """))
            
            # 4. 检查数据完整性
            result = conn.execute(text("SELECT COUNT(*) FROM users_new"))
            new_count = result.scalar()
            if new_count != count:
                raise Exception(f"数据复制不完整: 原表{count}条，新表{new_count}条")
            
            print(f"✅ 数据复制成功: {new_count} 条记录")
            
            # 5. 删除旧表
            print("🗑️ 删除旧表...")
            conn.execute(text("DROP TABLE users;"))
            
            # 6. 重命名新表
            print("🔄 重命名新表...")
            conn.execute(text("ALTER TABLE users_new RENAME TO users;"))
            
            # 7. 重建索引和约束
            print("📇 重建索引...")
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_tg_id ON users(tg_id) WHERE tg_id IS NOT NULL;"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_invite_code ON users(invite_code);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_referral_code ON users(referral_code);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_uuid ON users(uuid);"))
            
            trans.commit()
            print("✅ 迁移成功！tg_id字段现在可以为NULL")
            print(f"✅ 所有 {count} 条记录已保留")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ 迁移失败: {e}")
            print("   已回滚，数据库未修改")
            if 'backup_path' in locals():
                print(f"   可以使用备份恢复: {backup_path}")
            raise


if __name__ == "__main__":
    upgrade()

