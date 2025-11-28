"""
直接测试登录逻辑
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from shared.database.connection import AsyncSessionLocal
from shared.database.models import AdminUser
from api.utils.auth import verify_password, create_access_token
from sqlalchemy import select
import hashlib

async def test_login_direct(username: str, password: str):
    """直接测试登录逻辑"""
    print(f'\n{"="*80}')
    print(f'测试登录: {username} / {password}')
    print(f'{"="*80}\n')
    
    async with AsyncSessionLocal() as db:
        # 查找管理员
        result = await db.execute(
            select(AdminUser).where(AdminUser.username == username)
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            print(f'❌ 用户 {username} 不存在')
            return False
        
        print(f'✅ 找到用户: {admin.username}')
        print(f'   ID: {admin.id}')
        print(f'   邮箱: {admin.email or "未设置"}')
        print(f'   是否激活: {admin.is_active}')
        print(f'   密码哈希: {admin.password_hash}')
        print('')
        
        # 测试密码验证
        print('测试密码验证:')
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        print(f'  输入的密码: {password}')
        print(f'  计算的 SHA256: {sha256_hash}')
        print(f'  数据库中的哈希: {admin.password_hash}')
        print(f'  直接匹配: {sha256_hash == admin.password_hash}')
        
        # 直接 SHA256 匹配
        if sha256_hash == admin.password_hash:
            print('  ✅ SHA256 直接匹配成功')
            password_valid = True
        else:
            # 使用 verify_password 函数
            password_valid = verify_password(password, admin.password_hash)
            print(f'  verify_password 结果: {password_valid}')
        
        if password_valid:
            # 生成 token
            token = create_access_token(data={"sub": admin.id})
            print('')
            print(f'✅✅✅ 登录成功！')
            print(f'Token: {token[:50]}...')
            return True
        else:
            print('')
            print('❌ 密码验证失败')
            return False

async def main():
    """测试所有账户"""
    accounts = [
        ("admin", "admin123"),
        ("test", "test123"),
    ]
    
    for username, password in accounts:
        await test_login_direct(username, password)
        print('')

if __name__ == "__main__":
    asyncio.run(main())

