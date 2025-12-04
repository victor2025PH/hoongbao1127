"""
Lucky Red 紅包遊戲 - AI 系統對接 SDK

文件：lucky_red_ai_sdk.py
版本：2.0
日期：2025-12-02

使用方法：
1. pip install httpx
2. 複製此文件到您的項目
3. 參考下方範例使用

GitHub: [紅包遊戲項目地址]
"""

import httpx
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum


class Currency(str, Enum):
    """支持的幣種"""
    USDT = "usdt"
    TON = "ton"
    STARS = "stars"
    POINTS = "points"


class PacketType(str, Enum):
    """紅包類型"""
    RANDOM = "random"  # 手氣紅包（隨機金額）
    EQUAL = "equal"    # 炸彈紅包（平分金額，帶炸彈數字）


@dataclass
class APIResponse:
    """API 響應"""
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[Dict[str, Any]]
    raw_response: Optional[httpx.Response] = None
    
    @property
    def error_message(self) -> str:
        """獲取錯誤信息"""
        if self.error:
            return self.error.get("detail", str(self.error))
        return ""


class LuckyRedAIError(Exception):
    """Lucky Red API 錯誤"""
    def __init__(self, message: str, response: APIResponse = None):
        self.message = message
        self.response = response
        super().__init__(message)


