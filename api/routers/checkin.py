"""
Lucky Red - 簽到路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta

from shared.database.connection import get_db_session
from shared.database.models import User, CheckinRecord

router = APIRouter()

# 簽到獎勵配置
CHECKIN_REWARDS = {
    1: 10,   # 第1天
    2: 20,   # 第2天
    3: 30,   # 第3天
    4: 40,   # 第4天
    5: 50,   # 第5天
    6: 60,   # 第6天
    7: 100,  # 第7天 (獎勵加倍)
}


class CheckinResponse(BaseModel):
    """簽到響應"""
    success: bool
    day: int
    reward: int
    streak: int
    message: str


class CheckinStatus(BaseModel):
    """簽到狀態"""
    today_checked: bool
    streak: int
    last_checkin: datetime | None
    next_reward: int


@router.post("/{tg_id}", response_model=CheckinResponse)
async def do_checkin(
    tg_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """執行簽到"""
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    today = datetime.utcnow().date()
    
    # 檢查今天是否已簽到
    if user.last_checkin and user.last_checkin.date() == today:
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    # 計算連續簽到
    if user.last_checkin:
        yesterday = today - timedelta(days=1)
        if user.last_checkin.date() == yesterday:
            # 連續簽到
            new_streak = (user.checkin_streak % 7) + 1
        else:
            # 中斷，重新開始
            new_streak = 1
    else:
        new_streak = 1
    
    # 獲取獎勵
    reward = CHECKIN_REWARDS.get(new_streak, 10)
    
    # 更新用戶
    user.last_checkin = datetime.utcnow()
    user.checkin_streak = new_streak
    user.balance_points = (user.balance_points or 0) + reward
    user.xp = (user.xp or 0) + reward
    
    # 創建簽到記錄
    record = CheckinRecord(
        user_id=user.id,
        checkin_date=datetime.utcnow(),
        day_of_streak=new_streak,
        reward_points=reward,
    )
    db.add(record)
    
    await db.commit()
    
    # 融合任務系統：標記簽到任務完成
    try:
        from api.routers.tasks import mark_task_complete_internal
        # 異步調用任務完成標記（不阻塞簽到響應）
        import asyncio
        asyncio.create_task(mark_task_complete_internal("checkin", user.tg_id, db))
    except Exception as e:
        logger.warning(f"Failed to mark checkin task complete: {e}")
    
    return CheckinResponse(
        success=True,
        day=new_streak,
        reward=reward,
        streak=new_streak,
        message=f"簽到成功！獲得 {reward} 積分 🎉"
    )


@router.get("/status/{tg_id}", response_model=CheckinStatus)
async def get_checkin_status(
    tg_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """獲取簽到狀態"""
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    today = datetime.utcnow().date()
    today_checked = user.last_checkin and user.last_checkin.date() == today
    
    # 計算下次獎勵
    if today_checked:
        next_day = (user.checkin_streak % 7) + 1
    else:
        if user.last_checkin and user.last_checkin.date() == today - timedelta(days=1):
            next_day = (user.checkin_streak % 7) + 1
        else:
            next_day = 1
    
    next_reward = CHECKIN_REWARDS.get(next_day, 10)
    
    return CheckinStatus(
        today_checked=today_checked,
        streak=user.checkin_streak or 0,
        last_checkin=user.last_checkin,
        next_reward=next_reward,
    )


@router.get("/history/{tg_id}")
async def get_checkin_history(
    tg_id: int,
    days: int = 30,
    db: AsyncSession = Depends(get_db_session)
):
    """獲取簽到歷史"""
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    since = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(CheckinRecord)
        .where(
            and_(
                CheckinRecord.user_id == user.id,
                CheckinRecord.checkin_date >= since
            )
        )
        .order_by(CheckinRecord.checkin_date.desc())
    )
    records = result.scalars().all()
    
    return [
        {
            "date": r.checkin_date.isoformat(),
            "day": r.day_of_streak,
            "reward": r.reward_points,
        }
        for r in records
    ]

