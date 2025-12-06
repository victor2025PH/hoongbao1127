"""
推荐系统服务
处理Tier 1 & Tier 2推荐佣金
"""
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from shared.database.models import User, LedgerEntry, LedgerCategory, CurrencyType
from api.services.ledger_service import LedgerService


class ReferralService:
    """推荐系统服务"""
    
    # 推荐佣金比例
    TIER_1_RATE = Decimal('0.10')  # 10% - 直接推荐
    TIER_2_RATE = Decimal('0.05')  # 5% - 二级推荐
    
    @staticmethod
    async def process_referral_reward(
        db: AsyncSession,
        user_id: int,
        amount: Decimal,
        currency: str,
        reward_type: str = 'deposit',  # deposit, redpacket, game_win
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理推荐奖励（Tier 1 & Tier 2）
        
        Args:
            db: 数据库会话
            user_id: 产生奖励的用户ID
            amount: 奖励金额
            currency: 币种
            reward_type: 奖励类型
            metadata: 元数据
        
        Returns:
            处理结果
        """
        result = {
            'tier1_rewards': [],
            'tier2_rewards': [],
            'total_tier1': Decimal('0'),
            'total_tier2': Decimal('0')
        }
        
        # 获取用户
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user or not user.referrer_id:
            logger.info(f"用户 {user_id} 没有推荐人，跳过推荐奖励")
            return result
        
        # Tier 1: 直接推荐人
        tier1_referrer_id = user.referrer_id
        tier1_reward = amount * ReferralService.TIER_1_RATE
        
        # 给Tier 1推荐人发放奖励
        tier1_result = await ReferralService._give_referral_reward(
            db=db,
            referrer_id=tier1_referrer_id,
            referred_user_id=user_id,
            amount=tier1_reward,
            currency=currency,
            tier=1,
            reward_type=reward_type,
            metadata=metadata
        )
        
        if tier1_result:
            result['tier1_rewards'].append(tier1_result)
            result['total_tier1'] = tier1_reward
        
        # Tier 2: 二级推荐人
        tier1_referrer_result = await db.execute(select(User).where(User.id == tier1_referrer_id))
        tier1_referrer = tier1_referrer_result.scalar_one_or_none()
        
        if tier1_referrer and tier1_referrer.referrer_id:
            tier2_referrer_id = tier1_referrer.referrer_id
            tier2_reward = amount * ReferralService.TIER_2_RATE
            
            # 给Tier 2推荐人发放奖励
            tier2_result = await ReferralService._give_referral_reward(
                db=db,
                referrer_id=tier2_referrer_id,
                referred_user_id=user_id,
                amount=tier2_reward,
                currency=currency,
                tier=2,
                reward_type=reward_type,
                metadata=metadata
            )
            
            if tier2_result:
                result['tier2_rewards'].append(tier2_result)
                result['total_tier2'] = tier2_reward
        
        logger.info(
            f"推荐奖励处理完成: user={user_id}, amount={amount} {currency}, "
            f"tier1={result['total_tier1']}, tier2={result['total_tier2']}"
        )
        
        return result
    
    @staticmethod
    async def _give_referral_reward(
        db: AsyncSession,
        referrer_id: int,
        referred_user_id: int,
        amount: Decimal,
        currency: str,
        tier: int,
        reward_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        给推荐人发放奖励
        
        Args:
            db: 数据库会话
            referrer_id: 推荐人ID
            referred_user_id: 被推荐人ID
            amount: 奖励金额
            currency: 币种
            tier: 层级（1或2）
            reward_type: 奖励类型
            metadata: 元数据
        
        Returns:
            奖励结果
        """
        try:
            # 使用LedgerService发放奖励
            entry_result = await LedgerService.create_entry(
                db=db,
                user_id=referrer_id,
                amount=amount,
                currency=currency.upper(),
                entry_type='REFERRAL_BONUS',
                related_type='referral',
                related_id=referred_user_id,
                description=f"Tier {tier}推荐奖励: {amount} {currency}",
                metadata={
                    'tier': tier,
                    'referred_user_id': referred_user_id,
                    'reward_type': reward_type,
                    **(metadata or {})
                },
                created_by='system'
            )
            
            logger.info(
                f"Tier {tier}推荐奖励发放成功: referrer={referrer_id}, "
                f"referred={referred_user_id}, amount={amount} {currency}"
            )
            
            return {
                'referrer_id': referrer_id,
                'referred_user_id': referred_user_id,
                'amount': str(amount),
                'currency': currency,
                'tier': tier,
                'entry_id': entry_result['entry_id']
            }
        except Exception as e:
            logger.error(f"发放Tier {tier}推荐奖励失败: {e}")
            return None
    
    @staticmethod
    async def get_referral_stats(
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """
        获取推荐统计
        
        Args:
            db: 数据库会话
            user_id: 用户ID
        
        Returns:
            推荐统计信息
        """
        # 统计直接推荐人数（Tier 1）
        tier1_count_result = await db.execute(
            select(func.count(User.id)).where(User.referrer_id == user_id)
        )
        tier1_count = tier1_count_result.scalar_one_or_none() or 0
        
        # 统计二级推荐人数（Tier 2）
        # 先获取所有直接推荐人
        tier1_users_result = await db.execute(
            select(User.id).where(User.referrer_id == user_id)
        )
        tier1_user_ids = [row[0] for row in tier1_users_result.fetchall()]
        
        tier2_count = 0
        if tier1_user_ids:
            tier2_count_result = await db.execute(
                select(func.count(User.id)).where(User.referrer_id.in_(tier1_user_ids))
            )
            tier2_count = tier2_count_result.scalar_one_or_none() or 0
        
        # 统计推荐奖励总额
        referral_entries_result = await db.execute(
            select(
                func.sum(LedgerEntry.amount),
                func.count(LedgerEntry.id)
            ).where(
                LedgerEntry.user_id == user_id,
                LedgerEntry.category == LedgerCategory.REFERRAL_BONUS
            )
        )
        stats = referral_entries_result.first()
        total_reward = stats[0] or Decimal('0')
        reward_count = stats[1] or 0
        
        # 按层级统计
        tier1_reward_result = await db.execute(
            select(func.sum(LedgerEntry.amount)).where(
                LedgerEntry.user_id == user_id,
                LedgerEntry.category == LedgerCategory.REFERRAL_BONUS,
                LedgerEntry.meta_data['tier'].astext == '1'
            )
        )
        tier1_reward = tier1_reward_result.scalar_one_or_none() or Decimal('0')
        
        tier2_reward_result = await db.execute(
            select(func.sum(LedgerEntry.amount)).where(
                LedgerEntry.user_id == user_id,
                LedgerEntry.category == LedgerCategory.REFERRAL_BONUS,
                LedgerEntry.meta_data['tier'].astext == '2'
            )
        )
        tier2_reward = tier2_reward_result.scalar_one_or_none() or Decimal('0')
        
        return {
            'tier1_count': tier1_count,
            'tier2_count': tier2_count,
            'total_referrals': tier1_count + tier2_count,
            'total_reward': str(total_reward),
            'reward_count': reward_count,
            'tier1_reward': str(tier1_reward),
            'tier2_reward': str(tier2_reward)
        }
    
    @staticmethod
    async def get_referral_tree(
        db: AsyncSession,
        user_id: int,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        获取推荐树
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            max_depth: 最大深度（默认2层）
        
        Returns:
            推荐树结构
        """
        async def build_tree(current_user_id: int, depth: int) -> Optional[Dict[str, Any]]:
            if depth > max_depth:
                return None
            
            # 获取用户信息
            user_result = await db.execute(select(User).where(User.id == current_user_id))
            user = user_result.scalar_one_or_none()
            
            if not user:
                return None
            
            # 获取直接推荐人
            referrals_result = await db.execute(
                select(User).where(User.referrer_id == current_user_id)
            )
            referrals = referrals_result.scalars().all()
            
            tree = {
                'user_id': user.id,
                'username': user.username,
                'referral_code': user.referral_code,
                'referrals': []
            }
            
            for referral in referrals:
                child_tree = await build_tree(referral.id, depth + 1)
                if child_tree:
                    tree['referrals'].append(child_tree)
            
            return tree
        
        result = await build_tree(user_id, 0)
        return result if result else {
            'user_id': user_id,
            'username': None,
            'referral_code': None,
            'referrals': []
        }

