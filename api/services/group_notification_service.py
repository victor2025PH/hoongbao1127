"""
群組通知服務
發送紅包相關通知到 Telegram 群組
"""
import httpx
from decimal import Decimal
from typing import Optional, List
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.database.models import RedPacket, RedPacketClaim, User
from shared.config.settings import get_settings

settings = get_settings()


class GroupNotificationService:
    """群組通知服務"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.bot_token = settings.BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def _send_message(
        self, 
        chat_id: int, 
        text: str, 
        parse_mode: str = "Markdown",
        reply_markup: Optional[dict] = None
    ) -> bool:
        """發送消息到 Telegram"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup
                
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Message sent to chat {chat_id}")
                    return True
                else:
                    logger.error(f"Failed to send message: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending message to {chat_id}: {e}")
            return False
    
    async def notify_packet_created(
        self,
        packet: RedPacket,
        sender: User
    ) -> bool:
        """
        紅包創建通知
        
        Args:
            packet: 紅包對象
            sender: 發送者
        """
        if not packet.chat_id:
            return False
        
        type_text = "🎲 手氣紅包" if packet.packet_type.value == "random" else "💣 炸彈紅包"
        
        text = f"""🧧 *{packet.message or '恭喜發財'}*

{type_text}
💰 總金額：{float(packet.total_amount):.2f} {packet.currency.value.upper()}
👥 數量：{packet.total_count} 份
👤 發送者：{sender.first_name or sender.username or f'用戶{sender.tg_id}'}

🎁 點擊下方按鈕搶紅包！"""

        miniapp_url = getattr(settings, 'MINIAPP_URL', 'https://mini.usdt2026.cc')
        
        reply_markup = {
            "inline_keyboard": [[
                {
                    "text": "🧧 搶紅包",
                    "url": f"{miniapp_url}/claim/{packet.uuid}"
                }
            ]]
        }
        
        return await self._send_message(packet.chat_id, text, reply_markup=reply_markup)
    
    async def notify_packet_completed(self, packet_id: int) -> bool:
        """
        紅包領完通知 - 發送結果到群組
        
        Args:
            packet_id: 紅包數據庫 ID
        """
        # 獲取紅包
        result = await self.db.execute(select(RedPacket).where(RedPacket.id == packet_id))
        packet = result.scalar_one_or_none()
        
        if not packet or not packet.chat_id:
            return False
        
        # 獲取發送者
        sender_result = await self.db.execute(select(User).where(User.id == packet.sender_id))
        sender = sender_result.scalar_one_or_none()
        
        # 獲取所有領取記錄
        claims_result = await self.db.execute(
            select(RedPacketClaim)
            .where(RedPacketClaim.red_packet_id == packet.id)
            .order_by(RedPacketClaim.claimed_at)
        )
        claims = claims_result.scalars().all()
        
        if not claims:
            return False
        
        # 構建領取列表
        claim_list = []
        luckiest = None
        biggest_bomb = None
        
        for claim in claims:
            user_result = await self.db.execute(select(User).where(User.id == claim.user_id))
            user = user_result.scalar_one_or_none()
            user_name = user.first_name or user.username or f"用戶{user.tg_id}" if user else "未知用戶"
            
            amount_str = f"{float(claim.amount):.4f}"
            
            if claim.is_bomb:
                claim_list.append(f"💣 {user_name}: {amount_str} (雷！賠 {float(claim.penalty_amount or 0):.2f})")
                if biggest_bomb is None or (claim.penalty_amount or 0) > (biggest_bomb.get('penalty', 0)):
                    biggest_bomb = {
                        "name": user_name,
                        "amount": float(claim.amount),
                        "penalty": float(claim.penalty_amount or 0)
                    }
            else:
                if claim.is_luckiest:
                    claim_list.append(f"🏆 {user_name}: {amount_str} 👑手氣最佳")
                    luckiest = {"name": user_name, "amount": float(claim.amount)}
                else:
                    claim_list.append(f"🧧 {user_name}: {amount_str}")
        
        # 構建通知消息
        sender_name = sender.first_name or sender.username or f"用戶{sender.tg_id}" if sender else "未知"
        type_text = "🎲 手氣紅包" if packet.packet_type.value == "random" else "💣 炸彈紅包"
        
        text = f"""🎊 *紅包已被搶完！*

{type_text} - 來自 *{sender_name}*
💰 總金額：{float(packet.total_amount):.2f} {packet.currency.value.upper()}

📋 *領取詳情：*
"""
        
        # 只顯示前 10 個
        for i, line in enumerate(claim_list[:10]):
            text += f"{line}\n"
        
        if len(claim_list) > 10:
            text += f"... 共 {len(claim_list)} 人領取\n"
        
        # 添加特殊結果
        if luckiest:
            text += f"\n👑 *手氣最佳*：{luckiest['name']} ({luckiest['amount']:.4f})"
        
        if biggest_bomb and packet.bomb_number is not None:
            text += f"\n💥 *最大雷公*：{biggest_bomb['name']} (賠付 {biggest_bomb['penalty']:.2f})"
        
        return await self._send_message(packet.chat_id, text)
    
    async def notify_packet_expired(self, packet_id: int) -> bool:
        """
        紅包過期通知
        
        Args:
            packet_id: 紅包數據庫 ID
        """
        result = await self.db.execute(select(RedPacket).where(RedPacket.id == packet_id))
        packet = result.scalar_one_or_none()
        
        if not packet or not packet.chat_id:
            return False
        
        unclaimed_amount = packet.total_amount - packet.claimed_amount
        unclaimed_count = packet.total_count - packet.claimed_count
        
        if unclaimed_count <= 0:
            return False
        
        text = f"""⏰ *紅包已過期*

💰 未領取金額：{float(unclaimed_amount):.2f} {packet.currency.value.upper()}
📦 剩餘份數：{unclaimed_count} 份

未領取的金額已退還給發送者。"""
        
        return await self._send_message(packet.chat_id, text)


async def notify_packet_result(db: AsyncSession, packet_id: int):
    """
    便捷函數：通知紅包結果
    
    在紅包領完後調用此函數發送群組通知
    """
    service = GroupNotificationService(db)
    await service.notify_packet_completed(packet_id)