class LuckyRedAIClient:
    """
    Lucky Red 紅包遊戲 AI API 客戶端
    
    使用範例:
    ```python
    client = LuckyRedAIClient(
        api_key="your-api-key",
        base_url="http://localhost:8080"
    )
    
    # 查詢餘額
    result = client.get_balance(telegram_user_id=123456789)
    print(result.data)
    
    # 發送紅包
    result = client.send_packet(
        telegram_user_id=123456789,
        total_amount=10.0,
        total_count=5
    )
    print(result.data['share_url'])
    ```
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8080",
        ai_system_id: str = "ai-chat-system",
        timeout: float = 30.0,
        raise_on_error: bool = False
    ):
        """
        初始化客戶端
        
        Args:
            api_key: API 金鑰
            base_url: API 服務器地址
            ai_system_id: AI 系統標識（用於日誌追蹤）
            timeout: 請求超時時間（秒）
            raise_on_error: 是否在 API 錯誤時拋出異常
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.ai_system_id = ai_system_id
        self.timeout = timeout
        self.raise_on_error = raise_on_error
    
    def _get_headers(self, telegram_user_id: int) -> Dict[str, str]:
        """生成請求 headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Telegram-User-Id": str(telegram_user_id),
            "X-AI-System-Id": self.ai_system_id,
            "Content-Type": "application/json"
        }
    
    def _handle_response(self, response: httpx.Response) -> APIResponse:
        """處理 API 響應"""
        try:
            data = response.json()
        except Exception:
            data = {"success": False, "error": {"detail": response.text}}
        
        result = APIResponse(
            success=data.get("success", response.status_code == 200),
            data=data.get("data"),
            error=data.get("error") or ({"detail": data.get("detail")} if "detail" in data else None),
            raw_response=response
        )
        
        # HTTP 錯誤
        if response.status_code >= 400:
            result.success = False
            if not result.error:
                result.error = {"detail": f"HTTP {response.status_code}"}
        
        # 是否拋出異常
        if self.raise_on_error and not result.success:
            raise LuckyRedAIError(result.error_message, result)
        
        return result
    
    # ==================== 同步 API ====================
    
    def check_health(self) -> APIResponse:
        """
        檢查 API 健康狀態
        
        Returns:
            APIResponse with status info
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/api/v2/ai/status")
            return self._handle_response(response)
    
    def get_balance(self, telegram_user_id: int) -> APIResponse:
        """
        查詢用戶餘額
        
        Args:
            telegram_user_id: Telegram 用戶 ID
            
        Returns:
            APIResponse with balances data:
            {
                "user_id": 123456789,
                "balances": {
                    "usdt": 100.0,
                    "ton": 5.0,
                    "stars": 1000,
                    "points": 500
                },
                "total_usdt_equivalent": 125.0
            }
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/v2/ai/wallet/balance",
                headers=self._get_headers(telegram_user_id)
            )
            return self._handle_response(response)
    
    def get_profile(self, telegram_user_id: int) -> APIResponse:
        """
        獲取用戶資料
        
        Args:
            telegram_user_id: Telegram 用戶 ID
            
        Returns:
            APIResponse with user profile data
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/v2/ai/user/profile",
                headers=self._get_headers(telegram_user_id)
            )
            return self._handle_response(response)
    
    def send_packet(
        self,
        telegram_user_id: int,
        total_amount: float,
        total_count: int,
        currency: Union[str, Currency] = Currency.USDT,
        packet_type: Union[str, PacketType] = PacketType.RANDOM,
        message: str = "🤖 AI 紅包",
        chat_id: Optional[int] = None,
        bomb_number: Optional[int] = None
    ) -> APIResponse:
        """
        發送紅包
        
        Args:
            telegram_user_id: 發送者 Telegram ID
            total_amount: 紅包總金額
            total_count: 紅包份數（1-100）
            currency: 幣種（usdt, ton, stars, points）
            packet_type: 類型（random=手氣, equal=炸彈）
            message: 祝福語
            chat_id: 目標群組 ID（可選）
            bomb_number: 炸彈數字 0-9（炸彈紅包必填）
            
        Returns:
            APIResponse with packet data:
            {
                "packet_id": "uuid",
                "share_url": "https://t.me/...",
                "remaining_balance": 90.0
            }
            
        Raises:
            LuckyRedAIError: 如果 raise_on_error=True 且發生錯誤
        """
        # 處理枚舉
        if isinstance(currency, Currency):
            currency = currency.value
        if isinstance(packet_type, PacketType):
            packet_type = packet_type.value
        
        payload = {
            "currency": currency,
            "packet_type": packet_type,
            "total_amount": total_amount,
            "total_count": total_count,
            "message": message
        }
        
        if chat_id is not None:
            payload["chat_id"] = chat_id
        if bomb_number is not None:
            payload["bomb_number"] = bomb_number
        
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/v2/ai/packets/send",
                headers=self._get_headers(telegram_user_id),
                json=payload
            )
            return self._handle_response(response)
    
    def send_random_packet(
        self,
        telegram_user_id: int,
        total_amount: float,
        total_count: int,
        currency: str = "usdt",
        message: str = "🎲 手氣紅包"
    ) -> APIResponse:
        """
        發送手氣紅包（便捷方法）
        """
        return self.send_packet(
            telegram_user_id=telegram_user_id,
            total_amount=total_amount,
            total_count=total_count,
            currency=currency,
            packet_type=PacketType.RANDOM,
            message=message
        )
    
    def send_bomb_packet(
        self,
        telegram_user_id: int,
        total_amount: float,
        total_count: int,
        bomb_number: int,
        currency: str = "usdt",
        message: str = "💣 炸彈紅包"
    ) -> APIResponse:
        """
        發送炸彈紅包（便捷方法）
        
        Args:
            total_count: 必須是 5（雙雷）或 10（單雷）
            bomb_number: 炸彈數字 0-9
        """
        if total_count not in [5, 10]:
            return APIResponse(
                success=False,
                data=None,
                error={"detail": "炸彈紅包份數必須是 5（雙雷）或 10（單雷）"}
            )
        
        return self.send_packet(
            telegram_user_id=telegram_user_id,
            total_amount=total_amount,
            total_count=total_count,
            currency=currency,
            packet_type=PacketType.EQUAL,
            message=message,
            bomb_number=bomb_number
        )
    
    def claim_packet(
        self,
        telegram_user_id: int,
        packet_uuid: str
    ) -> APIResponse:
        """
        領取紅包
        
        Args:
            telegram_user_id: 領取者 Telegram ID
            packet_uuid: 紅包 UUID
            
        Returns:
            APIResponse with claim result:
            {
                "claimed_amount": 2.5,
                "is_bomb": false,
                "penalty_amount": 0,
                "new_balance": 102.5,
                "message": "恭喜獲得 2.5 USDT"
            }
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/v2/ai/packets/claim",
                headers=self._get_headers(telegram_user_id),
                json={"packet_uuid": packet_uuid}
            )
            return self._handle_response(response)
    
    def transfer(
        self,
        from_user_id: int,
        to_user_id: int,
        amount: float,
        currency: str = "usdt",
        note: str = ""
    ) -> APIResponse:
        """
        內部轉帳（零手續費）
        
        Args:
            from_user_id: 轉出方 Telegram ID
            to_user_id: 接收方 Telegram ID
            amount: 轉帳金額
            currency: 幣種
            note: 備註
            
        Returns:
            APIResponse with transfer result
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/v2/ai/wallet/transfer",
                headers=self._get_headers(from_user_id),
                json={
                    "to_user_id": to_user_id,
                    "currency": currency,
                    "amount": amount,
                    "note": note
                }
            )
            return self._handle_response(response)
    
    def get_packet_info(
        self,
        telegram_user_id: int,
        packet_uuid: str
    ) -> APIResponse:
        """
        獲取紅包詳情
        
        Args:
            telegram_user_id: 查詢者 Telegram ID
            packet_uuid: 紅包 UUID
            
        Returns:
            APIResponse with packet details
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/v2/ai/packets/{packet_uuid}",
                headers=self._get_headers(telegram_user_id)
            )
            return self._handle_response(response)
    
    # ==================== 異步 API ====================
    
    async def async_get_balance(self, telegram_user_id: int) -> APIResponse:
        """異步查詢用戶餘額"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v2/ai/wallet/balance",
                headers=self._get_headers(telegram_user_id)
            )
            return self._handle_response(response)
    
    async def async_get_profile(self, telegram_user_id: int) -> APIResponse:
        """異步獲取用戶資料"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v2/ai/user/profile",
                headers=self._get_headers(telegram_user_id)
            )
            return self._handle_response(response)
    
    async def async_send_packet(
        self,
        telegram_user_id: int,
        total_amount: float,
        total_count: int,
        **kwargs
    ) -> APIResponse:
        """異步發送紅包"""
        payload = {
            "currency": kwargs.get("currency", "usdt"),
            "packet_type": kwargs.get("packet_type", "random"),
            "total_amount": total_amount,
            "total_count": total_count,
            "message": kwargs.get("message", "🤖 AI 紅包")
        }
        if kwargs.get("chat_id"):
            payload["chat_id"] = kwargs["chat_id"]
        if kwargs.get("bomb_number") is not None:
            payload["bomb_number"] = kwargs["bomb_number"]
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v2/ai/packets/send",
                headers=self._get_headers(telegram_user_id),
                json=payload
            )
            return self._handle_response(response)
    
    async def async_claim_packet(
        self,
        telegram_user_id: int,
        packet_uuid: str
    ) -> APIResponse:
        """異步領取紅包"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v2/ai/packets/claim",
                headers=self._get_headers(telegram_user_id),
                json={"packet_uuid": packet_uuid}
            )
            return self._handle_response(response)
    
    async def async_transfer(
        self,
        from_user_id: int,
        to_user_id: int,
        amount: float,
        currency: str = "usdt",
        note: str = ""
    ) -> APIResponse:
        """異步內部轉帳"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v2/ai/wallet/transfer",
                headers=self._get_headers(from_user_id),
                json={
                    "to_user_id": to_user_id,
                    "currency": currency,
                    "amount": amount,
                    "note": note
                }
            )
            return self._handle_response(response)


# ==================== 使用範例 ====================

def example_sync():
    """同步使用範例"""
    print("=" * 50)
    print("同步 API 使用範例")
    print("=" * 50)
    
    # 初始化客戶端
    client = LuckyRedAIClient(
        api_key="test-api-key",
        base_url="http://localhost:8080",
        ai_system_id="example-ai-bot"
    )
    
    user_id = 123456789
    
    # 1. 查詢餘額
    print("\n1. 查詢餘額:")
    result = client.get_balance(user_id)
    if result.success:
        print(f"   USDT: {result.data['balances']['usdt']}")
        print(f"   TON: {result.data['balances']['ton']}")
    else:
        print(f"   錯誤: {result.error_message}")
    
    # 2. 發送手氣紅包
    print("\n2. 發送手氣紅包:")
    result = client.send_random_packet(
        telegram_user_id=user_id,
        total_amount=10.0,
        total_count=5,
        message="AI 測試紅包 🎉"
    )
    if result.success:
        print(f"   紅包 ID: {result.data['packet_id']}")
        print(f"   分享連結: {result.data['share_url']}")
        packet_id = result.data['packet_id']
    else:
        print(f"   錯誤: {result.error_message}")
        packet_id = None
    
    # 3. 領取紅包
    if packet_id:
        print("\n3. 領取紅包:")
        result = client.claim_packet(
            telegram_user_id=987654321,
            packet_uuid=packet_id
        )
        if result.success:
            print(f"   領取金額: {result.data['claimed_amount']}")
            print(f"   是否踩雷: {result.data['is_bomb']}")
        else:
            print(f"   錯誤: {result.error_message}")


async def example_async():
    """異步使用範例"""
    print("\n" + "=" * 50)
    print("異步 API 使用範例")
    print("=" * 50)
    
    client = LuckyRedAIClient(
        api_key="test-api-key",
        base_url="http://localhost:8080"
    )
    
    # 異步查詢餘額
    result = await client.async_get_balance(123456789)
    if result.success:
        print(f"\n異步查詢餘額: {result.data['balances']}")
    
    # 異步發送紅包
    result = await client.async_send_packet(
        telegram_user_id=123456789,
        total_amount=5.0,
        total_count=3
    )
    if result.success:
        print(f"異步發送紅包成功: {result.data['packet_id']}")


if __name__ == "__main__":
    # 運行同步範例
    example_sync()
    
    # 運行異步範例
    import asyncio
    asyncio.run(example_async())
