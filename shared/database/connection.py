"""
Lucky Red (搶紅包) - 數據庫連接
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator
from pathlib import Path
import os

from shared.config.settings import get_settings
from shared.database.models import Base

settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 獲取數據庫 URL，支持 SQLite 本地開發
database_url = settings.DATABASE_URL

# 檢查是否使用 SQLite（本地開發）
is_sqlite = database_url.startswith("sqlite")

if is_sqlite:
    # SQLite 配置
    # 确保使用绝对路径
    if database_url.startswith("sqlite:///./"):
        # 相对路径，转换为绝对路径
        db_path = database_url.replace("sqlite:///./", "")
        db_abs_path = str(BASE_DIR / db_path)
        database_url = f"sqlite:///{db_abs_path}"
    
    sync_engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},  # SQLite 需要這個參數
    )
    
    # SQLite 異步需要 aiosqlite
    # 使用绝对路径
    async_database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    async_engine = create_async_engine(
        async_database_url,
        connect_args={"check_same_thread": False},
        echo=False,  # 调试时可以设为 True
    )
else:
    # PostgreSQL 配置
    # 同步引擎 (用於 Bot)
    sync_engine = create_engine(
        database_url.replace("postgresql://", "postgresql+psycopg2://"),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    
    # 異步引擎 (用於 API)
    async_engine = create_async_engine(
        database_url.replace("postgresql://", "postgresql+asyncpg://"),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def init_db():
    """初始化數據庫表"""
    Base.metadata.create_all(bind=sync_engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """獲取同步數據庫會話"""
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """獲取異步數據庫會話"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依賴注入用"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

