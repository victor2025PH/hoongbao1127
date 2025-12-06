"""
支付Webhook路由
处理支付提供者的回调通知
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, Dict, Any
from loguru import logger

from shared.database.connection import get_db_session
from shared.database.models import User
from api.services.ledger_service import LedgerService
from sqlalchemy import select

router = APIRouter(prefix="/payment/webhook", tags=["支付Webhook"])


class AlchemyPayWebhook(BaseModel):
    """Alchemy Pay Webhook数据"""
    transaction_id: str
    order_id: str
    amount: str
    currency: str
    status: str  # success, failed, pending
    timestamp: int
    sign: str


@router.post("/alchemy")
async def alchemy_pay_webhook(
    request: Request,
    webhook_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db_session)
):
    """
    处理Alchemy Pay Webhook回调
    """
    try:
        from api.services.payment_providers.alchemy_pay import AlchemyPayProvider
        
        provider = AlchemyPayProvider()
        signature = webhook_data.get('sign', '')
        
        # 验证签名
        if not provider.verify_webhook(webhook_data, signature):
            logger.warning(f"❌ Alchemy Pay Webhook签名验证失败")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        transaction_id = webhook_data.get('transaction_id')
        order_id = webhook_data.get('order_id')
        status = webhook_data.get('status')
        amount = webhook_data.get('amount')
        currency = webhook_data.get('currency')
        
        logger.info(f"📥 Alchemy Pay Webhook: {transaction_id}, status={status}")
        
        # 如果支付成功，处理充值
        if status == 'success':
            # 从order_id或metadata中获取user_id
            # 这里假设order_id格式为 "ORDER_USERID_TIMESTAMP"
            try:
                user_id = int(order_id.split('_')[1]) if '_' in order_id else None
            except:
                user_id = None
            
            if not user_id:
                # 尝试从metadata中获取
                metadata = webhook_data.get('metadata', {})
                user_id = metadata.get('user_id')
            
            if user_id:
                # 查找用户
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                
                if user:
                    # 计算虚拟USDT金额（需要获取汇率）
                    from api.services.payment_service import get_payment_service
                    payment_service = get_payment_service()
                    exchange_rate = await payment_service.get_exchange_rate(currency, 'USDT')
                    from decimal import Decimal
                    virtual_usdt = Decimal(amount) / exchange_rate
                    
                    # 使用LedgerService充值
                    await LedgerService.create_entry(
                        db=db,
                        user_id=user.id,
                        amount=virtual_usdt,
                        currency='USDT',
                        entry_type='FIAT_DEPOSIT',
                        related_type='payment',
                        description=f"Alchemy Pay充值: {amount} {currency} -> {virtual_usdt} USDT",
                        metadata={
                            'transaction_id': transaction_id,
                            'order_id': order_id,
                            'provider': 'alchemy_pay',
                            'fiat_amount': amount,
                            'fiat_currency': currency,
                            'exchange_rate': str(exchange_rate)
                        },
                        created_by='payment_gateway'
                    )
                    
                    logger.info(f"✅ Alchemy Pay充值成功: user_id={user.id}, {amount} {currency} -> {virtual_usdt} USDT")
                else:
                    logger.warning(f"⚠️ 用户未找到: user_id={user_id}")
            else:
                logger.warning(f"⚠️ 无法从Webhook中获取user_id")
        
        return {"status": "ok", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(f"❌ 处理Alchemy Pay Webhook失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

