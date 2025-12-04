"""
邀請獎勵服務
處理邀請返佣、里程碑獎勵等
"""
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from shared.database.models import User, Transaction, CurrencyType


class InviteConfig:
    """邀請獎勵配置"""
    ENABLED = True
    
    # 基礎獎勵
    INVITER_REWARD = Decimal("1.0")  # 邀請人獎勵
    INVITEE_REWARD = Decimal("0.5")  # 被邀請人獎勵
    
    # 充值返佣比例
    LEVEL1_COMMISSION = Decimal("0.05")  # 一級返佣 5%
    LEVEL2_COMMISSION = Decimal("0.02")  # 二級返佣 2%
    
    # 里程碑獎勵
    MILESTONES = {
        5: Decimal("5.0"),
        10: Decimal("15.0"),
        25: Decimal("50.0"),
        50: Decimal("150.0"),
        100: Decimal("500.0"),
    }


async def process_deposit_commission(
    db: AsyncSession,
    user_id: int,
    deposit_amount: Decimal,
    currency: CurrencyType = CurrencyType.USDT
) -> dict:
    """
    處理充值返佣
    當用戶充值時，給邀請人返佣
    
    Args:
        db: 數據庫會話
        user_id: 充值用戶的數據庫 ID
        deposit_amount: 充值金額
        currency: 幣種
        
    Returns:
        返佣結果
    """
    if not InviteConfig.ENABLED:
        return {"success": False, "reason": "invite_disabled"}
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.invited_by:
        return {"success": False, "reason": "no_inviter"}
    
    commissions = []
    
    # 一級返佣
    level1_result = await db.execute(select(User).where(User.tg_id == user.invited_by))
    level1_inviter = level1_result.scalar_one_or_none()
    
    if level1_inviter:
        commission1 = deposit_amount * InviteConfig.LEVEL1_COMMISSION
        balance_field = f"balance_{currency.value}"
        
        current_balance = getattr(level1_inviter, balance_field, 0) or Decimal(0)
        new_balance = current_balance + commission1
        setattr(level1_inviter, balance_field, new_balance)
        
        level1_inviter.invite_earnings = (level1_inviter.invite_earnings or Decimal(0)) + commission1
        
        tx = Transaction(
            user_id=level1_inviter.id,
            type="invite_commission",
            currency=currency,
            amount=commission1,
            balance_before=current_balance,
            balance_after=new_balance,
            note=f"一級返佣 - 用戶 {user.tg_id} 充值 {deposit_amount}",
            status="completed"
        )
        db.add(tx)
        
        commissions.append({
            "level": 1,
            "inviter_tg_id": level1_inviter.tg_id,
            "amount": float(commission1),
            "rate": "5%"
        })
        
        logger.info(f"Level 1 commission: {level1_inviter.tg_id} +{commission1} for user {user.tg_id} deposit")
        
        # 二級返佣
        if level1_inviter.invited_by:
            level2_result = await db.execute(select(User).where(User.tg_id == level1_inviter.invited_by))
            level2_inviter = level2_result.scalar_one_or_none()
            
            if level2_inviter:
                commission2 = deposit_amount * InviteConfig.LEVEL2_COMMISSION
                
                current_balance2 = getattr(level2_inviter, balance_field, 0) or Decimal(0)
                new_balance2 = current_balance2 + commission2
                setattr(level2_inviter, balance_field, new_balance2)
                
                level2_inviter.invite_earnings = (level2_inviter.invite_earnings or Decimal(0)) + commission2
                
                tx2 = Transaction(
                    user_id=level2_inviter.id,
                    type="invite_commission",
                    currency=currency,
                    amount=commission2,
                    balance_before=current_balance2,
                    balance_after=new_balance2,
                    note=f"二級返佣 - 用戶 {user.tg_id} 充值 {deposit_amount}",
                    status="completed"
                )
                db.add(tx2)
                
                commissions.append({
                    "level": 2,
                    "inviter_tg_id": level2_inviter.tg_id,
                    "amount": float(commission2),
                    "rate": "2%"
                })
                
                logger.info(f"Level 2 commission: {level2_inviter.tg_id} +{commission2}")
    
    await db.commit()
    
    return {
        "success": True,
        "commissions": commissions,
        "total_commission": sum(c["amount"] for c in commissions)
    }


async def check_milestone_reward(db: AsyncSession, user_id: int) -> dict:
    """
    檢查並發放里程碑獎勵
    
    Args:
        db: 數據庫會話
        user_id: 用戶數據庫 ID
        
    Returns:
        獎勵結果
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return {"success": False, "reason": "user_not_found"}
    
    invite_count = user.invite_count or 0
    rewards_given = []
    
    for milestone, reward in InviteConfig.MILESTONES.items():
        if invite_count >= milestone:
            # 檢查是否已領取該里程碑獎勵
            existing = await db.execute(
                select(Transaction).where(
                    Transaction.user_id == user.id,
                    Transaction.type == "invite_milestone",
                    Transaction.note.like(f"%達成 {milestone} 人%")
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            # 發放獎勵
            user.balance_usdt = (user.balance_usdt or Decimal(0)) + reward
            user.invite_earnings = (user.invite_earnings or Decimal(0)) + reward
            
            tx = Transaction(
                user_id=user.id,
                type="invite_milestone",
                currency=CurrencyType.USDT,
                amount=reward,
                balance_before=user.balance_usdt - reward,
                balance_after=user.balance_usdt,
                note=f"邀請里程碑獎勵 - 達成 {milestone} 人",
                status="completed"
            )
            db.add(tx)
            
            rewards_given.append({
                "milestone": milestone,
                "reward": float(reward)
            })
            
            logger.info(f"Milestone reward: user {user.tg_id} reached {milestone}, +{reward} USDT")
    
    if rewards_given:
        await db.commit()
    
    return {
        "success": True,
        "rewards": rewards_given,
        "total_reward": sum(r["reward"] for r in rewards_given)
    }


async def get_invite_stats(db: AsyncSession, user_id: int) -> dict:
    """
    獲取用戶邀請統計
    
    Args:
        db: 數據庫會話
        user_id: 用戶數據庫 ID
        
    Returns:
        邀請統計
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return {"success": False, "reason": "user_not_found"}
    
    # 獲取被邀請人列表
    invitees_result = await db.execute(
        select(User).where(User.invited_by == user.tg_id)
    )
    invitees = invitees_result.scalars().all()
    
    # 計算下一個里程碑
    invite_count = user.invite_count or 0
    next_milestone = None
    next_reward = None
    for m, r in sorted(InviteConfig.MILESTONES.items()):
        if invite_count < m:
            next_milestone = m
            next_reward = float(r)
            break
    
    return {
        "success": True,
        "stats": {
            "invite_code": user.invite_code,
            "invite_count": invite_count,
            "invite_earnings": float(user.invite_earnings or 0),
            "invitees": [
                {
                    "tg_id": i.tg_id,
                    "username": i.username,
                    "first_name": i.first_name,
                    "joined_at": i.created_at.isoformat() if i.created_at else None
                }
                for i in invitees[:20]  # 最多返回20個
            ],
            "next_milestone": next_milestone,
            "next_milestone_reward": next_reward,
            "progress_to_next": invite_count / next_milestone if next_milestone else 1.0
        }
    }
