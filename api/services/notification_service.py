"""
統一通知服務

整合 WebSocket、Telegram Bot、站內消息等多種通知渠道
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.database.models import User, Message

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """通知類型"""
    BALANCE_UPDATE = "balance_update"
    PACKET_RECEIVED = "packet_received"
    PACKET_CLAIMED = "packet_claimed"
    PACKET_EXPIRED = "packet_expired"
    DEPOSIT_SUCCESS = "deposit_success"
    WITHDRAW_APPROVED = "withdraw_approved"
    WITHDRAW_REJECTED = "withdraw_rejected"
    INVITE_REWARD = "invite_reward"
    CHECKIN_REWARD = "checkin_reward"
    SYSTEM = "system"


class NotificationService:
    """通知服務"""
    
    @staticmethod
    async def notify_balance_change(
        db: AsyncSession,
        user_id: int,
        currency: str,
        amount: Decimal,
        reason: str,
        new_balance: Decimal
    ):
        """
        通知餘額變動
        
        同時發送：
        1. WebSocket 實時推送
        2. 站內消息記錄
        """
        try:
            # 1. WebSocket 推送
            from api.routers.websocket import push_balance_update
            await push_balance_update(user_id, {
                "currency": currency,
                "change": float(amount),
                "reason": reason,
                "new_balance": float(new_balance)
            })
        except Exception as e:
            logger.error(f"[Notification] WebSocket push failed: {e}")
        
        # 2. 記錄站內消息
        try:
            sign = "+" if amount > 0 else ""
            message = Message(
                user_id=user_id,
                type="balance",
                title=f"餘額變動：{sign}{amount} {currency}",
                content=f"原因：{reason}\n當前餘額：{new_balance} {currency}",
                is_read=False
            )
            db.add(message)
            await db.commit()
        except Exception as e:
            logger.error(f"[Notification] Save message failed: {e}")
    
    @staticmethod
    async def notify_packet_claimed(
        db: AsyncSession,
        claimer_id: int,
        sender_id: int,
        amount: Decimal,
        currency: str,
        packet_id: str,
        is_bomb: bool = False,
        is_lucky: bool = False
    ):
        """
        通知紅包領取
        
        同時通知領取者和發送者
        """
        try:
            from api.routers.websocket import push_packet_claimed, push_notification
            
            # 通知領取者
            if is_bomb:
                title = "💣 踩到炸彈！"
                message = f"您踩到了炸彈紅包，賠付 {amount} {currency}"
            elif is_lucky:
                title = "🎉 運氣王！"
                message = f"恭喜！您獲得了最大紅包 {amount} {currency}"
            else:
                title = "🧧 紅包到賬"
                message = f"您領取了 {amount} {currency}"
            
            await push_notification(claimer_id, title, message, "success" if not is_bomb else "warning")
            
            # 通知發送者
            await push_packet_claimed(sender_id, {
                "packet_id": packet_id,
                "claimer_id": claimer_id,
                "amount": float(amount),
                "currency": currency
            })
            
        except Exception as e:
            logger.error(f"[Notification] Packet claimed notification failed: {e}")
    
    @staticmethod
    async def notify_packet_completed(
        db: AsyncSession,
        sender_id: int,
        packet_id: str,
        total_amount: Decimal,
        claim_count: int,
        currency: str
    ):
        """通知紅包已被領完"""
        try:
            from api.routers.websocket import push_notification
            
            await push_notification(
                sender_id,
                "🧧 紅包已領完",
                f"您的紅包已被全部領取！共 {claim_count} 人領取，總額 {total_amount} {currency}",
                "info"
            )
        except Exception as e:
            logger.error(f"[Notification] Packet completed notification failed: {e}")
    
    @staticmethod
    async def notify_deposit_success(
        db: AsyncSession,
        user_id: int,
        amount: Decimal,
        currency: str,
        tx_hash: Optional[str] = None
    ):
        """通知充值成功"""
        try:
            from api.routers.websocket import push_notification, push_balance_update
            
            await push_notification(
                user_id,
                "💰 充值成功",
                f"您已成功充值 {amount} {currency}",
                "success"
            )
            
            # 獲取最新餘額並推送
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                await push_balance_update(user_id, {
                    "usdt": float(user.balance_usdt),
                    "ton": float(user.balance_ton),
                    "stars": float(user.balance_stars)
                })
                
        except Exception as e:
            logger.error(f"[Notification] Deposit notification failed: {e}")
    
    @staticmethod
    async def notify_withdraw_result(
        db: AsyncSession,
        user_id: int,
        amount: Decimal,
        currency: str,
        approved: bool,
        reason: Optional[str] = None
    ):
        """通知提現結果"""
        try:
            from api.routers.websocket import push_notification
            
            if approved:
                await push_notification(
                    user_id,
                    "✅ 提現成功",
                    f"您的 {amount} {currency} 提現請求已審核通過",
                    "success"
                )
            else:
                message = f"您的 {amount} {currency} 提現請求被拒絕"
                if reason:
                    message += f"\n原因：{reason}"
                await push_notification(
                    user_id,
                    "❌ 提現被拒",
                    message,
                    "error"
                )
                
        except Exception as e:
            logger.error(f"[Notification] Withdraw notification failed: {e}")
    
    @staticmethod
    async def notify_invite_reward(
        db: AsyncSession,
        user_id: int,
        invitee_name: str,
        reward_amount: Decimal,
        reward_type: str = "direct"  # direct, commission, milestone
    ):
        """通知邀請獎勵"""
        try:
            from api.routers.websocket import push_notification
            
            if reward_type == "direct":
                title = "👥 邀請獎勵"
                message = f"感謝邀請 {invitee_name}！您獲得 {reward_amount} USDT 獎勵"
            elif reward_type == "commission":
                title = "💎 返佣到賬"
                message = f"{invitee_name} 充值，您獲得 {reward_amount} USDT 返佣"
            else:
                title = "🏆 里程碑獎勵"
                message = f"恭喜達成邀請里程碑！獲得 {reward_amount} USDT 獎勵"
            
            await push_notification(user_id, title, message, "success")
            
        except Exception as e:
            logger.error(f"[Notification] Invite reward notification failed: {e}")
    
    @staticmethod
    async def broadcast_system_message(
        title: str,
        content: str,
        user_ids: Optional[List[int]] = None
    ):
        """廣播系統消息"""
        try:
            from api.routers.websocket import manager
            
            message = {
                "type": "system",
                "data": {
                    "title": title,
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            if user_ids:
                for user_id in user_ids:
                    await manager.send_to_user(user_id, message)
            else:
                await manager.broadcast(message)
                
        except Exception as e:
            logger.error(f"[Notification] System broadcast failed: {e}")


# 單例實例
notification_service = NotificationService()
