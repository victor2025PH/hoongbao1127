"""
消息發送服務 - 統一管理所有消息發送
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from shared.database.models import (
    User, Message, MessageType, MessageStatus, UserNotificationSettings
)
from api.routers.messages import manager
from shared.config.settings import get_settings

settings = get_settings()


class MessageService:
    """消息發送服務"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def send_message(
        self,
        user_id: int,
        message_type: MessageType,
        content: str,
        title: Optional[str] = None,
        action_url: Optional[str] = None,
        send_telegram: Optional[bool] = None,  # None 表示根據設置自動判斷
        metadata: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        source_name: Optional[str] = None,
        can_reply: bool = False
    ) -> Message:
        """
        發送消息的核心方法
        - 如果用戶在 miniapp 中：在 miniapp 中顯示
        - 如果用戶不在 miniapp 中：通過 Telegram Bot 發送
        - 根據用戶設置決定是否發送
        """
        # 獲取用戶
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # 獲取通知設置
        result = await self.db.execute(
            select(UserNotificationSettings).where(UserNotificationSettings.user_id == user_id)
        )
        notification_settings = result.scalar_one_or_none()
        
        if not notification_settings:
            # 創建默認設置
            notification_settings = UserNotificationSettings(
                user_id=user_id,
                notification_method="both"
            )
            self.db.add(notification_settings)
            await self.db.flush()
        
        # 檢查該類型消息是否啟用
        type_enabled = self._check_type_enabled(message_type, notification_settings)
        if not type_enabled:
            logger.info(f"Message type {message_type} is disabled for user {user_id}")
            # 即使禁用，也創建消息記錄（但不發送通知）
            send_telegram = False
        
        # 創建消息記錄
        message = Message(
            user_id=user_id,
            message_type=message_type,
            status=MessageStatus.UNREAD,
            title=title,
            content=content,
            action_url=action_url,
            meta_data=metadata,  # 使用 meta_data 而不是 metadata
            source=source,
            source_name=source_name,
            can_reply=can_reply
        )
        self.db.add(message)
        await self.db.flush()
        
        # 決定發送方式
        if send_telegram is None:
            # 根據設置自動判斷
            notification_method = notification_settings.notification_method
            user_online = manager.is_user_online(user_id)
            
            if notification_method == "off":
                # 關閉所有通知
                send_telegram = False
            elif notification_method == "miniapp_only":
                # 僅在 miniapp 中提示
                send_telegram = False
            elif notification_method == "telegram_only":
                # 僅通過 Telegram 發送
                send_telegram = True
            elif notification_method == "both":
                # 雙提示：在線用戶在 miniapp 中提示，離線用戶通過 Telegram 發送
                if user_online:
                    send_telegram = False  # 在線用戶，通過 WebSocket 推送
                else:
                    send_telegram = True   # 離線用戶，通過 Telegram 發送
            else:
                send_telegram = False
        
        # 發送通知
        if send_telegram:
            # 通過 Telegram Bot 發送
            await self._send_via_telegram(user, message)
        else:
            # 通過 WebSocket 推送（如果用戶在線）
            if manager.is_user_online(user_id):
                await self._send_via_websocket(user_id, message)
        
        await self.db.commit()
        await self.db.refresh(message)
        
        return message
    
    def _check_type_enabled(self, message_type: MessageType, settings: UserNotificationSettings) -> bool:
        """檢查該類型消息是否啟用"""
        type_map = {
            MessageType.SYSTEM: settings.enable_system,
            MessageType.REDPACKET: settings.enable_redpacket,
            MessageType.BALANCE: settings.enable_balance,
            MessageType.ACTIVITY: settings.enable_activity,
            MessageType.MINIAPP: settings.enable_miniapp,
            MessageType.TELEGRAM: settings.enable_telegram,
            MessageType.BOT: settings.enable_system,  # Bot 消息使用系統設置
        }
        return type_map.get(message_type, True)
    
    async def _send_via_websocket(self, user_id: int, message: Message):
        """通過 WebSocket 推送消息"""
        try:
            message_data = {
                "type": "new_message",
                "message": {
                    "id": message.id,
                    "message_type": message.message_type.value,
                    "title": message.title,
                    "content": message.content,
                    "action_url": message.action_url,
                    "created_at": message.created_at.isoformat(),
                }
            }
            await manager.send_personal_message(message_data, user_id)
            logger.info(f"Message {message.id} sent via WebSocket to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send message via WebSocket: {e}")
    
    async def _send_via_telegram(self, user: User, message: Message):
        """通過 Telegram Bot 發送消息"""
        try:
            from telegram import Bot
            from telegram.error import TelegramError
            
            bot = Bot(token=settings.BOT_TOKEN)
            
            # 構建消息文本
            text_parts = []
            if message.title:
                text_parts.append(f"*{message.title}*")
            text_parts.append(message.content)
            
            if message.action_url:
                text_parts.append(f"\n[點擊查看]({message.action_url})")
            
            text = "\n\n".join(text_parts)
            
            # 發送消息
            await bot.send_message(
                chat_id=user.tg_id,
                text=text,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            logger.info(f"Message {message.id} sent via Telegram to user {user.tg_id}")
        except TelegramError as e:
            logger.error(f"Failed to send message via Telegram: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
    
    async def send_redpacket_notification(
        self,
        user_id: int,
        redpacket_id: int,
        amount: float,
        currency: str,
        is_claimed: bool = True
    ):
        """發送紅包相關通知"""
        if is_claimed:
            title = "🎉 紅包已領取"
            content = f"恭喜！您領取了 {amount} {currency.upper()} 紅包"
        else:
            title = "🧧 新紅包"
            content = f"您收到一個 {amount} {currency.upper()} 紅包"
        
        return await self.send_message(
            user_id=user_id,
            message_type=MessageType.REDPACKET,
            title=title,
            content=content,
            action_url=f"/packets/{redpacket_id}",
            metadata={"redpacket_id": redpacket_id, "amount": amount, "currency": currency},
            source="system",
            source_name="紅包系統"
        )
    
    async def send_balance_notification(
        self,
        user_id: int,
        amount: float,
        currency: str,
        transaction_type: str,
        balance_after: float
    ):
        """發送餘額變動通知"""
        type_map = {
            "deposit": ("💰 充值成功", f"您已充值 {amount} {currency.upper()}"),
            "withdraw": ("💸 提現成功", f"您已提現 {amount} {currency.upper()}"),
            "send": ("📤 發送成功", f"您已發送 {amount} {currency.upper()}"),
            "receive": ("📥 收到", f"您收到 {amount} {currency.upper()}"),
        }
        
        title, content = type_map.get(transaction_type, ("💰 餘額變動", f"您的 {currency.upper()} 餘額已變動"))
        content += f"\n當前餘額: {balance_after} {currency.upper()}"
        
        return await self.send_message(
            user_id=user_id,
            message_type=MessageType.BALANCE,
            title=title,
            content=content,
            action_url="/wallet",
            metadata={
                "amount": amount,
                "currency": currency,
                "type": transaction_type,
                "balance_after": balance_after
            },
            source="system",
            source_name="錢包系統"
        )
    
    async def send_system_notification(
        self,
        user_id: int,
        title: str,
        content: str,
        action_url: Optional[str] = None
    ):
        """發送系統通知"""
        return await self.send_message(
            user_id=user_id,
            message_type=MessageType.SYSTEM,
            title=title,
            content=content,
            action_url=action_url,
            source="system",
            source_name="系統"
        )

