"""
Lucky Red - 任務紅包路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
from loguru import logger

from shared.database.connection import get_db_session
from shared.database.models import (
    User, RedPacket, RedPacketClaim, TaskCompletion, DailyTask,
    CurrencyType, RedPacketType, RedPacketStatus, RedPacketVisibility, RedPacketSource
)
from api.utils.telegram_auth import get_tg_id_from_header

router = APIRouter()

# 每日任務配置
DAILY_TASKS = {
    "checkin": {
        "task_name": "每日簽到",
        "task_description": "完成每日簽到，領取紅包獎勵",
        "requirement": {"action": "checkin"},
        "reward_amount": Decimal("0.1"),
        "reward_currency": CurrencyType.USDT,
    },
    "claim_packet": {
        "task_name": "搶紅包",
        "task_description": "領取1個紅包即可完成任務",
        "requirement": {"action": "claim", "count": 1},
        "reward_amount": Decimal("0.05"),
        "reward_currency": CurrencyType.USDT,
    },
    "send_packet": {
        "task_name": "發紅包",
        "task_description": "發送1個紅包即可完成任務",
        "requirement": {"action": "send", "count": 1},
        "reward_amount": Decimal("0.1"),
        "reward_currency": CurrencyType.USDT,
    },
    "share_app": {
        "task_name": "分享應用",
        "task_description": "分享應用鏈接給好友",
        "requirement": {"action": "share", "count": 1},
        "reward_amount": Decimal("0.05"),
        "reward_currency": CurrencyType.USDT,
    },
    "invite_friend": {
        "task_name": "邀請好友",
        "task_description": "邀請1個好友註冊",
        "requirement": {"action": "invite", "count": 1},
        "reward_amount": Decimal("0.5"),
        "reward_currency": CurrencyType.USDT,
    },
}

# 成就任務配置
ACHIEVEMENT_TASKS = {
    "invite_5": {
        "task_name": "邀請達人",
        "task_description": "邀請5個好友",
        "requirement": {"action": "invite", "count": 5},
        "reward_amount": Decimal("2.0"),
        "reward_currency": CurrencyType.USDT,
    },
    "invite_10": {
        "task_name": "邀請大師",
        "task_description": "邀請10個好友",
        "requirement": {"action": "invite", "count": 10},
        "reward_amount": Decimal("5.0"),
        "reward_currency": CurrencyType.USDT,
    },
    "claim_10": {
        "task_name": "搶包達人",
        "task_description": "領取10個紅包",
        "requirement": {"action": "claim", "count": 10},
        "reward_amount": Decimal("1.0"),
        "reward_currency": CurrencyType.USDT,
    },
    "send_10": {
        "task_name": "發包達人",
        "task_description": "發送10個紅包",
        "requirement": {"action": "send", "count": 10},
        "reward_amount": Decimal("2.0"),
        "reward_currency": CurrencyType.USDT,
    },
    "checkin_7": {
        "task_name": "簽到達人",
        "task_description": "連續簽到7天",
        "requirement": {"action": "checkin", "streak": 7},
        "reward_amount": Decimal("1.0"),
        "reward_currency": CurrencyType.USDT,
    },
}


class TaskStatus(BaseModel):
    """任務狀態"""
    task_type: str
    task_name: str
    task_description: str
    completed: bool
    can_claim: bool
    progress: Dict[str, Any]  # 完成進度
    reward_amount: float
    reward_currency: str
    red_packet_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    claimed_at: Optional[datetime] = None


class TaskClaimResponse(BaseModel):
    """任務領取響應"""
    success: bool
    amount: float
    currency: str
    message: str


async def check_task_completion(
    db: AsyncSession,
    user_id: int,
    task_type: str
) -> Optional[TaskCompletion]:
    """檢查任務是否已完成"""
    result = await db.execute(
        select(TaskCompletion).where(
            and_(
                TaskCompletion.user_id == user_id,
                TaskCompletion.task_type == task_type
            )
        ).order_by(TaskCompletion.completed_at.desc())
    )
    return result.scalar_one_or_none()


async def get_or_create_task_packet(
    db: AsyncSession,
    task_type: str,
    task_config: Dict[str, Any]
) -> RedPacket:
    """獲取或創建任務紅包"""
    # 查找現有的任務紅包（今天創建的）
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(RedPacket).where(
            and_(
                RedPacket.task_type == task_type,
                RedPacket.source_type == RedPacketSource.TASK,
                RedPacket.visibility == RedPacketVisibility.TASK,
                RedPacket.status == RedPacketStatus.ACTIVE,
                RedPacket.created_at >= today_start
            )
        ).order_by(RedPacket.created_at.desc())
    )
    packet = result.scalar_one_or_none()
    
    if packet:
        return packet
    
    # 創建新的任務紅包
    # 使用系統用戶作為發送者（需要創建一個系統用戶，或使用 admin 用戶）
    admin_result = await db.execute(
        select(User).where(User.is_admin == True).limit(1)
    )
    admin_user = admin_result.scalar_one_or_none()
    
    if not admin_user:
        # 如果沒有管理員，使用第一個用戶
        admin_result = await db.execute(select(User).limit(1))
        admin_user = admin_result.scalar_one_or_none()
        if not admin_user:
            raise HTTPException(status_code=500, detail="No user found to create task packet")
    
    packet = RedPacket(
        uuid=str(uuid.uuid4()),
        sender_id=admin_user.id,
        currency=task_config["reward_currency"],
        packet_type=RedPacketType.EQUAL,  # 任務紅包使用平分
        total_amount=task_config["reward_amount"] * Decimal("1000"),  # 1000個用戶可領取
        total_count=1000,
        message=f"🎯 {task_config['task_name']} - {task_config['task_description']}",
        chat_id=None,  # 公開紅包
        visibility=RedPacketVisibility.TASK,
        source_type=RedPacketSource.TASK,
        task_type=task_type,
        task_requirement=task_config["requirement"],
        task_completed_users=[],
        expires_at=datetime.utcnow() + timedelta(days=1),  # 24小時過期
    )
    
    db.add(packet)
    await db.commit()
    await db.refresh(packet)
    
    return packet


async def check_user_task_progress(
    db: AsyncSession,
    user: User,
    task_type: str,
    task_config: Dict[str, Any]
) -> Dict[str, Any]:
    """檢查用戶任務完成進度"""
    requirement = task_config["requirement"]
    action = requirement.get("action")
    
    progress = {
        "current": 0,
        "target": requirement.get("count", 1),
        "completed": False,
    }
    
    if action == "checkin":
        # 檢查今日是否已簽到
        today = datetime.utcnow().date()
        if user.last_checkin and user.last_checkin.date() == today:
            progress["current"] = 1
            progress["completed"] = True
        else:
            progress["current"] = 0
    
    elif action == "invite":
        # 檢查邀請數量
        invite_count = user.invite_count or 0
        target_count = requirement.get("count", 1)
        progress["current"] = invite_count
        progress["target"] = target_count
        progress["completed"] = invite_count >= target_count
    
    elif action == "claim":
        # 檢查領取紅包數量（今日）
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(func.count(RedPacketClaim.id)).where(
                and_(
                    RedPacketClaim.user_id == user.id,
                    RedPacketClaim.claimed_at >= today_start
                )
            )
        )
        claim_count = result.scalar() or 0
        target_count = requirement.get("count", 1)
        progress["current"] = claim_count
        progress["target"] = target_count
        progress["completed"] = claim_count >= target_count
    
    elif action == "send":
        # 檢查發送紅包數量（今日）
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(func.count(RedPacket.id)).where(
                and_(
                    RedPacket.sender_id == user.id,
                    RedPacket.created_at >= today_start
                )
            )
        )
        send_count = result.scalar() or 0
        target_count = requirement.get("count", 1)
        progress["current"] = send_count
        progress["target"] = target_count
        progress["completed"] = send_count >= target_count
    
    elif action == "share":
        # 分享任務（需要前端記錄分享次數）
        # 暫時使用邀請次數作為代理
        share_count = 0  # TODO: 從用戶記錄中獲取分享次數
        target_count = requirement.get("count", 1)
        progress["current"] = share_count
        progress["target"] = target_count
        progress["completed"] = share_count >= target_count
    
    return progress


@router.get("/status", response_model=List[TaskStatus])
async def get_task_status(
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    db: AsyncSession = Depends(get_db_session)
):
    """獲取用戶任務狀態"""
    if tg_id is None:
        raise HTTPException(status_code=401, detail="Telegram user ID is required")
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    tasks = []
    
    # 每日任務
    for task_type, task_config in DAILY_TASKS.items():
        # 檢查任務完成進度
        progress = await check_user_task_progress(db, user, task_type, task_config)
        
        # 檢查是否已領取
        completion = await check_task_completion(db, user.id, task_type)
        
        # 獲取或創建任務紅包
        try:
            packet = await get_or_create_task_packet(db, task_type, task_config)
        except Exception as e:
            logger.error(f"Failed to get/create task packet for {task_type}: {e}")
            continue
        
        tasks.append(TaskStatus(
            task_type=task_type,
            task_name=task_config["task_name"],
            task_description=task_config["task_description"],
            completed=progress["completed"],
            can_claim=progress["completed"] and completion is not None and completion.claimed_at is None,
            progress=progress,
            reward_amount=float(task_config["reward_amount"]),
            reward_currency=task_config["reward_currency"].value,
            red_packet_id=packet.uuid if packet else None,
            completed_at=completion.completed_at if completion else None,
            claimed_at=completion.claimed_at if completion else None,
        ))
    
    # 成就任務
    for task_type, task_config in ACHIEVEMENT_TASKS.items():
        progress = await check_user_task_progress(db, user, task_type, task_config)
        completion = await check_task_completion(db, user.id, task_type)
        
        # 成就任務只創建一次
        if progress["completed"] and completion is None:
            # 自動創建完成記錄（但未領取）
            try:
                packet = await get_or_create_task_packet(db, task_type, task_config)
                completion = TaskCompletion(
                    user_id=user.id,
                    red_packet_id=packet.id,
                    task_type=task_type,
                    completed_at=datetime.utcnow(),
                )
                db.add(completion)
                await db.commit()
                await db.refresh(completion)
            except Exception as e:
                logger.error(f"Failed to create achievement completion for {task_type}: {e}")
                continue
        
        if completion:
            packet_result = await db.execute(
                select(RedPacket).where(RedPacket.id == completion.red_packet_id)
            )
            packet = packet_result.scalar_one_or_none()
            
            tasks.append(TaskStatus(
                task_type=task_type,
                task_name=task_config["task_name"],
                task_description=task_config["task_description"],
                completed=progress["completed"],
                can_claim=progress["completed"] and completion.claimed_at is None,
                progress=progress,
                reward_amount=float(task_config["reward_amount"]),
                reward_currency=task_config["reward_currency"].value,
                red_packet_id=packet.uuid if packet else None,
                completed_at=completion.completed_at,
                claimed_at=completion.claimed_at,
            ))
    
    return tasks


@router.post("/{task_type}/claim", response_model=TaskClaimResponse)
async def claim_task_packet(
    task_type: str,
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    db: AsyncSession = Depends(get_db_session)
):
    """領取任務紅包"""
    if tg_id is None:
        raise HTTPException(status_code=401, detail="Telegram user ID is required")
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 檢查任務是否已完成
    completion = await check_task_completion(db, user.id, task_type)
    if not completion:
        raise HTTPException(status_code=400, detail="Task not completed")
    
    if completion.claimed_at:
        raise HTTPException(status_code=400, detail="Task reward already claimed")
    
    # 獲取任務紅包
    result = await db.execute(
        select(RedPacket).where(RedPacket.id == completion.red_packet_id)
    )
    packet = result.scalar_one_or_none()
    
    if not packet:
        raise HTTPException(status_code=404, detail="Task packet not found")
    
    if packet.status != RedPacketStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Task packet is not active")
    
    if packet.expires_at and packet.expires_at < datetime.utcnow():
        packet.status = RedPacketStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=400, detail="Task packet expired")
    
    # 檢查是否已領取過這個紅包
    result = await db.execute(
        select(RedPacketClaim).where(
            and_(
                RedPacketClaim.red_packet_id == packet.id,
                RedPacketClaim.user_id == user.id
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already claimed this packet")
    
    # 計算領取金額（任務紅包使用平分）
    remaining_amount = packet.total_amount - packet.claimed_amount
    remaining_count = packet.total_count - packet.claimed_count
    
    if remaining_count <= 0:
        packet.status = RedPacketStatus.COMPLETED
        await db.commit()
        raise HTTPException(status_code=400, detail="Task packet is empty")
    
    amount = remaining_amount / remaining_count
    
    # 創建領取記錄
    claim = RedPacketClaim(
        red_packet_id=packet.id,
        user_id=user.id,
        amount=amount,
    )
    db.add(claim)
    
    # 更新紅包狀態
    packet.claimed_amount += amount
    packet.claimed_count += 1
    
    if packet.claimed_count >= packet.total_count:
        packet.status = RedPacketStatus.COMPLETED
        packet.completed_at = datetime.utcnow()
    
    # 更新用戶餘額
    balance_field = f"balance_{packet.currency.value}"
    current_balance = getattr(user, balance_field, 0) or Decimal(0)
    new_balance = current_balance + amount
    setattr(user, balance_field, new_balance)
    
    # 更新任務完成記錄
    completion.claimed_at = datetime.utcnow()
    completion.reward_amount = amount
    
    await db.commit()
    
    return TaskClaimResponse(
        success=True,
        amount=float(amount),
        currency=packet.currency.value.upper(),
        message=f"任務完成！獲得 {amount} {packet.currency.value.upper()} 🎉"
    )


async def mark_task_complete_internal(
    task_type: str,
    tg_id: int,
    db: AsyncSession
) -> Dict[str, Any]:
    """標記任務完成（內部函數，由其他API調用）"""
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return {"success": False, "message": "User not found"}
    
    # 檢查任務配置
    task_config = DAILY_TASKS.get(task_type) or ACHIEVEMENT_TASKS.get(task_type)
    if not task_config:
        return {"success": False, "message": "Invalid task type"}
    
    # 檢查任務進度
    progress = await check_user_task_progress(db, user, task_type, task_config)
    if not progress["completed"]:
        return {"success": False, "message": "Task not completed"}
    
    # 檢查是否已記錄完成
    completion = await check_task_completion(db, user.id, task_type)
    if completion:
        return {"success": True, "message": "Task already completed"}
    
    # 獲取或創建任務紅包
    try:
        packet = await get_or_create_task_packet(db, task_type, task_config)
    except Exception as e:
        logger.error(f"Failed to get/create task packet: {e}")
        return {"success": False, "message": "Failed to create task packet"}
    
    # 創建任務完成記錄
    completion = TaskCompletion(
        user_id=user.id,
        red_packet_id=packet.id,
        task_type=task_type,
        completed_at=datetime.utcnow(),
    )
    db.add(completion)
    
    # 更新紅包的已完成用戶列表
    if packet.task_completed_users is None:
        packet.task_completed_users = []
    if user.id not in packet.task_completed_users:
        packet.task_completed_users.append(user.id)
    
    await db.commit()
    
    return {"success": True, "message": "Task marked as completed"}


@router.post("/{task_type}/complete")
class TaskCompleteRequest(BaseModel):
    """任務完成請求"""
    tg_id: int


@router.post("/{task_type}/complete")
async def mark_task_complete(
    task_type: str,
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    request_body: Optional[TaskCompleteRequest] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """標記任務完成（API端點）"""
    # 支持從請求體獲取 tg_id（用於 Bot 調用）
    if tg_id is None and request_body and request_body.tg_id:
        tg_id = request_body.tg_id
    
    if tg_id is None:
        raise HTTPException(status_code=401, detail="Telegram user ID is required")
    
    result = await mark_task_complete_internal(task_type, tg_id, db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

