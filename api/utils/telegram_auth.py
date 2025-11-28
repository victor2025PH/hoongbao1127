"""
Telegram 認證工具
從 initData 中解析用戶 ID
"""
from fastapi import Header, HTTPException
from typing import Optional
import urllib.parse
import json
from loguru import logger


def parse_telegram_init_data(init_data: str) -> Optional[dict]:
    """解析 Telegram initData 字符串"""
    try:
        # initData 格式: key1=value1&key2=value2&hash=...
        params = urllib.parse.parse_qs(init_data)
        
        # 解析 user 字段（如果存在）
        user_str = params.get('user', [None])[0]
        if user_str:
            user_data = json.loads(user_str)
            return user_data
        return None
    except Exception as e:
        logger.warning(f"Failed to parse initData: {e}")
        return None


def get_tg_id_from_header(
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")
) -> Optional[int]:
    """從請求頭中獲取 Telegram 用戶 ID"""
    if not x_telegram_init_data:
        return None
    
    try:
        user_data = parse_telegram_init_data(x_telegram_init_data)
        if user_data and 'id' in user_data:
            return int(user_data['id'])
    except Exception as e:
        logger.warning(f"Failed to extract tg_id from header: {e}")
    
    return None

