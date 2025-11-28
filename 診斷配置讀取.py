#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""診斷配置讀取問題"""
import sys
import os
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("配置讀取診斷")
print("=" * 60)
print()

# 1. 檢查 .env 文件
from shared.config.settings import ENV_FILE
print(f"1. .env 文件路徑: {ENV_FILE}")
print(f"   文件存在: {ENV_FILE.exists()}")
print()

if ENV_FILE.exists():
    print("2. .env 文件內容（BOT_TOKEN 相關行）:")
    try:
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if 'BOT_TOKEN' in line.upper():
                    print(f"   第 {i} 行: {line.strip()}")
    except Exception as e:
        print(f"   讀取失敗: {e}")
    print()

# 3. 檢查環境變量（dotenv 加載後）
print("3. 環境變量檢查:")
try:
    from dotenv import load_dotenv
    print("   dotenv 模組已導入")
    if ENV_FILE.exists():
        load_dotenv(dotenv_path=ENV_FILE, override=True)
        print("   已執行 load_dotenv")
        bot_token_env = os.getenv("BOT_TOKEN")
        if bot_token_env:
            print(f"   ✅ 環境變量 BOT_TOKEN: {bot_token_env[:20]}...")
        else:
            print("   ❌ 環境變量 BOT_TOKEN: 未設置")
except ImportError:
    print("   ❌ dotenv 模組未安裝")
except Exception as e:
    print(f"   ❌ 加載失敗: {e}")
print()

# 4. 測試 Settings 讀取
print("4. Settings 讀取測試:")
try:
    from shared.config.settings import get_settings
    settings = get_settings()
    print(f"   BOT_TOKEN 長度: {len(settings.BOT_TOKEN)}")
    if settings.BOT_TOKEN:
        print(f"   ✅ BOT_TOKEN: {settings.BOT_TOKEN[:20]}...")
    else:
        print("   ❌ BOT_TOKEN: 空")
        print()
        print("   可能的原因:")
        print("   1. .env 文件格式不正確")
        print("   2. dotenv 未正確加載")
        print("   3. pydantic-settings 未讀取環境變量")
except Exception as e:
    print(f"   ❌ 讀取失敗: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)

