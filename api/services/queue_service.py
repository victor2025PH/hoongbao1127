"""
异步队列服务 - 使用BullMQ或Celery
用于Redis抢红包结果的异步同步到PostgreSQL
"""
from typing import Optional, Dict, Any
from loguru import logger
import json
from datetime import datetime

# 尝试导入BullMQ
_bullmq_available = False
try:
    from bullmq import Queue, Worker
    _bullmq_available = True
except ImportError:
    logger.warning("⚠️ bullmq未安装，将使用内存队列（仅用于开发）")

# 尝试导入Celery
_celery_available = False
try:
    from celery import Celery
    _celery_available = True
except ImportError:
    logger.warning("⚠️ celery未安装，将使用内存队列（仅用于开发）")


class QueueService:
    """异步队列服务"""
    
    def __init__(self):
        self.queue_type = None
        self.queue = None
        self.worker = None
        
        # 优先使用BullMQ（更现代，基于Redis）
        if _bullmq_available:
            try:
                from bullmq import Queue, Worker
                self.queue = Queue('ledger-sync', connection={
                    'host': 'localhost',
                    'port': 6379
                })
                self.queue_type = 'bullmq'
                logger.info("✅ 使用BullMQ队列服务")
            except Exception as e:
                logger.warning(f"⚠️ BullMQ初始化失败: {e}，将使用内存队列")
        
        # 如果BullMQ不可用，尝试Celery
        elif _celery_available:
            try:
                self.celery_app = Celery(
                    'ledger_sync',
                    broker='redis://localhost:6379/0',
                    backend='redis://localhost:6379/0'
                )
                self.queue_type = 'celery'
                logger.info("✅ 使用Celery队列服务")
            except Exception as e:
                logger.warning(f"⚠️ Celery初始化失败: {e}，将使用内存队列")
        
        # 如果都不可用，使用内存队列（仅用于开发）
        if not self.queue_type:
            self.queue_type = 'memory'
            self.memory_queue = []
            logger.warning("⚠️ 使用内存队列（仅用于开发，数据不会持久化）")
    
    async def enqueue_ledger_sync(
        self,
        packet_uuid: str,
        user_id: int,
        claim_id: str,
        amount: float,
        currency: str,
        packet_status: Dict[str, Any]
    ) -> bool:
        """
        将账本同步任务加入队列
        
        Args:
            packet_uuid: 红包UUID
            user_id: 用户ID
            claim_id: 领取记录ID
            amount: 领取金额
            currency: 币种
            packet_status: 红包状态
        
        Returns:
            是否成功
        """
        job_data = {
            'packet_uuid': packet_uuid,
            'user_id': user_id,
            'claim_id': claim_id,
            'amount': amount,
            'currency': currency,
            'packet_status': packet_status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            if self.queue_type == 'bullmq':
                await self.queue.add('sync-ledger', job_data)
                logger.info(f"✅ 账本同步任务已加入BullMQ队列: {packet_uuid}")
                return True
            elif self.queue_type == 'celery':
                from api.services.queue_workers import sync_ledger_task
                sync_ledger_task.delay(**job_data)
                logger.info(f"✅ 账本同步任务已加入Celery队列: {packet_uuid}")
                return True
            else:
                # 内存队列（仅用于开发）
                self.memory_queue.append(job_data)
                logger.warning(f"⚠️ 账本同步任务已加入内存队列: {packet_uuid}（数据不会持久化）")
                return True
        except Exception as e:
            logger.error(f"❌ 加入队列失败: {e}")
            return False


# 单例实例
_queue_service = None

def get_queue_service() -> QueueService:
    """获取队列服务实例（单例）"""
    global _queue_service
    if _queue_service is None:
        _queue_service = QueueService()
    return _queue_service

