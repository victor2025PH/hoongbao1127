"""
链下账本服务 - 复式记账系统
所有游戏操作都在链下完成，只有存取款上链
"""
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json
from loguru import logger

from shared.database.models import User, UserBalance
from shared.database.connection import get_db_session

# Redis连接（单例模式，可选）
_redis_client = None
_redis_available = False

try:
    import redis
    _redis_available = True
except ImportError:
    logger.warning("⚠️ redis模块未安装，将使用数据库模式（不影响基本功能）")

def get_redis_client():
    """获取Redis客户端（单例，可选）"""
    global _redis_client
    if not _redis_available:
        return None
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            # 测试连接
            _redis_client.ping()
            logger.info("✅ Redis连接成功")
        except Exception as e:
            logger.warning(f"⚠️ Redis连接失败: {e}，将使用数据库模式")
            _redis_client = None
    return _redis_client


class LedgerService:
    """链下账本服务"""
    
    @staticmethod
    async def create_entry(
        db: AsyncSession,
        user_id: int,
        amount: Decimal,
        currency: str,
        entry_type: str,
        related_type: Optional[str] = None,
        related_id: Optional[int] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: str = 'system'
    ) -> Dict[str, Any]:
        """
        创建账本条目并更新余额（原子操作）
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            amount: 金额（正数=增加，负数=减少）
            currency: 币种（USDT, TON, STARS, POINTS）
            entry_type: 条目类型（DEPOSIT, WITHDRAW, GAME_WIN, etc.）
            related_type: 关联类型（red_packet, game_bet, etc.）
            related_id: 关联ID
            description: 描述
            metadata: 元数据
            created_by: 创建者
        
        Returns:
            账本条目信息
        """
        from shared.database.models import LedgerEntry
        
        currency = currency.upper()
        balance_field = f'{currency.lower()}_balance'
        
        # 获取当前余额（优先从Redis）
        balance_before = await LedgerService.get_balance(db, user_id, currency)
        
        # 计算新余额
        balance_after = balance_before + amount
        
        # 检查余额是否足够（如果是减少操作）
        if balance_after < 0:
            raise ValueError(f"Insufficient balance: {currency} {balance_before}, required: {abs(amount)}")
        
        # 获取或创建余额记录
        result = await db.execute(
            select(UserBalance).where(UserBalance.user_id == user_id)
        )
        balance = result.scalar_one_or_none()
        
        if not balance:
            balance = UserBalance(user_id=user_id)
            db.add(balance)
        
        # 更新余额
        setattr(balance, balance_field, balance_after)
        balance.updated_at = datetime.utcnow()
        
        # 创建账本条目
        from shared.database.models import LedgerCategory
        import uuid as uuid_lib
        
        entry_category = LedgerCategory(entry_type.lower())
        
        entry = LedgerEntry(
            uuid=str(uuid_lib.uuid4()),
            user_id=user_id,
            amount=amount,
            currency=currency_enum,
            balance_after=balance_after,
            category=entry_category,  # 使用category字段
            ref_type=related_type,  # 使用ref_type字段
            ref_id=str(related_id) if related_id else None,  # 使用ref_id字段（字符串类型）
            note=description,  # 使用note字段
            meta_data=metadata,  # 使用meta_data字段
            created_at=datetime.utcnow()
        )
        
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        
        # 更新Redis缓存
        await LedgerService._update_redis_balance(user_id, currency, balance_after)
        
        logger.info(
            f"Ledger entry created: user={user_id}, type={entry_type}, "
            f"amount={amount} {currency}, balance: {balance_before} -> {balance_after}"
        )
        
        return {
            'entry_id': entry.id,
            'user_id': user_id,
            'amount': str(amount),
            'currency': currency,
            'balance_before': str(balance_before),
            'balance_after': str(balance_after),
            'type': entry_type
        }
    
    @staticmethod
    async def get_balance(
        db: AsyncSession,
        user_id: int,
        currency: str = 'USDT'
    ) -> Decimal:
        """
        获取用户余额（优先从Redis缓存）
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            currency: 币种
        
        Returns:
            余额
        """
        currency = currency.upper()
        balance_field = f'{currency.lower()}_balance'
        cache_key = f"user:balance:{user_id}:{currency.lower()}"
        
        # 尝试从Redis获取
        try:
            r = get_redis_client()
            if r:
                cached = r.get(cache_key)
                if cached:
                    return Decimal(cached)
        except Exception as e:
            logger.warning(f"Redis cache miss: {e}")
        
        # 从数据库获取
        result = await db.execute(
            select(UserBalance).where(UserBalance.user_id == user_id)
        )
        balance = result.scalar_one_or_none()
        
        if not balance:
            return Decimal('0')
        
        amount = getattr(balance, balance_field, Decimal('0'))
        
        # 更新Redis缓存（1小时过期）
        try:
            r = get_redis_client()
            if r:
                r.setex(cache_key, 3600, str(amount))
        except Exception as e:
            logger.warning(f"Failed to update Redis cache: {e}")
        
        return amount
    
    @staticmethod
    async def _update_redis_balance(user_id: int, currency: str, balance: Decimal):
        """更新Redis余额缓存"""
        try:
            r = get_redis_client()
            if r:
                cache_key = f"user:balance:{user_id}:{currency.lower()}"
                r.setex(cache_key, 3600, str(balance))  # 1小时过期
        except Exception as e:
            logger.warning(f"Failed to update Redis balance cache: {e}")
    
    @staticmethod
    async def get_all_balances(
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Decimal]:
        """获取用户所有币种余额"""
        result = await db.execute(
            select(UserBalance).where(UserBalance.user_id == user_id)
        )
        balance = result.scalar_one_or_none()
        
        if not balance:
            return {
                'USDT': Decimal('0'),
                'TON': Decimal('0'),
                'STARS': Decimal('0'),
                'POINTS': Decimal('0')
            }
        
        return {
            'USDT': balance.usdt_balance or Decimal('0'),
            'TON': balance.ton_balance or Decimal('0'),
            'STARS': balance.stars_balance or Decimal('0'),
            'POINTS': balance.points_balance or Decimal('0')
        }
    
    @staticmethod
    async def get_ledger_history(
        db: AsyncSession,
        user_id: int,
        currency: Optional[str] = None,
        entry_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """获取账本历史"""
        from shared.database.models import LedgerEntry
        from sqlalchemy import and_
        
        query = select(LedgerEntry).where(LedgerEntry.user_id == user_id)
        
        if currency:
            query = query.where(LedgerEntry.currency == currency.upper())
        
        if entry_type:
            from shared.database.models import LedgerCategory
            entry_category = LedgerCategory(entry_type.lower())
            query = query.where(LedgerEntry.category == entry_category)
        
        query = query.order_by(LedgerEntry.created_at.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        entries = result.scalars().all()
        
        return [
            {
                'id': entry.id,
                'amount': str(entry.amount),
                'currency': entry.currency,
                'type': entry.type,
                'balance_before': str(entry.balance_before),
                'balance_after': str(entry.balance_after),
                'description': entry.description,
                'created_at': entry.created_at.isoformat()
            }
            for entry in entries
        ]

