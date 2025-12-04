"""
反 Sybil 攻擊中間件

用於防止機器人農場搶空紅包池
實現以下規則：
1. 新帳戶（< 24 小時）且未充值不能搶紅包
2. 同一 IP 超過 5 個活躍會話則拒絕
3. 同一 IP 每小時搶紅包次數限制
4. 設備指紋異常檢測
"""
import json
from datetime import datetime, timedelta
from typing import Optional, Callable
from decimal import Decimal

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from shared.database.connection import AsyncSessionLocal
from shared.database.models import (
    User, Transaction, IPSession, DeviceFingerprint, 
    SybilAlert, RiskLevel
)


class AntiSybilMiddleware(BaseHTTPMiddleware):
    """
    反 Sybil 攻擊中間件
    
    在敏感操作（如搶紅包）前進行風險檢查
    """
    
    # ==================== 配置常量 ====================
    
    # 新帳戶限制
    NEW_ACCOUNT_AGE_HOURS = 24
    
    # IP 限制
    MAX_IP_SESSIONS = 5
    MAX_CLAIMS_PER_IP_PER_HOUR = 20
    IP_SESSION_TIMEOUT_MINUTES = 30
    
    # 指紋限制
    MAX_USERS_PER_FINGERPRINT = 3
    
    # 需要檢查的路徑模式
    PROTECTED_PATHS = [
        ("/packets/", "/claim"),      # 搶紅包
        ("/redpackets/", "/claim"),   # 搶紅包（兼容路徑）
    ]
    
    # ==================== 中間件入口 ====================
    
    async def dispatch(self, request: Request, call_next: Callable):
        """中間件分發"""
        # 檢查是否為需要保護的路徑
        if not self._should_check(request):
            return await call_next(request)
        
        # 執行 Sybil 檢查
        try:
            await self._check_sybil_risk(request)
        except HTTPException as e:
            # 返回錯誤響應
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Anti-Sybil check error: {e}")
            # 不阻止請求，但記錄錯誤
        
        return await call_next(request)
    
    # ==================== 路徑檢查 ====================
    
    def _should_check(self, request: Request) -> bool:
        """檢查是否需要進行 Sybil 檢查"""
        path = request.url.path.lower()
        method = request.method.upper()
        
        # 只檢查 POST 請求
        if method != "POST":
            return False
        
        # 檢查路徑模式
        for path_prefix, path_suffix in self.PROTECTED_PATHS:
            if path_prefix in path and path_suffix in path:
                return True
        
        return False
    
    # ==================== Sybil 風險檢查 ====================
    
    async def _check_sybil_risk(self, request: Request):
        """
        執行 Sybil 風險檢查
        
        檢查順序：
        1. 新帳戶且未充值
        2. IP 會話限制
        3. IP 請求頻率
        4. 設備指紋異常
        """
        # 獲取請求信息
        ip_address = self._get_client_ip(request)
        fingerprint_id = request.headers.get("X-Fingerprint-ID")
        
        # 嘗試獲取用戶信息（如果已認證）
        user = await self._get_user_from_request(request)
        
        async with AsyncSessionLocal() as db:
            # 規則 1：新帳戶且未充值
            if user:
                is_new_without_deposit = await self._is_new_account_without_deposit(db, user)
                if is_new_without_deposit:
                    await self._record_alert(
                        db, "new_account", "SYBIL_NEW_ACCOUNT",
                        user_id=user.id, ip_address=ip_address,
                        fingerprint_id=fingerprint_id,
                        message="新帳戶嘗試搶紅包",
                        request=request
                    )
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "code": "SYBIL_NEW_ACCOUNT",
                            "message": "新帳戶需要等待 24 小時或完成首次充值後才能搶紅包",
                            "wait_hours": self.NEW_ACCOUNT_AGE_HOURS,
                        }
                    )
            
            # 規則 2：同一 IP 過多活躍會話
            active_sessions = await self._count_active_ip_sessions(db, ip_address)
            if active_sessions > self.MAX_IP_SESSIONS:
                await self._record_alert(
                    db, "ip_limit", "SYBIL_IP_LIMIT",
                    user_id=user.id if user else None,
                    ip_address=ip_address,
                    fingerprint_id=fingerprint_id,
                    message=f"IP 活躍會話數: {active_sessions}",
                    request=request
                )
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "SYBIL_IP_LIMIT",
                        "message": "檢測到異常活動，請稍後再試",
                        "active_sessions": active_sessions,
                    }
                )
            
            # 規則 3：同一 IP 搶紅包次數限制
            claims_count = await self._count_ip_claims_last_hour(db, ip_address)
            if claims_count > self.MAX_CLAIMS_PER_IP_PER_HOUR:
                await self._record_alert(
                    db, "rate_limit", "SYBIL_RATE_LIMIT",
                    user_id=user.id if user else None,
                    ip_address=ip_address,
                    fingerprint_id=fingerprint_id,
                    message=f"IP 小時內請求數: {claims_count}",
                    request=request
                )
                raise HTTPException(
                    status_code=429,
                    detail={
                        "code": "SYBIL_RATE_LIMIT",
                        "message": "搶紅包次數過於頻繁，請稍後再試",
                        "claims_count": claims_count,
                        "limit": self.MAX_CLAIMS_PER_IP_PER_HOUR,
                    }
                )
            
            # 規則 4：設備指紋異常
            if fingerprint_id and user:
                risk_level = await self._check_fingerprint_risk(db, fingerprint_id, user.id)
                if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                    await self._record_alert(
                        db, "fingerprint", "SYBIL_FINGERPRINT",
                        user_id=user.id,
                        ip_address=ip_address,
                        fingerprint_id=fingerprint_id,
                        message=f"設備指紋風險等級: {risk_level.value}",
                        request=request
                    )
                    
                    # CRITICAL 級別直接拒絕
                    if risk_level == RiskLevel.CRITICAL:
                        raise HTTPException(
                            status_code=403,
                            detail={
                                "code": "SYBIL_FINGERPRINT",
                                "message": "檢測到風險行為，操作已被阻止",
                                "risk_level": risk_level.value,
                            }
                        )
            
            # 更新 IP 會話
            await self._update_ip_session(db, ip_address, user.id if user else None)
    
    # ==================== 檢查函數 ====================
    
    async def _is_new_account_without_deposit(
        self, 
        db: AsyncSession, 
        user: User
    ) -> bool:
        """檢查是否為新帳戶且未充值"""
        # 計算帳戶年齡
        account_age = datetime.utcnow() - user.created_at
        
        if account_age.total_seconds() < self.NEW_ACCOUNT_AGE_HOURS * 3600:
            # 檢查是否有充值記錄
            result = await db.execute(
                select(Transaction).where(
                    Transaction.user_id == user.id,
                    Transaction.type == "deposit",
                    Transaction.status == "completed"
                ).limit(1)
            )
            has_deposit = result.scalar_one_or_none() is not None
            return not has_deposit
        
        return False
    
    async def _count_active_ip_sessions(
        self, 
        db: AsyncSession, 
        ip_address: str
    ) -> int:
        """計算 IP 活躍會話數"""
        cutoff = datetime.utcnow() - timedelta(minutes=self.IP_SESSION_TIMEOUT_MINUTES)
        
        result = await db.execute(
            select(func.count(IPSession.id)).where(
                IPSession.ip_address == ip_address,
                IPSession.last_activity > cutoff,
                IPSession.is_active == True
            )
        )
        return result.scalar() or 0
    
    async def _count_ip_claims_last_hour(
        self, 
        db: AsyncSession, 
        ip_address: str
    ) -> int:
        """計算 IP 過去一小時的搶紅包次數"""
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        # 從 IP 會話表獲取統計
        result = await db.execute(
            select(func.sum(IPSession.packet_claims)).where(
                IPSession.ip_address == ip_address,
                IPSession.last_activity > one_hour_ago
            )
        )
        return result.scalar() or 0
    
    async def _check_fingerprint_risk(
        self, 
        db: AsyncSession, 
        fingerprint_id: str, 
        user_id: int
    ) -> RiskLevel:
        """評估設備指紋風險"""
        # 檢查此指紋關聯的不同用戶數
        result = await db.execute(
            select(func.count(func.distinct(DeviceFingerprint.user_id))).where(
                DeviceFingerprint.fingerprint_id == fingerprint_id
            )
        )
        linked_users = result.scalar() or 0
        
        if linked_users > self.MAX_USERS_PER_FINGERPRINT:
            return RiskLevel.CRITICAL
        elif linked_users > 1:
            return RiskLevel.HIGH
        
        return RiskLevel.LOW
    
    # ==================== 輔助函數 ====================
    
    def _get_client_ip(self, request: Request) -> str:
        """獲取客戶端 IP 地址"""
        # 檢查代理頭
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 取第一個 IP（原始客戶端）
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # 直接連接
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def _get_user_from_request(self, request: Request) -> Optional[User]:
        """從請求中獲取用戶（如果已認證）"""
        # 嘗試從 request.state 獲取（如果有認證中間件）
        if hasattr(request.state, "user"):
            return request.state.user
        
        # 嘗試從 Telegram init data 獲取
        init_data = request.headers.get("X-Telegram-Init-Data")
        if init_data:
            # 這裡應該解析 init_data 並獲取用戶
            # 簡化處理，實際應該使用認證模組
            pass
        
        return None
    
    async def _update_ip_session(
        self, 
        db: AsyncSession, 
        ip_address: str, 
        user_id: Optional[int]
    ):
        """更新或創建 IP 會話"""
        # 查找現有會話
        result = await db.execute(
            select(IPSession).where(
                IPSession.ip_address == ip_address,
                IPSession.user_id == user_id,
                IPSession.is_active == True
            ).order_by(IPSession.last_activity.desc()).limit(1)
        )
        session = result.scalar_one_or_none()
        
        if session:
            session.last_activity = datetime.utcnow()
            session.packet_claims += 1
        else:
            session = IPSession(
                ip_address=ip_address,
                user_id=user_id,
                is_active=True,
                packet_claims=1,
            )
            db.add(session)
        
        await db.commit()
    
    async def _record_alert(
        self,
        db: AsyncSession,
        alert_type: str,
        alert_code: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        fingerprint_id: Optional[str] = None,
        message: Optional[str] = None,
        request: Optional[Request] = None
    ):
        """記錄安全警報"""
        meta_data = {}
        if request:
            meta_data = {
                "path": str(request.url.path),
                "method": request.method,
                "headers": dict(request.headers),
            }
        
        alert = SybilAlert(
            user_id=user_id,
            ip_address=ip_address,
            fingerprint_id=fingerprint_id,
            alert_type=alert_type,
            alert_code=alert_code,
            message=message,
            request_path=str(request.url.path) if request else None,
            request_method=request.method if request else None,
            meta_data=meta_data,
        )
        db.add(alert)
        await db.commit()
        
        logger.warning(
            f"Sybil alert: {alert_code} | "
            f"user={user_id} | ip={ip_address} | "
            f"fingerprint={fingerprint_id} | "
            f"message={message}"
        )


