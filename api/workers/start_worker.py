"""
启动队列Worker
用于处理异步任务（账本同步等）
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
from api.services.queue_workers import create_bullmq_worker


async def start_bullmq_worker():
    """启动BullMQ Worker"""
    worker = await create_bullmq_worker()
    if worker:
        logger.info("✅ BullMQ Worker运行中...")
        # Worker会持续运行
        await asyncio.sleep(float('inf'))
    else:
        logger.warning("⚠️ BullMQ Worker未启动，请检查Redis连接")


async def start_celery_worker():
    """启动Celery Worker（需要在命令行运行）"""
    logger.info("ℹ️ Celery Worker需要在命令行运行:")
    logger.info("   celery -A api.services.queue_workers worker --loglevel=info")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='启动队列Worker')
    parser.add_argument('--type', choices=['bullmq', 'celery'], default='bullmq',
                        help='队列类型')
    
    args = parser.parse_args()
    
    if args.type == 'bullmq':
        asyncio.run(start_bullmq_worker())
    elif args.type == 'celery':
        asyncio.run(start_celery_worker())

