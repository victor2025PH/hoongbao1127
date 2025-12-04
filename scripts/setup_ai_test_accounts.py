"""
AI 系統對接 - 測試帳號設置腳本

用途：
1. 為用戶充值測試餘額
2. 批量創建/註冊 AI 帳號
3. 為 AI 帳號充值

使用方法：
    python scripts/setup_ai_test_accounts.py

文件路徑：c:\hbgm001\scripts\setup_ai_test_accounts.py
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# 添加項目根目錄
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from shared.database.connection import get_db, async_session_factory
from shared.database.models import User, Transaction, CurrencyType


async def get_or_create_user(db, tg_id: int, username: str = None, first_name: str = None) -> User:
    """獲取或創建用戶"""
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            tg_id=tg_id,
            username=username or f"ai_user_{tg_id}",
            first_name=first_name or f"AI User {tg_id}",
            balance_usdt=Decimal("0"),
            balance_ton=Decimal("0"),
            balance_stars=0,
            balance_points=0,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"✅ 創建新用戶: tg_id={tg_id}, username={user.username}")
    else:
        print(f"📌 用戶已存在: tg_id={tg_id}, username={user.username}")
    
    return user


async def add_balance(db, user: User, currency: str, amount: Decimal, note: str = "測試充值"):
    """為用戶添加餘額"""
    balance_field = f"balance_{currency}"
    current_balance = getattr(user, balance_field) or Decimal("0")
    new_balance = current_balance + amount
    
    setattr(user, balance_field, new_balance)
    
    # 創建交易記錄
    transaction = Transaction(
        user_id=user.id,
        type="deposit",
        currency=CurrencyType(currency),
        amount=amount,
        balance_before=current_balance,
        balance_after=new_balance,
        ref_id=f"ai_test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        note=note,
        status="completed"
    )
    db.add(transaction)
    await db.commit()
    
    print(f"💰 充值成功: {user.username} +{amount} {currency.upper()} (餘額: {new_balance})")


async def setup_test_user(tg_id: int, usdt_amount: float = 100.0):
    """設置測試用戶"""
    async with async_session_factory() as db:
        user = await get_or_create_user(db, tg_id)
        await add_balance(db, user, "usdt", Decimal(str(usdt_amount)), "AI 對接測試充值")
        return user


async def setup_ai_accounts(ai_tg_ids: list, usdt_amount: float = 50.0):
    """批量設置 AI 帳號"""
    async with async_session_factory() as db:
        results = []
        for i, tg_id in enumerate(ai_tg_ids, 1):
            username = f"ai_player_{i}"
            first_name = f"AI Player {i}"
            
            user = await get_or_create_user(db, tg_id, username, first_name)
            await add_balance(db, user, "usdt", Decimal(str(usdt_amount)), f"AI 帳號 {i} 測試充值")
            
            results.append({
                "tg_id": tg_id,
                "username": user.username,
                "balance_usdt": float(user.balance_usdt)
            })
        
        return results


async def show_user_balance(tg_id: int):
    """顯示用戶餘額"""
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"\n📊 用戶餘額 (tg_id: {tg_id})")
            print(f"   USDT: {user.balance_usdt}")
            print(f"   TON:  {user.balance_ton}")
            print(f"   Stars: {user.balance_stars}")
            print(f"   Points: {user.balance_points}")
        else:
            print(f"❌ 用戶不存在: {tg_id}")


async def main():
    """主函數"""
    print("=" * 60)
    print("🤖 AI 系統對接 - 測試帳號設置")
    print("=" * 60)
    
    # 1. 設置真實測試用戶 (由 AI 聊天後台提供的 Telegram ID)
    test_user_tg_id = 5433982810
    print(f"\n📌 設置測試用戶: {test_user_tg_id}")
    await setup_test_user(test_user_tg_id, usdt_amount=100.0)
    
    # 2. 設置 AI 帳號（示例：生成 5 個測試 AI 帳號）
    # 實際使用時，請替換為真實的 AI Telegram ID
    ai_test_ids = [
        1000000001,  # AI 帳號 1
        1000000002,  # AI 帳號 2
        1000000003,  # AI 帳號 3
        1000000004,  # AI 帳號 4
        1000000005,  # AI 帳號 5
    ]
    
    print(f"\n📌 設置 AI 帳號: {len(ai_test_ids)} 個")
    await setup_ai_accounts(ai_test_ids, usdt_amount=50.0)
    
    # 3. 顯示所有帳號餘額
    print("\n" + "=" * 60)
    print("📊 帳號餘額總覽")
    print("=" * 60)
    
    await show_user_balance(test_user_tg_id)
    for tg_id in ai_test_ids:
        await show_user_balance(tg_id)
    
    print("\n✅ 設置完成！")
    print("\n📝 下一步：")
    print("   1. 啟動 API 服務器: python -m api.main")
    print("   2. 測試 API 連通性: curl http://localhost:8080/api/v2/ai/status")
    print("   3. 開始對接測試")


if __name__ == "__main__":
    asyncio.run(main())
