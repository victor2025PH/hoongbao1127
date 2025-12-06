"""
Lucky Red - 錢包路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from loguru import logger

from shared.database.connection import get_db_session
from shared.database.models import User, Transaction, CurrencyType
from api.utils.telegram_auth import get_tg_id_from_header

router = APIRouter()


class BalanceResponse(BaseModel):
    """餘額響應"""
    usdt: float
    ton: float
    stars: int
    points: int
    total_usdt: float  # 折算成 USDT 的總值


class TransactionResponse(BaseModel):
    """交易記錄響應"""
    id: int
    type: str
    currency: str
    amount: float
    note: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DepositRequest(BaseModel):
    """充值請求"""
    currency: CurrencyType
    amount: float = Field(..., gt=0)
    tx_hash: Optional[str] = None


class WithdrawRequest(BaseModel):
    """提現請求"""
    currency: CurrencyType
    amount: float = Field(..., gt=0)
    address: str = Field(..., min_length=10, max_length=128)


class DepositResponse(BaseModel):
    """充值響應"""
    success: bool
    transaction_id: int
    message: str
    status: str  # pending, completed
    note: Optional[str] = None


class WithdrawResponse(BaseModel):
    """提現響應"""
    success: bool
    transaction_id: int
    message: str
    status: str  # pending, completed
    note: Optional[str] = None


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    db: AsyncSession = Depends(get_db_session)
):
    """獲取餘額（带缓存）"""
    if tg_id is None:
        raise HTTPException(status_code=401, detail="Telegram user ID is required")
    
    # 尝试从缓存获取
    from api.services.cache_service import get_cache_service
    cache = get_cache_service()
    cache_key = f"balance:{tg_id}"
    cached_balance = await cache.get(cache_key)
    
    if cached_balance:
        return BalanceResponse(**cached_balance)
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 使用 LedgerService 获取余额（如果可用）
    try:
        from api.services.ledger_service import LedgerService
        from decimal import Decimal
        
        usdt = float(await LedgerService.get_balance(db, user.id, 'USDT') or Decimal('0'))
        ton = float(await LedgerService.get_balance(db, user.id, 'TON') or Decimal('0'))
        stars = int(await LedgerService.get_balance(db, user.id, 'STARS') or Decimal('0'))
        points = int(await LedgerService.get_balance(db, user.id, 'POINTS') or Decimal('0'))
    except:
        # 回退到用户表余额
        usdt = float(user.balance_usdt or 0)
        ton = float(user.balance_ton or 0)
        stars = user.balance_stars or 0
        points = user.balance_points or 0
    
    # 簡單折算 (實際應該使用匯率 API)
    total_usdt = usdt + ton * 5.0 + stars * 0.01 + points * 0.001
    
    balance_response = BalanceResponse(
        usdt=usdt,
        ton=ton,
        stars=stars,
        points=points,
        total_usdt=round(total_usdt, 2),
    )
    
    # 缓存 30 秒
    await cache.set(cache_key, balance_response.model_dump(), expire=30)
    
    return balance_response


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session)
):
    """獲取交易記錄"""
    if tg_id is None:
        raise HTTPException(status_code=401, detail="Telegram user ID is required")
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    transactions = result.scalars().all()
    
    return transactions


@router.post("/deposit", response_model=DepositResponse)
async def deposit(
    request: DepositRequest,
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    db: AsyncSession = Depends(get_db_session)
):
    """充值 (需要管理員審核)"""
    if tg_id is None:
        raise HTTPException(status_code=401, detail="Telegram user ID is required")
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 驗證金額
    amount = Decimal(str(request.amount))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    # 檢查最小充值金額（例如 1 USDT）
    min_deposit = Decimal("1.0")
    if amount < min_deposit:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum deposit amount is {min_deposit} {request.currency.value.upper()}"
        )
    
    # 獲取當前餘額
    balance_field = f"balance_{request.currency.value}"
    current_balance = getattr(user, balance_field, 0) or Decimal(0)
    
    # 創建充值交易記錄（狀態為 pending，等待管理員審核）
    transaction = Transaction(
        user_id=user.id,
        type="deposit",
        currency=request.currency,
        amount=amount,
        balance_before=current_balance,
        balance_after=current_balance,  # 審核通過後才會更新
        ref_id=request.tx_hash,  # 交易哈希
        note=f"充值 {amount} {request.currency.value.upper()}" + (f" (TX: {request.tx_hash})" if request.tx_hash else ""),
        status="pending"
    )
    
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    
    logger.info(f"Deposit request created: user_id={user.id}, amount={amount}, currency={request.currency.value}, tx_id={transaction.id}")
    
    return DepositResponse(
        success=True,
        transaction_id=transaction.id,
        message=f"充值申請已提交，等待管理員審核。金額: {amount} {request.currency.value.upper()}",
        status="pending",
        note="請等待管理員審核，審核通過後餘額將自動到賬"
    )


@router.post("/withdraw", response_model=WithdrawResponse)
async def withdraw(
    request: WithdrawRequest,
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    db: AsyncSession = Depends(get_db_session)
):
    """提現 (需要管理員審核)"""
    if tg_id is None:
        raise HTTPException(status_code=401, detail="Telegram user ID is required")
    
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 驗證金額
    amount = Decimal(str(request.amount))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    # 檢查最小提現金額（例如 10 USDT）
    min_withdraw = Decimal("10.0")
    if amount < min_withdraw:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum withdraw amount is {min_withdraw} {request.currency.value.upper()}"
        )
    
    # 檢查餘額
    balance_field = f"balance_{request.currency.value}"
    current_balance = getattr(user, balance_field, 0) or Decimal(0)
    
    if current_balance < amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Current: {current_balance} {request.currency.value.upper()}, Required: {amount} {request.currency.value.upper()}"
        )
    
    # 驗證地址格式（簡單驗證）
    if not request.address or len(request.address) < 10:
        raise HTTPException(status_code=400, detail="Invalid withdrawal address")
    
    # 凍結餘額（扣除，但狀態為 pending，審核通過後才真正轉出）
    new_balance = current_balance - amount
    setattr(user, balance_field, new_balance)
    
    # 創建提現交易記錄（狀態為 pending，等待管理員審核）
    transaction = Transaction(
        user_id=user.id,
        type="withdraw",
        currency=request.currency,
        amount=amount,
        balance_before=current_balance,
        balance_after=new_balance,  # 已凍結
        ref_id=request.address,  # 提現地址
        note=f"提現 {amount} {request.currency.value.upper()} 到 {request.address}",
        status="pending"
    )
    
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    
    logger.info(f"Withdraw request created: user_id={user.id}, amount={amount}, currency={request.currency.value}, address={request.address}, tx_id={transaction.id}")
    
    return WithdrawResponse(
        success=True,
        transaction_id=transaction.id,
        message=f"提現申請已提交，等待管理員審核。金額: {amount} {request.currency.value.upper()}",
        status="pending",
        note=f"餘額已凍結，審核通過後將轉賬到地址: {request.address}"
    )

