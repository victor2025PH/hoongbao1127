"""
测试 JWT Token 生成和验证
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.utils.auth import create_access_token, SECRET_KEY
from shared.config.settings import get_settings
from jose import jwt

def test_jwt():
    """测试 JWT Token"""
    settings = get_settings()
    
    print("=" * 80)
    print("JWT Token 测试")
    print("=" * 80)
    print()
    
    print("配置检查:")
    print(f"  Settings JWT_SECRET: {getattr(settings, 'JWT_SECRET', 'Not found')}")
    print(f"  Auth SECRET_KEY: {SECRET_KEY}")
    print(f"  匹配: {getattr(settings, 'JWT_SECRET', '') == SECRET_KEY}")
    print()
    
    # 生成 Token
    print("生成 Token:")
    token = create_access_token(data={"sub": 1})
    print(f"  Token: {token[:50]}...")
    print()
    
    # 验证 Token
    print("验证 Token:")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        print(f"  ✅ Token 验证成功")
        print(f"  Payload: {payload}")
        print()
        
        # 使用 settings 中的 JWT_SECRET 验证
        settings_secret = getattr(settings, "JWT_SECRET", SECRET_KEY)
        payload2 = jwt.decode(token, settings_secret, algorithms=["HS256"])
        print(f"  ✅ 使用 Settings JWT_SECRET 验证成功")
        print()
        
        return True
    except Exception as e:
        print(f"  ❌ Token 验证失败: {str(e)}")
        print()
        return False

if __name__ == "__main__":
    test_jwt()

