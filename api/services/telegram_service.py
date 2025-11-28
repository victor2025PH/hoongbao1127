"""
Telegram Bot 服務封裝
用於管理群組和發送消息
"""
from telegram import Bot
from telegram.error import TelegramError
from typing import Optional, List, Dict, Any
from loguru import logger
from shared.config.settings import get_settings
from shared.database.connection import get_db_session
from shared.database.models import TelegramGroup, TelegramMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

settings = get_settings()

# 全局 Bot 實例
_bot_instance: Optional[Bot] = None


def get_bot() -> Bot:
    """獲取 Bot 實例（單例模式）"""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = Bot(token=settings.BOT_TOKEN)
    return _bot_instance


class TelegramBotService:
    """Telegram Bot 服務類"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.bot = get_bot()
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = "Markdown",
        reply_markup: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """發送文本消息"""
        try:
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                **kwargs
            )
            
            # 記錄消息到數據庫
            await self._save_message_record(
                message_id=message.message_id,
                chat_id=chat_id,
                chat_type="private" if chat_id > 0 else "group",
                message_type="text",
                content=text,
                keyboard=reply_markup,
                status="sent"
            )
            
            return {
                "success": True,
                "message_id": message.message_id,
                "chat_id": message.chat.id,
                "text": message.text
            }
        except TelegramError as e:
            logger.error(f"Failed to send message to {chat_id}: {str(e)}")
            await self._save_message_record(
                message_id=None,
                chat_id=chat_id,
                chat_type="private" if chat_id > 0 else "group",
                message_type="text",
                content=text,
                status="failed"
            )
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_photo(
        self,
        chat_id: int,
        photo: str,
        caption: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """發送圖片"""
        try:
            message = await self.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                **kwargs
            )
            
            await self._save_message_record(
                message_id=message.message_id,
                chat_id=chat_id,
                chat_type="private" if chat_id > 0 else "group",
                message_type="photo",
                content=caption or "",
                media_url=photo,
                status="sent"
            )
            
            return {
                "success": True,
                "message_id": message.message_id,
                "chat_id": message.chat.id
            }
        except TelegramError as e:
            logger.error(f"Failed to send photo to {chat_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_batch_messages(
        self,
        chat_ids: List[int],
        text: str,
        **kwargs
    ) -> Dict[str, Any]:
        """批量發送消息"""
        results = {
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for chat_id in chat_ids:
            result = await self.send_message(chat_id, text, **kwargs)
            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "chat_id": chat_id,
                    "error": result.get("error", "Unknown error")
                })
        
        return results
    
    async def get_chat(self, chat_id: int) -> Dict[str, Any]:
        """獲取群組/用戶信息"""
        try:
            chat = await self.bot.get_chat(chat_id=chat_id)
            
            # 更新或創建群組記錄
            if chat_id < 0:  # 群組 ID 為負數
                await self._update_group_record(chat)
            
            return {
                "success": True,
                "chat": {
                    "id": chat.id,
                    "title": getattr(chat, "title", None),
                    "type": chat.type,
                    "username": getattr(chat, "username", None),
                    "description": getattr(chat, "description", None),
                }
            }
        except TelegramError as e:
            logger.error(f"Failed to get chat {chat_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_chat_member(self, chat_id: int, user_id: int) -> Dict[str, Any]:
        """獲取群組成員信息"""
        try:
            member = await self.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            return {
                "success": True,
                "member": {
                    "user_id": member.user.id,
                    "status": str(member.status),
                    "is_member": str(member.status) in ["member", "administrator", "creator"]
                }
            }
        except TelegramError as e:
            logger.error(f"Failed to get chat member {user_id} in {chat_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def resolve_username(self, username: str) -> Optional[int]:
        """解析用戶名獲取 Telegram ID"""
        try:
            # 移除 @ 符號
            username = username.lstrip("@")
            chat = await self.bot.get_chat(f"@{username}")
            return chat.id
        except TelegramError as e:
            logger.error(f"Failed to resolve username @{username}: {str(e)}")
            return None
    
    async def get_chat_by_link(self, link: str) -> Dict[str, Any]:
        """通過鏈接獲取群組信息"""
        try:
            # 從 t.me/xxx 格式提取用戶名
            if "t.me/" in link:
                username = link.split("t.me/")[-1].split("/")[0].lstrip("@")
                chat = await self.bot.get_chat(f"@{username}")
                return {
                    "success": True,
                    "chat": {
                        "id": chat.id,
                        "title": getattr(chat, "title", None),
                        "type": chat.type,
                        "username": getattr(chat, "username", None),
                    }
                }
            return {
                "success": False,
                "error": "Invalid link format"
            }
        except TelegramError as e:
            logger.error(f"Failed to get chat by link {link}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _save_message_record(
        self,
        message_id: Optional[int],
        chat_id: int,
        chat_type: str,
        message_type: str,
        content: str,
        media_url: Optional[str] = None,
        keyboard: Optional[Dict] = None,
        status: str = "sent",
        from_user_id: Optional[int] = None,
        to_user_id: Optional[int] = None
    ):
        """保存消息記錄到數據庫"""
        try:
            message_record = TelegramMessage(
                message_id=message_id,
                chat_id=chat_id,
                chat_type=chat_type,
                from_user_id=from_user_id,
                to_user_id=to_user_id or (chat_id if chat_id > 0 else None),
                message_type=message_type,
                content=content,
                media_url=media_url,
                keyboard=keyboard,
                status=status,
                sent_at=datetime.utcnow() if status == "sent" else None
            )
            self.db.add(message_record)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to save message record: {str(e)}")
            await self.db.rollback()
    
    async def _update_group_record(self, chat):
        """更新或創建群組記錄"""
        try:
            result = await self.db.execute(
                select(TelegramGroup).where(TelegramGroup.chat_id == chat.id)
            )
            group = result.scalar_one_or_none()
            
            if group:
                # 更新現有記錄
                group.title = getattr(chat, "title", group.title)
                group.type = chat.type
                group.username = getattr(chat, "username", group.username)
                group.description = getattr(chat, "description", group.description)
                group.updated_at = datetime.utcnow()
            else:
                # 創建新記錄
                group = TelegramGroup(
                    chat_id=chat.id,
                    title=getattr(chat, "title", None),
                    type=chat.type,
                    username=getattr(chat, "username", None),
                    description=getattr(chat, "description", None),
                )
                self.db.add(group)
            
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update group record: {str(e)}")
            await self.db.rollback()

