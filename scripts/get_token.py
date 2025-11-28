"""
获取测试 Token
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.utils.auth import create_access_token

# 直接生成 token（用于测试）
token = create_access_token(data={"sub": 1})
print(token)

