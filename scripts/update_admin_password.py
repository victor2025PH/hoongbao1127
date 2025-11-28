"""
修改管理员账户密码
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database.connection import SyncSessionLocal
from shared.database.models import AdminUser
import hashlib

def update_admin_password(username: str, new_password: str):
    """修改管理员密码"""
    db = SyncSessionLocal()
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == username).first()
        
        if not admin:
            print(f"❌ 用户 {username} 不存在")
            return False
        
        # 使用 SHA256 哈希（测试环境）
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        # 更新密码
        admin.password_hash = new_hash
        db.commit()
        
        print(f"✅ 密码更新成功！")
        print(f"   用户名: {username}")
        print(f"   新密码: {new_password}")
        print(f"   新密码哈希: {new_hash}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 更新失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def create_or_update_admin(username: str, password: str, email: str = None):
    """创建或更新管理员账户"""
    db = SyncSessionLocal()
    try:
        from shared.database.models import Role
        
        admin = db.query(AdminUser).filter(AdminUser.username == username).first()
        
        # 使用 SHA256 哈希（测试环境）
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if admin:
            # 更新现有账户
            admin.password_hash = password_hash
            if email:
                admin.email = email
            admin.is_active = True
            print(f"✅ 更新现有账户: {username}")
        else:
            # 创建新账户
            # 获取或创建超级管理员角色
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
            
            admin = AdminUser(
                username=username,
                password_hash=password_hash,
                email=email,
                role_id=admin_role.id,
                is_active=True
            )
            db.add(admin)
            print(f"✅ 创建新账户: {username}")
        
        db.commit()
        
        print(f"   用户名: {username}")
        print(f"   密码: {password}")
        print(f"   邮箱: {email or '未设置'}")
        print(f"   密码哈希: {password_hash}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 操作失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="修改或创建管理员账户")
    parser.add_argument("--username", required=True, help="用户名")
    parser.add_argument("--password", required=True, help="新密码")
    parser.add_argument("--email", help="邮箱（可选）")
    parser.add_argument("--update-only", action="store_true", help="仅更新现有账户，不创建新账户")
    
    args = parser.parse_args()
    
    if args.update_only:
        update_admin_password(args.username, args.password)
    else:
        create_or_update_admin(args.username, args.password, args.email)

