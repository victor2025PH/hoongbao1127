"""
Redis高并发抢红包服务
使用Redis + Lua脚本处理10k+并发请求，防止超卖
"""
import json
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple
from loguru import logger
import uuid as uuid_lib
from datetime import datetime

# Redis连接（单例模式，可选）
_redis_client = None
_redis_available = False

try:
    import redis
    _redis_available = True
except ImportError:
    logger.warning("⚠️ redis模块未安装，Redis抢红包功能将不可用（将使用数据库模式）")

def get_redis_client():
    """获取Redis客户端（单例，可选）"""
    global _redis_client
    if not _redis_available:
        return None
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            # 测试连接
            _redis_client.ping()
            logger.info("✅ Redis连接成功")
        except Exception as e:
            logger.warning(f"⚠️ Redis连接失败: {e}，将使用数据库模式")
            _redis_client = None
    return _redis_client


# Lua脚本：原子性抢红包
CLAIM_RED_PACKET_SCRIPT = """
local packet_key = KEYS[1]
local user_claim_key = KEYS[2]
local user_id = ARGV[1]
local claim_id = ARGV[2]

-- 检查红包是否存在
local packet_data = redis.call('HGETALL', packet_key)
if #packet_data == 0 then
    return {0, 'RED_PACKET_NOT_FOUND'}
end

-- 解析红包数据
local packet = {}
for i = 1, #packet_data, 2 do
    packet[packet_data[i]] = packet_data[i + 1]
end

-- 检查是否已领取
if redis.call('EXISTS', user_claim_key) == 1 then
    return {0, 'ALREADY_CLAIMED'}
end

-- 检查红包是否已领完
local claimed_count = tonumber(packet['claimed_count']) or 0
local total_count = tonumber(packet['total_count']) or 0
if claimed_count >= total_count then
    return {0, 'RED_PACKET_EMPTY'}
end

-- 检查红包是否过期
local expires_at = tonumber(packet['expires_at'])
if expires_at and expires_at < tonumber(ARGV[3]) then
    return {0, 'RED_PACKET_EXPIRED'}
end

-- 计算领取金额
local remaining_amount = tonumber(packet['remaining_amount'])
local remaining_count = total_count - claimed_count
local amount = 0

if packet['packet_type'] == 'EQUAL' then
    -- 固定金额红包
    amount = remaining_amount / remaining_count
else
    -- 随机金额红包
    if remaining_count == 1 then
        amount = remaining_amount
    else
        -- 随机算法：0.01 到 (剩余金额 * 0.9 / 剩余数量 * 2)
        local max_amount = remaining_amount * 0.9 / remaining_count * 2
        amount = math.random(1, math.floor(max_amount * 100)) / 100
        amount = math.min(amount, remaining_amount - 0.01 * (remaining_count - 1))
    end
end

-- 四舍五入到8位小数
amount = math.floor(amount * 100000000 + 0.5) / 100000000

-- 更新红包状态
local new_claimed_count = claimed_count + 1
local new_claimed_amount = tonumber(packet['claimed_amount']) + amount
local new_remaining_amount = remaining_amount - amount

redis.call('HINCRBY', packet_key, 'claimed_count', 1)
redis.call('HSET', packet_key, 'claimed_amount', new_claimed_amount)
redis.call('HSET', packet_key, 'remaining_amount', new_remaining_amount)

if new_claimed_count >= total_count then
    redis.call('HSET', packet_key, 'status', 'COMPLETED')
end

-- 记录用户领取
redis.call('HSET', user_claim_key, 'user_id', user_id)
redis.call('HSET', user_claim_key, 'amount', amount)
redis.call('HSET', user_claim_key, 'claim_id', claim_id)
redis.call('HSET', user_claim_key, 'claimed_at', ARGV[3])
redis.call('EXPIRE', user_claim_key, 86400)  -- 24小时过期

return {1, tostring(amount), tostring(new_remaining_amount), tostring(new_claimed_count)}
"""


