"""
簡單創建管理員用戶（直接使用 SQL）
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database.connection import SyncSessionLocal, init_db
from shared.database.models import AdminUser, Role
import hashlib

def create_admin_simple(username: str, password: str, email: str = None):
    """簡單創建管理員（使用 SHA256，僅用於測試）"""
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
                permissions=["admin:*"]
            )
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            print("✅ 創建超級管理員角色")
        
        # 使用簡單的 SHA256 哈希（僅用於測試，生產環境應使用 bcrypt）
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        admin_user = AdminUser(
            username=username,
            password_hash=password_hash,  # 臨時使用 SHA256
            email=email,
            role_id=admin_role.id,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        
        print(f"✅ 管理員用戶 {username} 創建成功（使用 SHA256 哈希）")
        print(f"   用戶名: {username}")
        print(f"   密碼: {password}")
        print(f"   郵箱: {email or '未設置'}")
        print(f"   角色: {admin_role.name}")
        print(f"   ⚠️  注意：這是測試版本，使用 SHA256 哈希，生產環境應使用 bcrypt")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ 創建失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="創建管理員用戶（簡單版）")
    parser.add_argument("--username", required=True, help="用戶名")
    parser.add_argument("--password", required=True, help="密碼")
    parser.add_argument("--email", help="郵箱（可選）")
    
    args = parser.parse_args()
    
    create_admin_simple(args.username, args.password, args.email)

