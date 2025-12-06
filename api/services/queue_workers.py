"""
队列工作器 - 处理异步任务
"""
from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from shared.database.connection import get_db_session
from shared.database.models import RedPacket, RedPacketClaim, RedPacketStatus
from sqlalchemy import select
from datetime import datetime
from decimal import Decimal

# Celery任务定义（如果使用Celery）
_celery_app = None

try:
    from celery import Celery
    _celery_app = Celery(
        'ledger_sync',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
    )
except ImportError:
    pass


def sync_ledger_from_redis(
    packet_uuid: str,
    user_id: int,
    claim_id: str,
    amount: float,
    currency: str,
    packet_status: dict
):
    """
    从Redis同步账本到PostgreSQL（同步函数，用于Celery）
    """
    from shared.config.settings import get_settings
    from api.services.ledger_service import LedgerService
    
    settings = get_settings()
    
    # 创建异步引擎
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async def _sync():
        async with async_session() as db:
            try:
                # 查找红包
                result = await db.execute(
                    select(RedPacket).where(RedPacket.uuid == packet_uuid)
                )
                packet = result.scalar_one_or_none()
                
                if not packet:
                    logger.warning(f"⚠️ 红包未找到: {packet_uuid}")
                    return
                
                # 创建领取记录
                claim = RedPacketClaim(
                    red_packet_id=packet.id,
                    user_id=user_id,
                    amount=Decimal(str(amount)),
                    is_bomb=False,
                    penalty_amount=None,
                )
                db.add(claim)
                await db.flush()
                
                # 更新红包状态
                packet.claimed_amount += Decimal(str(amount))
                packet.claimed_count = packet_status.get('claimed_count', 0)
                if packet_status.get('status') == 'COMPLETED':
                    packet.status = RedPacketStatus.COMPLETED
                    packet.completed_at = datetime.utcnow()
                
                # 使用LedgerService更新余额
                await LedgerService.create_entry(
                    db=db,
                    user_id=user_id,
                    amount=Decimal(str(amount)),
                    currency=currency.upper(),
                    entry_type='CLAIM_PACKET',
                    related_type='red_packet',
                    related_id=packet.id,
                    description=f"領取紅包: {amount} {currency}",
                    created_by='user'
                )
                
                await db.commit()
                logger.info(f"✅ 账本同步成功: packet={packet_uuid}, user={user_id}, amount={amount}")
                
            except Exception as e:
                logger.error(f"❌ 账本同步失败: {e}")
                await db.rollback()
                raise
    
    # 运行异步函数
    import asyncio
    asyncio.run(_sync())


# Celery任务（如果使用Celery）
if _celery_app:
    @_celery_app.task(name='sync_ledger')
    def sync_ledger_task(**kwargs):
        """Celery任务：同步账本"""
        sync_ledger_from_redis(**kwargs)
        return {"status": "success"}


# BullMQ Worker（如果使用BullMQ）
async def create_bullmq_worker():
    """创建BullMQ Worker"""
    try:
        from bullmq import Worker
        
        async def process_job(job):
            """处理任务"""
            data = job.data
            sync_ledger_from_redis(
                packet_uuid=data['packet_uuid'],
                user_id=data['user_id'],
                claim_id=data['claim_id'],
                amount=data['amount'],
                currency=data['currency'],
                packet_status=data['packet_status']
            )
            return {"status": "success"}
        
        worker = Worker(
            'ledger-sync',
            process_job,
            connection={
                'host': 'localhost',
                'port': 6379
            }
        )
        
        logger.info("✅ BullMQ Worker已启动")
        return worker
    except Exception as e:
        logger.warning(f"⚠️ BullMQ Worker创建失败: {e}")
        return None

