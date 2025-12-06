"""
Redis 缓存服务
提供统一的缓存接口，支持自动回退到内存缓存
"""
import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
import redis
from loguru import logger

from shared.config.settings import get_settings

settings = get_settings()


class CacheService:
    """缓存服务 - 支持 Redis 和内存缓存"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: dict = {}
        self.use_redis = False
        
        # 尝试连接 Redis
        if settings.REDIS_URL:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # 测试连接
                self.redis_client.ping()
                self.use_redis = True
                logger.info("✅ Redis 缓存已启用")
            except Exception as e:
                logger.warning(f"Redis 连接失败，使用内存缓存: {e}")
                self.use_redis = False
        else:
            logger.info("Redis 未配置，使用内存缓存")
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [prefix]
        if args:
            key_parts.extend(str(arg) for arg in args)
        if kwargs:
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        key_str = ":".join(key_parts)
        # 如果键太长，使用哈希
        if len(key_str) > 200:
            key_str = f"{prefix}:{hashlib.md5(key_str.encode()).hexdigest()}"
        return key_str
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if self.use_redis and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get 失败: {e}")
        
        # 回退到内存缓存
        return self.memory_cache.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        try:
            value_str = json.dumps(value, default=str)
            
            if self.use_redis and self.redis_client:
                try:
                    if expire:
                        self.redis_client.setex(key, expire, value_str)
                    else:
                        self.redis_client.set(key, value_str)
                    return True
                except Exception as e:
                    logger.warning(f"Redis set 失败: {e}")
            
            # 回退到内存缓存
            self.memory_cache[key] = value
            # 简单的内存缓存清理（保留最近 1000 个键）
            if len(self.memory_cache) > 1000:
                # 删除最旧的 100 个键
                keys_to_delete = list(self.memory_cache.keys())[:100]
                for k in keys_to_delete:
                    del self.memory_cache[k]
            return True
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete 失败: {e}")
        
        if key in self.memory_cache:
            del self.memory_cache[key]
        return True
    
    async def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有键"""
        count = 0
        if self.use_redis and self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    count = self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis delete_pattern 失败: {e}")
        
        # 内存缓存也删除匹配的键
        keys_to_delete = [k for k in self.memory_cache.keys() if pattern.replace('*', '') in k]
        for k in keys_to_delete:
            del self.memory_cache[k]
            count += 1
        
        return count
    
    async def clear(self) -> bool:
        """清空所有缓存"""
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                logger.warning(f"Redis clear 失败: {e}")
        
        self.memory_cache.clear()
        return True


# 全局缓存服务实例
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """获取缓存服务实例"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def cached(
    prefix: str,
    expire: Optional[int] = 300,
    key_func: Optional[Callable] = None
):
    """
    缓存装饰器
    
    Args:
        prefix: 缓存键前缀
        expire: 过期时间（秒），None 表示不过期
        key_func: 自定义键生成函数
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache._make_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_value
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, expire)
            logger.debug(f"缓存设置: {cache_key}")
            
            return result
        return wrapper
    return decorator

