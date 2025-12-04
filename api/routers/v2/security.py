"""
Lucky Red API v2 - 安全端點
設備指紋、IP 會話管理
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from shared.database.connection import get_db_session
from shared.database.models import (
    DeviceFingerprint, IPSession, SybilAlert, 
    User, RiskLevel
)

router = APIRouter(prefix="/api/v2/security", tags=["安全-v2"])


# ==================== Pydantic 模型 ====================

class DeviceInfo(BaseModel):
    """設備信息"""
    fingerprint: str
    platform: str
    userAgent: str
    screenResolution: str
    timezone: str
    language: str
    colorDepth: int
    deviceMemory: Optional[int] = None
    hardwareConcurrency: Optional[int] = None
    touchSupport: bool


class FingerprintRegisterRequest(BaseModel):
    """設備指紋註冊請求"""
    fingerprint_id: str
    device_info: Optional[DeviceInfo] = None
    user_id: Optional[int] = None


class FingerprintResponse(BaseModel):
    """設備指紋響應"""
    success: bool
    fingerprint_id: str
    risk_level: str
    message: Optional[str] = None


class RiskCheckRequest(BaseModel):
    """風險檢查請求"""
    fingerprint_id: Optional[str] = None
    action: str  # claim_packet, withdraw, etc.


class RiskCheckResponse(BaseModel):
    """風險檢查響應"""
    allowed: bool
    risk_level: str
    risk_score: float
    warnings: list[str] = []
    blocked_reason: Optional[str] = None


# ==================== API 端點 ====================

@router.post("/fingerprint", response_model=FingerprintResponse)
async def register_fingerprint(
    request: FingerprintRegisterRequest,
    req: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    註冊或更新設備指紋
    
    前端在初始化時調用，用於反 Sybil 檢測
    """
    fingerprint_id = request.fingerprint_id
    
    # 查找現有指紋記錄
    result = await db.execute(
        select(DeviceFingerprint).where(
            DeviceFingerprint.fingerprint_id == fingerprint_id
        )
    )
    existing = result.scalars().all()
    
    # 計算此指紋關聯的用戶數
    unique_users = set(f.user_id for f in existing if f.user_id)
    
    # 評估風險等級
    risk_level = RiskLevel.LOW
    if len(unique_users) > 3:
        risk_level = RiskLevel.CRITICAL
    elif len(unique_users) > 1:
        risk_level = RiskLevel.HIGH
    elif len(unique_users) == 1 and request.user_id and request.user_id not in unique_users:
        risk_level = RiskLevel.MEDIUM
    
    # 創建或更新記錄
    if request.user_id:
        # 檢查此用戶是否已有此指紋的記錄
        user_fingerprint = None
        for f in existing:
            if f.user_id == request.user_id:
                user_fingerprint = f
                break
        
        if user_fingerprint:
            # 更新現有記錄
            user_fingerprint.last_seen = datetime.utcnow()
            user_fingerprint.request_count += 1
            user_fingerprint.risk_level = risk_level
            if request.device_info:
                user_fingerprint.device_info = request.device_info.model_dump() if hasattr(request.device_info, 'model_dump') else dict(request.device_info)
        else:
            # 創建新記錄
            new_fingerprint = DeviceFingerprint(
                user_id=request.user_id,
                fingerprint_id=fingerprint_id,
                device_info=request.device_info.model_dump() if request.device_info and hasattr(request.device_info, 'model_dump') else None,
                risk_level=risk_level,
                confidence_score=Decimal("0.85"),  # FingerprintJS 默認置信度
            )
            db.add(new_fingerprint)
    
    await db.commit()
    
    # 生成警告訊息
    message = None
    if risk_level == RiskLevel.CRITICAL:
        message = "檢測到高風險設備"
    elif risk_level == RiskLevel.HIGH:
        message = "此設備關聯多個帳戶"
    
    return FingerprintResponse(
        success=True,
        fingerprint_id=fingerprint_id,
        risk_level=risk_level.value,
        message=message,
    )


