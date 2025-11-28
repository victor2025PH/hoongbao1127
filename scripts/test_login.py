"""
测试登录逻辑
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from shared.database.connection import AsyncSessionLocal
from shared.database.models import AdminUser
from api.utils.auth import verify_password, create_access_token
from sqlalchemy import select

async def test_login():
    """测试登录逻辑"""
    async with AsyncSessionLocal() as db:
        # 查找管理员
        result = await db.execute(
            select(AdminUser).where(AdminUser.username == "admin")
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("❌ 管理员不存在")
            return
        
        print(f"✅ 找到管理员: {admin.username}")
        print(f"   密码哈希: {admin.password_hash}")
        print(f"   是否激活: {admin.is_active}")
        
        # 测试密码验证
        test_password = "admin123"
        print(f"\n测试密码: {test_password}")
        result = verify_password(test_password, admin.password_hash)
        print(f"验证结果: {result}")
        
        if result:
            # 生成 token
            token = create_access_token(data={"sub": admin.id})
            print(f"\n✅ 登录成功！")
            print(f"Token: {token[:50]}...")
        else:
            print("\n❌ 密码验证失败")
            
            # 调试：检查 SHA256
            import hashlib
            sha256_hash = hashlib.sha256(test_password.encode()).hexdigest()
            print(f"计算的 SHA256: {sha256_hash}")
            print(f"数据库中的哈希: {admin.password_hash}")
            print(f"是否匹配: {sha256_hash == admin.password_hash}")

if __name__ == "__main__":
    asyncio.run(test_login())