# ==================== 獨立函數（可被其他模組使用） ====================

async def check_sybil_eligibility(
    db: AsyncSession,
    user_id: int,
    ip_address: str,
    fingerprint_id: Optional[str] = None,
    action: str = "claim_packet"
) -> tuple[bool, Optional[str]]:
    """
    檢查用戶是否有資格執行操作
    
    Returns:
        tuple: (is_eligible, error_message)
    """
    middleware = AntiSybilMiddleware(app=None)  # 只用其方法
    
    # 獲取用戶
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return False, "用戶不存在"
    
    # 執行檢查
    try:
        # 新帳戶檢查
        if await middleware._is_new_account_without_deposit(db, user):
            return False, "新帳戶需要等待 24 小時或完成首次充值"
        
        # IP 檢查
        active_sessions = await middleware._count_active_ip_sessions(db, ip_address)
        if active_sessions > middleware.MAX_IP_SESSIONS:
            return False, "檢測到異常活動"
        
        # 頻率檢查
        claims = await middleware._count_ip_claims_last_hour(db, ip_address)
        if claims > middleware.MAX_CLAIMS_PER_IP_PER_HOUR:
            return False, "操作過於頻繁"
        
        # 指紋檢查
        if fingerprint_id:
            risk = await middleware._check_fingerprint_risk(db, fingerprint_id, user_id)
            if risk == RiskLevel.CRITICAL:
                return False, "檢測到風險行為"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Sybil eligibility check error: {e}")
        return True, None  # 錯誤時允許通過
