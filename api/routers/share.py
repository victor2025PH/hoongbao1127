"""
Lucky Red - 分享路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from shared.database.connection import get_db_session
from shared.database.models import User
from api.utils.telegram_auth import get_tg_id_from_header
from api.routers.tasks import mark_task_complete_internal
from loguru import logger

router = APIRouter()


class ShareResponse(BaseModel):
    """分享響應"""
    success: bool
    share_count: int
    message: str


@router.post("/record", response_model=ShareResponse)
async def record_share(
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    db: AsyncSession = Depends(get_db_session)
):
    """記錄分享行為"""
    if tg_id is None:
        raise HTTPException(status_code=401, detail="Telegram user ID is required")
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 更新分享次數
    user.share_count = (user.share_count or 0) + 1
    await db.commit()
    
    # 檢查分享任務完成
    try:
        await mark_task_complete_internal("share_app", tg_id, db)
    except Exception as e:
        logger.warning(f"Failed to mark share task complete: {e}")
    
    return ShareResponse(
        success=True,
        share_count=user.share_count,
        message=f"分享成功！已分享 {user.share_count} 次"
    )

