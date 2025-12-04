"""
流動性管理服務

處理 Telegram Stars 的 21 天持有期問題
實現以下功能：
1. Stars 充值時設定冷卻期
2. 流水解鎖機制
3. 提現資格檢查
4. 資金來源追蹤
"""
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from loguru import logger

from shared.database.models import (
    User, LedgerEntry, UserBalance,
    CurrencyType, CurrencySource, WithdrawableStatus, LedgerCategory
)


# ==================== 數據類 ====================

@dataclass
class WithdrawalCheck:
    """提現檢查結果"""
    eligible: bool
    withdrawable_amount: Decimal
    locked_amount: Decimal = Decimal("0")
    cooldown_amount: Decimal = Decimal("0")
    turnover_pending: Decimal = Decimal("0")
    message: Optional[str] = None
    unlock_date: Optional[datetime] = None


@dataclass
class SourceBalance:
    """來源餘額"""
    source: CurrencySource
    total: Decimal
    withdrawable: Decimal
    locked: Decimal
    cooldown_until: Optional[datetime] = None


@dataclass
class DepositResult:
    """充值結果"""
    success: bool
    ledger_entry_id: int
    amount: Decimal
    currency: CurrencyType
    source: CurrencySource
    withdrawable_status: WithdrawableStatus
    cooldown_until: Optional[datetime] = None
    turnover_required: Decimal = Decimal("0")
    message: str = ""


# ==================== 服務類 ====================

