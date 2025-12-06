"""
监控告警服务
用于发送系统告警通知
"""
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from shared.config.settings import get_settings
from api.services.cache_service import get_cache_service

settings = get_settings()


class AlertService:
    """告警服务"""
    
    def __init__(self):
        self.alert_cache = {}  # 防止重复告警
        self.alert_cooldown = 300  # 5 分钟内不重复发送相同告警
    
    def _get_alert_key(self, alert_type: str, details: str) -> str:
        """生成告警键"""
        return f"alert:{alert_type}:{hash(details)}"
    
    async def _should_send_alert(self, alert_key: str) -> bool:
        """检查是否应该发送告警（防止重复）"""
        cache = get_cache_service()
        last_sent = await cache.get(alert_key)
        
        if last_sent:
            return False
        
        # 记录告警已发送
        await cache.set(alert_key, True, expire=self.alert_cooldown)
        return True
    
    async def send_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "warning",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        发送告警
        
        Args:
            alert_type: 告警类型（error, warning, info）
            message: 告警消息
            severity: 严重程度（critical, error, warning, info）
            details: 详细信息
        """
        alert_key = self._get_alert_key(alert_type, message)
        
        # 检查是否应该发送
        if not await self._should_send_alert(alert_key):
            logger.debug(f"告警已发送过，跳过: {alert_type}")
            return
        
        # 记录告警
        logger.warning(f"🚨 告警 [{severity.upper()}]: {message}")
        if details:
            logger.warning(f"详细信息: {details}")
        
        # 根据严重程度决定是否发送通知
        if severity in ["critical", "error"]:
            await self._send_notification(alert_type, message, severity, details)
    
    async def _send_notification(
        self,
        alert_type: str,
        message: str,
        severity: str,
        details: Optional[Dict[str, Any]]
    ):
        """发送通知（邮件、Telegram 等）"""
        # TODO: 实现邮件通知
        # TODO: 实现 Telegram Bot 通知
        # TODO: 实现 Webhook 通知
        
        # 目前只记录日志
        logger.info(f"通知发送: {alert_type} - {message}")
    
    async def check_system_health(self):
        """检查系统健康状态"""
        from api.routers.health import detailed_health_check
        from shared.database.connection import get_db_session
        
        try:
            # 检查数据库
            async for db in get_db_session():
                try:
                    from sqlalchemy import text
                    result = await db.execute(text("SELECT 1"))
                    result.scalar()
                except Exception as e:
                    await self.send_alert(
                        "database_error",
                        f"数据库连接失败: {str(e)}",
                        severity="critical",
                        details={"error": str(e)}
                    )
                finally:
                    await db.close()
                    break
            
            # 检查 Redis（如果配置）
            if settings.REDIS_URL:
                cache = get_cache_service()
                try:
                    # 尝试设置和获取一个测试值
                    test_key = "health_check_test"
                    await cache.set(test_key, "test", expire=10)
                    value = await cache.get(test_key)
                    if value != "test":
                        await self.send_alert(
                            "redis_error",
                            "Redis 缓存异常",
                            severity="warning"
                        )
                except Exception as e:
                    await self.send_alert(
                        "redis_error",
                        f"Redis 连接失败: {str(e)}",
                        severity="warning",
                        details={"error": str(e)}
                    )
        
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
    
    async def check_error_rate(self, error_count: int, time_window: int = 60):
        """检查错误率"""
        if error_count > 10:  # 1 分钟内超过 10 个错误
            await self.send_alert(
                "high_error_rate",
                f"错误率过高: {error_count} 个错误/{time_window}秒",
                severity="error",
                details={"error_count": error_count, "time_window": time_window}
            )
    
    async def check_slow_requests(self, slow_count: int, threshold: float = 1.0):
        """检查慢请求"""
        if slow_count > 5:  # 超过 5 个慢请求
            await self.send_alert(
                "slow_requests",
                f"慢请求过多: {slow_count} 个请求超过 {threshold} 秒",
                severity="warning",
                details={"slow_count": slow_count, "threshold": threshold}
            )


# 全局告警服务实例
_alert_service: Optional[AlertService] = None


def get_alert_service() -> AlertService:
    """获取告警服务实例"""
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service

