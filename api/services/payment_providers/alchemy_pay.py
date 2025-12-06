"""
Alchemy Pay 支付提供者
真实支付API集成
"""
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from loguru import logger
import httpx
import hmac
import hashlib
import json
from urllib.parse import urlencode

from shared.config.settings import get_settings

settings = get_settings()


class AlchemyPayProvider:
    """Alchemy Pay支付提供者"""
    
    def __init__(self):
        # 从环境变量获取配置
        self.api_key = getattr(settings, 'ALCHEMY_PAY_API_KEY', '')
        self.api_secret = getattr(settings, 'ALCHEMY_PAY_API_SECRET', '')
        self.base_url = getattr(settings, 'ALCHEMY_PAY_BASE_URL', 'https://api.alchemypay.org')
        self.merchant_id = getattr(settings, 'ALCHEMY_PAY_MERCHANT_ID', '')
        
        if not self.api_key or not self.api_secret:
            logger.warning("⚠️ Alchemy Pay配置未设置，将使用Mock模式")
            self.is_mock = True
        else:
            self.is_mock = False
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """生成签名"""
        # 按key排序
        sorted_params = sorted(params.items())
        # 构建签名字符串
        sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params if k != 'sign'])
        sign_str += f"&key={self.api_secret}"
        # HMAC-SHA256签名
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        return signature
    
    async def process_payment(
        self,
        amount: Decimal,
        currency: str,
        metadata: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        处理支付（Alchemy Pay）
        
        Args:
            amount: 支付金额（法币，如CNY）
            currency: 法币类型（CNY, USD等）
            metadata: 支付元数据（包含用户信息、订单信息等）
        
        Returns:
            (是否成功, 交易ID, 额外信息)
        """
        if self.is_mock:
            # Mock模式
            transaction_id = f"ALCHEMY_MOCK_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            logger.info(f"✅ Alchemy Pay Mock支付成功: {transaction_id}, 金额: {amount} {currency}")
            return True, transaction_id, {
                'provider': 'alchemy_pay',
                'transaction_id': transaction_id,
                'amount': str(amount),
                'currency': currency,
                'status': 'completed',
                'completed_at': datetime.utcnow().isoformat(),
                'is_mock': True
            }
        
        try:
            # 构建请求参数
            params = {
                'merchant_id': self.merchant_id,
                'amount': str(amount),
                'currency': currency.upper(),
                'order_id': metadata.get('order_id', f"ORDER_{datetime.utcnow().timestamp()}"),
                'notify_url': metadata.get('notify_url', f"{settings.API_BASE_URL}/api/v1/payment/webhook/alchemy"),
                'return_url': metadata.get('return_url', ''),
                'timestamp': int(datetime.utcnow().timestamp()),
            }
            
            # 生成签名
            params['sign'] = self._generate_signature(params)
            
            # 发送请求
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/payment/create",
                    json=params,
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {self.api_key}'
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 200:
                        transaction_id = result.get('data', {}).get('transaction_id')
                        payment_url = result.get('data', {}).get('payment_url')
                        
                        logger.info(f"✅ Alchemy Pay支付创建成功: {transaction_id}")
                        return True, transaction_id, {
                            'provider': 'alchemy_pay',
                            'transaction_id': transaction_id,
                            'payment_url': payment_url,
                            'amount': str(amount),
                            'currency': currency,
                            'status': 'pending',
                            'created_at': datetime.utcnow().isoformat()
                        }
                    else:
                        error_msg = result.get('message', 'Unknown error')
                        logger.error(f"❌ Alchemy Pay支付失败: {error_msg}")
                        return False, None, {'error': error_msg}
                else:
                    logger.error(f"❌ Alchemy Pay API错误: {response.status_code}")
                    return False, None, {'error': f'API error: {response.status_code}'}
                    
        except Exception as e:
            logger.error(f"❌ Alchemy Pay支付异常: {e}")
            return False, None, {'error': str(e)}
    
    async def verify_webhook(self, data: Dict[str, Any], signature: str) -> bool:
        """验证Webhook签名"""
        if self.is_mock:
            return True
        
        try:
            # 重新计算签名
            calculated_sign = self._generate_signature(data)
            return calculated_sign == signature
        except Exception as e:
            logger.error(f"❌ Webhook签名验证失败: {e}")
            return False

