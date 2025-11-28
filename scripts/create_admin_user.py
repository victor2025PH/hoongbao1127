"""
創建管理員用戶腳本
"""
import sys
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database.connection import SyncSessionLocal, init_db
from shared.database.models import AdminUser, Role
from api.utils.auth import get_password_hash

def create_admin_user(username: str, password: str, email: str = None):
    """創建管理員用戶"""
    # 初始化數據庫
    init_db()
    
    db = SyncSessionLocal()
    try:
        # 檢查用戶是否已存在
        existing_user = db.query(AdminUser).filter(AdminUser.username == username).first()
        if existing_user:
            print(f"❌ 用戶 {username} 已存在")
            return False
        
        # 創建超級管理員角色（如果不存在）
        admin_role = db.query(Role).filter(Role.name == "超級管理員").first()
        if not admin_role:
            admin_role = Role(
                name="超級管理員",
                description="擁有所有權限",
                permissions=["admin:*"]  # 所有權限
            )
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            print("✅ 創建超級管理員角色")
        
        # 創建管理員用戶
        # 確保密碼長度不超過 bcrypt 限制
        password_to_hash = password[:72] if len(password) > 72 else password
        password_hash = get_password_hash(password_to_hash)
        admin_user = AdminUser(
            username=username,
            password_hash=password_hash,
            email=email,
            role_id=admin_role.id,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        
        print(f"✅ 管理員用戶 {username} 創建成功")
        print(f"   用戶名: {username}")
        print(f"   郵箱: {email or '未設置'}")
        print(f"   角色: {admin_role.name}")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ 創建失敗: {str(e)}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="創建管理員用戶")
    parser.add_argument("--username", required=True, help="用戶名")
    parser.add_argument("--password", required=True, help="密碼")
    parser.add_argument("--email", help="郵箱（可選）")
    
    args = parser.parse_args()
    
    create_admin_user(args.username, args.password, args.email)

