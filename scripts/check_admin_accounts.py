"""
检查数据库中的所有管理员账户
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database.connection import SyncSessionLocal
from shared.database.models import AdminUser
import hashlib

def check_admin_accounts():
    """检查所有管理员账户并尝试匹配密码"""
    db = SyncSessionLocal()
    try:
        admins = db.query(AdminUser).all()
        
        print('')
        print('=' * 80)
        print('数据库中的所有管理员账户')
        print('=' * 80)
        
        if not admins:
            print('❌ 数据库中没有管理员账户')
            return
        
        # 测试密码列表
        test_passwords = [
            'admin', 'admin123', 'Admin123', 'ADMIN123',
            'password', 'Password', '123456',
            'root', 'administrator',
            'test', 'test123', 'Test123', 'TEST123'
        ]
        
        for i, admin in enumerate(admins, 1):
            print('')
            print(f'【账户 #{i}】')
            print(f'  ID: {admin.id}')
            print(f'  用户名: {admin.username}')
            print(f'  邮箱: {admin.email or "未设置"}')
            print(f'  是否激活: {admin.is_active}')
            print(f'  密码哈希: {admin.password_hash}')
            print(f'  创建时间: {admin.created_at}')
            print('')
            print('  尝试匹配密码:')
            
            found = False
            for pwd in test_passwords:
                test_hash = hashlib.sha256(pwd.encode()).hexdigest()
                if test_hash == admin.password_hash:
                    print(f'  ✅✅✅ 找到密码: {pwd}')
                    print('')
                    print(f'  📝 登录凭据:')
                    print(f'     用户名: {admin.username}')
                    print(f'     密码: {pwd}')
                    found = True
                    break
            
            if not found:
                print('  ❌ 未在测试列表中找到匹配密码')
            
            print('-' * 80)
        
        print('')
        print('=' * 80)
        print('检查完成')
        print('=' * 80)
        
    except Exception as e:
        print(f'❌ 错误: {str(e)}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_admin_accounts()