@router.post("/risk-check", response_model=RiskCheckResponse)
async def check_risk(
    request: RiskCheckRequest,
    req: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    執行風險檢查
    
    在執行敏感操作前調用（如搶紅包、提現）
    """
    warnings = []
    risk_score = 0.0
    ip_address = req.client.host if req.client else "unknown"
    
    # 1. IP 檢查
    ip_result = await db.execute(
        select(func.count(IPSession.id)).where(
            IPSession.ip_address == ip_address,
            IPSession.is_active == True
        )
    )
    active_sessions = ip_result.scalar() or 0
    
    if active_sessions > 5:
        risk_score += 0.4
        warnings.append(f"同一 IP 有 {active_sessions} 個活躍會話")
    elif active_sessions > 3:
        risk_score += 0.2
        warnings.append(f"同一 IP 有多個活躍會話")
    
    # 2. 指紋檢查
    if request.fingerprint_id:
        fp_result = await db.execute(
            select(func.count(func.distinct(DeviceFingerprint.user_id))).where(
                DeviceFingerprint.fingerprint_id == request.fingerprint_id
            )
        )
        linked_users = fp_result.scalar() or 0
        
        if linked_users > 3:
            risk_score += 0.5
            warnings.append("設備關聯過多帳戶")
        elif linked_users > 1:
            risk_score += 0.3
            warnings.append("設備關聯多個帳戶")
    
    # 3. 確定風險等級
    if risk_score >= 0.7:
        risk_level = RiskLevel.CRITICAL
    elif risk_score >= 0.5:
        risk_level = RiskLevel.HIGH
    elif risk_score >= 0.3:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.LOW
    
    # 4. 決定是否允許操作
    allowed = risk_level not in (RiskLevel.CRITICAL,)
    blocked_reason = None
    
    if not allowed:
        blocked_reason = "檢測到高風險行為，操作已被阻止"
        
        # 記錄警報
        alert = SybilAlert(
            ip_address=ip_address,
            fingerprint_id=request.fingerprint_id,
            alert_type="risk_check",
            alert_code=f"RISK_{request.action.upper()}",
            message="; ".join(warnings),
            request_path=str(req.url),
            request_method=req.method,
        )
        db.add(alert)
        await db.commit()
    
    return RiskCheckResponse(
        allowed=allowed,
        risk_level=risk_level.value,
        risk_score=risk_score,
        warnings=warnings,
        blocked_reason=blocked_reason,
    )


@router.post("/session/heartbeat")
async def session_heartbeat(
    req: Request,
    db: AsyncSession = Depends(get_db_session)
):
    """
    會話心跳
    
    前端定期調用以維持會話活躍狀態
    """
    ip_address = req.client.host if req.client else "unknown"
    session_id = req.headers.get("X-Session-ID")
    
    # 查找或創建會話
    result = await db.execute(
        select(IPSession).where(
            IPSession.ip_address == ip_address,
            IPSession.session_id == session_id,
            IPSession.is_active == True
        )
    )
    session = result.scalar_one_or_none()
    
    if session:
        session.last_activity = datetime.utcnow()
    else:
        session = IPSession(
            ip_address=ip_address,
            session_id=session_id,
            is_active=True,
        )
        db.add(session)
    
    await db.commit()
    
    return {"success": True, "session_id": session_id}


@router.get("/alerts/stats")
async def get_alert_stats(
    db: AsyncSession = Depends(get_db_session)
):
    """
    獲取安全警報統計
    
    管理後台使用
    """
    # 今日警報數
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    today_result = await db.execute(
        select(func.count(SybilAlert.id)).where(
            SybilAlert.created_at >= today_start
        )
    )
    today_count = today_result.scalar() or 0
    
    # 待審核數
    pending_result = await db.execute(
        select(func.count(SybilAlert.id)).where(
            SybilAlert.is_reviewed == False
        )
    )
    pending_count = pending_result.scalar() or 0
    
    # 按類型統計
    type_result = await db.execute(
        select(SybilAlert.alert_type, func.count(SybilAlert.id)).group_by(
            SybilAlert.alert_type
        )
    )
    by_type = {row[0]: row[1] for row in type_result.all()}
    
    return {
        "today_count": today_count,
        "pending_review": pending_count,
        "by_type": by_type,
    }