class RedisClaimService:
    """Redis高并发抢红包服务"""
    
    @staticmethod
    def _get_packet_key(packet_uuid: str) -> str:
        """获取红包Redis键"""
        return f"redpacket:{packet_uuid}"
    
    @staticmethod
    def _get_user_claim_key(packet_uuid: str, user_id: int) -> str:
        """获取用户领取记录Redis键"""
        return f"redpacket:claim:{packet_uuid}:{user_id}"
    
    @staticmethod
    async def init_packet(
        packet_uuid: str,
        packet_data: Dict[str, Any]
    ) -> bool:
        """
        初始化红包到Redis
        
        Args:
            packet_uuid: 红包UUID
            packet_data: 红包数据
        
        Returns:
            是否成功
        """
        r = get_redis_client()
        if not r:
            return False
        
        try:
            packet_key = RedisClaimService._get_packet_key(packet_uuid)
            
            # 计算剩余金额
            total_amount = float(packet_data['total_amount'])
            claimed_amount = float(packet_data.get('claimed_amount', 0))
            remaining_amount = total_amount - claimed_amount
            
            # 存储红包数据
            r.hset(packet_key, mapping={
                'uuid': packet_uuid,
                'sender_id': str(packet_data['sender_id']),
                'currency': packet_data['currency'],
                'packet_type': packet_data['packet_type'],
                'total_amount': str(total_amount),
                'total_count': str(packet_data['total_count']),
                'claimed_amount': str(claimed_amount),
                'claimed_count': str(packet_data.get('claimed_count', 0)),
                'remaining_amount': str(remaining_amount),
                'status': packet_data.get('status', 'ACTIVE'),
                'expires_at': str(int(packet_data.get('expires_at', 0))),
                'bomb_number': str(packet_data.get('bomb_number', '')),
            })
            
            # 设置过期时间（24小时）
            r.expire(packet_key, 86400)
            
            logger.info(f"✅ 初始化红包到Redis: {packet_uuid}")
            return True
        except Exception as e:
            logger.error(f"❌ 初始化红包到Redis失败: {e}")
            return False
    
    @staticmethod
    async def claim_packet(
        packet_uuid: str,
        user_id: int,
        claim_id: str
    ) -> Tuple[bool, Optional[str], Optional[Decimal], Optional[Dict[str, Any]]]:
        """
        抢红包（原子操作）
        
        Args:
            packet_uuid: 红包UUID
            user_id: 用户ID
            claim_id: 领取记录ID
        
        Returns:
            (是否成功, 错误信息, 领取金额, 红包状态)
        """
        r = get_redis_client()
        if not r:
            return False, "REDIS_NOT_AVAILABLE", None, None
        
        try:
            packet_key = RedisClaimService._get_packet_key(packet_uuid)
            user_claim_key = RedisClaimService._get_user_claim_key(packet_uuid, user_id)
            current_timestamp = int(datetime.utcnow().timestamp())
            
            # 执行Lua脚本
            result = r.eval(
                CLAIM_RED_PACKET_SCRIPT,
                2,  # KEYS数量
                packet_key,
                user_claim_key,
                str(user_id),
                claim_id,
                str(current_timestamp)
            )
            
            if result[0] == 0:
                # 失败
                error_code = result[1]
                return False, error_code, None, None
            
            # 成功
            amount = Decimal(str(result[1]))
            remaining_amount = Decimal(str(result[2]))
            claimed_count = int(result[3])
            
            # 获取红包状态
            packet_data = r.hgetall(packet_key)
            
            return True, None, amount, {
                'remaining_amount': float(remaining_amount),
                'claimed_count': claimed_count,
                'status': packet_data.get('status', 'ACTIVE')
            }
            
        except Exception as e:
            logger.error(f"❌ Redis抢红包失败: {e}")
            return False, "REDIS_ERROR", None, None
    
    @staticmethod
    async def get_packet_status(packet_uuid: str) -> Optional[Dict[str, Any]]:
        """获取红包状态"""
        r = get_redis_client()
        if not r:
            return None
        
        try:
            packet_key = RedisClaimService._get_packet_key(packet_uuid)
            packet_data = r.hgetall(packet_key)
            
            if not packet_data:
                return None
            
            return {
                'uuid': packet_data.get('uuid'),
                'claimed_count': int(packet_data.get('claimed_count', 0)),
                'total_count': int(packet_data.get('total_count', 0)),
                'claimed_amount': float(packet_data.get('claimed_amount', 0)),
                'remaining_amount': float(packet_data.get('remaining_amount', 0)),
                'status': packet_data.get('status', 'ACTIVE'),
            }
        except Exception as e:
            logger.error(f"❌ 获取红包状态失败: {e}")
            return None
    
    @staticmethod
    async def check_user_claimed(packet_uuid: str, user_id: int) -> bool:
        """检查用户是否已领取"""
        r = get_redis_client()
        if not r:
            return False
        
        try:
            user_claim_key = RedisClaimService._get_user_claim_key(packet_uuid, user_id)
            return r.exists(user_claim_key) == 1
        except Exception as e:
            logger.error(f"❌ 检查用户领取状态失败: {e}")
            return False

