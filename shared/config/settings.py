"""
Lucky Red (搶紅包) - 全局配置
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

# 項目根目錄
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# .env 文件路徑
ENV_FILE = BASE_DIR / ".env"

# 確保 .env 文件被加載（在類定義之前）
# 使用 dotenv 手動加載，確保環境變量被設置
_loaded_env = False
if ENV_FILE.exists():
    try:
        from dotenv import load_dotenv
        # 加載 .env 文件到環境變量
        load_dotenv(dotenv_path=ENV_FILE, override=True)
        _loaded_env = True
    except ImportError:
        # 如果 dotenv 未安裝，嘗試使用 pydantic-settings 的內置支持
        pass


class Settings(BaseSettings):
    """應用配置"""
    
    model_config = SettingsConfigDict(
        # 使用絕對路徑，如果文件存在
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        # 允許從環境變量讀取
        env_ignore_empty=False  # 改為 False，確保空值也被讀取
    )
    
    # 項目信息
    APP_NAME: str = "Lucky Red"
    APP_NAME_ZH: str = "搶紅包"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Telegram Bot
    # pydantic-settings 會自動從環境變量讀取（通過 model_config.env_file）
    # 如果環境變量不存在，使用空字符串作為默認值
    BOT_TOKEN: str = ""
    BOT_USERNAME: str = ""
    
    # 管理員
    ADMIN_IDS: str = ""
    
    @property
    def admin_id_list(self) -> List[int]:
        """解析管理員 ID 列表"""
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]
    
    # 數據庫
    DATABASE_URL: str = "postgresql://luckyred:LuckyRed2025!@localhost:5432/luckyred"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    
    # JWT
    JWT_SECRET: str = "change-this-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    
    # 域名
    BOT_DOMAIN: str = "bot.usdt2026.cc"
    ADMIN_DOMAIN: str = "admin.usdt2026.cc"
    MINIAPP_DOMAIN: str = "mini.usdt2026.cc"
    MINIAPP_URL: str = "https://mini.usdt2026.cc"
    
    # 遊戲
    GAME_URL: str = ""
    
    # 日誌
    LOG_LEVEL: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    """獲取配置單例"""
    return Settings()