class LiquidityService:
    """
    流動性管理服務
    
    處理不同資金來源的管理和提現限制
    """
    
    # ==================== 配置常量 ====================
    
    # Stars 冷卻期（天）- Telegram 規定 21 天
    STARS_COOLDOWN_DAYS = 21
    
    # 流水倍數要求（例如：充值 100 USDT，需要 100 * 1.0 = 100 USDT 流水才能提現）
    STARS_TURNOVER_MULTIPLIER = Decimal("1.0")
    BONUS_TURNOVER_MULTIPLIER = Decimal("3.0")  # 獎勵資金需要更高流水
    
    # 最低提現金額
    MIN_WITHDRAW_AMOUNT = Decimal("10.0")
    
    # ==================== 充值處理 ====================
    
    async def process_stars_deposit(
        self,
        db: AsyncSession,
        user_id: int,
        stars_amount: int,
        usdt_equivalent: Decimal,
        exchange_rate: Decimal,
    ) -> DepositResult:
        """
        處理 Stars 充值並設定冷卻期
        
        Args:
            db: 資料庫會話
            user_id: 用戶 ID
            stars_amount: Stars 數量
            usdt_equivalent: 等值 USDT
            exchange_rate: 匯率
        
        Returns:
            DepositResult: 充值結果
        """
        # 計算冷卻期結束時間
        cooldown_until = datetime.utcnow() + timedelta(days=self.STARS_COOLDOWN_DAYS)
        
        # 計算流水要求
        turnover_required = usdt_equivalent * self.STARS_TURNOVER_MULTIPLIER
        
        # 獲取當前餘額
        user = await self._get_user(db, user_id)
        if not user:
            return DepositResult(
                success=False,
                ledger_entry_id=0,
                amount=usdt_equivalent,
                currency=CurrencyType.USDT,
                source=CurrencySource.STARS_CREDIT,
                withdrawable_status=WithdrawableStatus.COOLDOWN,
                message="用戶不存在"
            )
        
        current_balance = Decimal(str(user.balance_usdt or 0))
        new_balance = current_balance + usdt_equivalent
        
        # 創建帳本條目
        entry_uuid = str(uuid.uuid4())
        entry = LedgerEntry(
            uuid=entry_uuid,
            user_id=user_id,
            currency=CurrencyType.USDT,
            amount=usdt_equivalent,
            balance_after=new_balance,
            category=LedgerCategory.STARS_CONVERSION,
            currency_source=CurrencySource.STARS_CREDIT,
            withdrawable_status=WithdrawableStatus.COOLDOWN,
            cooldown_until=cooldown_until,
            turnover_required=turnover_required,
            turnover_completed=Decimal("0"),
            ref_type="stars_conversion",
            meta_data={
                "stars_amount": stars_amount,
                "exchange_rate": str(exchange_rate),
            }
        )
        db.add(entry)
        
        # 更新用戶餘額
        user.balance_usdt = new_balance
        
        # 更新餘額快取表
        await self._update_balance_cache(
            db, user_id, CurrencyType.USDT,
            delta_amount=usdt_equivalent,
            source=CurrencySource.STARS_CREDIT,
            is_locked=True
        )
        
        await db.commit()
        await db.refresh(entry)
        
        logger.info(
            f"Stars deposit processed: user={user_id}, "
            f"stars={stars_amount}, usdt={usdt_equivalent}, "
            f"cooldown_until={cooldown_until}"
        )
        
        return DepositResult(
            success=True,
            ledger_entry_id=entry.id,
            amount=usdt_equivalent,
            currency=CurrencyType.USDT,
            source=CurrencySource.STARS_CREDIT,
            withdrawable_status=WithdrawableStatus.COOLDOWN,
            cooldown_until=cooldown_until,
            turnover_required=turnover_required,
            message=f"充值成功，{self.STARS_COOLDOWN_DAYS} 天後可提現"
        )
    
    async def process_crypto_deposit(
        self,
        db: AsyncSession,
        user_id: int,
        amount: Decimal,
        currency: CurrencyType,
        tx_hash: Optional[str] = None,
    ) -> DepositResult:
        """
        處理加密貨幣充值（無冷卻期）
        """
        user = await self._get_user(db, user_id)
        if not user:
            return DepositResult(
                success=False,
                ledger_entry_id=0,
                amount=amount,
                currency=currency,
                source=CurrencySource.REAL_CRYPTO,
                withdrawable_status=WithdrawableStatus.WITHDRAWABLE,
                message="用戶不存在"
            )
        
        # 獲取當前餘額
        if currency == CurrencyType.USDT:
            current_balance = Decimal(str(user.balance_usdt or 0))
        elif currency == CurrencyType.TON:
            current_balance = Decimal(str(user.balance_ton or 0))
        else:
            current_balance = Decimal("0")
        
        new_balance = current_balance + amount
        
        # 創建帳本條目
        entry_uuid = str(uuid.uuid4())
        entry = LedgerEntry(
            uuid=entry_uuid,
            user_id=user_id,
            currency=currency,
            amount=amount,
            balance_after=new_balance,
            category=LedgerCategory.DEPOSIT,
            currency_source=CurrencySource.REAL_CRYPTO,
            withdrawable_status=WithdrawableStatus.WITHDRAWABLE,
            ref_type="crypto_deposit",
            ref_id=tx_hash,
        )
        db.add(entry)
        
        # 更新用戶餘額
        if currency == CurrencyType.USDT:
            user.balance_usdt = new_balance
        elif currency == CurrencyType.TON:
            user.balance_ton = new_balance
        
        # 更新餘額快取
        await self._update_balance_cache(
            db, user_id, currency,
            delta_amount=amount,
            source=CurrencySource.REAL_CRYPTO,
            is_locked=False
        )
        
        await db.commit()
        await db.refresh(entry)
        
        return DepositResult(
            success=True,
            ledger_entry_id=entry.id,
            amount=amount,
            currency=currency,
            source=CurrencySource.REAL_CRYPTO,
            withdrawable_status=WithdrawableStatus.WITHDRAWABLE,
            message="充值成功，可立即提現"
        )
    
    # ==================== 提現檢查 ====================
    
    async def check_withdrawal_eligibility(
        self,
        db: AsyncSession,
        user_id: int,
        amount: Decimal,
        currency: CurrencyType = CurrencyType.USDT,
    ) -> WithdrawalCheck:
        """
        檢查提現資格
        
        按優先順序使用資金：
        1. 真實加密貨幣（無限制）
        2. 已解鎖的 Stars（冷卻期已過 + 流水已完成）
        3. 獎勵資金（如果有）
        """
        # 獲取分類餘額
        source_balances = await self._get_source_balances(db, user_id, currency)
        
        # 計算可提現總額
        total_withdrawable = sum(sb.withdrawable for sb in source_balances)
        total_locked = sum(sb.locked for sb in source_balances)
        
        # 獲取待完成流水
        pending_turnover = await self._get_pending_turnover(db, user_id, currency)
        
        # 找到最早的解鎖日期
        unlock_date = None
        for sb in source_balances:
            if sb.cooldown_until and (unlock_date is None or sb.cooldown_until < unlock_date):
                unlock_date = sb.cooldown_until
        
        # 檢查最低提現金額
        if amount < self.MIN_WITHDRAW_AMOUNT:
            return WithdrawalCheck(
                eligible=False,
                withdrawable_amount=total_withdrawable,
                locked_amount=total_locked,
                turnover_pending=pending_turnover,
                message=f"最低提現金額為 {self.MIN_WITHDRAW_AMOUNT} {currency.value.upper()}"
            )
        
        # 檢查可提現金額是否足夠
        if amount > total_withdrawable:
            shortfall = amount - total_withdrawable
            return WithdrawalCheck(
                eligible=False,
                withdrawable_amount=total_withdrawable,
                locked_amount=total_locked,
                cooldown_amount=shortfall,
                turnover_pending=pending_turnover,
                unlock_date=unlock_date,
                message=f"可提現餘額不足，有 {total_locked} {currency.value.upper()} 仍在冷卻期"
            )
        
        return WithdrawalCheck(
            eligible=True,
            withdrawable_amount=total_withdrawable,
            locked_amount=total_locked,
            turnover_pending=pending_turnover,
            unlock_date=unlock_date,
            message="可以提現"
        )
    
    # ==================== 流水管理 ====================
    
    async def update_turnover(
        self,
        db: AsyncSession,
        user_id: int,
        game_amount: Decimal,
        currency: CurrencyType = CurrencyType.USDT,
    ) -> int:
        """
        更新遊戲流水，解鎖符合條件的資金
        
        Returns:
            int: 解鎖的條目數
        """
        # 獲取所有需要流水的帳本條目
        result = await db.execute(
            select(LedgerEntry).where(
                and_(
                    LedgerEntry.user_id == user_id,
                    LedgerEntry.currency == currency,
                    LedgerEntry.turnover_required > LedgerEntry.turnover_completed,
                    LedgerEntry.withdrawable_status.in_([
                        WithdrawableStatus.COOLDOWN,
                        WithdrawableStatus.LOCKED
                    ])
                )
            ).order_by(LedgerEntry.created_at)
        )
        entries = result.scalars().all()
        
        remaining_turnover = game_amount
        unlocked_count = 0
        
        for entry in entries:
            if remaining_turnover <= 0:
                break
            
            needed = entry.turnover_required - entry.turnover_completed
            applied = min(needed, remaining_turnover)
            
            entry.turnover_completed += applied
            remaining_turnover -= applied
            
            # 檢查是否滿足解鎖條件
            if entry.turnover_completed >= entry.turnover_required:
                # 檢查冷卻期
                if entry.cooldown_until is None or entry.cooldown_until <= datetime.utcnow():
                    entry.withdrawable_status = WithdrawableStatus.WITHDRAWABLE
                    unlocked_count += 1
                    
                    logger.info(
                        f"Funds unlocked: user={user_id}, "
                        f"entry={entry.id}, amount={entry.amount}"
                    )
        
        if entries:
            await db.commit()
            
            # 更新餘額快取
            await self._recalculate_balance_cache(db, user_id, currency)
        
        return unlocked_count
    
    async def check_cooldown_expirations(
        self,
        db: AsyncSession,
    ) -> int:
        """
        檢查並更新所有已過期的冷卻期
        
        應該由定時任務調用
        """
        # 查找所有冷卻期已過的條目
        result = await db.execute(
            select(LedgerEntry).where(
                and_(
                    LedgerEntry.withdrawable_status == WithdrawableStatus.COOLDOWN,
                    LedgerEntry.cooldown_until <= datetime.utcnow(),
                    LedgerEntry.turnover_completed >= LedgerEntry.turnover_required
                )
            )
        )
        entries = result.scalars().all()
        
        unlocked_count = 0
        affected_users = set()
        
        for entry in entries:
            entry.withdrawable_status = WithdrawableStatus.WITHDRAWABLE
            unlocked_count += 1
            affected_users.add(entry.user_id)
            
            logger.info(
                f"Cooldown expired, funds unlocked: "
                f"user={entry.user_id}, entry={entry.id}"
            )
        
        if entries:
            await db.commit()
            
            # 更新受影響用戶的餘額快取
            for user_id in affected_users:
                await self._recalculate_balance_cache(db, user_id, CurrencyType.USDT)
        
        return unlocked_count
    
    # ==================== 餘額查詢 ====================
    
    async def get_balance_breakdown(
        self,
        db: AsyncSession,
        user_id: int,
        currency: CurrencyType = CurrencyType.USDT,
    ) -> dict:
        """
        獲取餘額明細
        """
        source_balances = await self._get_source_balances(db, user_id, currency)
        pending_turnover = await self._get_pending_turnover(db, user_id, currency)
        
        total = sum(sb.total for sb in source_balances)
        withdrawable = sum(sb.withdrawable for sb in source_balances)
        locked = sum(sb.locked for sb in source_balances)
        
        # 找最早解鎖日期
        next_unlock = None
        for sb in source_balances:
            if sb.cooldown_until and (next_unlock is None or sb.cooldown_until < next_unlock):
                next_unlock = sb.cooldown_until
        
        return {
            "currency": currency.value,
            "total_balance": float(total),
            "withdrawable_balance": float(withdrawable),
            "locked_balance": float(locked),
            "pending_turnover": float(pending_turnover),
            "next_unlock_date": next_unlock.isoformat() if next_unlock else None,
            "by_source": [
                {
                    "source": sb.source.value,
                    "total": float(sb.total),
                    "withdrawable": float(sb.withdrawable),
                    "locked": float(sb.locked),
                    "cooldown_until": sb.cooldown_until.isoformat() if sb.cooldown_until else None,
                }
                for sb in source_balances
            ]
        }
    
    # ==================== 私有方法 ====================
    
    async def _get_user(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """獲取用戶"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def _get_source_balances(
        self,
        db: AsyncSession,
        user_id: int,
        currency: CurrencyType,
    ) -> List[SourceBalance]:
        """獲取按來源分類的餘額"""
        # 查詢帳本條目
        result = await db.execute(
            select(
                LedgerEntry.currency_source,
                LedgerEntry.withdrawable_status,
                func.sum(LedgerEntry.amount).label("total"),
                func.min(LedgerEntry.cooldown_until).label("cooldown_until"),
            ).where(
                and_(
                    LedgerEntry.user_id == user_id,
                    LedgerEntry.currency == currency,
                    LedgerEntry.amount > 0,  # 只計算貸方
                )
            ).group_by(
                LedgerEntry.currency_source,
                LedgerEntry.withdrawable_status,
            )
        )
        rows = result.all()
        
        # 整理結果
        source_data = {}
        for row in rows:
            source = row.currency_source
            if source not in source_data:
                source_data[source] = SourceBalance(
                    source=source,
                    total=Decimal("0"),
                    withdrawable=Decimal("0"),
                    locked=Decimal("0"),
                )
            
            amount = Decimal(str(row.total or 0))
            source_data[source].total += amount
            
            if row.withdrawable_status == WithdrawableStatus.WITHDRAWABLE:
                source_data[source].withdrawable += amount
            else:
                source_data[source].locked += amount
                if row.cooldown_until:
                    if source_data[source].cooldown_until is None:
                        source_data[source].cooldown_until = row.cooldown_until
                    else:
                        source_data[source].cooldown_until = min(
                            source_data[source].cooldown_until,
                            row.cooldown_until
                        )
        
        return list(source_data.values())
    
    async def _get_pending_turnover(
        self,
        db: AsyncSession,
        user_id: int,
        currency: CurrencyType,
    ) -> Decimal:
        """獲取待完成流水"""
        result = await db.execute(
            select(
                func.sum(LedgerEntry.turnover_required - LedgerEntry.turnover_completed)
            ).where(
                and_(
                    LedgerEntry.user_id == user_id,
                    LedgerEntry.currency == currency,
                    LedgerEntry.turnover_required > LedgerEntry.turnover_completed,
                )
            )
        )
        pending = result.scalar()
        return Decimal(str(pending or 0))
    
    async def _update_balance_cache(
        self,
        db: AsyncSession,
        user_id: int,
        currency: CurrencyType,
        delta_amount: Decimal,
        source: CurrencySource,
        is_locked: bool,
    ):
        """更新餘額快取"""
        # 查找現有快取
        result = await db.execute(
            select(UserBalance).where(
                and_(
                    UserBalance.user_id == user_id,
                    UserBalance.currency == currency,
                )
            )
        )
        cache = result.scalar_one_or_none()
        
        if not cache:
            cache = UserBalance(
                user_id=user_id,
                currency=currency,
            )
            db.add(cache)
        
        # 更新總餘額
        cache.total_balance = (cache.total_balance or Decimal("0")) + delta_amount
        
        # 更新來源餘額
        if source == CurrencySource.REAL_CRYPTO:
            cache.balance_real_crypto = (cache.balance_real_crypto or Decimal("0")) + delta_amount
        elif source == CurrencySource.STARS_CREDIT:
            cache.balance_stars_credit = (cache.balance_stars_credit or Decimal("0")) + delta_amount
        elif source == CurrencySource.BONUS:
            cache.balance_bonus = (cache.balance_bonus or Decimal("0")) + delta_amount
        elif source == CurrencySource.REFERRAL:
            cache.balance_referral = (cache.balance_referral or Decimal("0")) + delta_amount
        
        # 更新可提現/鎖定餘額
        if is_locked:
            cache.locked_balance = (cache.locked_balance or Decimal("0")) + delta_amount
        else:
            cache.withdrawable_balance = (cache.withdrawable_balance or Decimal("0")) + delta_amount
    
    async def _recalculate_balance_cache(
        self,
        db: AsyncSession,
        user_id: int,
        currency: CurrencyType,
    ):
        """重新計算餘額快取"""
        source_balances = await self._get_source_balances(db, user_id, currency)
        pending_turnover = await self._get_pending_turnover(db, user_id, currency)
        
        # 查找或創建快取
        result = await db.execute(
            select(UserBalance).where(
                and_(
                    UserBalance.user_id == user_id,
                    UserBalance.currency == currency,
                )
            )
        )
        cache = result.scalar_one_or_none()
        
        if not cache:
            cache = UserBalance(
                user_id=user_id,
                currency=currency,
            )
            db.add(cache)
        
        # 重置並重新計算
        cache.total_balance = Decimal("0")
        cache.balance_real_crypto = Decimal("0")
        cache.balance_stars_credit = Decimal("0")
        cache.balance_bonus = Decimal("0")
        cache.balance_referral = Decimal("0")
        cache.withdrawable_balance = Decimal("0")
        cache.locked_balance = Decimal("0")
        cache.pending_turnover = pending_turnover
        
        for sb in source_balances:
            cache.total_balance += sb.total
            cache.withdrawable_balance += sb.withdrawable
            cache.locked_balance += sb.locked
            
            if sb.source == CurrencySource.REAL_CRYPTO:
                cache.balance_real_crypto = sb.total
            elif sb.source == CurrencySource.STARS_CREDIT:
                cache.balance_stars_credit = sb.total
            elif sb.source == CurrencySource.BONUS:
                cache.balance_bonus = sb.total
            elif sb.source == CurrencySource.REFERRAL:
                cache.balance_referral = sb.total
        
        await db.commit()


# ==================== 單例實例 ====================

liquidity_service = LiquidityService()
