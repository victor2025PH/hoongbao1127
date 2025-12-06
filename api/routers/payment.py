"""
支付API路由
处理法币支付、加密货币充值和提现
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from loguru import logger

from shared.database.connection import get_db_session
from shared.database.models import User
from api.services.payment_service import get_payment_service
from api.services.ledger_service import LedgerService
from api.utils.telegram_auth import get_tg_id_from_header
from sqlalchemy import select

router = APIRouter(prefix="/payment", tags=["支付"])


class FiatPaymentRequest(BaseModel):
    """法币支付请求"""
    amount: Decimal
    fiat_currency: str  # CNY, USD等
    provider: str = "unionpay"  # unionpay, visa等
    metadata: Optional[dict] = None


class CryptoDepositRequest(BaseModel):
    """加密货币充值请求"""
    amount: Decimal
    crypto_currency: str  # USDT, TON等
    transaction_hash: str
    metadata: Optional[dict] = None


class WithdrawalRequest(BaseModel):
    """提现请求"""
    amount: Decimal
    currency: str
    destination: str  # 钱包地址或银行账户
    withdrawal_type: str = "crypto"  # crypto or fiat
    metadata: Optional[dict] = None


class PaymentResponse(BaseModel):
    """支付响应"""
    success: bool
    transaction_id: Optional[str] = None
    virtual_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    message: str
    payment_info: Optional[dict] = None


@router.post("/fiat", response_model=PaymentResponse)
async def process_fiat_payment(
    request: FiatPaymentRequest,
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    db: AsyncSession = Depends(get_db_session)
):
    """
    处理法币支付（UnionPay, Visa等）
    自动转换为虚拟USDT并充值到账户
    """
    if tg_id is None:
        raise HTTPException(status_code=401, detail="Telegram user ID is required")
    
    # 查找用户
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 处理支付
    payment_service = get_payment_service()
    success, transaction_id, virtual_usdt, payment_info = await payment_service.process_fiat_payment(
        amount=request.amount,
        fiat_currency=request.fiat_currency,
        provider=request.provider,
        metadata=request.metadata
    )
    
    if not success:
        return PaymentResponse(
            success=False,
            message=f"支付失败: {payment_info.get('error', 'Unknown error')}",
            payment_info=payment_info
        )
    
    # 使用LedgerService充值到账户
    try:
        await LedgerService.create_entry(
            db=db,
            user_id=user.id,
            amount=virtual_usdt,
            currency='USDT',
            entry_type='FIAT_DEPOSIT',
            related_type='payment',
            description=f"法币充值: {request.amount} {request.fiat_currency} -> {virtual_usdt} USDT",
            metadata={
                'transaction_id': transaction_id,
                'fiat_amount': str(request.amount),
                'fiat_currency': request.fiat_currency,
                'provider': request.provider,
                **payment_info
            },
            created_by='payment_gateway'
        )
        
        logger.info(f"✅ 法币充值成功: user_id={user.id}, {request.amount} {request.fiat_currency} -> {virtual_usdt} USDT")
        
        return PaymentResponse(
            success=True,
            transaction_id=transaction_id,
            virtual_amount=virtual_usdt,
            currency='USDT',
            message=f"支付成功！已充值 {virtual_usdt} USDT",
            payment_info=payment_info
        )
    except Exception as e:
        logger.error(f"❌ 充值失败: {e}")
        return PaymentResponse(
            success=False,
            message=f"充值失败: {str(e)}",
            payment_info=payment_info
        )


@router.post("/crypto/deposit", response_model=PaymentResponse)
async def process_crypto_deposit(
    request: CryptoDepositRequest,
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    db: AsyncSession = Depends(get_db_session)
):
    """
    处理加密货币充值
    """
    if tg_id is None:
        raise HTTPException(status_code=401, detail="Telegram user ID is required")
    
    # 查找用户
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 处理充值
    payment_service = get_payment_service()
    success, transaction_id, deposit_info = await payment_service.process_crypto_deposit(
        amount=request.amount,
        crypto_currency=request.crypto_currency,
        transaction_hash=request.transaction_hash,
        metadata=request.metadata
    )
    
    if not success:
        return PaymentResponse(
            success=False,
            message=f"充值失败: {deposit_info.get('error', 'Unknown error')}",
            payment_info=deposit_info
        )
    
    # 使用LedgerService充值到账户
    try:
        await LedgerService.create_entry(
            db=db,
            user_id=user.id,
            amount=request.amount,
            currency=request.crypto_currency.upper(),
            entry_type='DEPOSIT',
            related_type='blockchain',
            description=f"加密货币充值: {request.amount} {request.crypto_currency}",
            metadata={
                'transaction_id': transaction_id,
                'transaction_hash': request.transaction_hash,
                **deposit_info
            },
            created_by='blockchain'
        )
        
        logger.info(f"✅ 加密货币充值成功: user_id={user.id}, {request.amount} {request.crypto_currency}")
        
        return PaymentResponse(
            success=True,
            transaction_id=transaction_id,
            virtual_amount=request.amount,
            currency=request.crypto_currency.upper(),
            message=f"充值成功！已充值 {request.amount} {request.crypto_currency}",
            payment_info=deposit_info
        )
    except Exception as e:
        logger.error(f"❌ 充值失败: {e}")
        return PaymentResponse(
            success=False,
            message=f"充值失败: {str(e)}",
            payment_info=deposit_info
        )


@router.post("/withdraw", response_model=PaymentResponse)
async def process_withdrawal(
    request: WithdrawalRequest,
    tg_id: Optional[int] = Depends(get_tg_id_from_header),
    db: AsyncSession = Depends(get_db_session)
):
    """
    处理提现
    """
    if tg_id is None:
        raise HTTPException(status_code=401, detail="Telegram user ID is required")
    
    # 查找用户
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 检查余额
    current_balance = await LedgerService.get_balance(
        db=db,
        user_id=user.id,
        currency=request.currency.upper()
    )
    
    if current_balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # 处理提现
    payment_service = get_payment_service()
    success, transaction_id, withdrawal_info = await payment_service.process_withdrawal(
        amount=request.amount,
        currency=request.currency,
        destination=request.destination,
        withdrawal_type=request.withdrawal_type,
        metadata=request.metadata
    )
    
    if not success:
        return PaymentResponse(
            success=False,
            message=f"提现失败: {withdrawal_info.get('error', 'Unknown error')}",
            payment_info=withdrawal_info
        )
    
    # 使用LedgerService扣除余额
    try:
        await LedgerService.create_entry(
            db=db,
            user_id=user.id,
            amount=-request.amount,  # 负数表示扣除
            currency=request.currency.upper(),
            entry_type='WITHDRAW',
            related_type='payment',
            description=f"提现: {request.amount} {request.currency} -> {request.destination}",
            metadata={
                'transaction_id': transaction_id,
                'destination': request.destination,
                'withdrawal_type': request.withdrawal_type,
                **withdrawal_info
            },
            created_by='user'
        )
        
        logger.info(f"✅ 提现成功: user_id={user.id}, {request.amount} {request.currency}")
        
        return PaymentResponse(
            success=True,
            transaction_id=transaction_id,
            virtual_amount=request.amount,
            currency=request.currency.upper(),
            message=f"提现成功！已提现 {request.amount} {request.currency}",
            payment_info=withdrawal_info
        )
    except Exception as e:
        logger.error(f"❌ 提现失败: {e}")
        return PaymentResponse(
            success=False,
            message=f"提现失败: {str(e)}",
            payment_info=withdrawal_info
        )


@router.get("/exchange-rate")
async def get_exchange_rate(
    from_currency: str,
    to_currency: str = "USDT"
):
    """
    获取汇率（包含利润点）
    """
    payment_service = get_payment_service()
    rate = await payment_service.get_exchange_rate(from_currency, to_currency)
    
    return {
        'from_currency': from_currency,
        'to_currency': to_currency,
        'rate': str(rate),
        'profit_spread': str(payment_service.profit_spread)
    }

