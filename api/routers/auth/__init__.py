"""
认证路由模块
"""
# 注意：create_access_token 和 TokenResponse 定义在 api/routers/auth.py 文件中
# 其他模块应该直接从 api.routers.auth 导入，而不是从这个 __init__.py 导入
# 这样可以避免循环导入问题

# 这个文件主要用于标识 auth 是一个包，并导出子路由
from api.routers.auth import web, link

__all__ = ["web", "link"]

