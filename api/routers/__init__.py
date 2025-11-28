"""
Lucky Red - API 路由模塊
"""
from api.routers import auth, users, redpackets, wallet, checkin, chats, messages

# 管理后台路由（可选导入，避免循环依赖）
try:
    from api.routers import admin_telegram, admin_reports, admin_auth, admin_dashboard
    __all__ = ["auth", "users", "redpackets", "wallet", "checkin", "chats", "messages", 
               "admin_telegram", "admin_reports", "admin_auth", "admin_dashboard"]
except ImportError:
    __all__ = ["auth", "users", "redpackets", "wallet", "checkin", "chats", "messages"]

