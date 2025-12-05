"""
WebSocket 實時推送服務

功能：
- 用戶連接管理
- 餘額變動推送
- 紅包通知推送
- 系統消息推送
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.connection import get_db_session
from shared.database.models import User
from api.utils.telegram_auth import verify_telegram_init_data

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ 連接管理器 ============

class ConnectionManager:
    """WebSocket 連接管理器"""
    
    def __init__(self):
        # user_id -> set of websocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # websocket -> user_id
        self.connection_users: Dict[WebSocket, int] = {}
        # 心跳檢測間隔（秒）
        self.heartbeat_interval = 30
        
    async def connect(self, websocket: WebSocket, user_id: int):
        """建立連接"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.connection_users[websocket] = user_id
        
        logger.info(f"[WebSocket] User {user_id} connected. Total connections: {len(self.connection_users)}")
        
        # 發送連接成功消息
        await self.send_personal_message({
            "type": "connected",
            "data": {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }, websocket)
        
    def disconnect(self, websocket: WebSocket):
        """斷開連接"""
        user_id = self.connection_users.get(websocket)
        if user_id:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            del self.connection_users[websocket]
            logger.info(f"[WebSocket] User {user_id} disconnected. Total connections: {len(self.connection_users)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """發送個人消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"[WebSocket] Send error: {e}")
            
    async def send_to_user(self, user_id: int, message: dict):
        """向特定用戶發送消息"""
        if user_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"[WebSocket] Send to user {user_id} error: {e}")
                    disconnected.append(websocket)
            
            # 清理斷開的連接
            for ws in disconnected:
                self.disconnect(ws)
                
    async def broadcast(self, message: dict, exclude_user: int = None):
        """廣播消息給所有用戶"""
        disconnected = []
        for websocket, user_id in list(self.connection_users.items()):
            if exclude_user and user_id == exclude_user:
                continue
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"[WebSocket] Broadcast error: {e}")
                disconnected.append(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)
            
    def get_online_users(self) -> Set[int]:
        """獲取在線用戶列表"""
        return set(self.active_connections.keys())
    
    def is_user_online(self, user_id: int) -> bool:
        """檢查用戶是否在線"""
        return user_id in self.active_connections
    
    def get_connection_count(self) -> int:
        """獲取總連接數"""
        return len(self.connection_users)


# 全局連接管理器實例
manager = ConnectionManager()


# ============ WebSocket 端點 ============

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    initData: str = Query(None, description="Telegram init data"),
):
    """
    WebSocket 連接端點
    
    連接時需要提供 Telegram initData 進行身份驗證
    """
    user_id = None
    
    try:
        # 驗證身份
        if initData:
            user_data = verify_telegram_init_data(initData)
            if user_data:
                user_id = user_data.get("id")
        
        if not user_id:
            # 開發環境允許無認證連接
            import os
            if os.getenv("DEBUG", "false").lower() == "true":
                user_id = 0  # 測試用戶
                logger.warning("[WebSocket] Debug mode: allowing unauthenticated connection")
            else:
                await websocket.close(code=4001, reason="Unauthorized")
                return
        
        # 建立連接
        await manager.connect(websocket, user_id)
        
        # 保持連接並處理消息
        while True:
            try:
                # 等待客戶端消息
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=60  # 60秒超時
                )
                
                # 處理不同類型的消息
                msg_type = data.get("type")
                
                if msg_type == "ping":
                    # 心跳響應
                    await manager.send_personal_message({
                        "type": "pong",
                        "data": {"timestamp": datetime.utcnow().isoformat()}
                    }, websocket)
                    
                elif msg_type == "subscribe":
                    # 訂閱特定頻道（預留）
                    channel = data.get("channel")
                    logger.info(f"[WebSocket] User {user_id} subscribed to {channel}")
                    
                else:
                    logger.debug(f"[WebSocket] Unknown message type: {msg_type}")
                    
            except asyncio.TimeoutError:
                # 發送心跳檢測
                try:
                    await manager.send_personal_message({
                        "type": "ping",
                        "data": {}
                    }, websocket)
                except:
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"[WebSocket] User {user_id} disconnected normally")
    except Exception as e:
        logger.error(f"[WebSocket] Error: {e}")
    finally:
        manager.disconnect(websocket)


# ============ 推送工具函數 ============

async def push_balance_update(user_id: int, balance_data: dict):
    """
    推送餘額更新
    
    Args:
        user_id: 用戶 ID
        balance_data: 餘額數據 {usdt, ton, stars, points}
    """
    await manager.send_to_user(user_id, {
        "type": "balance_update",
        "data": {
            **balance_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    })
    logger.info(f"[WebSocket] Pushed balance update to user {user_id}")


async def push_packet_claimed(user_id: int, packet_data: dict):
    """
    推送紅包領取通知
    
    Args:
        user_id: 用戶 ID
        packet_data: 紅包數據
    """
    await manager.send_to_user(user_id, {
        "type": "packet_claimed",
        "data": {
            **packet_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    })


async def push_packet_created(packet_data: dict, exclude_sender: int = None):
    """
    廣播新紅包創建
    
    Args:
        packet_data: 紅包數據
        exclude_sender: 排除發送者
    """
    await manager.broadcast({
        "type": "packet_created",
        "data": {
            **packet_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    }, exclude_user=exclude_sender)


async def push_notification(user_id: int, title: str, message: str, notification_type: str = "info"):
    """
    推送通知消息
    
    Args:
        user_id: 用戶 ID
        title: 通知標題
        message: 通知內容
        notification_type: 類型 (info, success, warning, error)
    """
    await manager.send_to_user(user_id, {
        "type": "notification",
        "data": {
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    })


async def push_transaction_status(user_id: int, transaction_data: dict):
    """
    推送交易狀態更新
    
    Args:
        user_id: 用戶 ID
        transaction_data: 交易數據
    """
    await manager.send_to_user(user_id, {
        "type": "transaction_update",
        "data": {
            **transaction_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    })


# ============ 狀態查詢端點 ============

@router.get("/ws/status")
async def get_websocket_status():
    """獲取 WebSocket 服務狀態"""
    return {
        "status": "ok",
        "online_users": len(manager.get_online_users()),
        "total_connections": manager.get_connection_count(),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ws/online")
async def get_online_users():
    """獲取在線用戶列表（管理員用）"""
    return {
        "online_users": list(manager.get_online_users()),
        "count": len(manager.get_online_users())
    }
