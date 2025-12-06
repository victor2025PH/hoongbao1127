"""
API 速率限制中间件
防止 API 滥用和 DDoS 攻击
"""
import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from loguru import logger

from api.services.cache_service import get_cache_service


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        # 默认限制：每分钟 60 次请求
        self.default_limit = kwargs.get('default_limit', 60)
        self.default_window = kwargs.get('default_window', 60)  # 秒
        
        # 不同端点的限制配置
        self.endpoint_limits: Dict[str, Tuple[int, int]] = {
            # 端点路径: (限制次数, 时间窗口秒)
            '/api/v1/redpackets/claim': (10, 60),  # 抢红包：每分钟 10 次
            '/api/v1/redpackets/create': (20, 60),  # 发红包：每分钟 20 次
            '/api/v1/auth/telegram': (5, 60),  # 登录：每分钟 5 次
            '/api/v1/checkin': (1, 86400),  # 签到：每天 1 次
            '/api/v1/wallet/deposit': (10, 300),  # 充值：每 5 分钟 10 次
            '/api/v1/wallet/withdraw': (5, 300),  # 提现：每 5 分钟 5 次
        }
    
    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用用户 ID（如果已认证）
        tg_id = request.headers.get('X-Telegram-Init-Data')
        if tg_id:
            # 从 Telegram 数据中提取用户 ID（简化版）
            try:
                # 实际应该解析 Telegram Init Data
                # 这里使用 IP 作为后备
                pass
            except:
                pass
        
        # 使用 IP 地址作为标识
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        
        return f"rate_limit:{client_ip}"
    
    def _get_limit(self, path: str) -> Tuple[int, int]:
        """获取端点的限制配置"""
        # 检查精确匹配
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # 检查前缀匹配
        for endpoint, limit in self.endpoint_limits.items():
            if path.startswith(endpoint):
                return limit
        
        # 返回默认限制
        return (self.default_limit, self.default_window)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过健康检查和监控端点
        if request.url.path in ['/health', '/health/detailed', '/health/metrics']:
            return await call_next(request)
        
        # 获取客户端标识和限制配置
        client_id = self._get_client_id(request)
        limit, window = self._get_limit(request.url.path)
        
        # 生成缓存键
        cache_key = f"{client_id}:{request.url.path}"
        
        try:
            cache = get_cache_service()
            
            # 获取当前计数
            current_count = await cache.get(cache_key)
            if current_count is None:
                current_count = 0
            
            # 检查是否超过限制
            if current_count >= limit:
                logger.warning(f"速率限制触发: {client_id} -> {request.url.path} ({current_count}/{limit})")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {limit} requests per {window} seconds."
                )
            
            # 增加计数
            await cache.set(cache_key, current_count + 1, expire=window)
            
            # 处理请求
            response = await call_next(request)
            
            # 添加速率限制响应头
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit - current_count - 1))
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"速率限制中间件错误: {e}")
            # 出错时不阻止请求
            return await call_next(request)

