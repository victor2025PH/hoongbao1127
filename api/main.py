"""
Lucky Red (搶紅包) - API 主入口
"""
import sys
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from shared.config.settings import get_settings
from shared.database.connection import init_db
from api.routers import auth, users, redpackets, wallet, checkin, chats, messages
from api.routers import admin_telegram, admin_reports, admin_auth, admin_dashboard, admin_users, admin_redpackets, admin_transactions, admin_checkin, admin_invite

settings = get_settings()

# 配置日誌
logger.remove()
logger.add(
    sys.stderr,
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期"""
    logger.info(f"🚀 Starting {settings.APP_NAME} API v{settings.APP_VERSION}")
    
    # 初始化數據庫
    init_db()
    logger.info("✅ Database initialized")
    
    yield
    
    logger.info("👋 Shutting down...")


# 創建應用
app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="搶紅包遊戲 API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"https://{settings.MINIAPP_DOMAIN}",
        f"https://{settings.ADMIN_DOMAIN}",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局異常處理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# 健康檢查
@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


# 註冊路由
app.include_router(auth.router, prefix="/api/auth", tags=["認證"])
app.include_router(users.router, prefix="/api/users", tags=["用戶"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用戶-v1"])  # 兼容 miniapp 的 /v1/users 路径
app.include_router(redpackets.router, prefix="/api/redpackets", tags=["紅包"])
app.include_router(wallet.router, prefix="/api/wallet", tags=["錢包"])
app.include_router(checkin.router, prefix="/api/checkin", tags=["簽到"])
app.include_router(chats.router, prefix="/api/v1/chats", tags=["群組"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["消息"])

# 管理后台路由
app.include_router(admin_auth.router, tags=["管理后台-认证"])
app.include_router(admin_dashboard.router, tags=["管理后台-仪表盘"])
app.include_router(admin_telegram.router, tags=["管理后台-Telegram"])
app.include_router(admin_reports.router, tags=["管理后台-报表"])
app.include_router(admin_users.router, tags=["管理后台-用户管理"])
app.include_router(admin_redpackets.router, tags=["管理后台-红包管理"])
app.include_router(admin_transactions.router, tags=["管理后台-交易管理"])
app.include_router(admin_checkin.router, tags=["管理后台-签到管理"])
app.include_router(admin_invite.router, tags=["管理后台-邀请管理"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )

