"""
管理后台 - 认证路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from passlib.context import CryptContext

from shared.database.connection import get_db_session
from shared.database.models import AdminUser
from api.utils.auth import verify_password, create_access_token, get_current_active_admin, AdminUser as AdminUserType
from loguru import logger

router = APIRouter(prefix="/api/v1/admin/auth", tags=["管理后台-认证"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: str
    admin: dict


@router.get("/test-login")
async def test_login_endpoint():
    """测试登录逻辑（临时端点）"""
    from shared.database.connection import AsyncSessionLocal
    from shared.database.models import AdminUser
    from sqlalchemy import select
    import hashlib
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AdminUser).where(AdminUser.username == "admin")
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            return {"error": "Admin not found"}
        
        test_password = "123456"
        sha256_hash = hashlib.sha256(test_password.encode()).hexdigest()
        db_hash = admin.password_hash.strip() if admin.password_hash else ""
        
        return {
            "admin_username": admin.username,
            "admin_id": admin.id,
            "db_hash": db_hash,
            "computed_hash": sha256_hash,
            "match": sha256_hash == db_hash,
            "db_hash_length": len(db_hash),
            "computed_hash_length": len(sha256_hash),
            "db_hash_repr": repr(db_hash),
            "computed_hash_repr": repr(sha256_hash),
        }

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """管理員登錄"""
    # 查找管理員
    result = await db.execute(
        select(AdminUser).where(AdminUser.username == request.username)
    )
    admin = result.scalar_one_or_none()
    
    if not admin:
        logger.warning(f"User not found: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶名或密碼錯誤"
        )
    
    if not admin.is_active:
        logger.warning(f"Account disabled: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="賬戶已被禁用"
        )
    
    # 驗證密碼
    logger.info(f"Login attempt: username={request.username}")
    logger.info(f"Admin found: {admin.username}, ID: {admin.id}, Active: {admin.is_active}")
    
    # 清理密码哈希（去除可能的空格和换行符）
    db_hash = admin.password_hash.strip() if admin.password_hash else ""
    logger.info(f"Password hash in DB (length: {len(db_hash)}): {db_hash}")
    
    # 直接使用 SHA256 验证（用于测试环境）
    import hashlib
    sha256_hash = hashlib.sha256(request.password.encode()).hexdigest()
    logger.info(f"Computed SHA256 (length: {len(sha256_hash)}): {sha256_hash}")
    logger.info(f"Hash match: {sha256_hash == db_hash}")
    logger.info(f"Hash bytes match: {db_hash.encode() == sha256_hash.encode()}")
    
    # 直接 SHA256 匹配（测试环境，强制使用）
    # 使用多种方式验证，确保匹配
    password_valid = False
    if sha256_hash == db_hash:
        password_valid = True
        logger.info("✅ Password verified via SHA256 direct match (string)")
    elif db_hash.encode() == sha256_hash.encode():
        password_valid = True
        logger.info("✅ Password verified via SHA256 direct match (bytes)")
    else:
        # 尝试 verify_password 作为后备
        password_valid = verify_password(request.password, db_hash)
        logger.info(f"verify_password result: {password_valid}")
    
    if not password_valid:
        logger.error(f"❌ Password verification failed!")
        logger.error(f"DB hash: {repr(db_hash)}")
        logger.error(f"Computed: {repr(sha256_hash)}")
        logger.error(f"Lengths - DB: {len(db_hash)}, Computed: {len(sha256_hash)}")
        logger.error(f"First 10 chars - DB: {db_hash[:10]}, Computed: {sha256_hash[:10]}")
        logger.error(f"Last 10 chars - DB: {db_hash[-10:]}, Computed: {sha256_hash[-10:]}")
    
    if not password_valid:
        logger.error(f"❌ Password verification failed for user: {request.username}")
        logger.error(f"Expected hash: {db_hash}")
        logger.error(f"Computed hash: {sha256_hash}")
        logger.error(f"Hash lengths - DB: {len(db_hash)}, Computed: {len(sha256_hash)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶名或密碼錯誤"
        )
    
    logger.info(f"✅ Password verified successfully for {request.username}")
    
    # 生成 token
    token = create_access_token(data={"sub": admin.id})
    
    # 更新最後登錄時間
    from datetime import datetime
    admin.last_login_at = datetime.utcnow()
    await db.commit()
    
    return LoginResponse(
        success=True,
        token=token,
        admin={
            "id": admin.id,
            "username": admin.username,
            "email": admin.email,
            "role_id": admin.role_id,
        }
    )


@router.get("/me")
async def get_current_admin_info(
    admin: AdminUserType = Depends(get_current_active_admin)
):
    """獲取當前管理員信息"""
    return {
        "success": True,
        "data": {
            "id": admin.id,
            "username": admin.username,
            "email": admin.email,
            "role_id": admin.role_id,
        }
    }

